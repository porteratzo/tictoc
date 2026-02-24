# porter_bench

A Python benchmarking library for measuring execution time and memory usage across named pipeline steps and training loop iterations.

## Installation

```bash
pip install -e ".[dev]"
pre-commit install
# or
make install
```

## Quick start

```python
from porter_bench import bench_dict

for i in range(10):
    bench_dict["my_pipeline"].gstep()   # boundary between iterations

    data = load()
    bench_dict["my_pipeline"].step("load")

    result = process(data)
    bench_dict["my_pipeline"].step("process")

    bench_dict["my_pipeline"].gstop()

bench_dict.save()  # writes JSON files to TICTOC_PERFORMANCE/<timestamp>/
```

## Usage

### Pipeline benchmarking

`bench_dict["name"]` lazily creates a `Benchmarker`. The `gstep`/`gstop` pair marks iteration boundaries; `step(topic)` records time for a named sub-step within that iteration.

```python
from porter_bench import bench_dict

bench = bench_dict["pipeline"]
bench.set_save_on_gstop(4)  # auto-save every 4 iterations

for _ in range(20):
    bench.gstep()
    bench.step("load")
    bench.step("compute")
    bench.step("postprocess")
    bench.gstop()

bench_dict.save()
```

### Training loop with IterBench

`IterBench` wraps any iterable and calls `gstep()`/`gstop()` automatically around each iteration:

```python
from porter_bench import bench_dict
from porter_bench.GlobalBenchmarker import IterBench

for batch in IterBench(dataloader, bench_dict, "training"):
    bench_dict["training"].step("forward")
    bench_dict["training"].step("backward")
```

### Memory tracking

```python
bench = bench_dict["memory"]
bench.enable_memory_tracking(per_step=True)          # RAM tracking per step
bench.memory_benchmaker.enable_max_memory(poll_time=0.05)  # peak RAM polling

# Optional CUDA tracking (requires torch with CUDA)
bench.memory_benchmaker.enable_cuda_memory_tracking()
```

### Low-level timer utilities

```python
from porter_bench import timer
from porter_bench.basic import CountDownClock, TimedCounter

# Simple timer
timer.tic()
result = do_work()
elapsed = timer.toc()          # seconds since tic
elapsed = timer.ttoc()         # toc + reset

# Countdown
clock = CountDownClock(count_down_time=4.0)
while not clock.completed():
    print("time left:", clock.time_left())

# Frequency counter
counter = TimedCounter()
counter.start()
for _ in range(100):
    do_work()
    counter.count()
counter.stop()
print("frequency:", counter.get_frequency(), "Hz")
```

### Auto-save options

```python
bench.set_save_on_gstop(N)   # save every N iterations
bench.set_save_on_step(True)  # save after every step
```

## Loading and visualising results

```python
from porter_bench.utils import load_record
from porter_bench.DataHandler import DataHandler

record = load_record(".")          # loads latest run from TICTOC_PERFORMANCE/
handler = DataHandler({"run": record})

handler.plot_times(record_name="pipeline")
handler.make_bars(record_name="pipeline")
handler.plot_crono(record_name="pipeline")
handler.plot_memory_usage(record_name="memory")
```

Or run the standalone script after `make example`:

```bash
python generate_plots.py --path . --output PLOTS --show
```

Plots are saved to `PLOTS/` as `<name>_times.png`, `<name>_bars.png`, `<name>_crono.png`, `<name>_memory.png`.

## Output files

All JSON files are written under `TICTOC_PERFORMANCE/<timestamp>/<name>/`:

| File | Contents |
|---|---|
| `*_STEP_DICT_DATA.json` | Per-iteration step timings |
| `*_STEP_DICT_SUMMARY.json` | Aggregated mean/min/max stats |
| `*_MEMORY.json` | RAM and CUDA memory snapshots |

## Development

```bash
make test    # pytest
make lint    # pre-commit run --all-files
make example # run example.py then generate_plots.py
```

### TICTOC_TOGGLES

`TICTOC_TOGGLES` is an 8-bit binary string environment variable that exposes boolean feature flags for automating test variations without code changes. Each bit position is an independent toggle (index 0 = rightmost bit).

```bash
TICTOC_TOGGLES="00000001" pytest   # toggle 0 on
TICTOC_TOGGLES="00000011" pytest   # toggles 0 and 1 on
TICTOC_TOGGLES="10000000" pytest   # toggle 7 on
```

Inside the library, `TICTOC_TOGGLES` is parsed into a `list[bool]` of length 8, importable as:

```python
from porter_bench import TICTOC_TOGGLES

if TICTOC_TOGGLES[0]:
    # behaviour variant A
else:
    # behaviour variant B
```

This lets you drive conditional code paths — alternative algorithms, stricter assertions, extra logging — purely from the environment, making it easy to test both branches in CI or a single `pytest` run.
