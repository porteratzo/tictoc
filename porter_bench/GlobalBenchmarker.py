"""Manager class for multiple named Benchmarker instances."""

import os
import threading
from typing import Dict, List, Optional, Union

from .basic import get_timestamp
from .Benchmarker import Benchmarker

DEFAULT_SAVING_DIR = "TICTOC_PERFORMANCE"


class GlobalBenchmarker:
    """Manage a collection of named Benchmarker instances.

    Attributes:
        benchmarkers (Dict[str, Benchmarker]): Benchmark instances keyed by name.
        enable (bool): Whether all benchmarks are enabled. Defaults to True.
        time_string (str): A timestamp string for file naming.
        default_path (str): The default path for storing benchmark results.
    """

    def __init__(self) -> None:
        """Initialise with an empty benchmarker registry and a fresh timestamp."""
        self.benchmarkers: Dict[str, Benchmarker] = {}
        self.enabled = True
        self.time_string = get_timestamp()
        self.default_path = os.path.join(DEFAULT_SAVING_DIR, self.time_string)
        self._lock = threading.Lock()

    def set_default_path(self, path: str) -> None:
        """Set the default path for storing benchmark results.

        Args:
            path (str): The base directory for storing results.
        """
        with self._lock:
            self.time_string = get_timestamp()
            self.default_path = os.path.join(path, f"{self.time_string}")

    def enable(self) -> None:
        """Enable all benchmark instances."""
        with self._lock:
            self.enabled = True
            benchmarkers_snapshot = list(self.benchmarkers.values())

        # Call enable on benchmarkers outside the lock to avoid potential deadlocks
        for bench in benchmarkers_snapshot:
            bench.enable()

    def disable(self) -> None:
        """Disable all benchmark instances."""
        with self._lock:
            self.enabled = False
            benchmarkers_snapshot = list(self.benchmarkers.values())

        # Call disable on benchmarkers outside the lock to avoid potential deadlocks
        for bench in benchmarkers_snapshot:
            bench.disable()

    def __getitem__(self, item: str) -> Benchmarker:
        """Retrieve or lazily create a benchmark instance by name.

        Args:
            item (str): The name of the benchmark instance to retrieve.

        Returns:
            Benchmarker: The requested benchmark instance.
        """
        with self._lock:
            get_bench: Optional[Benchmarker] = self.benchmarkers.get(item, None)
            if get_bench is None:
                self.benchmarkers[item] = Benchmarker(f"{self.default_path}/{item}")
            return self.benchmarkers[item]

    def save(self) -> None:
        """Save results of all enabled benchmark instances to disk."""
        with self._lock:
            enabled = self.enabled
            benchmarkers_snapshot = list(self.benchmarkers.values())

        # Call save_data outside the lock to avoid potential deadlocks
        if enabled:
            for bench in benchmarkers_snapshot:
                bench.save_data()


class IterBench:
    """Wrap an iterable and record a benchmark step on each iteration.

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
        """Initialise the iterator wrapper with a dataloader and benchmark handle."""
        self.dataloader = dataloader
        self.name = name
        self.bench_handle = benchmark_handler

    def __len__(self) -> int:
        """Return the length of the wrapped data loader."""
        return len(self.dataloader)

    def __iter__(self) -> "IterBench":
        """Initialise the iterator and reset the iteration counter."""
        self.iter_obj = iter(self.dataloader)
        self.n = 0
        return self

    def __next__(self) -> Union[Dict, List]:
        """Advance to the next item, recording a benchmark step.

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
