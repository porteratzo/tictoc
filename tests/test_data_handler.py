"""Tests for DataHandler rendering.

Uses the Agg (non-interactive) matplotlib backend so no display is required,
making these tests CI-safe.
"""

import matplotlib
import matplotlib.pyplot as plt
import pytest

matplotlib.use("Agg")

from porter_bench.DataHandler import DataHandler
from porter_bench.utils import load_record


@pytest.fixture
def data_handler(saved_record):
    """Build a DataHandler from the saved_record fixture."""
    record = load_record(str(saved_record))
    return DataHandler({"test": record})


@pytest.fixture(autouse=True)
def close_plots():
    """Close all matplotlib figures after each test to avoid resource warnings."""
    yield
    plt.close("all")


class TestDataHandlerPlots:
    def test_make_bars_does_not_raise(self, data_handler):
        data_handler.make_bars("test")

    def test_plot_times_does_not_raise(self, data_handler):
        data_handler.plot_times("test")

    def test_plot_crono_does_not_raise(self, data_handler):
        data_handler.plot_crono("test")

    def test_plot_memory_usage_does_not_raise(self, data_handler):
        data_handler.plot_memory_usage("test")

    def test_make_bars_with_filter_val(self, data_handler):
        """Exercise the filter_val code path in TimePlotter.make_bars."""
        data_handler.make_bars("test", filter_val=0.01)

    def test_multiple_labels_in_record_dict(self, saved_record):
        """DataHandler with two entries must iterate over both without error."""
        record = load_record(str(saved_record))
        dh = DataHandler({"label_a": record, "label_b": record})
        dh.plot_times("test")
        dh.make_bars("test")


class TestDataHandlerConstruction:
    def test_construction_with_empty_record_dict(self):
        dh = DataHandler({})
        # No benchmarks; calling plot methods should be graceful no-ops
        dh.plot_times("nonexistent")
        dh.make_bars("nonexistent")
        dh.plot_memory_usage("nonexistent")
        dh.plot_crono("nonexistent")
