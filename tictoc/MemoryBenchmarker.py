from collections import defaultdict
from typing import List, Dict, Union, Tuple
import matplotlib.pyplot as plt
import numpy as np
import os

import json
import psutil
import gc
import sys
from time import time
from .TimeBenchmarker import START_TIME, STOP_TIME, SPECIAL_NAMES

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

    def __init__(self, top_n: int = 0) -> None:
        self._enable = True
        self.memory_usage_list: List[Dict[str, Union[int, str]]] = []
        self.memory_usage: Dict[str, Union[int, str]] = defaultdict(dict)

        self.started = False
        self.track_memory_in_step = False  # Enable/disable memory tracking in the step method
        self.top_n = top_n  # Number of top memory-consuming objects to track
        self.track_cuda_memory = False  # Enable/disable CUDA memory tracking

    def enable_memory_tracking_in_step(self) -> None:
        """
        Enables memory usage tracking specifically for the step method.
        """
        self.track_memory_in_step = True

    def set_top_n(self, top_n: int) -> None:
        """
        Sets the number of top memory-consuming objects to track.
        """
        self.top_n = top_n

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
            self.memory_usage = defaultdict(dict)
            self.save_stats("gstep")
            self.start()

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

    def step(self, topic: str = "") -> None:
        """
        Tracks time spent on a specific step within the current benchmark.

        Args:
            topic (str, optional): The name of the step being timed. Defaults to an empty string.
        """
        if self._enable:
            if self.track_memory_in_step:  # Check both flags
                self.save_stats(topic)

    def save_stats(self, topic):
        top_memory_objects = get_top_memory_objects(self.top_n)
        cuda_memory_usage = self.get_cuda_memory_usage() if self.track_cuda_memory else None
        self.memory_usage[topic] = {
            "total memory usage": psutil.Process().memory_info().rss,
            "cuda memory usage": cuda_memory_usage,
            "top_memory_objects": top_memory_objects,
        }
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
        with open(self.file + "_MEMORY.json", "w") as jsonfile:
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

    def plot_data(self) -> None:
        """
        Generates a time series plot of benchmark results, highlighting outliers and missing data.
        """

        for step_number, step_dict in enumerate(self.WORKING_LIST):
            for step_name in step_dict.keys():
                self.series.append(
                    {
                        "step_name": step_name,
                        "step_number": step_number,
                        "total": step_dict[step_name]["total memory usage"],
                        "top_objects": [i[1] for i in step_dict[step_name]["top_memory_objects"]],
                    }
                )
        series = self.series
        plt.figure(figsize=(18, 6))
        plt.title(os.path.basename(self.file))
        if len(series) == 0:
            return
        total_mem = [val["total"] for val in series]
        top_objects = np.array([val["top_objects"] for val in series])
        names = [f'{val["step_number"]}_{val["step_name"]}' for val in series]
        x_names = np.arange(len(names))
        more_names = ["object_" + str(i) for i in range(len(top_objects[0]))]

        total_mem_mb = [mem / (1024**2) for mem in total_mem]
        top_objects_mb = top_objects / (1024**2)

        plt.plot(x_names, total_mem_mb, label="Total Memory Usage (MB)")

        for n, name in enumerate(more_names):
            plt.plot(x_names, top_objects_mb[:, n], label=f"{name} (MB)")

        plt.xticks(x_names, names, rotation=45)
        plt.ylabel("Memory Usage (MB)")
        plt.xlabel("Step")
        plt.tight_layout()
        plt.legend()
        plt.savefig(self.file + "_MEMORY_TIMELINE.png", dpi=200)

    def plot_cuda_data(self) -> None:
        """
        Generates a plot for CUDA memory usage metrics.
        """
        series = self.WORKING_LIST
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
