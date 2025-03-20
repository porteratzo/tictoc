import os
from collections import defaultdict
from typing import List, Dict, Union
import matplotlib.pyplot as plt
from matplotlib.container import BarContainer
from matplotlib.lines import Line2D

import numpy as np
import json
import psutil
from .basic import Timer
import gc
import sys
from .BaseSaver import BaseSaver


class TimeBenchmarker:
    """
    A class for benchmarking performance during code execution.

    Attributes:
        enable (bool): Whether benchmarking is enabled. Defaults to True.
        step_timer (Timer): A timer object for tracking step times.
        global_timer (Timer): A timer object for tracking overall execution time.
        global_dict_list (List[DefaultDict[str, int]]): A list of dictionaries storing step times
            for each step within a benchmark.
        step_dict (DefaultDict[str, int]): A dictionary storing accumulated time for each step
            within the current benchmark.
        started (bool): Flag indicating if a benchmark has been started.
    """

    def __init__(self) -> None:
        self._enable = True
        self.step_timer = Timer()
        self.global_timer = Timer()

        self.step_dict_list: List[Dict[str, int]] = []
        self.step_dict: Dict[str, int] = defaultdict(int)

        self.started = False

    def enable(self) -> None:
        """
        Enables benchmarking by setting the `enable` flag to True.
        """
        self._enable = True

    def disable(self) -> None:
        """
        Disables benchmarking by setting the `enable` flag to False.
        """
        self._enable = False

    def start(self) -> None:
        """
        Starts a new benchmark by resetting the step and global timers and setting the `started`
          flag to True.
        """
        if self._enable:
            self.step_timer.tic()
            self.global_timer.tic()
            self.started = True

    def gstep(self) -> None:
        """
        Ends the current step within a benchmark, stores accumulated step time and memory usage,
        resets the step timer, and starts a new step.
        """
        if self._enable:
            self.gstop()
            self.step_dict = defaultdict(int)
            self.start()

    def gstop(self) -> None:
        """
        Ends the current benchmark, stores accumulated step time and memory usage for the overall
         execution,
        and resets the `started` flag.
        """
        if self._enable:
            if self.started:
                if "global" not in self.step_dict.keys():
                    self.step_dict["global"] = self.global_timer.ttoc()
                self.step_dict_list.append(self.step_dict)
                self.started = False

    def step(self, topic: str = "") -> None:
        """
        Tracks time spent on a specific step within the current benchmark.

        Args:
            topic (str, optional): The name of the step being timed. Defaults to an empty string.
        """
        if self._enable:
            self.step_dict[topic] += self.step_timer.ttoc()


