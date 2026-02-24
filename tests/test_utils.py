"""Tests for porter_bench.utils data-processing functions.

These tests operate on in-memory data (no disk I/O required) to keep them
fast and hermetic.
"""

import pandas as pd
import pytest

from porter_bench.utils import (
    filter_no_change,
    find_clusters,
    get_absolutes,
    get_calls,
    get_infos,
)

# ---------------------------------------------------------------------------
# Minimal dataset that mirrors what TimeBenchmarker actually produces:
#   absolutes  -> summed times per step per iteration
#   individual_calls -> list of per-call records (time, crono_counter, extra)
#   info -> STEP_NUMBER, START_TIME, STOP_TIME
# ---------------------------------------------------------------------------
SAMPLE_STEP_DICT_DATA = {
    "bench": [
        {
            "absolutes": {"work": 0.10, "io": 0.05, "GLOBAL": 0.15},
            "info": {"STEP_NUMBER": 0, "START_TIME": 1000.0, "STOP_TIME": 1000.15},
            "individual_calls": {
                "work": [{"time": 0.10, "crono_counter": 0, "extra": None}],
                "io": [{"time": 0.05, "crono_counter": 1, "extra": None}],
                "GLOBAL": [{"time": 0.15, "crono_counter": 2, "extra": None}],
            },
        },
        {
            "absolutes": {"work": 0.12, "io": 0.06, "GLOBAL": 0.18},
            "info": {"STEP_NUMBER": 1, "START_TIME": 1000.2, "STOP_TIME": 1000.38},
            "individual_calls": {
                "work": [{"time": 0.12, "crono_counter": 0, "extra": None}],
                "io": [{"time": 0.06, "crono_counter": 1, "extra": None}],
                "GLOBAL": [{"time": 0.18, "crono_counter": 2, "extra": None}],
            },
        },
    ]
}


class TestGetAbsolutes:
    def test_returns_dict_of_dataframes(self):
        result = get_absolutes(SAMPLE_STEP_DICT_DATA)
        assert isinstance(result, dict)
        assert "bench" in result
        assert isinstance(result["bench"], pd.DataFrame)

    def test_columns_match_step_names(self):
        df = get_absolutes(SAMPLE_STEP_DICT_DATA)["bench"]
        assert "work" in df.columns
        assert "io" in df.columns
        assert "GLOBAL" in df.columns

    def test_row_count_equals_iterations(self):
        df = get_absolutes(SAMPLE_STEP_DICT_DATA)["bench"]
        assert len(df) == 2

    def test_values_match_absolutes(self):
        df = get_absolutes(SAMPLE_STEP_DICT_DATA)["bench"]
        assert df["work"].iloc[0] == pytest.approx(0.10)
        assert df["work"].iloc[1] == pytest.approx(0.12)


class TestGetCalls:
    def test_returns_dict_of_dataframes(self):
        result = get_calls(SAMPLE_STEP_DICT_DATA)
        assert isinstance(result["bench"], pd.DataFrame)

    def test_columns_match_step_names(self):
        df = get_calls(SAMPLE_STEP_DICT_DATA)["bench"]
        assert "work" in df.columns

    def test_row_count_equals_iterations(self):
        df = get_calls(SAMPLE_STEP_DICT_DATA)["bench"]
        assert len(df) == 2

    def test_call_records_are_lists(self):
        df = get_calls(SAMPLE_STEP_DICT_DATA)["bench"]
        for cell in df["work"]:
            assert isinstance(cell, list)


class TestGetInfos:
    def test_returns_dict_of_dataframes(self):
        result = get_infos(SAMPLE_STEP_DICT_DATA)
        assert isinstance(result["bench"], pd.DataFrame)

    def test_step_number_column_present(self):
        df = get_infos(SAMPLE_STEP_DICT_DATA)["bench"]
        assert "STEP_NUMBER" in df.columns

    def test_step_numbers_are_sequential(self):
        df = get_infos(SAMPLE_STEP_DICT_DATA)["bench"]
        assert list(df["STEP_NUMBER"]) == [0, 1]


class TestFindClusters:
    def _make_crono(self, names: list[str], total: float = 0.1) -> list[dict]:
        return [{"step_name": n, "step_number": 0, "total": total} for n in names]

    def test_non_repeating_sequence_length_preserved(self):
        crono = self._make_crono(["a", "b", "c"])
        result = find_clusters(crono, max_length=3, cluster_filter=0.05)
        assert len(result) == 3

    def test_repeating_pair_is_collapsed(self):
        # a b a b  -> should be shorter than 4
        crono = self._make_crono(["a", "b", "a", "b"])
        result = find_clusters(crono, max_length=4, cluster_filter=0.05)
        assert len(result) < 4

    def test_single_element_sequence(self):
        crono = self._make_crono(["x"])
        result = find_clusters(crono, max_length=5, cluster_filter=0.05)
        assert len(result) == 1

    def test_memory_spike_prevents_cluster(self):
        """A large timing difference in the repeated block should break the cluster."""
        crono = [
            {"step_name": "a", "step_number": 0, "total": 0.1},
            {"step_name": "b", "step_number": 0, "total": 0.1},
            {"step_name": "a", "step_number": 0, "total": 10.0},  # spike
            {"step_name": "b", "step_number": 0, "total": 0.1},
        ]
        result = find_clusters(crono, max_length=4, cluster_filter=0.05)
        # Should NOT compress into one cluster due to the spike
        assert len(result) >= 3


class TestFilterNoChange:
    def test_all_identical_values_filtered(self):
        crono = [
            {"step_name": "a", "total": 100.0},
            {"step_name": "b", "total": 100.0},
            {"step_name": "c", "total": 100.0},
        ]
        result, rejected = filter_no_change(0.05, crono)
        # All values equal; only the first entry passes the threshold
        assert len(result) == 1
        assert len(rejected) == 2

    def test_all_changing_values_pass_through(self):
        crono = [
            {"step_name": "a", "total": 100.0},
            {"step_name": "b", "total": 200.0},
            {"step_name": "c", "total": 300.0},
        ]
        result, rejected = filter_no_change(0.05, crono)
        assert len(result) == 3
        assert len(rejected) == 0

    def test_first_element_always_included(self):
        crono = [
            {"step_name": "a", "total": 50.0},
            {"step_name": "b", "total": 51.0},  # tiny change, should be rejected
        ]
        result, rejected = filter_no_change(0.5, crono)
        assert result[0]["step_name"] == "a"

    def test_non_float_filter_uses_default(self):
        """Passing a non-float filter_no_change should fall back to 0.05."""
        crono = [
            {"step_name": "a", "total": 100.0},
            {"step_name": "b", "total": 100.0},
        ]
        result, rejected = filter_no_change("bad_value", crono)
        # Should behave identically to passing 0.05
        assert len(result) == 1
