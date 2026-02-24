"""Shared pytest fixtures for the porter_bench test suite."""

from unittest.mock import MagicMock

import pytest

from porter_bench.Benchmarker import Benchmarker
from porter_bench.GlobalBenchmarker import GlobalBenchmarker

# A simple relative file path used by most benchmarker fixtures.
# All I/O tests use monkeypatch.chdir(tmp_path) so writes land in tmp_path.
_BENCH_FILE = "run/test"


@pytest.fixture
def bench_file(tmp_path, monkeypatch):
    """Change cwd to tmp_path and return a relative benchmarker file path."""
    monkeypatch.chdir(tmp_path)
    return _BENCH_FILE


@pytest.fixture
def tmp_benchmarker(bench_file):
    """Return a fresh Benchmarker pointing at a temp directory."""
    return Benchmarker(bench_file)


@pytest.fixture
def mock_memory(monkeypatch):
    """Patch psutil.Process to return a fixed 100 MB RSS value.

    This keeps memory tests fast, hermetic, and independent of the host machine.
    """
    mock_proc = MagicMock()
    mock_proc.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
    monkeypatch.setattr("porter_bench.MemoryBenchmarker.psutil.Process", mock_proc)
    return mock_proc


@pytest.fixture
def tmp_global(tmp_path, monkeypatch):
    """Return a fresh GlobalBenchmarker writing to a temp directory."""
    monkeypatch.chdir(tmp_path)
    return GlobalBenchmarker()


@pytest.fixture
def saved_record(tmp_path, monkeypatch):
    """Run three benchmark iterations, save to disk, and return the root path.

    Memory tracking is intentionally left disabled: the start()+gstop() workflow
    does not bootstrap MemoryBenchmarker.started, so memory_usage_list stays
    empty. Tests that need memory data should use the gstep workflow directly.

    Uses a GlobalBenchmarker so that the directory layout matches what
    load_record() / get_latest_record() expect:
        <tmp_path>/TICTOC_PERFORMANCE/<timestamp>/test_*.json
    """
    monkeypatch.chdir(tmp_path)
    gb = GlobalBenchmarker()
    for _ in range(3):
        gb["test"].start()
        gb["test"].step("work")
        gb["test"].step("io")
        gb["test"].gstop()
    gb.save()
    return tmp_path
