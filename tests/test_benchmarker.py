"""Tests for the Benchmarker facade (time + memory combined)."""

import json
import os

import pytest

from porter_bench.Benchmarker import Benchmarker


class TestBenchmarkerDefaults:
    def test_memory_disabled_by_default(self, tmp_benchmarker):
        assert not tmp_benchmarker.memory_benchmaker._enable

    def test_enabled_by_default(self, tmp_benchmarker):
        assert tmp_benchmarker.enabled

    def test_enable_memory_tracking_enables_sub_benchmarker(
        self, tmp_benchmarker, mock_memory
    ):
        tmp_benchmarker.enable_memory_tracking()
        assert tmp_benchmarker.memory_benchmaker._enable

    def test_enable_memory_per_step_sets_flag(self, tmp_benchmarker, mock_memory):
        tmp_benchmarker.enable_memory_tracking(per_step=True)
        assert tmp_benchmarker.memory_benchmaker.track_memory_in_step


class TestBenchmarkerLifecycle:
    def test_start_step_gstop_records_one_entry(self, tmp_benchmarker):
        tmp_benchmarker.start()
        tmp_benchmarker.step("work")
        tmp_benchmarker.gstop()
        assert len(tmp_benchmarker.time_benchmaker.step_dict_list) == 1

    def test_gstep_records_multiple_iterations(self, tmp_benchmarker):
        N = 4
        tmp_benchmarker.start()
        for _ in range(N):
            tmp_benchmarker.step("work")
            tmp_benchmarker.gstep()
        assert len(tmp_benchmarker.time_benchmaker.step_dict_list) == N

    def test_gstop_without_start_is_noop(self, tmp_benchmarker):
        tmp_benchmarker.gstop()
        assert len(tmp_benchmarker.time_benchmaker.step_dict_list) == 0

    def test_disable_prevents_data_collection(self, tmp_benchmarker):
        tmp_benchmarker.disable()
        tmp_benchmarker.start()
        tmp_benchmarker.step("work")
        tmp_benchmarker.gstop()
        assert len(tmp_benchmarker.time_benchmaker.step_dict_list) == 0

    def test_enable_after_disable_resumes_collection(self, tmp_benchmarker):
        tmp_benchmarker.disable()
        tmp_benchmarker.enable()
        tmp_benchmarker.start()
        tmp_benchmarker.step("work")
        tmp_benchmarker.gstop()
        assert len(tmp_benchmarker.time_benchmaker.step_dict_list) == 1

    def test_memory_data_collected_when_enabled(self, tmp_benchmarker, mock_memory):
        # MemoryBenchmarker.started is only set to True via gstep(); the first
        # gstep() call bootstraps it, and the subsequent gstop() saves the data.
        tmp_benchmarker.enable_memory_tracking()
        tmp_benchmarker.start()
        tmp_benchmarker.gstep()  # bootstraps memory tracking
        tmp_benchmarker.gstop()  # saves first memory entry
        assert len(tmp_benchmarker.memory_benchmaker.memory_usage_list) == 1

    def test_memory_not_collected_when_disabled(self, tmp_benchmarker, mock_memory):
        # memory tracking is disabled by default
        tmp_benchmarker.start()
        tmp_benchmarker.step("work")
        tmp_benchmarker.gstop()
        assert len(tmp_benchmarker.memory_benchmaker.memory_usage_list) == 0

    def test_gstop_adds_gstop_step_to_time(self, tmp_benchmarker):
        """Benchmarker.gstop() inserts an internal 'gstop' timing step."""
        tmp_benchmarker.start()
        tmp_benchmarker.step("work")
        tmp_benchmarker.gstop()
        entry = tmp_benchmarker.time_benchmaker.step_dict_list[0]
        assert "gstop" in entry


class TestBenchmarkerSave:
    def test_save_data_creates_all_three_files(self, tmp_benchmarker, bench_file):
        tmp_benchmarker.start()
        tmp_benchmarker.step("work")
        tmp_benchmarker.gstop()
        tmp_benchmarker.save_data()

        assert os.path.exists(bench_file + "_STEP_DICT_DATA.json")
        assert os.path.exists(bench_file + "_STEP_DICT_SUMMARY.json")
        assert os.path.exists(bench_file + "_MEMORY.json")

    def test_save_produces_valid_step_dict_json(self, tmp_benchmarker, bench_file):
        tmp_benchmarker.start()
        tmp_benchmarker.step("work")
        tmp_benchmarker.gstop()
        tmp_benchmarker.save_data()

        with open(bench_file + "_STEP_DICT_DATA.json") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
        assert "work" in data[0]["absolutes"]

    def test_save_produces_valid_summary_json(self, tmp_benchmarker, bench_file):
        tmp_benchmarker.start()
        tmp_benchmarker.step("work")
        tmp_benchmarker.gstop()
        tmp_benchmarker.save_data()

        with open(bench_file + "_STEP_DICT_SUMMARY.json") as f:
            summary = json.load(f)
        assert "work" in summary
        assert "mean" in summary["work"]

    def test_save_produces_valid_memory_json(self, tmp_benchmarker, bench_file):
        tmp_benchmarker.start()
        tmp_benchmarker.step("work")
        tmp_benchmarker.gstop()
        tmp_benchmarker.save_data()

        with open(bench_file + "_MEMORY.json") as f:
            mem = json.load(f)
        assert isinstance(mem, list)

    def test_save_disabled_benchmarker_creates_no_files(
        self, tmp_benchmarker, bench_file
    ):
        tmp_benchmarker.disable()
        tmp_benchmarker.save_data()
        assert not os.path.exists(bench_file + "_STEP_DICT_DATA.json")

    def test_save_on_gstop_triggers_at_interval(self, bench_file, mock_memory):
        b = Benchmarker(bench_file, save_on_gstop=2)
        for _ in range(2):
            b.start()
            b.step("work")
            b.gstop()
        assert os.path.exists(bench_file + "_STEP_DICT_DATA.json")

    def test_save_on_gstop_does_not_trigger_early(self, bench_file, mock_memory):
        b = Benchmarker(bench_file, save_on_gstop=3)
        b.start()
        b.step("work")
        b.gstop()  # only 1 gstop; threshold is 3
        assert not os.path.exists(bench_file + "_STEP_DICT_DATA.json")

    def test_save_on_step_triggers_immediately(self, bench_file):
        b = Benchmarker(bench_file)
        b.set_save_on_step(True)
        b.start()
        b.step("work")
        assert os.path.exists(bench_file + "_STEP_DICT_DATA.json")

    def test_multiple_iterations_saved_correctly(self, tmp_benchmarker, bench_file):
        for _ in range(5):
            tmp_benchmarker.start()
            tmp_benchmarker.step("task")
            tmp_benchmarker.gstop()
        tmp_benchmarker.save_data()

        with open(bench_file + "_STEP_DICT_DATA.json") as f:
            data = json.load(f)
        assert len(data) == 5
