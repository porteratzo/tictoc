"""porter_bench: a Python benchmarking library for time and memory profiling."""

import logging
import os
from typing import Any

from .basic import CountDownClock, TimedCounter, Timer
from .Benchmarker import Benchmarker
from .GlobalBenchmarker import GlobalBenchmarker
from .MemoryBenchmarker import TICTOC_CUDA_AVAILABLE

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

bench_dict = GlobalBenchmarker()
benchmarker = Benchmarker("performance_benchmark/default")
timer = Timer()

TICTOC_TOGGLES: Any = os.getenv("TICTOC_TOGGLES", "0" * 8)
if TICTOC_TOGGLES is not None:

    def change_toggles(tictoc_toggles: int) -> list[bool]:
        """Convert an integer bitmask into a list of 8 boolean toggle values."""
        # Example: Change toggles based on the decimal value of TRY_CHANGE
        toggles = [False] * 8  # Assume 8 toggles for simplicity

        for i in range(len(toggles)):
            if tictoc_toggles & (1 << i):
                toggles[i] = True

        return toggles

    TICTOC_TOGGLES = change_toggles(int(TICTOC_TOGGLES, 2))
    logging.info(f"Active toggles: {TICTOC_TOGGLES}")
