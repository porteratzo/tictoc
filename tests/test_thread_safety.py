"""Thread-safety tests for the porter_bench library.

Covers:
- Distinct benchmarkers per thread (original pattern)
- Shared benchmarker accessed from multiple threads
- enable/disable race conditions
- Concurrent save() under active writes
"""

import threading
import time

import pytest

from porter_bench.Benchmarker import Benchmarker
from porter_bench.GlobalBenchmarker import GlobalBenchmarker


class TestDistinctBenchmarkersConcurrency:
    """Each thread operates exclusively on its own named benchmarker."""

    def test_concurrent_distinct_benchmarkers(self, tmp_global):
        errors: list[Exception] = []
        num_workers = 10
        num_iterations = 30
        true_total_iterations = (
            num_iterations + num_iterations // 5
        )  # account for extra checkpoint steps

        def worker(worker_id: int) -> None:
            try:
                for i in range(num_iterations):
                    b = tmp_global[f"worker_{worker_id}"]
                    b.gstep()
                    b.step("op_a")
                    b.step("op_b")
                    b.gstop()
                    if i % 5 == 0:
                        b.gstep()
                        b.step("checkpoint")
                        b.gstop()
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=(i,)) for i in range(num_workers)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"

        for i in range(num_workers):
            b = tmp_global[f"worker_{i}"]
            assert len(b.time_benchmaker.step_dict_list) == true_total_iterations


class TestSharedBenchmarkerConcurrency:
    """Multiple threads write to the same Benchmarker instance."""

    def test_shared_benchmarker_data_integrity(self, bench_file):
        b = Benchmarker(bench_file)
        errors: list[Exception] = []
        num_threads = 5
        num_iterations = 20

        def worker() -> None:
            try:
                for _ in range(num_iterations):
                    b.start()
                    b.step("work")
                    b.gstop()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        total = len(b.time_benchmaker.step_dict_list)
        assert total == num_threads * num_iterations

    def test_enable_disable_toggle_while_writing(self, bench_file):
        """Toggling enable/disable from one thread must not crash writer threads."""
        b = Benchmarker(bench_file)
        errors: list[Exception] = []
        stop_event = threading.Event()

        def writer() -> None:
            try:
                while not stop_event.is_set():
                    b.start()
                    b.step("work")
                    b.gstop()
            except Exception as e:
                errors.append(e)

        def toggler() -> None:
            for _ in range(20):
                b.disable()
                time.sleep(0.001)
                b.enable()
                time.sleep(0.001)

        writers = [threading.Thread(target=writer) for _ in range(3)]
        toggler_thread = threading.Thread(target=toggler)

        for t in writers:
            t.start()
        toggler_thread.start()
        toggler_thread.join()
        stop_event.set()
        for t in writers:
            t.join()

        assert not errors, f"Thread errors: {errors}"

    def test_concurrent_save_does_not_crash(self, bench_file, mock_memory):
        """Calling save_data() from one thread while writers are active must not raise."""
        b = Benchmarker(bench_file)
        b.enable_memory_tracking()
        errors: list[Exception] = []
        stop_event = threading.Event()

        def writer() -> None:
            try:
                while not stop_event.is_set():
                    b.start()
                    b.step("work")
                    b.gstop()
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        def saver() -> None:
            for _ in range(5):
                try:
                    b.save_data()
                    time.sleep(0.005)
                except Exception as e:
                    errors.append(e)

        writers = [threading.Thread(target=writer) for _ in range(3)]
        saver_thread = threading.Thread(target=saver)

        for t in writers:
            t.start()
        saver_thread.start()
        saver_thread.join()
        stop_event.set()
        for t in writers:
            t.join()

        assert not errors, f"Thread errors: {errors}"

    def test_global_benchmarker_concurrent_getitem(self, tmp_global):
        """Concurrent __getitem__ for new and existing keys must not corrupt state."""
        errors: list[Exception] = []

        def accessor(name: str, n: int) -> None:
            try:
                for _ in range(n):
                    b = tmp_global[name]
                    b.start()
                    b.step("x")
                    b.gstop()
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=accessor, args=(f"key_{i}", 20)) for i in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"

    def test_save_on_gstop_concurrent_writes(self, bench_file, mock_memory):
        """auto-save on every gstop from multiple threads must produce valid JSON."""
        import json

        b = Benchmarker(bench_file, save_on_gstop=1)
        b.enable_memory_tracking()
        errors: list[Exception] = []
        num_threads = 4
        num_iters = 15

        def worker() -> None:
            try:
                for _ in range(num_iters):
                    b.start()
                    b.step("t")
                    b.gstop()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"

        # The JSON files should still be parseable after concurrent saves
        with open(bench_file + "_STEP_DICT_DATA.json") as f:
            data = json.load(f)
        assert isinstance(data, list)
