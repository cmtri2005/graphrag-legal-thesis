"""Parse and summarize Docker runtime metrics for graph-stack measurements."""
from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any


_SIZE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGT]?i?B)\s*$", re.IGNORECASE)
_UNITS = {
    "b": 1,
    "kb": 1_000,
    "mb": 1_000**2,
    "gb": 1_000**3,
    "tb": 1_000**4,
    "kib": 1 << 10,
    "mib": 1 << 20,
    "gib": 1 << 30,
    "tib": 1 << 40,
}


def parse_size(value: str) -> int:
    """Convert the human-readable size emitted by ``docker stats`` to bytes."""
    match = _SIZE.fullmatch(value)
    if match is None:
        raise ValueError(f"unsupported Docker size: {value!r}")
    return round(float(match.group(1)) * _UNITS[match.group(2).lower()])


def parse_percent(value: str) -> float:
    if not value.endswith("%"):
        raise ValueError(f"unsupported Docker percentage: {value!r}")
    try:
        return float(value[:-1])
    except ValueError as exc:
        raise ValueError(f"unsupported Docker percentage: {value!r}") from exc


def parse_stats_lines(lines: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Parse one ``docker stats --no-stream --format '{{json .}}'`` sample."""
    parsed: dict[str, dict[str, Any]] = {}
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("docker stats did not emit JSON lines") from exc
        name = row.get("Name") or row.get("Container")
        memory = row.get("MemUsage")
        if not isinstance(name, str) or not isinstance(memory, str) or "/" not in memory:
            raise ValueError("docker stats row lacks Name or MemUsage")
        used, limit = (part.strip() for part in memory.split("/", 1))
        if name in parsed:
            raise ValueError(f"duplicate Docker stats row for {name}")
        parsed[name] = {
            "memory_bytes": parse_size(used),
            "memory_limit_bytes": parse_size(limit),
            "memory_percent": parse_percent(str(row.get("MemPerc", ""))),
            "cpu_percent": parse_percent(str(row.get("CPUPerc", ""))),
            "pids": int(row["PIDs"]) if str(row.get("PIDs", "")).isdigit() else None,
        }
    if not parsed:
        raise ValueError("docker stats returned no container rows")
    return parsed


def summarize_samples(
    samples: list[dict[str, dict[str, Any]]], expected_names: Iterable[str]
) -> dict[str, Any]:
    """Return start/final/peak memory and CPU without hiding missing samples."""
    if not samples:
        raise ValueError("at least one Docker stats sample is required")
    expected = tuple(expected_names)
    for index, sample in enumerate(samples, 1):
        missing = set(expected) - set(sample)
        if missing:
            raise ValueError(
                f"Docker stats sample {index} misses containers: {', '.join(sorted(missing))}"
            )
    containers = {}
    for name in expected:
        rows = [sample[name] for sample in samples]
        containers[name] = {
            "start_memory_bytes": rows[0]["memory_bytes"],
            "final_memory_bytes": rows[-1]["memory_bytes"],
            "peak_memory_bytes": max(row["memory_bytes"] for row in rows),
            "memory_limit_bytes": rows[-1]["memory_limit_bytes"],
            "peak_memory_percent": max(row["memory_percent"] for row in rows),
            "peak_cpu_percent": max(row["cpu_percent"] for row in rows),
            "final_pids": rows[-1]["pids"],
        }
    return {
        "sample_count": len(samples),
        "containers": containers,
        "start_memory_bytes": sum(item["start_memory_bytes"] for item in containers.values()),
        "final_memory_bytes": sum(item["final_memory_bytes"] for item in containers.values()),
        "peak_memory_bytes_sum": sum(item["peak_memory_bytes"] for item in containers.values()),
    }


def parse_inspect(payload: str, expected_names: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Keep the small subset of ``docker inspect`` that proves run health."""
    try:
        rows = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("docker inspect did not emit JSON") from exc
    if not isinstance(rows, list):
        raise ValueError("docker inspect payload must be a list")
    parsed = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("docker inspect row must be an object")
        name = str(row.get("Name", "")).removeprefix("/")
        state = row.get("State")
        if not name or not isinstance(state, dict):
            raise ValueError("docker inspect row lacks Name or State")
        health = state.get("Health") or {}
        parsed[name] = {
            "status": state.get("Status"),
            "running": state.get("Running"),
            "oom_killed": state.get("OOMKilled"),
            "exit_code": state.get("ExitCode"),
            "health": health.get("Status"),
            "restart_count": row.get("RestartCount"),
            "image": row.get("Config", {}).get("Image"),
        }
    missing = set(expected_names) - set(parsed)
    if missing:
        raise ValueError(f"docker inspect misses containers: {', '.join(sorted(missing))}")
    return {name: parsed[name] for name in expected_names}
