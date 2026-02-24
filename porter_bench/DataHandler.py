"""High-level data handler for visualising loaded benchmark records."""

from typing import Any, Dict

import matplotlib.pyplot as plt

from porter_bench.MemoryBenchmarker import MemoryPlotter
from porter_bench.TimeBenchmarker import TimePlotter

COLORS = ["b", "g", "r", "c", "m", "y", "k", "w"]


class DataHandler:
    """Wrap a dict of loaded benchmark records and expose plotting helpers."""

    def __init__(self, record_dict: Dict[str, Dict], record_path: str = "") -> None:
        """Initialise with a dict of named benchmark records."""
        self.time_plotter = TimePlotter(record_path)
        self.memory_plotter = MemoryPlotter(record_path)
        self.record_dict = record_dict

    def plot_memory_usage(
        self,
        record_name: str = "global",
        filter_no_change_val: float | None = None,
        **kwargs: Any,
    ) -> list:
        """Plot memory usage over time for every record in the dict."""
        plt.title(record_name)
        rejected = []
        for n, name in enumerate(self.record_dict.keys()):
            rejected.append(
                self.memory_plotter.plot_data(
                    self.record_dict[name]["memory"][record_name],
                    filter_no_change_val=filter_no_change_val,
                    label=name,
                    highlight_color=COLORS[n],
                    **kwargs,
                )
            )
        return rejected

    def make_bars(self, record_name: str = "global", **kwargs: Any) -> None:
        """Render bar charts of mean step times for every record in the dict."""
        for name in self.record_dict.keys():
            self.time_plotter.make_bars(
                self.record_dict[name]["summary"][record_name], label=name, **kwargs
            )

    def plot_times(self, record_name: str = "global") -> None:
        """Plot absolute step-time series for every record in the dict."""
        plt.title(record_name)
        line_styles = ["-", "--", "-.", ":"]
        for n, name in enumerate(self.record_dict.keys()):
            self.time_plotter.plot_data(
                self.record_dict[name]["absolutes"][record_name],
                label=name,
                linestyle=line_styles[n % len(line_styles)],
            )

    def plot_crono(self, record_name: str = "global") -> None:
        """Plot a chronological step timeline for every record in the dict."""
        plt.title(record_name)
        for n, name in enumerate(self.record_dict.keys()):
            self.time_plotter.crono_plot(
                self.record_dict[name]["calls"][record_name], label=name
            )

    def plot_cuda_memory(self, record_name: str = "global") -> None:
        """Plot CUDA memory usage for every record in the dict."""
        plt.title(record_name)
        for name in self.record_dict.keys():
            self.memory_plotter.plot_cuda_data(
                self.record_dict[name]["memory"][record_name]
            )
