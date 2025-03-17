from .benchmarkers import GlobalBenchmarker, Benchmarker
from .basic import Timer

bench_dict = GlobalBenchmarker()
benchmarker = Benchmarker('performance_benchmark/default')
timer = Timer()
