from porter_bench.TimeBenchmarker import TimePlotter
from porter_bench.MemoryBenchmarker import MemoryPlotter
from typing import Dict

import matplotlib.pyplot as plt

COLORS = ["b", "g", "r", "c", "m", "y", "k", "w"]


class DataHandler:
    def __init__(self, record_dict: Dict[str, Dict], record_path=""):
        self.time_plotter = TimePlotter(record_path)
        self.memory_plotter = MemoryPlotter(record_path)
        self.record_dict = record_dict

    def plot_memory_usage(
        self, record_name="global", filter_no_change_val=None, **kwargs
    ):
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

    def make_bars(self, record_name="global", **kwargs):
        for name in self.record_dict.keys():
            self.time_plotter.make_bars(
                self.record_dict[name]["summary"][record_name], label=name, **kwargs
            )

    def plot_times(self, record_name="global"):
        plt.title(record_name)
        line_styles = ["-", "--", "-.", ":"]
        for n, name in enumerate(self.record_dict.keys()):
            self.time_plotter.plot_data(
                self.record_dict[name]["absolutes"][record_name],
                label=name,
                linestyle=line_styles[n % len(line_styles)],
            )

    def plot_crono(self, record_name="global"):
        plt.title(record_name)
        for n, name in enumerate(self.record_dict.keys()):
            self.time_plotter.crono_plot(
                self.record_dict[name]["calls"][record_name], label=name
            )
