import time
from datetime import datetime


def get_timestamp() -> str:
    """
    Gets the current date and time in a formatted string.

    Returns:
        str: The current date and time formatted as "%d-%m-%y_%X"
    """
    current_datetime = datetime.now()
    return current_datetime.strftime("%H:%M-%d:%m:%Y")


class Timer:
    """
    A simple timer class offering functionalities like starting, stopping, and retrieving elapsed time.
    """

    def __init__(self) -> None:
        """
        Initializes the timer with the starting time set to the current time.
        """
        self.clock_time: float = time.perf_counter()

    def tic(self):
        """
        Resets the timer by setting the starting time.
        """
        self.clock_time: float = time.perf_counter()

    def toc(self) -> float:
        """
        Returns the elapsed time in seconds since the last `tic` call.

        Returns:
            float: The elapsed time in seconds.
        """
        return time.perf_counter() - self.clock_time

    def ttoc(self) -> float:
        """
        Returns the elapsed time in seconds since the last `tic` call, then resets the timer.

        Returns:
            float: The elapsed time in seconds.
        """
        val = self.toc()
        self.tic()
        return val

    def ptoc(self, message: str = None) -> None:
        """
        Prints a message followed by the elapsed time in seconds since the last `tic` call.

        Args:
            message (str, optional): The message to print before the elapsed time. Defaults to None.
        """
        print(message, self.toc())

    def pttoc(self, message: str = None) -> None:
        """
        Prints a message followed by the elapsed time in seconds since the last `tic` call, then resets the timer.

        Args:
            message (str, optional): The message to print before the elapsed time. Defaults to None.
        """
        print(message, self.ttoc())


class CountDownClock(Timer):
    """
    Inherits from the `timer` class and adds functionality for a countdown timer.
    """

    def __init__(self, count_down_time: float = 10.0) -> None:
        """
        Initializes the countdown timer with a starting countdown time and sets the starting time using the parent class constructor.

        Args:
            count_down_time (float, optional): The initial countdown time in seconds. Defaults to 10.0
        """
        super().__init__()
        self.count_down_time: float = count_down_time

    def set_count_down(self, count_down_time: float) -> None:
        """
        Resets the countdown timer to a new value and starts the timer.

        Args:
            count_down_time (float): The new countdown time in seconds.
        """
        self.tic()
        self.count_down_time = count_down_time

    def reset(self) -> None:
        """
        Resets the countdown timer to its initial value and starts the timer.
        """
        self.tic()

    def time_left(self) -> float:
        """
        Returns the remaining time in seconds on the countdown timer.

        Returns:
            float: The remaining time in seconds.
        """
        return self.count_down_time - self.toc()

    def completed(self) -> bool:
        """
        Checks if the countdown timer has reached zero.

        Returns:
            bool: True if the countdown timer has completed, False otherwise.
        """
        return self.count_down_time < self.toc()


class TimedCounter:
    """
    A class that combines a timer and a counter, tracking both elapsed time and the number of counts within that time, and can return frequency of counts
    """

    def __init__(self, enabled: bool = True) -> None:
        """
        Initializes the timed counter.

        Args:
            enabled (bool, optional): Whether the timed counter functionality is enabled. Defaults to True.
                If disabled, timer and counter functionality are not available.
        """
        if enabled:
            self.timer = Timer()
            self.counter = 0
            self.stop_time = 0
            self.stop_count = 0
        self.enabled = enabled

    def start(self) -> None:
        """
        Starts the timer if enabled and the counter is currently at zero.
        """
        if self.enabled:
            if self.counter == 0:
                self.timer.tic()

    def stop(self) -> None:
        """
        Stops the timer and records the current count and elapsed time if enabled.
        """
        if self.enabled:
            self.stop_time = self.timer.toc()
            self.stop_count = self.counter

    def count(self) -> None:
        """
        Increments the counter by 1 if enabled.
        """
        if self.enabled:
            self.counter += 1

    def get_frequency(self) -> float:
        """
        Calculates the average count rate (counts per second) if enabled.

        Returns:
            float: The average count rate in counts per second, or 0.0 if no time has elapsed.
        """
        if self.enabled:
            if self.stop_time == 0:
                return self.counter / self.timer.toc()
            else:
                return self.stop_count / self.stop_time

    def reset(self) -> None:
        """
        Resets the timer and counter if enabled.
        """
        if self.enabled:
            self.timer.tic()
            self.counter = 0

    def disable(self) -> None:
        """
        Disables the timed counter functionality.
        """
        self.enabled = False
