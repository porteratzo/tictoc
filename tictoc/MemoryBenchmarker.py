from collections import defaultdict
from typing import List, Dict, Union, Tuple
import matplotlib.pyplot as plt
import numpy as np
import os

import json
import psutil
import gc
import sys
from time import time, sleep
import threading
from .TimeBenchmarker import START_TIME, STOP_TIME, SPECIAL_NAMES
from .utils import APPENDED_MEMORY_NAME, find_clusters, filter_no_change
from .basic import CountDownClock

try:
    import torch

    TICTOC_CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    TICTOC_CUDA_AVAILABLE = False

SPECIALS = True


class MemoryBenchmarker:
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

    def __init__(self, top_n: int = 0, gc_countdown_time=0.1) -> None:
        self._enable = True
        self.memory_usage_list: List[Dict[str, Union[int, str]]] = []
        self.memory_usage: Dict[str, list] = defaultdict(list)

        self.started = False
        self.track_memory_in_step = False  # Enable/disable memory tracking in the step method
        self.top_n = top_n  # Number of top memory-consuming objects to track
        self.track_cuda_memory = False  # Enable/disable CUDA memory tracking
        self.crono_counter = 0
        self.track_max_memory = False

        self.gc_countdown = CountDownClock(gc_countdown_time)

    def enable_memory_tracking_in_step(self) -> None:
        """
        Enables memory usage tracking specifically for the step method.
        """
        self.track_memory_in_step = True

    def enable_max_memory(self, poll_time=0.1):
        self.track_max_memory = True
        self.MaxMemoryMonitor = MaxMemoryMonitor(poll_time)

    def set_top_n(self, top_n: int) -> None:
        """
        Sets the number of top memory-consuming objects to track.
        """
        self.top_n = top_n

    def set_gc_time(self, set_gc_time: float) -> None:
        """
        Sets the number of top memory-consuming objects to track.
        """
        self.gc_countdown.set_count_down(set_gc_time)

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

    def enable_cuda_memory_tracking(self) -> None:
        """
        Enables CUDA memory usage tracking.
        """
        if TICTOC_CUDA_AVAILABLE:
            self.track_cuda_memory = True

    def disable_cuda_memory_tracking(self) -> None:
        """
        Disables CUDA memory usage tracking.
        """
        self.track_cuda_memory = False

    def start(self) -> None:
        """
        Starts a new benchmark by resetting the step and global timers and setting the `started`
          flag to True.
        """
        if self._enable:
            self.started = True

    def gstep(self) -> None:
        """
        Ends the current step within a benchmark, stores accumulated step time and memory usage,
        resets the step timer, and starts a new step.
        """
        if self._enable:
            self.memory_usage = defaultdict(list)
            self.crono_counter = 0
            self.save_stats("gstep")
            self.start()
            if self.track_max_memory:
                self.MaxMemoryMonitor.start()

    def gstop(self) -> None:
        """
        Ends the current benchmark, stores accumulated step time and memory usage for the overall
         execution,
        and resets the `started` flag.
        """
        if self._enable:
            if self.started:
                self.started = False
                self.save_stats("gstop")
                self.memory_usage_list.append(self.memory_usage)
                if self.track_max_memory:
                    self.MaxMemoryMonitor.stop()

    def step(self, topic: str = "", extra=None) -> None:
        """
        Tracks time spent on a specific step within the current benchmark.

        Args:
            topic (str, optional): The name of the step being timed. Defaults to an empty string.
        """
        if self._enable and self.track_memory_in_step:  # Check both flags
            if self.gc_countdown.completed():
                gc.collect()
                self.gc_countdown.reset()
            self.save_stats(topic, extra=extra)

    def save_stats(self, topic, extra=None):
        top_memory_objects = get_top_memory_objects(self.top_n)
        cuda_memory_usage = self.get_cuda_memory_usage() if self.track_cuda_memory else None
        max_used = self.MaxMemoryMonitor.step() if self.track_max_memory else None
        self.memory_usage[topic].append(
            {
                "total memory usage": psutil.Process().memory_info().rss,
                "cuda memory usage": cuda_memory_usage,
                "top_memory_objects": top_memory_objects,
                "crono_counter": self.crono_counter,
                "extra": extra,
                "max memory usage": max_used,
            }
        )
        self.crono_counter += 1
        if topic == "gstep":
            self.memory_usage[START_TIME] = time()
        elif topic == "gstop":
            self.memory_usage[STOP_TIME] = time()

    def get_cuda_memory_usage(self) -> Dict[str, int]:
        """
        Retrieves CUDA memory usage if a GPU is available.

        Returns:
            Dict[str, int]: A dictionary containing CUDA memory usage statistics.
        """
        if TICTOC_CUDA_AVAILABLE:
            return {
                "allocated": torch.cuda.memory_allocated(),
                "reserved": torch.cuda.memory_reserved(),
                "max_allocated": torch.cuda.max_memory_allocated(),
                "max_reserved": torch.cuda.max_memory_reserved(),
            }
        return {}

    def save_data(self, file):
        MemorySaver(self, file).save_data()


