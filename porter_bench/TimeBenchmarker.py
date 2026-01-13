import os
from collections import defaultdict
from typing import List, Dict
import matplotlib.pyplot as plt
from matplotlib.container import BarContainer
from matplotlib.lines import Line2D
from scipy.ndimage import gaussian_filter1d

import numpy as np
import json
from time import time
from .basic import Timer
from .utils import APPENDED_STEP_DATA_NAME, APPENDED_SUMMARY_NAME, filter_no_change, find_clusters

START_TIME = "START_TIME"
STOP_TIME = "STOP_TIME"
SPECIAL_NAMES = [START_TIME, STOP_TIME]


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
        self.step_dict: Dict[str, list] = defaultdict(list)

        self.started = False
        self.crono_counter = 0

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
            self.crono_counter = 0
            self.step_dict = defaultdict(list)
            self.step_dict[START_TIME] = time()
            self.start()

    def gstop(self) -> None:
        """
        Ends the current benchmark, stores accumulated step time and memory usage for the overall
         execution,
        and resets the `started` flag.
        """
        if self._enable:
            if self.started:
                if "GLOBAL" not in self.step_dict.keys():
                    self.step_dict["GLOBAL"] = [
                        {"time": self.global_timer.ttoc(), "crono_counter": self.crono_counter}
                    ]
                self.step_dict[STOP_TIME] = time()
                self.step_dict_list.append(self.step_dict)
                self.started = False

    def step(self, topic: str = "", extra=None) -> None:
        """
        Tracks time spent on a specific step within the current benchmark.

        Args:
            topic (str, optional): The name of the step being timed. Defaults to an empty string.
        """
        if self._enable:
            self.step_dict[topic].append(
                {"time": self.step_timer.ttoc(), "crono_counter": self.crono_counter, 'extra':extra}
            )
            self.crono_counter += 1

    def save_data(self, file):
        TimerSaver(self, file).save_data()


class TimerSaver:
    def __init__(self, benchmarker: TimeBenchmarker, file: str = "performance/base") -> None:
        self.file = file
        self.folder = os.path.join(*file.split("/")[:-1])
        self.benchmarker = benchmarker

        self.series = defaultdict(dict)

        self.WORKING_LIST = self.benchmarker.step_dict_list.copy()
        if self.benchmarker.started:
            self.WORKING_LIST.append(self.benchmarker.step_dict)

    def summarize_data(self):
        self.df_means, self.series = summurize(self.WORKING_LIST)

    def save_data(self) -> None:
        self.write_summary()
        # self.make_bars()
        # self.plot_data()
        self.save_json()

    def write_summary(self) -> None:
        """
        Writes a summary of the benchmark results to a Json file.

        Args:
            df_means (Dict[str, float]): A dictionary containing the mean times for each step.
        """
        self.summarize_data()
        with open(self.file + f"{APPENDED_SUMMARY_NAME}.json", "w") as jsonfile:
            json.dump(self.df_means, jsonfile, indent=4)

    def save_json(self) -> None:
        """
        Saves the global dictionary list as a JSON file.
        """
        final_format = self.format_json()

        with open(self.file + f"{APPENDED_STEP_DATA_NAME}.json", "w") as jsonfile:
            json.dump(final_format, jsonfile, indent=4)

    def format_json(self):
        final_format = []
        for n, step_dict in enumerate(self.WORKING_LIST):
            formated_step_dict = {"absolutes": {}, "info": {}, "individual_calls": {}}
            working_keys = list(step_dict.keys())
            for key in working_keys:
                if key in SPECIAL_NAMES:
                    continue
                formated_step_dict["absolutes"][key] = sum([i["time"] for i in step_dict[key]])
                formated_step_dict["individual_calls"][key] = step_dict[key]
            formated_step_dict["info"]["STEP_NUMBER"] = n
            formated_step_dict["info"][START_TIME] = step_dict[START_TIME]
            formated_step_dict["info"][STOP_TIME] = step_dict.get(STOP_TIME, 0)
            final_format.append(formated_step_dict)
        return final_format


