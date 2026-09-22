#!/usr/bin/env python3
"""D6: measure the loaded Docker graph stack, optionally during a full reload.

The default mode is read-only: sample RAM/CPU for the four existing containers.
``--run-loader`` reruns the idempotent D2 loader against the existing Neo4j
volume while sampling. It never clears a database or removes a Docker volume.

The original cold-load duration is a separate measurement: recreating it needs
an explicitly isolated empty volume. Do not represent an idempotent MERGE pass
as a cold load in the Phase 3 report.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from legal_crawler.graph.resource_metrics import (
    parse_inspect, parse_stats_lines, summarize_samples,
)


CONTAINERS = (
    "legal-kg-neo4j",
    "legal-kg-milvus",
    "legal-kg-etcd",
    "legal-kg-minio",
)


def docker_stats(containers: tuple[str, ...] = CONTAINERS) -> dict[str, dict[str, Any]]:
    result = subprocess.run(
        ["docker", "stats", "--no-stream", "--format", "{{json .}}", *containers],
        check=True,
        text=True,
        capture_output=True,
    )
    return parse_stats_lines(result.stdout.splitlines())


def docker_state(containers: tuple[str, ...] = CONTAINERS) -> dict[str, dict[str, Any]]:
    result = subprocess.run(
        ["docker", "inspect", *containers], check=True, text=True, capture_output=True,
    )
    state = parse_inspect(result.stdout, containers)
    unhealthy = [
        name for name, item in state.items()
        if not item["running"] or item["oom_killed"] or item["health"] != "healthy"
    ]
    if unhealthy:
        raise ValueError(f"containers are not healthy for D6: {', '.join(unhealthy)}")
    return state


def host_info() -> dict[str, Any]:
    total_memory = None
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                total_memory = int(line.split()[1]) * 1024
                break
    return {
        "platform": platform.platform(),
        "logical_cpu_count": os.cpu_count(),
        "visible_memory_bytes": total_memory,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _loader_command(args: argparse.Namespace, report: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/pipeline/load_neo4j.py",
        "--data", str(args.data),
        "--index", str(args.index or args.data / "temporal.sqlite"),
        "--batch-size", str(args.batch_size),
        "--report", str(report),
    ]


def _run_loader_while_sampling(
    args: argparse.Namespace,
    loader_report: Path,
    samples: list[dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Run the idempotent loader and never leave its child process orphaned."""
    process = subprocess.Popen(_loader_command(args, loader_report))
    try:
        while process.poll() is None:
            time.sleep(args.sample_interval)
            samples.append(docker_stats())
        if process.returncode:
            raise RuntimeError(f"full-corpus loader exited with code {process.returncode}")
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise
    if not loader_report.is_file():
        raise RuntimeError("loader passed but did not write its timing report")
    return json.loads(loader_report.read_text(encoding="utf-8"))


def measure(args: argparse.Namespace) -> dict[str, Any]:
    state_before = docker_state()
    samples = [docker_stats()]
    loader = None
    mode = "loaded_stack_steady_state"
    started = time.monotonic()
    if args.run_loader:
        mode = "idempotent_full_corpus_reload"
        loader_report = args.report.with_name(args.report.stem + ".loader.json")
        loader_report.unlink(missing_ok=True)
        loader = _run_loader_while_sampling(args, loader_report, samples)
    while len(samples) < args.samples - 1:
        time.sleep(args.sample_interval)
        samples.append(docker_stats())
    samples.append(docker_stats())
    state_after = docker_state()
    return {
        "schema_version": 1,
        "check": "D6 graph-stack resources and full-corpus load time",
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "host": host_info(),
        "container_state_before": state_before,
        "container_state_after": state_after,
        "docker": summarize_samples(samples, CONTAINERS),
        "loader": loader,
        "notes": [
            "Docker memory is container cgroup usage from docker stats.",
            "Peak-memory sum is the sum of each container peak; peaks may occur at different instants.",
            "The loader mode is an idempotent MERGE pass over the full corpus, not an empty-volume cold load.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--index", type=Path, default=None)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--samples", type=int, default=3,
                        help="minimum samples including before/final observations")
    parser.add_argument("--sample-interval", type=float, default=5.0)
    parser.add_argument("--run-loader", action="store_true",
                        help="rerun full D2 MERGE loader while sampling; never clears data")
    parser.add_argument("--report", type=Path,
                        default=Path("data/derived/neo4j_resource_report.json"))
    args = parser.parse_args()
    if args.samples < 2:
        parser.error("--samples must be at least 2 (start and final)")
    if args.sample_interval <= 0:
        parser.error("--sample-interval must be positive")
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")
    try:
        report = measure(args)
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as exc:
        print(f"D6 FAIL: {exc}", file=sys.stderr)
        return 1
    write_report(args.report, report)
    memory = report["docker"]
    print(
        f"D6 PASS: mode={report['mode']}; samples={memory['sample_count']}; "
        f"final={memory['final_memory_bytes'] / (1 << 30):.2f} GiB; "
        f"sum-of-peaks={memory['peak_memory_bytes_sum'] / (1 << 30):.2f} GiB; "
        f"report={args.report}"
    )
    if report["loader"]:
        print(f"full-corpus MERGE={report['loader']['total_seconds']:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
