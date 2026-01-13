# BDD Testing for Porter Bench (TicToc)

This directory contains Behavior-Driven Development (BDD) tests for the porter_bench library using pytest-bdd.

## Overview

BDD testing uses natural language specifications (Gherkin syntax) to describe the expected behavior of the system. This makes tests readable by both technical and non-technical stakeholders.

## Directory Structure

```
tests/
├── __init__.py                    # Tests package initialization
├── conftest.py                    # Shared pytest fixtures and configuration
├── README.md                      # This file
├── features/                      # BDD feature files (Gherkin scenarios)
│   ├── timer.feature             # Timer functionality scenarios
│   ├── benchmarker.feature       # Benchmarker functionality scenarios
│   └── countdown_clock.feature   # CountDownClock functionality scenarios
├── test_timer_bdd.py             # Step definitions for timer tests
├── test_benchmarker_bdd.py       # Step definitions for benchmarker tests
└── test_countdown_clock_bdd.py   # Step definitions for countdown clock tests
```

## Installation

Install the development dependencies including pytest-bdd:

```bash
pip install -e .[dev]
# or
pip install -r requirements-dev.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_timer_bdd.py
```

### Run tests with coverage report
```bash
pytest --cov=porter_bench --cov-report=html
```

### Run only BDD tests
```bash
pytest -m bdd
```

### Run specific feature
```bash
pytest tests/test_timer_bdd.py::test_basic_timer
```

### Verbose output
```bash
pytest -v
```

## Writing BDD Tests

### 1. Create a Feature File

Feature files are written in Gherkin syntax and stored in `tests/features/`. Example:

```gherkin
Feature: Timer Functionality
  As a developer
  I want to measure execution time
  So that I can track performance

  Scenario: Basic timer usage
    Given a new timer instance
    When I start the timer
    And I wait for 0.1 seconds
    And I stop the timer
    Then the elapsed time should be approximately 0.1 seconds
```

### 2. Implement Step Definitions

Step definitions connect Gherkin steps to Python code. Example:

```python
from pytest_bdd import given, when, then, scenario, parsers
from porter_bench.basic import Timer

@scenario('features/timer.feature', 'Basic timer usage')
def test_basic_timer():
    pass

@given('a new timer instance')
def timer(context):
    context['timer'] = Timer()

@when('I start the timer')
def start_timer(context):
    context['timer'].tic()

@then(parsers.parse('the elapsed time should be approximately {seconds:f} seconds'))
def check_time(seconds, context):
    elapsed = context['timer'].toc()
    assert abs(elapsed - seconds) < 0.01
```

## Gherkin Keywords

- **Feature**: High-level description of functionality
- **Scenario**: Specific test case
- **Background**: Steps that run before each scenario
- **Given**: Setup/preconditions
- **When**: Actions/events
- **Then**: Expected outcomes/assertions
- **And/But**: Additional steps

## Test Markers

Tests can be tagged with markers for selective execution:

- `@pytest.mark.bdd` - BDD tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.timer` - Timer-related tests
- `@pytest.mark.benchmarker` - Benchmarker-related tests
- `@pytest.mark.memory` - Memory-related tests

## Coverage Reports

After running tests with coverage, view the HTML report:

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Best Practices

1. **Keep scenarios focused**: Each scenario should test one behavior
2. **Use descriptive names**: Feature and scenario names should be clear
3. **Avoid technical details in features**: Features should be readable by non-developers
4. **Reuse step definitions**: Write generic, reusable steps
5. **Use Background for common setup**: Reduce duplication with Background sections
6. **Parametrize when appropriate**: Use scenario outlines for testing multiple inputs

## Example: Scenario Outline

```gherkin
Scenario Outline: Timer with different durations
  Given a new timer instance
  When I start the timer
  And I wait for <duration> seconds
  And I stop the timer
  Then the elapsed time should be approximately <duration> seconds

  Examples:
    | duration |
    | 0.05     |
    | 0.10     |
    | 0.20     |
```

## Continuous Integration

Tests are automatically run in CI/CD pipelines. The pytest.ini configuration ensures:
- Coverage reports are generated
- Tests are discovered automatically
- Output is formatted for CI systems

## Contributing

When adding new functionality:

1. Write feature file first (test-driven development)
2. Implement step definitions
3. Run tests to verify they fail
4. Implement the feature
5. Run tests to verify they pass
6. Ensure coverage is maintained

## Resources

- [pytest-bdd documentation](https://pytest-bdd.readthedocs.io/)
- [Gherkin syntax reference](https://cucumber.io/docs/gherkin/reference/)
- [pytest documentation](https://docs.pytest.org/)
