import os
from collections import defaultdict
from typing import List, Dict, Union
import matplotlib.pyplot as plt
from matplotlib.container import BarContainer
from matplotlib.lines import Line2D

import numpy as np
import csv
import json
import psutil
from .basic import Timer
import gc
import sys


class Benchmarker:
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
        file (str): The base filename for storing benchmark results (e.g., "performance/base").
        folder (str): The folder path for storing benchmark results derived from the base filename.
        started (bool): Flag indicating if a benchmark has been started.
    """

    def __init__(self, file: str = "performance/base", top_n: int = 5) -> None:
        self.enable = True
        self.step_timer = Timer()
        self.global_timer = Timer()

        self.step_dict_list: List[Dict[str, int]] = []
        self.step_dict: Dict[str, int] = defaultdict(int)
        self.memory_usage_list: List[Dict[str, Union[int, str]]] = []
        self.memory_usage: Dict[str, Union[int, str]] = defaultdict(dict)

        self.file = file
        self.folder = os.path.join(*file.split("/")[:-1])

        self.started = False
        self.track_memory_usage = False  # Enable/disable all memory tracking
        self.track_memory_in_step = False  # Enable/disable memory tracking in the step method
        self.top_n = top_n  # Number of top memory-consuming objects to track

    def enable_memory_tracking(self) -> None:
        """
        Enables all memory usage tracking.
        """
        self.track_memory_usage = True

    def disable_memory_tracking(self) -> None:
        """
        Disables all memory usage tracking.
        """
        self.track_memory_usage = False

    def enable_memory_tracking_in_step(self) -> None:
        """
        Enables memory usage tracking specifically for the step method.
        """
        self.track_memory_in_step = True

    def disable_memory_tracking_in_step(self) -> None:
        """
        Disables memory usage tracking specifically for the step method.
        """
        self.track_memory_in_step = False

    def enable(self) -> None:
        """
        Enables benchmarking by setting the `enable` flag to True.
        """
        self.enable = True

    def disable(self) -> None:
        """
        Disables benchmarking by setting the `enable` flag to False.
        """
        self.enable = False

    def start(self) -> None:
        """
        Starts a new benchmark by resetting the step and global timers and setting the `started`
          flag to True.
        """
        if self.enable:
            self.step_timer.tic()
            self.global_timer.tic()
            self.started = True

    def gstep(self) -> None:
        """
        Ends the current step within a benchmark, stores accumulated step time and memory usage,
        resets the step timer, and starts a new step.
        """
        if self.enable:
            self.gstop()
            self.step_dict = defaultdict(int)
            if self.track_memory_usage:  # Check if global memory tracking is enabled
                self.memory_usage = defaultdict(dict)
                top_memory_objects = self.get_top_memory_objects()
                self.memory_usage["gstep"] = {
                    "total memory usage": psutil.Process().memory_info().rss,
                    "top_memory_objects": top_memory_objects,
                }
            self.start()

    def get_top_memory_objects(self):
        """
        Retrieves the top N memory-consuming objects along with their types and sizes.

        Returns:
            List[Tuple[str, int]]: A list of tuples containing the type and size of the top objects.
        """
        gc.collect()
        all_objects = gc.get_objects()
        top_memory_objects = []
        for obj in all_objects:
            obj_size = sys.getsizeof(obj)
            obj_type = str(type(obj))
            if len(top_memory_objects) < self.top_n:
                top_memory_objects.append((obj_type, obj_size))
                top_memory_objects.sort(key=lambda x: x[1], reverse=True)
            elif obj_size > top_memory_objects[-1][1]:
                top_memory_objects[-1] = (obj_type, obj_size)
                top_memory_objects.sort(key=lambda x: x[1], reverse=True)
        return top_memory_objects

    def gstop(self) -> None:
        """
        Ends the current benchmark, stores accumulated step time and memory usage for the overall
         execution,
        and resets the `started` flag.
        """
        if self.enable:
            if self.started:
                if "global" not in self.step_dict.keys():
                    self.step_dict["global"] = self.global_timer.ttoc()
                self.step_dict_list.append(self.step_dict)
                self.started = False
                if self.track_memory_usage:
                    top_memory_objects = self.get_top_memory_objects()
                    self.memory_usage["gstop"] = {
                        "total memory usage": psutil.Process().memory_info().rss,
                        "top_memory_objects": top_memory_objects,
                    }
                    self.memory_usage_list.append(self.memory_usage)

    def step(self, topic: str = "") -> None:
        """
        Tracks time spent on a specific step within the current benchmark.

        Args:
            topic (str, optional): The name of the step being timed. Defaults to an empty string.
        """
        if self.enable:
            self.step_dict[topic] += self.step_timer.ttoc()
            if self.track_memory_usage and self.track_memory_in_step:  # Check both flags
                top_memory_objects = self.get_top_memory_objects()
                self.memory_usage[topic] = {
                    "total memory usage": psutil.Process().memory_info().rss,
                    "top_memory_objects": top_memory_objects,
                }

    def save_data(self) -> None:
        """
        Saves benchmark results by generating plots, writing summaries, creating visualizations,
        saving the global dictionary list as a JSON file, and saving memory usage data.
        """
        if self.enable:
            self.series = defaultdict(dict)
            for step_number, step_dict in enumerate(self.step_dict_list):
                for step_name in step_dict.keys():
                    self.series[step_name][step_number] = step_dict[step_name]
            df_means = {
                step_name: np.mean(list(self.series[step_name].values()))
                for step_name in self.series.keys()
            }

            os.makedirs(self.folder, exist_ok=True)
            self.write_summary(df_means)
            self.make_bars(df_means)
            self.plot_data()
            self.save_json()
            self.save_memory_usage()

    def make_bars(self, df_means: Dict[str, float]) -> None:
        """
        Creates a bar chart visualization of the benchmark results.

        Args:
            df_means (Dict[str, float]): A dictionary containing the mean times for each step.
        """

        def rescale(y):
            if (np.max(y) - np.min(y)) == 0:
                return 0
            return (y - np.min(y)) / (np.max(y) - np.min(y))

        plt.figure(figsize=(18, 6))
        mymap = plt.get_cmap("jet")
        plt.title(os.path.basename(self.file) + "_bar")
        plt.tight_layout()
        bar_container = plt.bar(
            np.arange(len(df_means.values())),
            [i for i in df_means.values()],
            label=list(df_means.keys()),
            color=mymap(rescale(list(df_means.values()))),
        )
        self.label_bar_heights(df_means, bar_container)
        plt.xticks(np.arange(len(df_means)), list(df_means.keys()))
        plt.legend(list(df_means.keys()))
        plt.savefig(self.file + "_bar.png", dpi=200)

    def label_bar_heights(self, df_means: Dict[str, float], bar_container: BarContainer) -> None:
        """
        Adds labels to the bar chart indicating the height of each bar.

        Args:
            df_means (Dict[str, float]): A dictionary containing the mean times for each step.
            bar_container (BarContainer): The container for the bars in the chart.
        """
        y_offset = max(df_means.values()) * 0.04
        for bar in bar_container:
            # Get height and label for the bar
            height = bar.get_height()
            # Annotate the bar with its label and value
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height + y_offset,
                f"{round(height,3)}",
                ha="center",
                va="top",
            )
        plt.xticks(np.arange(len(df_means)), list(df_means.keys()))
        plt.legend(list(df_means.keys()))
        plt.savefig(self.file + "_bar.png", dpi=200)

    def write_summary(self, df_means: Dict[str, float]) -> None:
        """
        Writes a summary of the benchmark results to a CSV file.

        Args:
            df_means (Dict[str, float]): A dictionary containing the mean times for each step.
        """
        with open(self.file + "_summary.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            # Write the data to the CSV file
            for row in df_means.items():
                writer.writerow(row)

    def plot_data(self) -> None:
        """
        Generates a time series plot of benchmark results, highlighting outliers and missing data.
        """
        series = self.series
        plt.figure(figsize=(18, 6))
        plt.title(os.path.basename(self.file))
        max_length = max([max(step_dict.keys()) for step_dict in series.values()])
        outlier_max = np.percentile(np.asarray(list(series["global"].values())), 75)
        outlier_max = outlier_max * 4
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

        plt.show()
        plt.savefig(self.file + ".png", dpi=200)

    def save_json(self) -> None:
        """
        Saves the global dictionary list as a JSON file.
        """
        with open(self.file + "_data.json", "w") as jsonfile:
            json.dump(self.step_dict_list, jsonfile, indent=4)

    def save_memory_usage(self) -> None:
        """
        Saves memory usage data to a JSON file.
        """
        with open(self.file + "_memory.json", "w") as jsonfile:
            json.dump(self.memory_usage_list, jsonfile, indent=4)
