from tictoc import bench_dict
from random import random


def demo_bench_dict_usage():
    import time

    bench = bench_dict["test"]
    for i in range(8):
        bench.gstep()
        if i == 0:
            bench.gstop()
            continue
        if i != 2:
            if i == 1:
                time.sleep(5)
            else:
                time.sleep(0.01 + random() * 0.02)  # Simulate some work
            bench.step("first simulated work")
            time.sleep(0.5 + random() * 0.1)  # Simulate another task
            bench.step("second simulated work")
        else:
            time.sleep(0.5 + random() * 0.1)  # Simulate another task
            bench.step("second simulated work")
        bench.gstop()
    bench_dict.save()


if __name__ == "__main__":
    demo_bench_dict_usage()