class TimePlotter:
    def __init__(self, folder_path: str = None) -> None:
        self.folder_path = folder_path
        self.series = defaultdict(dict)

    def make_bars(self, summary_data, label="", filter_val=0, figsize=(18, 6)) -> None:
        """
        Creates bar chart visualizations of the benchmark results with two subplots:
        one for the means and another for the quantile-filtered means.
        """

        def rescale(y):
            if (np.max(y) - np.min(y)) == 0:
                return 0
            return (y - np.min(y)) / (np.max(y) - np.min(y))

        means = [v["mean"] for k, v in summary_data.items() if k != "GLOBAL"]

        if len(means) == 0:
            return

        if filter_val > 0:
            higher_bound = max(means) * filter_val
            summary_data = {k: v for k, v in summary_data.items() if v["mean"] > higher_bound}
            means = [v["mean"] for k, v in summary_data.items() if k != "GLOBAL"]

        quantile_filtered_means = [
            v["quantile_filtered"] for k, v in summary_data.items() if k != "GLOBAL"
        ]
        quantile_filtered_means = np.nan_to_num(quantile_filtered_means, nan=0).tolist()
        step_names = list(summary_data.keys())

        fig, axes = plt.subplots(1, 2, figsize=figsize)
        fig.suptitle(os.path.basename(label) + "_bar")
        mymap = plt.get_cmap("jet")

        # Plot for means
        axes[0].set_title("Means")

        bar_container_means = axes[0].bar(
            np.arange(len(means) + (1 if "GLOBAL" in summary_data else 0)),
            means + [summary_data["GLOBAL"]["mean"]] if "GLOBAL" in summary_data else means,
            color=np.vstack([mymap(rescale(means)), [0, 0, 0, 1]]),
        )
        axes[0].set_xticks(np.arange(len(step_names)))
        axes[0].set_xticklabels(step_names, rotation=90, ha="right")
        label_bar_heights(bar_container_means, axes[0])

        # Plot for quantile-filtered means
        axes[1].set_title("Quantile-Filtered Means")
        bar_container_filtered = axes[1].bar(
            (
                np.arange(len(quantile_filtered_means) + 1)
                if "GLOBAL" in summary_data
                else np.arange(len(quantile_filtered_means))
            ),
            (
                quantile_filtered_means + [summary_data["GLOBAL"]["quantile_filtered"]]
                if "GLOBAL" in summary_data
                else quantile_filtered_means
            ),
            color=(
                np.vstack([mymap(rescale(quantile_filtered_means)), [0, 0, 0, 1]])
                if "GLOBAL" in summary_data
                else np.vstack([mymap(rescale(quantile_filtered_means))])
            ),
        )
        axes[1].set_xticks(np.arange(len(step_names)))
        axes[1].set_xticklabels(step_names, rotation=90, ha="right")
        label_bar_heights(bar_container_filtered, axes[1])

        plt.tight_layout(rect=[0, 0, 1, 0.95])

    def plot_data(
        self,
        absolutes_data,
        label="",
        linestyle=None,
        smooth: float = None,
        percentile=75,
        max_mult=4,
    ) -> None:
        """
        Generates a time series plot of benchmark results, highlighting outliers and missing data.
        """
        seriesDF = absolutes_data
        if len(seriesDF) == 0:
            return
        max_length = seriesDF.shape[0]
        if "GLOBAL" in seriesDF.keys():
            outlier_max = np.percentile(np.asarray(seriesDF["GLOBAL"]), percentile)
            outlier_max = outlier_max * max_mult
        else:
            outlier_max = float("inf")
        for n, step_name in enumerate(seriesDF.keys()):
            X = np.arange(max_length + 1)
            Y = np.zeros(max_length + 1)

            real_values = np.asarray(list(seriesDF[step_name]))
            real_steps = list(seriesDF[step_name].keys())
            for step_number, step_time in seriesDF[step_name].items():
                Y[step_number] = step_time

            Q3 = np.percentile(real_values, 75, interpolation="midpoint")
            upper_bound = Y > outlier_max

            Y = np.nan_to_num(Y, nan=0)
            Y_no_outliers = Y.copy()
            Y_no_outliers[upper_bound] = Q3

            if smooth is not None:
                Y_no_outliers = gaussian_filter1d(Y_no_outliers, smooth)

            (line1,) = plt.plot(
                X, Y_no_outliers, label=label + ":" + step_name, linestyle=linestyle
            )

            plt.plot(
                X[upper_bound],
                Y_no_outliers[upper_bound],
                color=line1.get_color(),
                marker=r"$\uparrow$",
                markersize=10,
                linestyle=linestyle,
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
                linestyle=linestyle,
                markersize=(len(seriesDF) - n - 1) * 4 + 4,
            )
        plt.tight_layout()
        custom_legend_elements = [
            Line2D(
                [0],
                [0],
                marker=r"$\uparrow$",
                color="b",
                markerfacecolor="k",
                markersize=8,
                label="Outlier",
            ),
            Line2D(
                [0], [0], marker="o", color="b", markerfacecolor="k", markersize=8, label="No Data"
            ),
        ]

        # Add the legend with both plot entries and custom entries
        plt.legend(handles=plt.gca().get_legend_handles_labels()[0] + custom_legend_elements)

    def crono_plot(self, call_data, label=""):
        series = []
        filter_no_change_val = None
        cluster = 5
        cluster_filter = 0.05
        for step_number, step_dict in call_data.iterrows():
            crono_series = {}
            for step_name in step_dict.keys():
                if isinstance(step_dict[step_name], list):
                    for record in step_dict[step_name]:
                        crono_series[record["crono_counter"]] = {
                            "step_name": step_name,
                            "step_number": step_number,
                            "total": record["time"],
                        }
            ordered_crono = [crono_series[n] for n in sorted(crono_series.keys())]
            if filter_no_change_val is not None:
                ordered_crono = filter_no_change(filter_no_change_val, ordered_crono)

            if cluster > 0:
                ordered_crono = find_clusters(ordered_crono, cluster, cluster_filter)

            series.extend(ordered_crono)

        total_times = [val["total"] for val in series]
        names = [f'{val["step_number"]}_{val["step_name"]}' for val in series]
        x_names = np.arange(len(names))

        plt.plot(x_names, total_times, label=label)

        plt.xticks(x_names, names, rotation=90)
        plt.ylabel("time (s)")
        plt.xlabel("Step")
        plt.tight_layout()
        plt.legend()
        plt.grid(True)


