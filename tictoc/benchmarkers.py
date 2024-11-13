import os
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt

import numpy as np
import csv
from .basic import timer


class benchmarker:
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
        self.step_timer = timer()
        self.global_timer = timer()
        self.global_dict = []
        self.step_dict = defaultdict(int)
        self.file = file
        self.folder = "/".join(file.split("/")[:-1])
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
                self.global_dict.append(self.step_dict)
                self.started = False

    def step(self, topic=""):
        """
        Tracks time spent on a specific step within the current benchmark.

        Args:
            topic (str, optional): The name of the step being timed. Defaults to "".
        """
        if self.enable:
            self.step_dict[topic] += self.step_timer.ttoc()

    def data_summary(self):
        """
        Generates a summary of benchmark results, including mean time for each step.

        Saves the summary data to a CSV file and creates a bar chart visualization.
        """
        if self.enable:
            self.gstop()

            self.series = defaultdict(dict)
            for n, i in enumerate(self.global_dict):
                for key in i.keys():
                    self.series[key][n] = i[key]
            means = {
                k: np.mean(list(self.series[k].values())) for k, v in self.series.items()
            }

            df = means
            os.makedirs(self.folder, exist_ok=True)
            with open(self.file + "_summary.csv", "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                # Write the data to the CSV file
                for row in df.items():
                    writer.writerow(row)

            plt.figure(figsize=(18, 6))
            mymap = plt.get_cmap("jet")
            plt.title(os.path.basename(self.file) + "_bar")
            plt.tight_layout()
            rescale = lambda y: (y - np.min(y)) / (np.max(y) - np.min(y))
            bar_container = plt.bar(
                np.arange(len(df.values())),
                [i for i in df.values()],
                label=list(df.keys()),
                color=mymap(rescale(list(df.values()))),
            )
            y_offset = max(df.values()) * 0.04
            for idx, bar in enumerate(bar_container):
                # Get height and label for the bar
                height = bar.get_height()
                label = list(df.keys())[idx]
                # Annotate the bar with its label and value
                plt.text(
                    bar.get_x() + bar.get_width() / 2, height + y_offset,
                    f'{round(height,3)}',
                    ha='center', va='top'
                )
            plt.xticks(np.arange(len(df)), list(df.keys()))
            plt.legend(list(df.keys()))
            plt.savefig(self.file + "_bar.png", dpi=200)

    def plot_data(self):
        """
        Generates a plot of benchmark results, showing time series data for each step.

        Optionally removes outliers using Interquartile Range (IQR).
        Saves the plot as a PNG image.
        """
        if self.enable:
            self.data_summary()
            series = self.series
            plt.figure(figsize=(18, 6))
            plt.title(os.path.basename(self.file))
            for keys in series.keys():
                X = np.array(list(series[keys].keys()))
                Y = np.array(list(series[keys].values()))

                Q1 = np.percentile(Y, 25, interpolation="midpoint")
                Q3 = np.percentile(Y, 75, interpolation="midpoint")
                IQR = Q3 - Q1
                bool_idx = (Y < (IQR + 1.5 * Q3)) & (Y > (IQR - 1.5 * Q1))
                X = X[bool_idx]
                Y = Y[bool_idx]

                plt.plot(X, Y)
            plt.tight_layout()
            plt.legend(list(series.keys()))
            plt.savefig(self.file + ".png", dpi=200)


class g_benchmarker:
    """
    A class for managing multiple benchmark instances.

    Attributes:
        benchmarkers (dict): A dictionary storing benchmark instances with names as keys.
        enable (bool): Whether all benchmarks are enabled. Defaults to True.
        time_string (str): A timestamp string for file naming.
    """

    def __init__(self) -> None:
        self.benchmarkers = {}
        self.enable = True
        today = datetime.now()
        self.time_string = today.strftime("%d:%m:%Y:%H:%M")

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

    def __getitem__(self, item: str) -> benchmarker:
        """
        Retrieves a specific benchmark instance by name.

        If the benchmark instance doesn't exist, a new one is created with a filename based on
        the provided name and the timestamp string.

        Args:
            item (str): The name of the benchmark instance to retrieve.

        Returns:
            benchmarker: The requested benchmark instance.
        """
        get_bench: benchmarker or None = self.benchmarkers.get(item, None)
        if get_bench is None:
            self.benchmarkers[item] = benchmarker(
                f"performance_{self.time_string}/{item}"
            )
        return self.benchmarkers[item]

    def save(self):
        """
        Calls the `plot_data` method on all enabled benchmark instances to save their results.
        """
        if self.enable:
            for bench in self.benchmarkers.values():
                bench.plot_data()


class start_bench:
    def __init__(self, dataloader, bench_handle, name="epoch") -> None:
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
                try:
                    result = next(self.iter_obj)
                    break
                except:
                    raise
            return result
        else:
            raise StopIteration