class MemorySaver:
    def __init__(
        self,
        benchmarker: MemoryBenchmarker,
        file: str = "performance/base",
    ) -> None:
        self.file = file
        self.folder = os.path.join(*file.split("/")[:-1])
        self.benchmarker = benchmarker

        self.series = []
        self.WORKING_LIST = self.benchmarker.memory_usage_list.copy()
        if self.benchmarker.started:
            self.WORKING_LIST.append(self.benchmarker.memory_usage)

    def save_data(self) -> None:
        """
        Saves benchmark results by generating plots, writing summaries, creating visualizations,
        saving the global dictionary list as a JSON file, and saving memory usage data.
        """
        # self.plot_data()
        # self.plot_cuda_data()  # Plot CUDA metrics
        self.save_memory_usage()

    def save_memory_usage(self) -> None:
        """
        Saves memory usage data to a JSON file.
        """
        final_format = self.format_json()
        with open(self.file + f"{APPENDED_MEMORY_NAME}.json", "w") as jsonfile:
            json.dump(final_format, jsonfile, indent=4)

    def format_json(self):
        final_format = []
        for n, step_dict in enumerate(self.WORKING_LIST):
            formated_step_dict = {"info": {}, "data": {}}
            working_keys = list(step_dict.keys())
            for key in working_keys:
                if key in SPECIAL_NAMES:
                    continue
                formated_step_dict["data"][key] = step_dict[key]
            formated_step_dict["info"]["STEP_NUMBER"] = n
            formated_step_dict["info"][START_TIME] = step_dict[START_TIME]
            formated_step_dict["info"][STOP_TIME] = step_dict.get(STOP_TIME, 0)
            final_format.append(formated_step_dict)
        return final_format


