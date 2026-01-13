import os
import logging
from .GlobalBenchmarker import GlobalBenchmarker
from .Benchmarker import Benchmarker
from .basic import *
from .MemoryBenchmarker import TICTOC_CUDA_AVAILABLE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bench_dict = GlobalBenchmarker()
benchmarker = Benchmarker("performance_benchmark/default")
timer = Timer()

TICTOC_TOGGLES = os.getenv("TICTOC_TOGGLES", "0"*8)
if TICTOC_TOGGLES is not None:

    def change_toggles(tictoc_toggles):
        # Example: Change toggles based on the decimal value of TRY_CHANGE
        toggles = [False] * 8  # Assume 8 toggles for simplicity

        for i in range(len(toggles)):
            if tictoc_toggles & (1 << i):
                toggles[i] = True

        return toggles

    TICTOC_TOGGLES = change_toggles(int(TICTOC_TOGGLES,2))
    logging.info(f"Active toggles: {TICTOC_TOGGLES}")
