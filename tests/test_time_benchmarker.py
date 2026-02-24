"""Tests for TimeBenchmarker lifecycle, edge cases, and summurize()."""

import time

import pytest

from porter_bench.TimeBenchmarker import TimeBenchmarker, summurize


class TestTimeBenchmarkerLifecycle:
    def test_single_iteration_start_step_gstop(self):
        tb = TimeBenchmarker()
        tb.start()
        tb.step("work")
        tb.gstop()
        assert len(tb.step_dict_list) == 1
        entry = tb.step_dict_list[0]
        assert "work" in entry
        assert "GLOBAL" in entry

    def test_multiple_gstep_iterations(self):
        N = 5
        tb = TimeBenchmarker()
        tb.start()
        for _ in range(N):
            tb.step("work")
            tb.gstep()
        assert len(tb.step_dict_list) == N

    def test_gstop_without_start_is_noop(self):
        tb = TimeBenchmarker()
        tb.gstop()
        assert len(tb.step_dict_list) == 0

    def test_multiple_calls_same_step_name_accumulate(self):
        """Multiple step() calls with the same name must all be stored."""
        tb = TimeBenchmarker()
        tb.start()
        tb.step("work")
        tb.step("work")
        tb.step("work")
        tb.gstop()
        assert len(tb.step_dict_list[0]["work"]) == 3

    def test_crono_counter_increments_per_step(self):
        tb = TimeBenchmarker()
        tb.start()
        tb.step("a")
        tb.step("b")
        tb.gstop()
        entry = tb.step_dict_list[0]
        assert entry["a"][0]["crono_counter"] == 0
        assert entry["b"][0]["crono_counter"] == 1

    def test_crono_counter_resets_on_gstep(self):
        tb = TimeBenchmarker()
        tb.start()
        tb.step("a")
        tb.gstep()
        tb.step("b")
        tb.gstep()
        # Second iteration: crono_counter should restart at 0
        assert tb.step_dict_list[1]["b"][0]["crono_counter"] == 0

    def test_disable_prevents_accumulation(self):
        tb = TimeBenchmarker()
        tb.disable()
        tb.start()
        tb.step("work")
        tb.gstop()
        assert len(tb.step_dict_list) == 0

    def test_enable_after_disable_resumes(self):
        tb = TimeBenchmarker()
        tb.disable()
        tb.start()
        tb.step("work")
        tb.gstop()
        assert len(tb.step_dict_list) == 0

        tb.enable()
        tb.start()
        tb.step("work")
        tb.gstop()
        assert len(tb.step_dict_list) == 1

    def test_global_key_always_present_after_gstop(self):
        tb = TimeBenchmarker()
        tb.start()
        tb.gstop()
        assert "GLOBAL" in tb.step_dict_list[0]

    def test_extra_data_stored_in_step(self):
        tb = TimeBenchmarker()
        tb.start()
        tb.step("work", extra={"key": "value"})
        tb.gstop()
        assert tb.step_dict_list[0]["work"][0]["extra"] == {"key": "value"}

    def test_step_time_is_positive_float(self):
        tb = TimeBenchmarker()
        tb.start()
        time.sleep(0.005)
        tb.step("work")
        tb.gstop()
        assert tb.step_dict_list[0]["work"][0]["time"] > 0

    def test_gstep_finalises_previous_and_starts_new(self):
        tb = TimeBenchmarker()
        tb.start()
        tb.step("iter_0")
        tb.gstep()  # closes iter_0, opens iter_1
        tb.step("iter_1")
        tb.gstep()  # closes iter_1, opens iter_2
        assert len(tb.step_dict_list) == 2
        assert "iter_0" in tb.step_dict_list[0]
        assert "iter_1" in tb.step_dict_list[1]


class TestSummurize:
    def _build_step_dict_list(self, n_iters: int = 5):
        """Build a step_dict_list with real timings via TimeBenchmarker."""
        tb = TimeBenchmarker()
        for _ in range(n_iters):
            tb.start()
            time.sleep(0.001)
            tb.step("task_a")
            time.sleep(0.001)
            tb.step("task_b")
            tb.gstop()
        return tb.step_dict_list

    def test_returns_expected_step_keys(self):
        df_means, _ = summurize(self._build_step_dict_list())
        assert "task_a" in df_means
        assert "task_b" in df_means
        assert "GLOBAL" in df_means

    def test_stats_fields_present(self):
        df_means, _ = summurize(self._build_step_dict_list())
        for stats in df_means.values():
            assert "mean" in stats
            assert "min" in stats
            assert "max" in stats
            assert "quantile_filtered" in stats

    def test_mean_within_min_max(self):
        df_means, _ = summurize(self._build_step_dict_list())
        for stats in df_means.values():
            assert stats["min"] <= stats["mean"] <= stats["max"]

    def test_global_is_last_key(self):
        df_means, _ = summurize(self._build_step_dict_list())
        keys = list(df_means.keys())
        assert keys[-1] == "GLOBAL"

    def test_series_reflects_all_iterations(self):
        n = 4
        _, series = summurize(self._build_step_dict_list(n_iters=n))
        for step in ("task_a", "task_b"):
            assert len(series[step]) == n

    def test_empty_list_returns_empty_dicts(self):
        df_means, series = summurize([])
        assert df_means == {}
        assert len(series) == 0