class TimerSaver(BaseSaver):
    def __init__(self, benchmarker: TimeBenchmarker, file: str = "performance/base") -> None:
        super().__init__(benchmarker, file)

        self.series = defaultdict(dict)
        for step_number, step_dict in enumerate(self.benchmarker.step_dict_list):
            for step_name in step_dict.keys():
                self.series[step_name][step_number] = step_dict[step_name]

        self.df_means = {}
        for step_name in self.series.keys():
            all_values = np.array(list(self.series[step_name].values()))
            step_dict = {}
            step_dict["mean"] = np.mean(all_values)
            step_dict["min"] = np.min(all_values) if len(all_values[all_values != 0]) > 0 else 0
            step_dict["max"] = np.max(all_values)  # Added max calculation
            upper_quantile = np.percentile(all_values, 75)
            lower_quantile = np.percentile(all_values, 25)
            quantile_range = upper_quantile - lower_quantile
            upper_bound = upper_quantile + quantile_range * 1.5
            lower_bound = lower_quantile - quantile_range * 1.5
            filtered_values = [v for v in all_values if v <= upper_bound and v >= lower_bound]
            step_dict["quantile_filtered"] = np.mean(filtered_values)
            self.df_means[step_name] = step_dict

        global_means = self.df_means.pop("global", None)
        if global_means is not None:
            self.df_means.update({"global": global_means})

    def save_data(self) -> None:
        self.write_summary()
        self.make_bars()
        self.plot_data()
        self.save_json()

    def make_bars(self) -> None:
        """
        Creates bar chart visualizations of the benchmark results with two subplots:
        one for the means and another for the quantile-filtered means.
        """

        def rescale(y):
            if (np.max(y) - np.min(y)) == 0:
                return 0
            return (y - np.min(y)) / (np.max(y) - np.min(y))

        means = [v["mean"] for k, v in self.df_means.items() if k != "global"]
        if len(means) == 0:
            return
        quantile_filtered_means = [
            v["quantile_filtered"] for k, v in self.df_means.items() if k != "global"
        ]
        step_names = list(self.df_means.keys())

        fig, axes = plt.subplots(1, 2, figsize=(18, 6))
        fig.suptitle(os.path.basename(self.file) + "_bar")
        mymap = plt.get_cmap("jet")

        # Plot for means
        axes[0].set_title("Means")

        bar_container_means = axes[0].bar(
            np.arange(len(means) + 1),
            means + [self.df_means["global"]["mean"]] if "global" in self.df_means else means,
            color=np.vstack([mymap(rescale(means)), [0, 0, 0, 1]]),
        )
        axes[0].set_xticks(np.arange(len(step_names)))
        axes[0].set_xticklabels(step_names, rotation=45, ha="right")
        self.label_bar_heights(bar_container_means, axes[0])

        # Plot for quantile-filtered means
        axes[1].set_title("Quantile-Filtered Means")
        bar_container_filtered = axes[1].bar(
            (
                np.arange(len(quantile_filtered_means) + 1)
                if "global" in self.df_means
                else np.arange(len(quantile_filtered_means))
            ),
            (
                quantile_filtered_means + [self.df_means["global"]["quantile_filtered"]]
                if "global" in self.df_means
                else quantile_filtered_means
            ),
            color=(
                np.vstack([mymap(rescale(quantile_filtered_means)), [0, 0, 0, 1]])
                if "global" in self.df_means
                else np.vstack([mymap(rescale(quantile_filtered_means))])
            ),
        )
        axes[1].set_xticks(np.arange(len(step_names)))
        axes[1].set_xticklabels(step_names, rotation=45, ha="right")
        self.label_bar_heights(bar_container_filtered, axes[1])

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig(self.file + "_bar.png", dpi=200)

    def label_bar_heights(self, bar_container: BarContainer, axis) -> None:
        """
        Adds labels to the bar chart indicating the height of each bar.

        Args:
            bar_container (BarContainer): The container for the bars in the chart.
            axis: The axis object to annotate the bars on.
        """
        y_offset = max([bar.get_height() for bar in bar_container]) * 0.04
        for bar in bar_container:
            height = bar.get_height()
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                height + y_offset,
                f"{round(height, 3)}",
                ha="center",
                va="top",
            )

    def write_summary(self) -> None:
        """
        Writes a summary of the benchmark results to a Json file.

        Args:
            df_means (Dict[str, float]): A dictionary containing the mean times for each step.
        """
        with open(self.file + "_summary.json", "w") as jsonfile:
            json.dump(self.df_means, jsonfile, indent=4)

    def plot_data(self) -> None:
        """
        Generates a time series plot of benchmark results, highlighting outliers and missing data.
        """
        series = self.series
        plt.figure(figsize=(18, 6))
        plt.title(os.path.basename(self.file))
        if len(series) == 0:
            return
        max_length = max([max(step_dict.keys()) for step_dict in series.values()])
        if "global" in series.keys():
            outlier_max = np.percentile(np.asarray(list(series["global"].values())), 75)
            outlier_max = outlier_max * 4
        else:
            outlier_max = float("inf")
        for n, step_name in enumerate(series.keys()):
            X = np.arange(max_length + 1)
            Y = np.zeros(max_length + 1)

            real_values = np.asarray(list(series[step_name].values()))
            real_steps = list(series[step_name].keys())
            for step_number, step_time in series[step_name].items():
                Y[step_number] = step_time

            Q3 = np.percentile(real_values, 75, interpolation="midpoint")
            upper_bound = Y > outlier_max

            Y_no_outliers = Y.copy()
            Y_no_outliers[upper_bound] = Q3

            (line1,) = plt.plot(X, Y_no_outliers, label=step_name)

            plt.plot(
                X[upper_bound],
                Y_no_outliers[upper_bound],
                color=line1.get_color(),
                marker=r"$\uparrow$",
                markersize=10,
                linestyle="",
                label="_nolegend_",
            )
            for k, (i, j) in enumerate(zip(X[upper_bound], Y_no_outliers[upper_bound])):
                plt.text(i, j, f"{Y[upper_bound][k]:.3e}", fontsize=9, ha="right")

            no_appear_steps = [i for i in range(max_length) if i not in real_steps]
            plt.plot(
                no_appear_steps,
                np.zeros(len(no_appear_steps)),
                color=line1.get_color(),
                marker="o",
                label="_nolegend_",
                linestyle="",
                markersize=(len(series) - n - 1) * 4 + 4,
            )
        plt.tight_layout()
        plt.legend()
        custom_legend_elements = [
            Line2D(
                [0], [0], marker="x", color="b", markerfacecolor="k", markersize=8, label="Outlier"
            ),
            Line2D(
                [0], [0], marker="o", color="b", markerfacecolor="k", markersize=8, label="No Data"
            ),
        ]

        # Add the legend with both plot entries and custom entries
        plt.legend(handles=plt.gca().get_legend_handles_labels()[0] + custom_legend_elements)

        plt.savefig(self.file + ".png", dpi=200)

    def save_json(self) -> None:
        """
        Saves the global dictionary list as a JSON file.
        """
        with open(self.file + "_data.json", "w") as jsonfile:
            json.dump(self.benchmarker.step_dict_list, jsonfile, indent=4)
