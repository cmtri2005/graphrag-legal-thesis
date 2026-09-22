import json

import pytest

from legal_crawler.graph.resource_metrics import (
    parse_inspect, parse_size, parse_stats_lines, summarize_samples,
)


@pytest.mark.parametrize(("raw", "expected"), [
    ("0B", 0),
    ("512KiB", 512 * 1024),
    ("1.5MiB", round(1.5 * (1 << 20))),
    ("2GiB", 2 * (1 << 30)),
    ("1.2GB", round(1.2 * 1_000**3)),
])
def test_parse_docker_size(raw, expected):
    assert parse_size(raw) == expected


def test_parse_one_docker_stats_sample():
    row = {
        "Name": "legal-kg-neo4j", "MemUsage": "1.25GiB / 4GiB",
        "MemPerc": "31.25%", "CPUPerc": "2.50%", "PIDs": "87",
    }
    result = parse_stats_lines([json.dumps(row)])
    assert result["legal-kg-neo4j"] == {
        "memory_bytes": round(1.25 * (1 << 30)),
        "memory_limit_bytes": 4 * (1 << 30),
        "memory_percent": 31.25,
        "cpu_percent": 2.5,
        "pids": 87,
    }


def test_summary_keeps_start_final_and_peak_per_container():
    samples = [
        {"neo4j": {"memory_bytes": 100, "memory_limit_bytes": 1000,
                    "memory_percent": 10.0, "cpu_percent": 1.0, "pids": 10}},
        {"neo4j": {"memory_bytes": 300, "memory_limit_bytes": 1000,
                    "memory_percent": 30.0, "cpu_percent": 8.0, "pids": 12}},
        {"neo4j": {"memory_bytes": 200, "memory_limit_bytes": 1000,
                    "memory_percent": 20.0, "cpu_percent": 2.0, "pids": 11}},
    ]
    result = summarize_samples(samples, ["neo4j"])
    assert result["containers"]["neo4j"] == {
        "start_memory_bytes": 100, "final_memory_bytes": 200,
        "peak_memory_bytes": 300, "memory_limit_bytes": 1000,
        "peak_memory_percent": 30.0, "peak_cpu_percent": 8.0, "final_pids": 11,
    }


def test_summary_rejects_a_missing_container_sample():
    with pytest.raises(ValueError, match="misses containers: minio"):
        summarize_samples([{"neo4j": {}}], ["neo4j", "minio"])


def test_parse_inspect_exposes_health_oom_and_restart_evidence():
    payload = json.dumps([{
        "Name": "/legal-kg-neo4j", "RestartCount": 0,
        "State": {"Status": "running", "Running": True, "OOMKilled": False,
                  "ExitCode": 0, "Health": {"Status": "healthy"}},
        "Config": {"Image": "neo4j:5.24.2-community"},
    }])
    assert parse_inspect(payload, ["legal-kg-neo4j"])["legal-kg-neo4j"] == {
        "status": "running", "running": True, "oom_killed": False,
        "exit_code": 0, "health": "healthy", "restart_count": 0,
        "image": "neo4j:5.24.2-community",
    }