class MemoryPlotter:
    def __init__(self, folder_path: str = None) -> None:
        self.folder_path = folder_path

    def plot_data(
        self,
        memory_data,
        label="",
        filter_no_change_val=None,
        cluster=3,
        cluster_filter=0.05,
        plot_extra=None,
        highlight=[],
        highlight_color="r",
    ) -> None:
        """
        Generates a time series plot of benchmark results, highlighting outliers and missing data.
        """

        series = []
        totally_rejected = []
        for step_number, step_dict in enumerate(memory_data):
            crono_series = {}
            for step_name in step_dict.keys():
                for record in step_dict[step_name]:
                    crono_series[record["crono_counter"]] = {
                        "step_name": step_name,
                        "step_number": step_number,
                        "total": record["total memory usage"],
                        "max": record["max memory usage"],
                        "top_objects": [i[1] for i in record["top_memory_objects"]],
                    }
                    if plot_extra is not None:
                        if not isinstance(plot_extra, list):
                            plot_extra = [plot_extra]
                        for pe in plot_extra:
                            val = (
                                record["extra"].get(pe, None)
                                if record["extra"] is not None
                                else None
                            )
                            crono_series[record["crono_counter"]].update({pe: val})
            ordered_crono = [crono_series[n] for n in sorted(crono_series.keys())]
            if filter_no_change_val is not None:
                ordered_crono, rejected = filter_no_change(filter_no_change_val, ordered_crono)
                not_rejected = [i["step_name"] for i in ordered_crono]
                totally_rejected = [
                    i["step_name"] for i in rejected if i["step_name"] not in not_rejected
                ]

            if cluster > 0:
                ordered_crono = find_clusters(ordered_crono, cluster, cluster_filter)
            series.extend(ordered_crono)

        # plt.figure(figsize=(18, 6))
        if len(series) == 0:
            return
        total_mem = [val["total"] for val in series]

        top_objects = np.array([val["top_objects"] for val in series])
        names = [f'{val["step_number"]}_{val["step_name"]}' for val in series]
        x_names = np.arange(len(names))
        more_names = ["object_" + str(i) for i in range(len(top_objects[0]))]

        total_mem_mb = [mem / (1024**2) for mem in total_mem]

        top_objects_mb = top_objects / (1024**2)

        plt.plot(x_names, total_mem_mb, label="Total Memory Usage (MB) " + label)

        max_mem = [val["max"] for val in series]
        if any([i is not None for i in max_mem]):
            max_mem_mb = [mem / (1024**2) for mem in max_mem]
            max_x_names = [i for i in x_names if (max_mem_mb[i] is not None) & (max_mem_mb[i] > 0)]

            max_mem_mb = [i for i in max_mem_mb if (i is not None) & (i > 0)]
            plt.plot(max_x_names, max_mem_mb, label="Max Memory Usage (MB) " + label, marker="o")

        if plot_extra is not None:
            for pe in plot_extra:
                extra_total_mem = [val[pe] for val in series]
                extra_x_names = [i for i in x_names if extra_total_mem[i] is not None]
                extra_total_mem = [i for i in extra_total_mem if i is not None]
                extra_total_mem = [mem / (1024**2) for mem in extra_total_mem]
                plt.plot(
                    extra_x_names,
                    extra_total_mem,
                    label="Total Memory Usage (MB) " + label + " " + pe,
                )

        for n, name in enumerate(more_names):
            plt.plot(x_names, top_objects_mb[:, n], label=f"{name} (MB)")

        max_height = max(total_mem_mb)
        highlight_label_added = False
        if len(highlight) > 0:
            for x_name, name in zip(x_names, names):
                if "_".join(name.split("_")[1:]) in highlight:
                    rect = plt.Rectangle(
                        (x_name - 0.5, 0),
                        1.0,
                        max_height * 1.05,
                        linewidth=2,
                        edgecolor=highlight_color,
                        facecolor="none",
                        label=label if not highlight_label_added else "__nolegend__",
                    )
                    plt.gca().add_patch(rect)
                    highlight_label_added = True

        plt.xticks(x_names, names, rotation=90)
        plt.ylabel("Memory Usage (MB)")
        plt.xlabel("Step")
        plt.tight_layout()
        plt.legend()
        plt.grid(True)
        return totally_rejected

    def plot_cuda_data(self, memory_data) -> None:
        """
        Generates a plot for CUDA memory usage metrics.
        """
        series = memory_data
        if not any("cuda memory usage" in entry[key] for entry in series for key in entry.keys()):
            # Skip plotting if no CUDA data is available
            return

        # Extract CUDA metrics
        step_names = []
        allocated = []
        reserved = []
        max_allocated = []
        max_reserved = []

        for step_number, step_dict in enumerate(series):
            for step_name, metrics in step_dict.items():
                if "cuda memory usage" in metrics and metrics["cuda memory usage"]:
                    step_names.append(f"{step_number}_{step_name}")
                    cuda_metrics = metrics["cuda memory usage"]
                    allocated.append(cuda_metrics["allocated"] / (1024**2))  # Convert to MB
                    reserved.append(cuda_metrics["reserved"] / (1024**2))  # Convert to MB
                    max_allocated.append(cuda_metrics["max_allocated"] / (1024**2))  # Convert to MB
                    max_reserved.append(cuda_metrics["max_reserved"] / (1024**2))  # Convert to MB

        # Plot CUDA metrics
        plt.figure(figsize=(18, 6))
        plt.title(f"{os.path.basename(self.file)} - CUDA Memory Usage")
        x_names = np.arange(len(step_names))

        plt.plot(x_names, allocated, label="Allocated (MB)")
        plt.plot(x_names, reserved, label="Reserved (MB)")
        plt.plot(x_names, max_allocated, label="Max Allocated (MB)")
        plt.plot(x_names, max_reserved, label="Max Reserved (MB)")

        plt.xticks(x_names, step_names, rotation=45)
        plt.ylabel("Memory Usage (MB)")
        plt.xlabel("Step")
        plt.tight_layout()
        plt.legend()
        plt.savefig(self.file + "_CUDA_MEMORY.png", dpi=200)


