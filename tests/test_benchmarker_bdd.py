"""BDD tests for Benchmarker functionality using pytest-bdd."""
import time

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from porter_bench.Benchmarker import Benchmarker


# Scenarios
@scenario("benchmarker.feature", "Basic step timing")
def test_basic_step_timing():
    """Test basic step timing functionality."""
    pass


@scenario("benchmarker.feature", "Multiple steps benchmarking")
def test_multiple_steps():
    """Test multiple steps benchmarking."""
    pass


@scenario("benchmarker.feature", "Repeated step measurements")
def test_repeated_measurements():
    """Test repeated step measurements."""
    pass


@scenario("benchmarker.feature", "Context manager for steps")
def test_context_manager():
    """Test context manager for steps."""
    pass


@scenario("benchmarker.feature", "Getting benchmarker results")
def test_get_results():
    """Test getting benchmarker results."""
    pass


# Fixtures
@pytest.fixture
def benchmarker_context():
    """Context dictionary to store benchmarker and results."""
    return {"benchmarker": None, "results": None}


# Given steps
@given("a new benchmarker instance")
def new_benchmarker(benchmarker_context):
    """Create a new benchmarker instance."""
    benchmarker_context["benchmarker"] = Benchmarker()
    benchmarker_context["benchmarker"].start()


# When steps
@when(parsers.parse("I wait for {seconds:f} seconds"))
def wait_seconds(seconds):
    """Wait for specified seconds."""
    time.sleep(seconds)


@when(parsers.parse('I start timing a step called "{step_name}"'))
def start_step(step_name, benchmarker_context):
    """Start timing a step."""
    # The benchmarker tracks time automatically
    pass


@when(parsers.parse('I stop timing the step "{step_name}"'))
def stop_step(step_name, benchmarker_context):
    """Stop timing a step."""
    benchmarker_context["benchmarker"].step(step_name)


@when(
    parsers.parse(
        'I measure step "{step_name}" {count:d} times with {delay:f} second delays'
    )
)
def measure_step_repeatedly(step_name, count, delay, benchmarker_context):
    """Measure a step multiple times."""
    benchmarker = benchmarker_context["benchmarker"]
    for _ in range(count):
        time.sleep(delay)
        benchmarker.step(step_name)


@when(
    parsers.parse(
        'I use benchmarker context manager for step "{step_name}" with {delay:f} second delay'
    )
)
def use_benchmarker_context(step_name, delay, benchmarker_context):
    """Use benchmarker as context manager."""
    benchmarker = benchmarker_context["benchmarker"]
    time.sleep(delay)
    benchmarker.step(step_name)


# Then steps
@then(parsers.parse('the benchmarker should have recorded the step "{step_name}"'))
def check_step_recorded(step_name, benchmarker_context):
    """Check if step was recorded."""
    benchmarker = benchmarker_context["benchmarker"]
    step_dict = benchmarker.time_benchmaker.step_dict
    assert step_name in step_dict, f"Step '{step_name}' not found in benchmarker"


@then(
    parsers.parse('the step "{step_name}" time should be approximately {seconds:f} seconds')
)
def check_step_time(step_name, seconds, benchmarker_context):
    """Check if step time is approximately as expected."""
    benchmarker = benchmarker_context["benchmarker"]
    step_dict = benchmarker.time_benchmaker.step_dict

    assert step_name in step_dict, f"Step '{step_name}' not found"

    step_data = step_dict[step_name]
    if isinstance(step_data, list) and len(step_data) > 0:
        # Get the most recent measurement
        last_measurement = step_data[-1]
        if isinstance(last_measurement, dict) and "time" in last_measurement:
            elapsed = last_measurement["time"]
        else:
            elapsed = last_measurement
    else:
        elapsed = step_data

    tolerance = seconds * 0.15 + 0.01  # 15% tolerance for benchmarker overhead
    assert abs(elapsed - seconds) < tolerance, (
        f"Expected approximately {seconds}s for step '{step_name}', but got {elapsed}s"
    )


@then(parsers.parse("the benchmarker should have {count:d} recorded steps"))
def check_step_count(count, benchmarker_context):
    """Check the number of recorded steps."""
    benchmarker = benchmarker_context["benchmarker"]
    step_dict = benchmarker.time_benchmaker.step_dict
    # Filter out special keys like GLOBAL, START_TIME, STOP_TIME
    actual_steps = [
        k for k in step_dict.keys()
        if k not in ["GLOBAL", "START_TIME", "STOP_TIME"]
    ]
    assert len(actual_steps) == count, (
        f"Expected {count} steps, but got {len(actual_steps)}: {actual_steps}"
    )


@then(parsers.parse('the step "{step_name}" should exist'))
def check_step_exists(step_name, benchmarker_context):
    """Check if a step exists."""
    benchmarker = benchmarker_context["benchmarker"]
    step_dict = benchmarker.time_benchmaker.step_dict
    assert step_name in step_dict, f"Step '{step_name}' does not exist"


@then(parsers.parse('the step "{step_name}" should have {count:d} measurements'))
def check_step_measurement_count(step_name, count, benchmarker_context):
    """Check the number of measurements for a step."""
    benchmarker = benchmarker_context["benchmarker"]
    step_dict = benchmarker.time_benchmaker.step_dict

    assert step_name in step_dict, f"Step '{step_name}' not found"

    step_data = step_dict[step_name]
    if isinstance(step_data, list):
        actual_count = len(step_data)
    else:
        actual_count = 1

    assert actual_count == count, (
        f"Expected {count} measurements for step '{step_name}', but got {actual_count}"
    )


@then(
    parsers.parse('the mean time for "{step_name}" should be approximately {seconds:f} seconds')
)
def check_mean_time(step_name, seconds, benchmarker_context):
    """Check if mean time for a step is approximately as expected."""
    benchmarker = benchmarker_context["benchmarker"]
    step_dict = benchmarker.time_benchmaker.step_dict

    assert step_name in step_dict, f"Step '{step_name}' not found"

    step_data = step_dict[step_name]
    if isinstance(step_data, list):
        times = []
        for measurement in step_data:
            if isinstance(measurement, dict) and "time" in measurement:
                times.append(measurement["time"])
            else:
                times.append(measurement)
        mean_time = sum(times) / len(times)
    else:
        mean_time = step_data

    tolerance = seconds * 0.15 + 0.01
    assert abs(mean_time - seconds) < tolerance, (
        f"Expected mean time approximately {seconds}s, but got {mean_time}s"
    )


@then("I should be able to get benchmark results")
def get_results(benchmarker_context):
    """Get benchmark results."""
    benchmarker = benchmarker_context["benchmarker"]
    benchmarker_context["results"] = benchmarker.time_benchmaker.step_dict


@then(parsers.parse('the results should contain step "{step_name}"'))
def check_results_contain_step(step_name, benchmarker_context):
    """Check if results contain a specific step."""
    results = benchmarker_context["results"]
    assert results is not None, "No results available"
    assert step_name in results, f"Step '{step_name}' not found in results"
