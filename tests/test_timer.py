"""Tests for the basic timer primitives in porter_bench.basic."""

import time

import pytest

from porter_bench.basic import CountDownClock, TimedCounter, Timer


class TestTimer:
    def test_toc_returns_positive_float(self):
        t = Timer()
        time.sleep(0.01)
        elapsed = t.toc()
        assert isinstance(elapsed, float)
        assert elapsed > 0

    def test_tic_resets_timer(self):
        t = Timer()
        time.sleep(0.05)
        t.tic()
        elapsed = t.toc()
        # Should be well below the original 50 ms
        assert elapsed < 0.05

    def test_ttoc_returns_elapsed_then_resets(self):
        t = Timer()
        time.sleep(0.01)
        elapsed1 = t.ttoc()
        elapsed2 = t.toc()
        assert elapsed1 > 0
        # After ttoc the internal timer was reset; elapsed2 should be << elapsed1
        assert elapsed2 < elapsed1

    def test_ptoc_prints_message(self, capsys):
        t = Timer()
        t.ptoc("hello")
        out = capsys.readouterr().out
        assert "hello" in out

    def test_pttoc_prints_and_resets(self, capsys):
        t = Timer()
        time.sleep(0.01)
        t.pttoc("label")
        capsys.readouterr()
        # Timer should have been reset; subsequent toc must be small
        assert t.toc() < 0.05


class TestCountDownClock:
    def test_not_completed_immediately(self):
        c = CountDownClock(count_down_time=10.0)
        assert not c.completed()

    def test_completed_after_elapsed(self):
        c = CountDownClock(count_down_time=0.02)
        time.sleep(0.05)
        assert c.completed()

    def test_reset_restarts_countdown(self):
        c = CountDownClock(count_down_time=0.02)
        time.sleep(0.05)
        assert c.completed()
        c.reset()
        assert not c.completed()

    def test_set_count_down_changes_duration(self):
        c = CountDownClock(count_down_time=0.02)
        time.sleep(0.05)
        assert c.completed()
        c.set_count_down(10.0)
        assert not c.completed()

    def test_time_left_decreases(self):
        c = CountDownClock(count_down_time=1.0)
        t1 = c.time_left()
        time.sleep(0.01)
        t2 = c.time_left()
        assert t2 < t1


class TestTimedCounter:
    def test_disabled_returns_none_frequency(self):
        tc = TimedCounter(enabled=False)
        assert tc.get_frequency() is None

    def test_basic_frequency_is_positive(self):
        tc = TimedCounter()
        tc.start()
        for _ in range(10):
            tc.count()
        tc.stop()
        freq = tc.get_frequency()
        assert freq is not None
        assert freq > 0

    def test_disable_makes_operations_noop(self):
        tc = TimedCounter()
        tc.disable()
        assert not tc.enabled
        assert tc.get_frequency() is None

    def test_reset_clears_counter(self):
        tc = TimedCounter()
        tc.start()
        tc.count()
        tc.count()
        tc.reset()
        assert tc.counter == 0

    def test_frequency_without_stop_uses_live_timer(self):
        tc = TimedCounter()
        tc.start()
        tc.count()
        tc.count()
        freq = tc.get_frequency()
        assert freq is not None and freq > 0

    def test_start_does_not_reset_running_timer(self):
        """Calling start() again while counter > 0 must NOT reset the timer."""
        tc = TimedCounter()
        tc.start()
        tc.count()
        time.sleep(0.01)
        tc.start()  # counter is 1, so tic() must be skipped
        time.sleep(0.01)
        tc.stop()
        # elapsed should be >= 20 ms since the second start was a no-op
        assert tc.stop_time >= 0.015
