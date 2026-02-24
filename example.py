"""Example usage of the porter_bench benchmarking library.

Demonstrates:
    1. Multi-step pipeline benchmarking via GlobalBenchmarker
    2. IterBench  — automatic per-iteration timing for training loops
    3. RAM memory  — tracking allocation and release across iterations
    4. CUDA memory — GPU allocation tracking (skipped without a GPU)
"""

import time
from random import random

import numpy as np
from tqdm import tqdm

from porter_bench import TICTOC_CUDA_AVAILABLE, bench_dict
from porter_bench.GlobalBenchmarker import IterBench

# ── 1. Multi-step data-processing pipeline ────────────────────────────────────


def demo_pipeline() -> None:
    """Benchmark a four-stage data-processing pipeline over 12 iterations."""
    bench = bench_dict["pipeline"]
    bench.set_save_on_gstop(4)  # auto-save every 4 iterations

    print("\n[1] Pipeline benchmark — 12 iterations")
    for _ in tqdm(range(12)):
        bench.gstep()

        # Stage 1 — simulate loading data
        data = np.random.random((100, 1_000))
        time.sleep(0.02 + random() * 0.01)
        bench.step("load")

        # Stage 2 — normalise
        data = (data - data.mean()) / (data.std() + 1e-8)
        time.sleep(0.01 + random() * 0.005)
        bench.step("normalise")

        # Stage 3 — heavy compute (SVD)
        _ = np.linalg.svd(data, compute_uv=False)
        time.sleep(0.05 + random() * 0.02)
        bench.step("compute")

        # Stage 4 — postprocess
        time.sleep(0.01 + random() * 0.005)
        bench.step("postprocess")

        bench.gstop()


# ── 2. Training loop via IterBench ────────────────────────────────────────────


def demo_training_loop() -> None:
    """Use IterBench to measure per-iteration time without manual gstep calls."""
    batches = [np.random.random((64, 256)) for _ in range(10)]

    print("\n[2] Training-loop benchmark via IterBench — 10 iterations")
    for batch in tqdm(IterBench(batches, bench_dict, "training")):
        # Forward pass
        output = batch @ batch.T
        time.sleep(0.03 + random() * 0.01)
        bench_dict["training"].step("forward")

        # Backward pass — simulate gradient computation
        _ = np.linalg.eigvalsh(output)
        time.sleep(0.02 + random() * 0.01)
        bench_dict["training"].step("backward")

        # Weight update
        time.sleep(0.005 + random() * 0.003)
        bench_dict["training"].step("update")


# ── 3. RAM memory tracking ────────────────────────────────────────────────────


def demo_memory_tracking() -> None:
    """Show RAM growth and release across iterations with per-step tracking."""
    bench = bench_dict["memory"]
    bench.enable_memory_tracking(per_step=True)
    bench.memory_benchmaker.enable_max_memory(poll_time=0.05)

    print("\n[3] Memory tracking — 8 iterations")
    retained: list = []
    for i in tqdm(range(8)):
        bench.gstep()

        # Allocate a progressively larger array
        arr = np.random.random((8_000 + i * 3_000, 512))
        retained.append(arr)
        time.sleep(0.02)
        bench.step("allocate")

        # Compute on the array
        _ = arr.sum(axis=0)
        time.sleep(0.01 + random() * 0.01)
        bench.step("compute")

        # Release every third iteration to create visible memory drops
        if i % 3 == 2:
            retained.clear()
        bench.step("maybe_free")

        bench.gstop()


# ── 4. CUDA memory tracking ───────────────────────────────────────────────────


def demo_cuda_memory() -> None:
    """Track GPU allocation and deallocation across 6 iterations."""
    import torch

    bench = bench_dict["cuda"]
    bench.enable_memory_tracking()
    bench.memory_benchmaker.enable_cuda_memory_tracking()

    print("\n[4] CUDA memory tracking — 6 iterations")
    gpu_tensors: list = []
    for i in tqdm(range(6)):
        bench.gstep()

        t = torch.randn(3_000 + i * 500, 512, device="cuda")
        gpu_tensors.append(t)
        time.sleep(0.01)
        bench.step("gpu_alloc")

        _ = t @ t.T
        time.sleep(0.02 + random() * 0.01)
        bench.step("gpu_compute")

        # Free halfway through to show a GPU memory drop
        if i == 3:
            gpu_tensors.clear()
            torch.cuda.empty_cache()
        bench.step("maybe_free_gpu")

        bench.gstop()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if TICTOC_CUDA_AVAILABLE:
        print("CUDA detected — GPU memory tracking will run.")
    else:
        print("No GPU detected — CUDA demo will be skipped.")

    demo_pipeline()
    demo_training_loop()
    demo_memory_tracking()

    if TICTOC_CUDA_AVAILABLE:
        demo_cuda_memory()
    else:
        print("\n[4] Skipping CUDA demo.")

    print("\n[5] Saving all benchmarks…")
    bench_dict.save()
    print("Done. Results written to TICTOC_PERFORMANCE/")