def label_bar_heights(bar_container: BarContainer, axis) -> None:
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


def summurize(working_list, percentile=75, filter_below=0):
    series = defaultdict(dict)
    for step_number, step_dict in enumerate(working_list):
        for step_name in step_dict.keys():
            if step_name in SPECIAL_NAMES:
                continue
            if isinstance(step_dict[step_name], list):
                series[step_name][step_number] = sum([i["time"] for i in step_dict[step_name]])

    df_means = {}
    for step_name in series.keys():
        all_values = np.array(list(series[step_name].values()))
        step_dict = {}
        step_dict["mean"] = np.mean(all_values)
        step_dict["min"] = np.min(all_values) if len(all_values[all_values != 0]) > 0 else 0
        step_dict["max"] = np.max(all_values)  # Added max calculation
        upper_quantile = np.percentile(all_values, percentile)
        lower_quantile = np.percentile(all_values, 100 - percentile)
        quantile_range = upper_quantile - lower_quantile
        upper_bound = upper_quantile + quantile_range * 1.5
        lower_bound = lower_quantile - quantile_range * 1.5
        lower_bound = max(lower_bound, filter_below)
        filtered_values = [v for v in all_values if v <= upper_bound and v >= lower_bound]
        step_dict["quantile_filtered"] = np.mean(filtered_values)
        df_means[step_name] = step_dict

    global_means = df_means.pop("GLOBAL", None)
    if global_means is not None:
        df_means.update({"GLOBAL": global_means})
    return df_means, series
