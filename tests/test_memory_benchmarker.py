"""Tests for MemoryBenchmarker and MaxMemoryMonitor."""

import threading
import time

import pytest

from porter_bench.MemoryBenchmarker import (
    TICTOC_CUDA_AVAILABLE,
    MaxMemoryMonitor,
    MemoryBenchmarker,
)


class TestMemoryBenchmarkerLifecycle:
    def test_start_gstop_appends_one_entry(self, mock_memory):
        mb = MemoryBenchmarker()
        mb.start()
        mb.gstop()
        assert len(mb.memory_usage_list) == 1

    def test_gstop_without_start_is_noop(self, mock_memory):
        mb = MemoryBenchmarker()
        mb.gstop()
        assert len(mb.memory_usage_list) == 0

    def test_disable_prevents_accumulation(self, mock_memory):
        mb = MemoryBenchmarker()
        mb.disable()
        mb.start()
        mb.gstop()
        assert len(mb.memory_usage_list) == 0

    def test_gstop_records_rss_value(self, mock_memory):
        mb = MemoryBenchmarker()
        mb.start()
        mb.gstop()
        record = mb.memory_usage_list[0]["gstop"][0]
        assert record["total memory usage"] == 100 * 1024 * 1024

    def test_gstep_resets_memory_usage_does_not_append(self, mock_memory):
        """MemoryBenchmarker.gstep() is a reset/start only; it does not save."""
        mb = MemoryBenchmarker()
        mb.start()
        mb.gstep()
        assert len(mb.memory_usage_list) == 0
        # But the new dict should already have a 'gstep' key
        assert "gstep" in mb.memory_usage

    def test_multiple_iterations_via_start_gstop(self, mock_memory):
        mb = MemoryBenchmarker()
        for _ in range(3):
            mb.start()
            mb.gstop()
        assert len(mb.memory_usage_list) == 3


class TestMemoryBenchmarkerStepTracking:
    def test_step_without_tracking_not_recorded(self, mock_memory):
        mb = MemoryBenchmarker()
        mb.start()
        mb.step("work")
        mb.gstop()
        # 'work' must NOT appear because track_memory_in_step is False by default
        assert "work" not in mb.memory_usage_list[0]

    def test_step_with_tracking_is_recorded(self, mock_memory):
        mb = MemoryBenchmarker()
        mb.enable_memory_tracking_in_step()
        mb.start()
        mb.step("work")
        mb.gstop()
        assert "work" in mb.memory_usage_list[0]

    def test_step_tracking_rss_value(self, mock_memory):
        mb = MemoryBenchmarker()
        mb.enable_memory_tracking_in_step()
        mb.start()
        mb.step("task")
        mb.gstop()
        record = mb.memory_usage_list[0]["task"][0]
        assert record["total memory usage"] == 100 * 1024 * 1024

    def test_crono_counter_increments_across_steps(self, mock_memory):
        mb = MemoryBenchmarker()
        mb.enable_memory_tracking_in_step()
        mb.start()
        mb.step("a")
        mb.step("b")
        mb.gstop()
        assert mb.memory_usage_list[0]["a"][0]["crono_counter"] == 0
        assert mb.memory_usage_list[0]["b"][0]["crono_counter"] == 1


@pytest.mark.skipif(not TICTOC_CUDA_AVAILABLE, reason="CUDA not available")
class TestCudaMemoryTracking:
    def test_cuda_memory_usage_keys(self):
        mb = MemoryBenchmarker()
        result = mb.get_cuda_memory_usage()
        for key in ("allocated", "reserved", "max_allocated", "max_reserved"):
            assert key in result

    def test_enable_cuda_tracking_sets_flag(self):
        mb = MemoryBenchmarker()
        mb.enable_cuda_memory_tracking()
        assert mb.track_cuda_memory


class TestMaxMemoryMonitor:
    def test_start_and_stop_no_thread_leak(self):
        before = threading.active_count()
        monitor = MaxMemoryMonitor(poll_time=0.01)
        monitor.start()
        assert threading.active_count() > before
        monitor.stop()
        time.sleep(0.05)  # Allow thread to terminate
        assert threading.active_count() == before

    def test_step_returns_non_negative(self):
        monitor = MaxMemoryMonitor(poll_time=0.01)
        monitor.start()
        time.sleep(0.05)
        result = monitor.step()
        monitor.stop()
        assert result >= 0

    def test_step_resets_peak(self):
        monitor = MaxMemoryMonitor(poll_time=0.01)
        monitor.start()
        time.sleep(0.05)
        first = monitor.step()
        second = monitor.step()
        monitor.stop()
        # After a reset the new peak is measured from scratch; both should be valid
        assert first >= 0
        assert second >= 0
