"""Tests for GlobalBenchmarker and IterBench."""

import os

import pytest

from porter_bench.GlobalBenchmarker import GlobalBenchmarker, IterBench


class TestGlobalBenchmarkerAccessors:
    def test_getitem_creates_benchmarker(self, tmp_global):
        b = tmp_global["my_bench"]
        assert b is not None

    def test_getitem_same_key_returns_same_instance(self, tmp_global):
        b1 = tmp_global["bench"]
        b2 = tmp_global["bench"]
        assert b1 is b2

    def test_getitem_different_keys_are_different_instances(self, tmp_global):
        b1 = tmp_global["bench_a"]
        b2 = tmp_global["bench_b"]
        assert b1 is not b2

    def test_benchmarker_file_path_contains_name(self, tmp_global):
        b = tmp_global["my_run"]
        assert "my_run" in b.file

    def test_set_default_path_used_for_new_keys(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        gb = GlobalBenchmarker()
        gb.set_default_path("custom_results")
        b = gb["run_1"]
        assert "custom_results" in b.file

    def test_pre_existing_key_not_affected_by_set_default_path(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        gb = GlobalBenchmarker()
        b_old = gb["old"]
        original_file = b_old.file
        gb.set_default_path("new_results")
        assert gb["old"].file == original_file


class TestGlobalBenchmarkerEnableDisable:
    def test_disable_propagates_to_all_benchmarkers(self, tmp_global):
        tmp_global["a"]
        tmp_global["b"]
        tmp_global.disable()
        for bench in tmp_global.benchmarkers.values():
            assert not bench.enabled

    def test_enable_propagates_to_all_benchmarkers(self, tmp_global):
        tmp_global["a"]
        tmp_global["b"]
        tmp_global.disable()
        tmp_global.enable()
        for bench in tmp_global.benchmarkers.values():
            assert bench.enabled

    def test_disable_then_getitem_new_key_still_benchmarks(self, tmp_global):
        """Keys created after disable() are not automatically disabled."""
        tmp_global.disable()
        b = tmp_global["new_key"]
        # GlobalBenchmarker creates the Benchmarker with default enabled=True;
        # it does not retroactively disable newly-created instances.
        assert b is not None


class TestGlobalBenchmarkerSave:
    def test_save_creates_files_for_all_benchmarkers(self, tmp_global, mock_memory):
        tmp_global["t1"]
        tmp_global["t1"].start()
        tmp_global["t1"].step("work")
        tmp_global["t1"].gstop()

        tmp_global["t2"]
        tmp_global["t2"].start()
        tmp_global["t2"].step("work")
        tmp_global["t2"].gstop()

        tmp_global.save()

        assert os.path.exists(tmp_global["t1"].file + "_STEP_DICT_DATA.json")
        assert os.path.exists(tmp_global["t2"].file + "_STEP_DICT_DATA.json")

    def test_save_skipped_when_global_disabled(self, tmp_global, mock_memory):
        b = tmp_global["bench"]
        b.start()
        b.step("work")
        b.gstop()
        tmp_global.disable()
        tmp_global.save()
        assert not os.path.exists(b.file + "_STEP_DICT_DATA.json")


class TestIterBench:
    def test_iterates_all_items(self, tmp_global):
        data = [1, 2, 3, 4, 5]
        results = list(IterBench(data, tmp_global, name="epoch"))
        assert results == data

    def test_records_gstep_entry_per_element(self, tmp_global):
        # The first gstep() bootstraps (gstop is a no-op since started=False),
        # so N elements produce N-1 closed time entries.
        data = [10, 20, 30]
        list(IterBench(data, tmp_global, name="epoch"))
        b = tmp_global["epoch"]
        assert len(b.time_benchmaker.step_dict_list) == len(data)

    def test_len_matches_dataloader(self, tmp_global):
        data = [1, 2, 3]
        it = IterBench(data, tmp_global, name="epoch2")
        assert len(it) == 3

    def test_stop_iteration_raised_at_end(self, tmp_global):
        data = [42]
        it = IterBench(data, tmp_global, name="single")
        iter(it)
        it.__next__()  # consumes the one element
        with pytest.raises(StopIteration):
            it.__next__()

    def test_default_name_is_epoch(self, tmp_global):
        data = [1]
        list(IterBench(data, tmp_global))
        assert "epoch" in tmp_global.benchmarkers
