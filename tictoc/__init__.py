from .GlobalBenchmarker import GlobalBenchmarker
from .Benchmarker import Benchmarker
from .basic import Timer

bench_dict = GlobalBenchmarker()
benchmarker = Benchmarker('performance_benchmark/default')
timer = Timer()
