"""Round-trip I/O tests: run a benchmark, save, reload, validate."""

import os

import pandas as pd
import pytest

from porter_bench.GlobalBenchmarker import GlobalBenchmarker
from porter_bench.utils import get_latest_record, load_record


class TestLoadRecord:
    def test_returns_all_expected_keys(self, saved_record):
        record = load_record(str(saved_record))
        for key in (
            "summary",
            "absolutes",
            "calls",
            "infos",
            "memory",
            "_raw_data",
            "_raw_memory",
        ):
            assert key in record, f"Missing key: {key}"

    def test_absolutes_are_dataframes(self, saved_record):
        record = load_record(str(saved_record))
        for df in record["absolutes"].values():
            assert isinstance(df, pd.DataFrame)

    def test_absolutes_columns_match_step_names(self, saved_record):
        record = load_record(str(saved_record))
        df = record["absolutes"]["test"]
        # "work" and "io" were used in the saved_record fixture
        assert "work" in df.columns
        assert "io" in df.columns

    def test_absolutes_row_count_equals_iterations(self, saved_record):
        record = load_record(str(saved_record))
        df = record["absolutes"]["test"]
        assert len(df) == 3  # 3 iterations in saved_record

    def test_summary_has_all_stat_fields(self, saved_record):
        record = load_record(str(saved_record))
        summary = record["summary"]["test"]
        for step_stats in summary.values():
            for field in ("mean", "min", "max", "quantile_filtered"):
                assert field in step_stats, f"Missing summary field: {field}"

    def test_summary_mean_within_min_max(self, saved_record):
        record = load_record(str(saved_record))
        for step_stats in record["summary"]["test"].values():
            assert step_stats["min"] <= step_stats["mean"] <= step_stats["max"]

    def test_calls_are_dataframes(self, saved_record):
        record = load_record(str(saved_record))
        for df in record["calls"].values():
            assert isinstance(df, pd.DataFrame)

    def test_infos_are_dataframes_with_step_number(self, saved_record):
        record = load_record(str(saved_record))
        for df in record["infos"].values():
            assert isinstance(df, pd.DataFrame)
            assert "STEP_NUMBER" in df.columns

    def test_memory_is_list(self, saved_record):
        """Memory key exists and is a list; may be empty if tracking was disabled."""
        record = load_record(str(saved_record))
        assert "test" in record["memory"]
        mem = record["memory"]["test"]
        assert isinstance(mem, list)
        for entry in mem:
            assert isinstance(entry, dict)

    def test_raw_data_contains_benchmark_name(self, saved_record):
        record = load_record(str(saved_record))
        assert "test" in record["_raw_data"]

    def test_raw_memory_contains_benchmark_name(self, saved_record):
        record = load_record(str(saved_record))
        assert "test" in record["_raw_memory"]


class TestGetLatestRecord:
    def test_returns_a_string(self, saved_record):
        result = get_latest_record(str(saved_record))
        assert isinstance(result, str)

    def test_returned_path_is_an_existing_directory(self, saved_record):
        result = get_latest_record(str(saved_record))
        assert os.path.isdir(result)

    def test_latest_record_contains_step_dict_data_file(self, saved_record):
        """The directory returned by get_latest_record must contain the JSON files."""
        result = get_latest_record(str(saved_record))
        files = os.listdir(result)
        assert any(f.endswith("_STEP_DICT_DATA.json") for f in files)
