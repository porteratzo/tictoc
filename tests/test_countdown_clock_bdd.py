"""BDD tests for CountDownClock functionality using pytest-bdd."""
import time

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from porter_bench.basic import CountDownClock


# Scenarios
@scenario("countdown_clock.feature", "Create countdown clock with duration")
def test_create_countdown():
    """Test creating a countdown clock."""
    pass


@scenario("countdown_clock.feature", "Countdown clock time progression")
def test_countdown_progression():
    """Test countdown clock time progression."""
    pass


@scenario("countdown_clock.feature", "Countdown clock expiry")
def test_countdown_expiry():
    """Test countdown clock expiry."""
    pass


@scenario("countdown_clock.feature", "Reset countdown clock")
def test_countdown_reset():
    """Test countdown clock reset."""
    pass


# Fixtures
@pytest.fixture
def countdown_context():
    """Context dictionary to store countdown clock and measurements."""
    return {"clock": None, "remaining_time": None}


# Given steps
@given(parsers.parse("a countdown clock with {duration:f} seconds duration"))
def create_countdown(duration, countdown_context):
    """Create a countdown clock with specified duration."""
    countdown_context["clock"] = CountDownClock(count_down_time=duration)


# When steps
@when(parsers.parse("I wait for {seconds:f} seconds"))
def wait_seconds(seconds):
    """Wait for specified seconds."""
    time.sleep(seconds)


@when("I check the remaining time immediately")
def check_remaining_immediately(countdown_context):
    """Check remaining time immediately."""
    countdown_context["remaining_time"] = countdown_context["clock"].time_left()


@when("I check the remaining time")
def check_remaining_time(countdown_context):
    """Check remaining time."""
    countdown_context["remaining_time"] = countdown_context["clock"].time_left()


@when("I reset the countdown clock")
def reset_countdown(countdown_context):
    """Reset the countdown clock."""
    countdown_context["clock"].reset()


# Then steps
@then(parsers.parse("the remaining time should be approximately {seconds:f} seconds"))
def check_remaining_approximately(seconds, countdown_context):
    """Check if remaining time is approximately as expected."""
    remaining = countdown_context["remaining_time"]
    tolerance = 0.05  # 50ms tolerance
    assert abs(remaining - seconds) < tolerance, (
        f"Expected approximately {seconds}s remaining, but got {remaining}s"
    )


@then("the countdown clock should be expired")
def check_expired(countdown_context):
    """Check if countdown clock is expired."""
    clock = countdown_context["clock"]
    assert clock.completed(), "Expected countdown clock to be expired, but it's not"
