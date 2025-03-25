from .GlobalBenchmarker import GlobalBenchmarker
from .Benchmarker import Benchmarker
from .basic import Timer
from .MemoryBenchmarker import CUDA_AVAILABLE
bench_dict = GlobalBenchmarker()
benchmarker = Benchmarker('performance_benchmark/default')
timer = Timer()