def get_top_memory_objects(top_n: int = 5) -> List[Tuple[str, int]]:
    """
    Retrieves the top N memory-consuming objects along with their types and sizes.

    Returns:
        List[Tuple[str, int]]: A list of tuples containing the type and size of the top objects.
    """
    if top_n == 0:
        return []
    else:
        gc.collect()
        if True:
            all_objects = gc.get_objects()
        else:
            all_objects = get_all_objects()
        top_memory_objects = []
        for obj in all_objects:
            obj_size = sys.getsizeof(obj)
            try:
                if SPECIALS and isinstance(obj, (list, tuple, set, dict)):
                    if len(obj) == 0:
                        pass
                    elif isinstance(obj, (list, tuple, set)):
                        item = next(iter(obj))
                        obj_size += sys.getsizeof(item) * len(obj)
                    elif isinstance(obj, dict):
                        key, value = next(iter(obj.items()))
                        obj_size += (sys.getsizeof(value) + sys.getsizeof(key)) * len(obj)
            except RuntimeError:
                pass
            except ValueError:
                pass

            if len(top_memory_objects) < top_n:
                obj_type = str(type(obj))
                top_memory_objects.append((obj_type, obj_size))
                top_memory_objects.sort(key=lambda x: x[1], reverse=True)
            elif obj_size > top_memory_objects[-1][1]:
                obj_type = str(type(obj))
                top_memory_objects[-1] = (obj_type, obj_size)
                top_memory_objects.sort(key=lambda x: x[1], reverse=True)
    return top_memory_objects


class MaxMemoryMonitor:
    def __init__(self, poll_time=0.1):
        self.max_memory_usage = 0
        self.running = False
        self.lock = threading.Lock()
        self.poll_time = poll_time
        self.thread = None

    def start(self):
        """Start the memory monitoring thread."""
        self.running = True
        self.max_memory_usage = 0
        self.thread = threading.Thread(target=self._monitor_memory)
        self.thread.start()

    def stop(self):
        """Stop the memory monitoring thread."""
        self.running = False
        if self.thread is not None:
            self.thread.join()

    def _monitor_memory(self):
        """Monitor memory usage in a separate thread."""
        while self.running:
            # Get current memory usage
            current_memory_usage = psutil.Process().memory_info().rss

            # Update max memory usage
            with self.lock:
                self.max_memory_usage = max(self.max_memory_usage, current_memory_usage)

            # Sleep for 0.1 seconds
            sleep(self.poll_time)

    def step(self):
        """Reset and return the max memory usage since the last step."""
        with self.lock:
            max_usage = self.max_memory_usage
            self.max_memory_usage = 0
        return max_usage


def _getr(slist, olist, seen):
    for e in slist:
        if id(e) in seen:
            continue
        seen[id(e)] = None
        olist.append(e)
        tl = gc.get_referents(e)
        if tl:
            _getr(tl, olist, seen)

    # The public function.


def get_all_objects():
    """Return a list of all live Python
    objects, not including the list itself."""
    gcl = gc.get_objects()
    olist = []
    seen = {}
    # Just in case:
    seen[id(gcl)] = None
    seen[id(olist)] = None
    seen[id(seen)] = None
    # _getr does the real work.
    _getr(gcl, olist, seen)
    return olist
