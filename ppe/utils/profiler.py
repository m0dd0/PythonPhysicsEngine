"""
Module containing a simple profiler to time different sections of a game loop.

Example:
    profiler = Profiler()
    with profiler.time("my_block"):
        # code to time
    timings = profiler.get_timings()

"""

import time
from contextlib import contextmanager
from typing import Dict
from collections import deque


class Profiler:
    """A simple profiler to time different sections of a game loop."""

    def __init__(self, smoothing_frames: int = 30):
        # TODO allow to print real time factor
        """
        Initializes the Profiler with a specified number of frames for smoothing.

        The Profiler will store the total frame time for the last `smoothing_frames`
        frames and compute a smoothed total frame time by averaging these values.

        This allows for a more stable FPS measurement over time.

        Args:
            smoothing_frames (int, optional): The number of frames to smooth over. Defaults to 30.
        """
        self.timings: Dict[str, float] = {}
        self.frame_start_time: float = 0.0
        self.total_frame_time: float = 0.0

        # FPS smoothing
        self.smoothing_frames = smoothing_frames

        self.total_frame_times = deque(maxlen=smoothing_frames)
        self.timing_deque = deque(maxlen=smoothing_frames)
        self.smoothed_total_frame_time: float = 0.0
        self.smoothed_timings: Dict[str, float] = {}

    def start_frame(self):
        """Marks the beginning of a new frame. All timing entries will be reset."""
        self.frame_start_time = time.perf_counter()
        self.timings.clear()

    def end_frame(self):
        """Marks the end of a frame and calculates total time. All timing entries will be reset."""
        self.total_frame_time = (
            time.perf_counter() - self.frame_start_time
        ) * 1000  # Convert to milliseconds

        # Update smoothed FPS calculation
        self.total_frame_times.append(self.total_frame_time)
        if len(self.total_frame_times) > 0:
            self.smoothed_total_frame_time = sum(self.total_frame_times) / len(
                self.total_frame_times
            )

        self.timing_deque.append(self.timings)
        self.timings = {}
        if len(self.timing_deque) > 0:
            self.smoothed_timings = {
                name: sum(timing.get(name, 0) for timing in self.timing_deque)
                / len(self.timing_deque)
                for name in self.timing_deque[0]
            }

    @contextmanager
    def time(self, name: str):
        """A context manager to time a block of code.
        
        Args:
            name (str): The name of the block to time. The execution time of code blocks 
                that are wrapped with the same name will be summed up.
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = (time.perf_counter() - start) * 1000  # Convert to milliseconds
            self.timings[name] = self.timings.get(name, 0) + duration

    def get_percentages(self) -> Dict[str, float]:
        """Returns the timing data as percentages of the total frame time.
        Note that calling this method requires the end_frame method to have been called first.

        Returns:
            Dict[str, float]: The timing data as percentages of the total frame time.
        """
        if self.total_frame_time == 0:
            return {name: 0 for name in self.timings}

        return {
            name: (duration / self.total_frame_time) * 100
            for name, duration in self.timings.items()
        }
