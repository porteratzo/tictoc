from tictoc import bench_dict
from random import random
import numpy as np
from tqdm import tqdm
import torch


def demo_bench_dict_usage():
    import time

    bench = bench_dict["test"]
    bench.enable_memory_tracking()
    bench.memory_benchmaker.enable_cuda_memory_tracking()
    # bench.enable_memory_tracking_in_step()
    my_list = [i for i in range(1000000)]
    for i in tqdm(range(8)):
        bench.gstep()
        my_list = my_list * 2
        if i == 0:
            bench.gstop()
            continue
        if i == 3:
            my_list = [i for i in range(1000000)]
            new_list = my_list * 2
            torch_tensor2 = torch.tensor(new_list)
            torch_tensor2 = torch_tensor2.to("cuda")
        if i > 3:
            new_list = new_list * 2

        if i == 6:
            new_list = [i for i in range(10_000_000)]

        if i == 1:
            np_array = np.random.random([10_000, 100_00])
            torch_tensor = torch.tensor(np_array)
            torch_tensor = torch_tensor.to("cuda")
            print(1)

        if i != 2:
            if i == 1:
                time.sleep(3)
            else:
                time.sleep(0.01 + random() * 0.02)  # Simulate some work
            bench.step("first simulated work")
            time.sleep(0.05 + random() * 0.1)  # Simulate another task
            bench.step("second simulated work")
        else:
            time.sleep(0.05 + random() * 0.1)  # Simulate another task
            bench.step("second simulated work")
        bench.gstop()
    bench_dict.save()


if __name__ == "__main__":
    demo_bench_dict_usage()
