# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Use the `porter_bench` conda environment:
```bash
conda activate porter_bench
```

## Commands

**Install (development):**
```bash
pip install -e ".[dev]"
pre-commit install
```

**Run tests:**
```bash
pytest
pytest test_thread_safety.py          # run a specific test file
pytest test_thread_safety.py::test_concurrent_access  # run a single test
```

**Lint and format:**
```bash
black .
isort .
flake8
mypy porter_bench/
pylint porter_bench/
pre-commit run --all-files            # run all hooks at once
```

**Run the example:**
```bash
python example.py
```

## Architecture

`porter_bench` is a Python benchmarking library for measuring execution time and memory usage. All classes use `threading.Lock` for thread safety — this is a core design invariant. Locks should be released before calling other class methods or doing I/O to prevent deadlocks.

### Core class hierarchy

```
GlobalBenchmarker          # dict-like manager; bench_dict["name"] auto-creates Benchmarker instances
└── Benchmarker            # high-level facade combining time + memory tracking
    ├── TimeBenchmarker    # time measurement; stores step_dict_list of per-iteration data
    └── MemoryBenchmarker  # RAM/CUDA memory tracking via psutil and torch
```

### Key abstractions

**Benchmarker lifecycle** (`gstep`/`gstop` pattern):
- `gstep()` — marks the boundary between iterations (calls `gstop` then starts a new iteration)
- `gstop()` — finalizes the current iteration and saves data to the list
- `step(topic)` — records time/memory for a named sub-step within the current iteration
- `start()` — begins a fresh iteration without closing a previous one

**GlobalBenchmarker** ([porter_bench/GlobalBenchmarker.py](porter_bench/GlobalBenchmarker.py)):
- Module-level singleton `bench_dict` is created at import time in `__init__.py`
- `bench_dict["name"]` creates a `Benchmarker` with path `TICTOC_PERFORMANCE/<timestamp>/<name>`
- `bench_dict.save()` saves all managed benchmarkers to JSON

**Data saving** ([porter_bench/TimeBenchmarker.py](porter_bench/TimeBenchmarker.py), [porter_bench/MemoryBenchmarker.py](porter_bench/MemoryBenchmarker.py)):
- `TimerSaver` / `MemorySaver` take a thread-safe snapshot, then write JSON files without holding locks
- Output files: `<file>_STEP_DICT_DATA.json`, `<file>_STEP_DICT_SUMMARY.json`, `<file>_MEMORY.json`

**Data loading and analysis** ([porter_bench/utils.py](porter_bench/utils.py), [porter_bench/DataHandler.py](porter_bench/DataHandler.py)):
- `load_record(path)` loads the latest saved benchmark run into a dict with keys `summary`, `absolutes`, `calls`, `memory`
- `DataHandler` wraps the loaded record dict and provides `plot_times()`, `plot_memory_usage()`, `make_bars()`, `plot_crono()`
- `TimePlotter` / `MemoryPlotter` handle matplotlib rendering; `summurize()` computes mean/min/max/quantile-filtered stats

**Optional auto-save:**
- `set_save_on_gstop(N)` — saves every N global stops
- `set_save_on_step(True)` — saves after every step call

**Environment variable:** `TICTOC_TOGGLES` (8-bit binary string) controls feature toggles; defaults to `"00000000"`.

**CUDA support:** Optional; detected via `torch.cuda.is_available()` and exposed as `TICTOC_CUDA_AVAILABLE`.
