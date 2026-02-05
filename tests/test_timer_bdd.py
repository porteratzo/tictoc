"""BDD tests for Timer functionality using pytest-bdd."""
import time

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from porter_bench.basic import Timer


# Scenarios
@scenario("timer.feature", "Basic timer start and stop")
def test_basic_timer():
    """Test basic timer start and stop functionality."""
    pass


@scenario("timer.feature", "Multiple timer measurements")
def test_multiple_measurements():
    """Test multiple timer measurements."""
    pass


@scenario("timer.feature", "Timer reset functionality")
def test_timer_reset():
    """Test timer reset functionality."""
    pass


@scenario("timer.feature", "Context manager usage")
def test_context_manager():
    """Test timer context manager usage."""
    pass


@scenario("timer.feature", "Getting timer statistics")
def test_timer_statistics():
    """Test getting timer statistics."""
    pass


# Fixtures to store test context
@pytest.fixture
def timer_context():
    """Context dictionary to store timer and measurements."""
    return {"timer": None, "measurements": [], "elapsed_time": None}


# Given steps
@given("a new timer instance")
def new_timer(timer_context):
    """Create a new timer instance."""
    timer_context["timer"] = Timer()
    timer_context["measurements"] = []


# When steps
@when("I start the timer")
def start_timer(timer_context):
    """Start the timer."""
    timer_context["timer"].tic()


@when(parsers.parse("I wait for {seconds:f} seconds"))
def wait_seconds(seconds, timer_context):
    """Wait for specified seconds."""
    time.sleep(seconds)


@when("I stop the timer")
def stop_timer(timer_context):
    """Stop the timer and record measurement."""
    elapsed = timer_context["timer"].toc()
    timer_context["measurements"].append(elapsed)
    timer_context["elapsed_time"] = elapsed


@when("I start the timer again")
def restart_timer(timer_context):
    """Restart the timer."""
    timer_context["timer"].tic()


@when("I reset the timer")
def reset_timer(timer_context):
    """Reset the timer."""
    timer_context["timer"].tic()
    timer_context["measurements"] = []


@when(parsers.parse("I use the timer as a context manager for {seconds:f} seconds"))
def use_timer_context_manager(seconds, timer_context):
    """Use timer as context manager."""
    timer = Timer()
    timer.tic()
    time.sleep(seconds)
    timer_context["elapsed_time"] = timer.toc()


# Then steps
@then(parsers.parse("the elapsed time should be approximately {seconds:f} seconds"))
def check_elapsed_time(seconds, timer_context):
    """Check if elapsed time is approximately as expected."""
    elapsed = timer_context["elapsed_time"]
    # Allow 10% tolerance for timing variations
    tolerance = seconds * 0.1 + 0.01  # Add small constant for very small times
    assert abs(elapsed - seconds) < tolerance, (
        f"Expected approximately {seconds}s, but got {elapsed}s"
    )


@then(parsers.parse("the timer should have {count:d} measurements"))
def check_measurement_count(count, timer_context):
    """Check the number of measurements."""
    assert len(timer_context["measurements"]) == count, (
        f"Expected {count} measurements, but got {len(timer_context['measurements'])}"
    )


@then("the timer measurements should be empty")
def check_empty_measurements(timer_context):
    """Check if measurements are empty."""
    assert len(timer_context["measurements"]) == 0, (
        f"Expected no measurements, but got {len(timer_context['measurements'])}"
    )


@then("the timer should provide mean time statistics")
def check_mean_statistics(timer_context):
    """Check if timer provides statistics."""
    assert len(timer_context["measurements"]) > 0, "No measurements available"


@then("the mean time should be greater than 0")
def check_positive_mean(timer_context):
    """Check if mean time is positive."""
    mean_time = sum(timer_context["measurements"]) / len(timer_context["measurements"])
    assert mean_time > 0, f"Expected positive mean time, but got {mean_time}"
