#!/usr/bin/env python3
"""
Test script to verify thread-safety of the benchmarking library.
"""

import threading
import time

from porter_bench import bench_dict


def worker(worker_id, num_iterations, errors):
    """Worker function that performs benchmarking operations."""
    try:
        for i in range(num_iterations):
            # Access GlobalBenchmarker to get/create benchmarker instances
            benchmarker = bench_dict[f"worker_{worker_id}"]

            # Start a benchmark
            benchmarker.start()

            # Perform some steps
            benchmarker.step(f"operation_1_{i}")
            time.sleep(0.001)  # Simulate some work

            benchmarker.step(f"operation_2_{i}")
            time.sleep(0.001)  # Simulate some work

            # Stop the benchmark
            benchmarker.gstop()

            # Occasionally use gstep
            if i % 10 == 0:
                benchmarker.start()
                benchmarker.step(f"checkpoint_{i}")
                benchmarker.gstep()
    except Exception as e:
        errors.append(e)


def test_concurrent_access():
    """Test concurrent access to the benchmarking library."""
    print("Starting thread-safety test...")
    print(f"Creating {10} worker threads with {50} iterations each...")

    threads = []
    errors = []
    num_workers = 10
    num_iterations = 50

    # Create and start threads
    start_time = time.time()
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(i, num_iterations, errors))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    if errors:
        raise ExceptionGroup("worker threads failed", errors)

    elapsed = time.time() - start_time

    print(f"All threads completed successfully in {elapsed:.2f} seconds!")
    print(
        f"Total operations: {num_workers * num_iterations * 3} (across {num_workers} threads)"
    )
    print("\nThread-safety test PASSED!")

    # Verify data integrity
    print("\nVerifying data integrity...")
    for i in range(num_workers):
        benchmarker = bench_dict[f"worker_{i}"]
        num_steps = len(benchmarker.time_benchmaker.step_dict_list)
        # Each worker calls gstop() num_iterations times
        assert (
            num_steps == num_iterations
        ), f"Worker {i}: expected {num_iterations} steps, got {num_steps}"

    print("\nData integrity verified!")


if __name__ == "__main__":
    test_concurrent_access()
