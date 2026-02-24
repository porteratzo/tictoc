"""High-level benchmarker combining time and memory tracking."""

import os
import threading
from typing import Any, Optional

from porter_bench.MemoryBenchmarker import MemoryBenchmarker
from porter_bench.TimeBenchmarker import TimeBenchmarker


class Benchmarker:
    """Facade combining time and memory benchmarking for a named workload.

    Attributes:
        enable (bool): Whether benchmarking is enabled. Defaults to True.
        step_timer (Timer): A timer object for tracking step times.
        global_timer (Timer): A timer object for tracking overall execution time.
        global_dict_list (List[DefaultDict[str, int]]): A list of dictionaries
            storing step times for each step within a benchmark.
        step_dict (DefaultDict[str, int]): A dictionary storing accumulated time
            for each step within the current benchmark.
        file (str): The base filename for storing benchmark results.
        folder (str): The folder path derived from the base filename.
        started (bool): Flag indicating if a benchmark has been started.
    """

    def __init__(
        self,
        file: str = "performance/base",
        save_on_gstop: int = 0,
        save_on_step: bool = False,
    ) -> None:
        """Initialise the benchmarker with the given file path and save settings."""
        self.enabled = True
        self.time_benchmaker = TimeBenchmarker()
        self.memory_benchmaker = MemoryBenchmarker()
        self.memory_benchmaker.disable()
        self.register_memory_timings = False

        self.file = file
        self.folder = os.path.join(*file.split("/")[:-1])
        self.save_on_gstop = save_on_gstop
        self.save_on_step = save_on_step

        self.started = False
        self._lock = threading.Lock()

    def set_save_on_step(self, save_on_step: bool = True) -> None:
        """Set the `save_on_step` flag to the specified value."""
        with self._lock:
            self.save_on_step = save_on_step

    def set_save_on_gstop(self, save_on_gstop: int = 1) -> None:
        """Set the `save_on_gstop` value to the specified value."""
        with self._lock:
            self.save_on_gstop = save_on_gstop

    def enable(self) -> None:
        """Enable benchmarking by setting the `enable` flag to True."""
        with self._lock:
            self.enabled = True

    def disable(self) -> None:
        """Disable benchmarking by setting the `enable` flag to False."""
        with self._lock:
            self.enabled = False

    def enable_memory_tracking(self, per_step: bool = False) -> None:
        """Enable memory tracking within the benchmark."""
        # Call these outside lock to avoid potential deadlock
        self.memory_benchmaker.enable()
        if per_step:
            self.memory_benchmaker.enable_memory_tracking_in_step()

        with self._lock:
            self.register_memory_timings = True

    def start(self) -> None:
        """Start a new benchmark iteration.

        Resets the step and global timers and sets the `started` flag to True.
        """
        with self._lock:
            if not self.enabled:
                return

        # Call time_benchmaker.start() outside lock to avoid potential deadlock
        self.time_benchmaker.start()

        with self._lock:
            if self.enabled:
                self.started = True

    def gstep(self) -> None:
        """Advance to the next benchmark iteration.

        Ends the current step, stores accumulated data, resets the step timer,
        and starts a new step.
        """
        with self._lock:
            enabled = self.enabled
            register_memory = self.register_memory_timings

        if enabled:
            self.gstop()
            self.time_benchmaker.gstep()
            self.memory_benchmaker.gstep()
            if register_memory:
                self.time_benchmaker.step("gstep_memory")
            self.start()

    def gstop(self) -> None:
        """End the current benchmark iteration.

        Stores accumulated step time and memory usage for the overall execution
        and resets the `started` flag.
        """
        with self._lock:
            if not self.enabled:
                return

            if not self.started:
                return

            register_memory = self.register_memory_timings
            save_on_gstop = self.save_on_gstop
            self.started = False

        # Perform benchmarking operations outside lock
        self.time_benchmaker.step("gstop")
        self.memory_benchmaker.gstop()
        if register_memory:
            self.time_benchmaker.step("gstop_memory")
        self.time_benchmaker.gstop()

        if save_on_gstop > 0:
            with self.time_benchmaker._lock:
                num_steps = len(self.time_benchmaker.step_dict_list)
            if num_steps % save_on_gstop == 0:
                self.save_data()

    def step(
        self,
        topic: str = "",
        memory_extra: Optional[Any] = None,
        time_extra: Optional[Any] = None,
    ) -> None:
        """Record time and memory for a named sub-step within the current iteration.

        Args:
            topic: The name of the step being timed. Defaults to an empty string.
            memory_extra: Optional extra data to attach to the memory record.
            time_extra: Optional extra data to attach to the time record.
        """
        with self._lock:
            if not self.enabled:
                return

            register_memory = self.register_memory_timings
            save_on_step = self.save_on_step

        # Perform benchmarking operations outside lock
        self.time_benchmaker.step(topic, extra=time_extra)
        self.memory_benchmaker.step(topic, extra=memory_extra)
        if register_memory:
            self.time_benchmaker.step(topic + "_MEMORY_STEP")

        if save_on_step:
            self.save_data()

    def save_data(self) -> None:
        """Save benchmark results to disk.

        Writes timing summaries, step data, and memory usage JSON files.
        """
        with self._lock:
            if not self.enabled:
                return

            folder = self.folder
            file = self.file

        # Perform file operations outside lock
        os.makedirs(folder, exist_ok=True)
        self.time_benchmaker.save_data(file)
        self.memory_benchmaker.save_data(file)
