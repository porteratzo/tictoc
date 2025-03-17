import os
from collections import defaultdict
from typing import DefaultDict, List, Dict, Optional
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import numpy as np
import csv
from .basic import Timer, get_timestamp


class Benchmarker:
    """
    A class for benchmarking performance during code execution.

    Attributes:
        enable (bool): Whether benchmarking is enabled. Defaults to True.
        step_timer (timer): A timer object for tracking step times.
        global_timer (timer): A timer object for tracking overall execution time.
        global_dict (list): A list of dictionaries storing step times for each step within a benchmark.
        step_dict (defaultdict(int)): A dictionary storing accumulated time for each step within the current benchmark.
        file (str): The base filename for storing benchmark results (e.g., "performance/base").
        folder (str): The folder path for storing benchmark results derived from the base filename.
        started (bool): Flag indicating if a benchmark has been started.
    """

    def __init__(self, file="performance/base") -> None:
        self.enable = True
        self.step_timer = Timer()
        self.global_timer = Timer()
        self.global_dict_list: List[DefaultDict[str, int]] = []
        self.step_dict: DefaultDict[str, int] = defaultdict(int)
        self.file = file
        self.folder = os.path.join(*file.split("/")[:-1])
        self.started = False

    def enable(self):
        """
        Enables benchmarking.
        """
        self.enable = True

    def disable(self):
        """
        Disables benchmarking.
        """
        self.enable = False

    def start(self):
        """
        Starts a new benchmark, resetting step and global timers.
        """
        if self.enable:
            self.step_timer.tic()
            self.global_timer.tic()
            self.started = True

    def gstep(self):
        """
        Ends the current step within a benchmark, stores accumulated step time,
        resets the step timer, and starts a new step.
        """
        if self.enable:
            self.gstop()
            self.step_dict = defaultdict(int)
            self.start()

    def gstop(self):
        """
        Ends the current benchmark, stores accumulated step time for the overall execution,
        and resets the started flag.
        """
        if self.enable:
            if self.started:
                if "global" not in self.step_dict.keys():
                    self.step_dict["global"] = self.global_timer.ttoc()
                self.global_dict_list.append(self.step_dict)
                self.started = False

    def step(self, topic=""):
        """
        Tracks time spent on a specific step within the current benchmark.

        Args:
            topic (str, optional): The name of the step being timed. Defaults to "".
        """
        if self.enable:
            self.step_dict[topic] += self.step_timer.ttoc()

    def make_bars(self, df_means):

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
        plt.savefig(self.file_path + "_bar.png", dpi=200)

    def label_bar_heights(self, df_means, bar_container):
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

    def write_summary(self, df_means):
        with open(self.file + "_summary.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            # Write the data to the CSV file
            for row in df_means.items():
                writer.writerow(row)

    def plot_data(self):
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

    def save_data(self):
        """
        Generates a plot of benchmark results, showing time series data for each step.
        Generates a summary of benchmark results, including mean time for each step.

        Saves the summary data to a CSV file and creates a bar chart visualization.

        Removes outliers using Interquartile Range (IQR).
        Saves the plot as a PNG image.
        """
        if self.enable:

            self.series = defaultdict(dict)
            for step_number, step_dict in enumerate(self.global_dict_list):
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


class g_benchmarker:
    """
    A class for managing multiple benchmark instances.

    Attributes:
        benchmarkers (dict): A dictionary storing benchmark instances with names as keys.
        enable (bool): Whether all benchmarks are enabled. Defaults to True.
        time_string (str): A timestamp string for file naming.
    """

    def __init__(self) -> None:
        self.benchmarkers: Dict[str:Benchmarker] = {}
        self.enable = True
        self.time_string = get_timestamp()
        self.default_path = f"performance_{self.time_string}"

    def set_default_path(self, path):
        self.time_string = get_timestamp()
        self.default_path = os.path.join(path, f"performance_{self.time_string}")

    def enable(self):
        """
        Enables all benchmark instances.
        """
        self.enable = True
        for bench in self.benchmarkers.values():
            bench.enable()

    def disable(self):
        """
        Disables all benchmark instances.
        """
        self.enable = False
        for bench in self.benchmarkers.values():
            bench.disable()

    def __getitem__(self, item: str) -> Benchmarker:
        """
        Retrieves a specific benchmark instance by name.

        If the benchmark instance doesn't exist, a new one is created with a filename based on
        the provided name and the timestamp string.

        Args:
            item (str): The name of the benchmark instance to retrieve.

        Returns:
            benchmarker: The requested benchmark instance.
        """
        get_bench: Optional[benchmarker] = self.benchmarkers.get(item, None)
        if get_bench is None:
            self.benchmarkers[item] = benchmarker(f"{self.default_path}/{item}")
        return self.benchmarkers[item]

    def save(self):
        """
        Calls the `plot_data` method on all enabled benchmark instances to save their results.
        """
        if self.enable:
            for bench in self.benchmarkers.values():
                bench.save_data()


class IterBench:
    """
    start a g_benchmarker at the start of an iterator like
    for i in start_bench(dataloader):
    """

    def __init__(
        self, dataloader, benchmark_halder: GlobalBenchmarker, name: str = "epoch"
    ) -> None:
        self.dataloader = dataloader
        self.name = name
        self.bench_handle = bench_handle

    def __len__(self):
        return len(self.dataloader)

    def __iter__(self):
        self.iter_obj = iter(self.dataloader)
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self.dataloader):
            self.bench_handle[self.name].gstep()
            self.n += 1
            while True:
                result = next(self.iter_obj)
                break
            return result
        else:
            raise StopIteration
