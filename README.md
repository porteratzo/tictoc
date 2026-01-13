# README for tictoc Repository

Welcome to the tictoc repository! This repository is dedicated to providing a comprehensive benchmarking tool that leverages the `bench_dict` object. This tool is designed to facilitate the measurement of execution time for various steps in your code, allowing for a detailed analysis of performance bottlenecks and efficiency improvements.

## Features

- **Step-wise Time Measurement**: Utilize the `benchdict` object to measure the time taken by individual steps within your code.
- **Global Step Tracking**: Track the time for overarching global steps, providing a broader view of your code's performance.
- **Automatic Data Saving**: Automatically saves the mean times of each step to a CSV file, making data analysis and sharing straightforward.
- **Visualization**: Generates a bar plot for the mean time per step and a time series for each global step, offering visual insights into your code's performance.

## Usage

Here's a quick start guide to using the BenchDict tool in your projects:

### Importing Required Modules

First, import the necessary modules from the `tictoc` package, along with other required libraries:

```python
from tictoc import bench_dict
from tictoc.basic import count_down_clock, timed_counter
import time
import random
```

### Using the Countdown Clock

You can use the `count_down_clock` to create a countdown timer. This example creates a 4-second countdown:

```python
count_down = count_down_clock(4)

# check if the timer is done
while not count_down.completed():
    # print how much time is remaining for the countdown to complete
    print('time left', count_down.time_left())
    time.sleep(1)
```

### Benchmarking with BenchDict

Initialize the `timed_counter`, this class can be used to obtain counts per second and use the `bench_dict` object to benchmark global steps and individual steps within those global steps:

```python
t_counter = timed_counter()
# start the timer of our counter
t_counter.start()

# reset the timer and the count of our timed counter
t_counter.reset()
for i in range(4):
    bench_dict['g'].gstep()  # Start of a global step for process 'g'
    bench_dict['g2'].gstep()  # Start of a global step for process 'g2'
    time.sleep(1 + random.random())  # Simulate a task
    bench_dict['g'].step('1')  # Mark the end of step 1 within the global step for process 'g'
    bench_dict['g2'].step('1')  # Mark the end of step 1 within the global step for process 'g2'
    bench_dict['g2'].gstop()  # End of the global step for process 'g2'
    time.sleep(1 + random.random())  # Simulate another task
    bench_dict['g'].step('2')  # Mark the end of step 2 within the global step for process 'g'
    bench_dict['g'].gstop()  # End of the global step for process 'g'
    t_counter.count()
    # print count/time from the timed_counter
    print('frequency', t_counter.get_frequency(), 'hz')
# stop the timer of timed_counter
t_counter.stop()

print('frequency', t_counter.get_frequency(), 'hz')
# save results of the benchmark into a file called performance_*timestamp*
bench_dict.save()  # Save the benchmark results
```

## Development and Testing

### BDD Testing

This project uses Behavior-Driven Development (BDD) testing with pytest-bdd. BDD tests are written in natural language (Gherkin syntax) making them readable by both technical and non-technical stakeholders.

#### Installation

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Or install with development extras:

```bash
pip install -e .[dev]
```

#### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage report:
```bash
pytest --cov=porter_bench --cov-report=html
```

Run specific test markers:
```bash
pytest -m bdd          # Run only BDD tests
pytest -m timer        # Run only timer tests
pytest -m benchmarker  # Run only benchmarker tests
```

#### Test Structure

BDD tests are organized in the `tests/` directory:
- `features/` - Gherkin feature files describing behavior
- `test_*_bdd.py` - Step definitions implementing the scenarios
- `conftest.py` - Shared test fixtures and configuration

For more details on writing and running BDD tests, see [tests/README.md](tests/README.md).

### Code Quality

The project includes comprehensive code quality tools:
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **mypy**: Type checking
- **Pre-commit hooks**: Automated quality checks

Run pre-commit checks:
```bash
pre-commit run --all-files
```
