from random import randint, random

import numpy as np
import torch
from tqdm import tqdm

from porter_bench import TICTOC_CUDA_AVAILABLE, bench_dict


def demo_bench_dict_usage():
    import time

    bench = bench_dict["test"]
    bench.enable_memory_tracking()
    bench.memory_benchmaker.enable_cuda_memory_tracking()
    bench.set_save_on_gstop(3)

    my_list = [i for i in range(500_000 + int(random() * 500_000))]
    for i in tqdm(range(8)):
        bench.gstep()
        my_list = my_list * 2
        if i == 0:
            bench.gstop()
            continue
        if i == 3:
            my_list = [i for i in range(500_000 + int(random() * 500_000))]
            new_list = my_list * 2
            if TICTOC_CUDA_AVAILABLE:
                torch_tensor2 = torch.tensor(new_list)
                torch_tensor2 = torch_tensor2.to("cuda")
        if i > 3:
            new_list = new_list * 2

        if i == 6:
            new_list = [i for i in range(5_000_000 + int(random() * 5_000_000))]
            if TICTOC_CUDA_AVAILABLE:
                torch_tensor2 = torch_tensor2.to("cpu")

        if i == 1:
            np_array = np.random.random(
                [5_000 + int(random() * 5_000), 5_000 + int(random() * 5_000)]
            )
            if TICTOC_CUDA_AVAILABLE:
                torch_tensor = torch.tensor(np_array)
                torch_tensor = torch_tensor.to("cuda")

        if i == 5:
            if TICTOC_CUDA_AVAILABLE:
                torch_tensor = torch_tensor.to("cpu")

        if i != 2:
            if i == 1:
                time.sleep(3)
            else:
                time.sleep(0.01 + random() * 0.02)  # Simulate some work
            bench.step("first simulated work")
            time.sleep(0.05 + random() * 0.1)  # Simulate another task
            bench.step("second simulated work")
            if i > 3 and i < 6:
                for i in range(randint(1, 3)):
                    time.sleep(0.05 + random() * 0.1)  # Simulate another task
                    bench.step("first simulated work")

        else:
            time.sleep(0.05 + random() * 0.1)  # Simulate another task
            bench.step("second simulated work")
        bench.gstop()
    bench_dict.save()


if __name__ == "__main__":
    demo_bench_dict_usage()
