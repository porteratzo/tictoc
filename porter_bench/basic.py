"""Core timer and counter primitives used by the benchmarking classes."""

import time
from datetime import datetime
from typing import Optional


def get_timestamp() -> str:
    """Return the current date and time as a formatted string."""
    current_datetime = datetime.now()
    return current_datetime.strftime("%H:%M-%d:%m:%Y")


class Timer:
    """Provide start, stop, and elapsed-time helpers for high-resolution timing."""

    def __init__(self) -> None:
        """Initialise the timer, recording the current time as the start."""
        self.clock_time: float = time.perf_counter()

    def tic(self) -> None:
        """Reset the timer by recording the current time as the new start."""
        self.clock_time = time.perf_counter()

    def toc(self) -> float:
        """Return the elapsed time in seconds since the last `tic` call.

        Returns:
            float: The elapsed time in seconds.
        """
        return time.perf_counter() - self.clock_time

    def ttoc(self) -> float:
        """Return elapsed time in seconds since the last `tic`, then reset.

        Returns:
            float: The elapsed time in seconds.
        """
        val = self.toc()
        self.tic()
        return val

    def ptoc(self, message: Optional[str] = None) -> None:
        """Print a message followed by the elapsed time since the last `tic`.

        Args:
            message (str, optional): The message to print before the elapsed
            time. Defaults to None.
        """
        print(message, self.toc())

    def pttoc(self, message: Optional[str] = None) -> None:
        """Print elapsed time since the last `tic`, then reset the timer.

        Args:
            message (str, optional): The message to print before the elapsed
            time. Defaults to None.
        """
        print(message, self.ttoc())


class CountDownClock(Timer):
    """Extend Timer with a configurable countdown and completion check."""

    def __init__(self, count_down_time: float = 10.0) -> None:
        """Initialise the countdown clock.

        Args:
            count_down_time (float, optional): The initial countdown time in
            seconds. Defaults to 10.0.
        """
        super().__init__()
        self.count_down_time: float = count_down_time

    def set_count_down(self, count_down_time: float) -> None:
        """Reset the countdown to a new duration and restart the timer.

        Args:
            count_down_time (float): The new countdown time in seconds.
        """
        self.tic()
        self.count_down_time = count_down_time

    def reset(self) -> None:
        """Reset the countdown timer to its initial value and restart."""
        self.tic()

    def time_left(self) -> float:
        """Return the remaining time in seconds on the countdown timer.

        Returns:
            float: The remaining time in seconds.
        """
        return self.count_down_time - self.toc()

    def completed(self) -> bool:
        """Check whether the countdown timer has reached zero.

        Returns:
            bool: True if the countdown timer has completed, False otherwise.
        """
        return self.count_down_time < self.toc()


class TimedCounter:
    """Combine a timer and a counter to compute event frequency.

    Tracks elapsed time and the number of counts within that time, and can
    return the frequency of counts.
    """

    def __init__(self, enabled: bool = True) -> None:
        """Initialise the timed counter.

        Args:
            enabled (bool, optional): Whether the timed counter functionality
            is enabled. Defaults to True. If disabled, timer and counter
            functionality are not available.
        """
        self.enabled: bool = enabled
        if enabled:
            self.timer: Timer = Timer()
            self.counter: int = 0
            self.stop_time: float = 0.0
            self.stop_count: int = 0

    def start(self) -> None:
        """Start the timer if enabled and the counter is currently at zero."""
        if self.enabled:
            if self.counter == 0:
                self.timer.tic()

    def stop(self) -> None:
        """Stop the timer and record the current count and elapsed time."""
        if self.enabled:
            self.stop_time = self.timer.toc()
            self.stop_count = self.counter

    def count(self) -> None:
        """Increment the counter by 1 if enabled."""
        if self.enabled:
            self.counter += 1

    def get_frequency(self) -> Optional[float]:
        """Calculate the average count rate (counts per second) if enabled.

        Returns:
            float: The average count rate in counts per second, or 0.0 if no
            time has elapsed.
        """
        if self.enabled:
            if self.stop_time == 0:
                return self.counter / self.timer.toc()
            else:
                return self.stop_count / self.stop_time
        return None

    def reset(self) -> None:
        """Reset the timer and counter if enabled."""
        if self.enabled:
            self.timer.tic()
            self.counter = 0

    def disable(self) -> None:
        """Disable the timed counter functionality."""
        self.enabled = False
