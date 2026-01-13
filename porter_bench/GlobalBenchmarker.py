import os
from typing import Dict, List, Optional, Union

from .basic import get_timestamp
from .Benchmarker import Benchmarker

DEFAULT_SAVING_DIR = "TICTOC_PERFORMANCE"


class GlobalBenchmarker:
    """
    A class for managing multiple benchmark instances.

    Attributes:
        benchmarkers (Dict[str, Benchmarker]): A dictionary storing benchmark instances with names as keys.
        enable (bool): Whether all benchmarks are enabled. Defaults to True.
        time_string (str): A timestamp string for file naming.
        default_path (str): The default path for storing benchmark results.
    """

    def __init__(self) -> None:
        self.benchmarkers: Dict[str, Benchmarker] = {}
        self.enabled = True
        self.time_string = get_timestamp()
        self.default_path = os.path.join(DEFAULT_SAVING_DIR, self.time_string)

    def set_default_path(self, path: str) -> None:
        """
        Sets the default path for storing benchmark results.

        Args:
            path (str): The base directory for storing results.
        """
        self.time_string = get_timestamp()
        self.default_path = os.path.join(path, f"{self.time_string}")

    def enable(self) -> None:
        """
        Enables all benchmark instances by setting their `enable` flags to True.
        """
        self.enabled = True
        for bench in self.benchmarkers.values():
            bench.enable()

    def disable(self) -> None:
        """
        Disables all benchmark instances by setting their `enable` flags to False.
        """
        self.enabled = False
        for bench in self.benchmarkers.values():
            bench.disable()

    def __getitem__(self, item: str) -> Benchmarker:
        """
        Retrieves or creates a benchmark instance by name.

        Args:
            item (str): The name of the benchmark instance to retrieve.

        Returns:
            Benchmarker: The requested benchmark instance.
        """
        get_bench: Optional[Benchmarker] = self.benchmarkers.get(item, None)
        if get_bench is None:
            self.benchmarkers[item] = Benchmarker(f"{self.default_path}/{item}")
        return self.benchmarkers[item]

    def save(self) -> None:
        """
        Saves the results of all enabled benchmark instances by calling their `save_data` methods.
        """
        if self.enabled:
            for bench in self.benchmarkers.values():
                bench.save_data()


class IterBench:
    """
    A wrapper for iterators that integrates benchmarking at each iteration step.

    Attributes:
        dataloader (Union[List, Dict]): The data loader or iterable to wrap.
        name (str): The name of the benchmark instance to use. Defaults to "epoch".
        bench_handle (GlobalBenchmarker): The global benchmark manager.
    """

    def __init__(
        self,
        dataloader: Union[List, Dict],
        benchmark_handler: GlobalBenchmarker,
        name: str = "epoch",
    ) -> None:
        self.dataloader = dataloader
        self.name = name
        self.bench_handle = benchmark_handler

    def __len__(self) -> int:
        """
        Returns the length of the wrapped data loader.

        Returns:
            int: The number of items in the data loader.
        """
        return len(self.dataloader)

    def __iter__(self) -> "IterBench":
        """
        Initializes the iterator and resets the iteration counter.

        Returns:
            IterBench: The iterator instance.
        """
        self.iter_obj = iter(self.dataloader)
        self.n = 0
        return self

    def __next__(self) -> Union[Dict, List]:
        """
        Advances to the next item in the data loader, recording a benchmark step.

        Returns:
            Union[Dict, List]: The next item in the data loader.

        Raises:
            StopIteration: If the end of the data loader is reached.
        """
        if self.n < len(self.dataloader):
            self.bench_handle[self.name].gstep()
            self.n += 1
            while True:
                result = next(self.iter_obj)
                break
            return result
        else:
            raise StopIteration
