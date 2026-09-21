from types import SimpleNamespace

import pytest

import measure_graph_resources


class _RunningProcess:
    returncode = None

    def __init__(self):
        self.terminated = False
        self.waited = False

    def poll(self):
        return None

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        self.waited = True
        self.returncode = -15
        return self.returncode


def test_sampling_failure_terminates_loader_child(monkeypatch, tmp_path):
    process = _RunningProcess()
    monkeypatch.setattr(measure_graph_resources, "_loader_command", lambda _args, _path: [])
    monkeypatch.setattr(
        measure_graph_resources.subprocess, "Popen", lambda _command: process,
    )
    monkeypatch.setattr(measure_graph_resources.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        measure_graph_resources,
        "docker_stats",
        lambda: (_ for _ in ()).throw(RuntimeError("stats unavailable")),
    )
    args = SimpleNamespace(sample_interval=0.1)

    with pytest.raises(RuntimeError, match="stats unavailable"):
        measure_graph_resources._run_loader_while_sampling(
            args, tmp_path / "loader.json", [],
        )

    assert process.terminated
    assert process.waited
