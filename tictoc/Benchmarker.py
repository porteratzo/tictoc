import os
from .TimeBenchmarker import TimeBenchmarker, TimerSaver
from .MemoryBenchmarker import MemoryBenchmarker, MemorySaver


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

    def __init__(
        self, file: str = "performance/base", save_on_gstop: int = None, save_on_step: bool = False
    ) -> None:
        self._enable = True
        self.time_benchmaker = TimeBenchmarker()
        self.memory_benchmaker = MemoryBenchmarker()
        self.memory_benchmaker.disable()
        self.register_memory_times = False
        self.register_memory_times_steps = False

        self.file = file
        self.folder = os.path.join(*file.split("/")[:-1])
        self.save_on_gstop = save_on_gstop
        self.save_on_step = save_on_step

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

    def enable_memory_tracking(self) -> None:
        """
        Enables memory tracking within the benchmark.
        """
        self.memory_benchmaker.enable()
        self.register_memory_times = True

    def enable_memory_tracking_in_step(self) -> None:
        """
        Enables memory tracking within each step of the benchmark.
        """
        self.memory_benchmaker.enable_memory_tracking_in_step()
        self.register_memory_times_steps = True

    def start(self) -> None:
        """
        Starts a new benchmark by resetting the step and global timers and setting the `started`
          flag to True.
        """
        if self._enable:
            self.time_benchmaker.start()
            self.started = True

    def gstep(self) -> None:
        """
        Ends the current step within a benchmark, stores accumulated step time and memory usage,
        resets the step timer, and starts a new step.
        """
        if self._enable:
            self.gstop()
            self.time_benchmaker.gstep()
            self.memory_benchmaker.gstep()
            if self.register_memory_times:
                self.time_benchmaker.step("gstep_memory")
            self.start()

    def gstop(self) -> None:
        """
        Ends the current benchmark, stores accumulated step time and memory usage for the overall
         execution,
        and resets the `started` flag.
        """
        if self._enable:
            if self.started:
                self.time_benchmaker.step("gstop")
                self.memory_benchmaker.gstop()
                if self.register_memory_times:
                    self.time_benchmaker.step("gstop_memory")
                self.time_benchmaker.gstop()
                self.started = False
                if self.save_on_gstop is not None:
                    if len(self.time_benchmaker.step_dict_list) % self.save_on_gstop == 0:
                        self.save_data()

    def step(self, topic: str = "") -> None:
        """
        Tracks time spent on a specific step within the current benchmark.

        Args:
            topic (str, optional): The name of the step being timed. Defaults to an empty string.
        """
        if self._enable:
            self.time_benchmaker.step(topic)
            self.memory_benchmaker.step(topic)
            if self.register_memory_times_steps:
                self.time_benchmaker.step(topic + "_memory")
            if self.save_on_step:
                os.makedirs(self.folder, exist_ok=True)
                orig_memory_usage, orig_memory_usage_list = self.memory_benchmaker.dummy_gstop()
                self.memory_benchmaker.save_data(self.file)
                self.memory_benchmaker.memory_usage, self.memory_benchmaker.memory_usage_list = (
                    orig_memory_usage,
                    orig_memory_usage_list,
                )

    def save_data(self, human_readable=False) -> None:
        """
        Saves benchmark results by generating plots, writing summaries, creating visualizations,
        saving the global dictionary list as a JSON file, and saving memory usage data.
        """
        if self._enable:
            os.makedirs(self.folder, exist_ok=True)
            TimerSaver(self.time_benchmaker, self.file).save_data()
            self.memory_benchmaker.save_data(self.file, human_readable=human_readable)
