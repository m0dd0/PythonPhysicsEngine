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

    def __init__(self, max_history_length=100):
        """
        Initializes the Profiler.

        Args:
            smoothing_frames (int): The number of frames to use for smoothing.
        """
        self.timings: Dict[str, float] = {}
        self.timings_history: deque = deque(maxlen=max_history_length)
        
        self.frame_start_time: float = None
        self.total_frame_time: float = 0.0
        self.total_frame_time_history: deque = deque(maxlen=max_history_length)

        self.dt_simulated_history: deque = deque(maxlen=max_history_length)
        self.total_frames_counter: int = 0


    def start_new_frame(self, dt_simulated: float):
        """Marks the beginning of a new frame. All timing entries will be reset and 
        the elapsed time of the previous frame will be added to the history."""
        assert len(self.total_frame_time_history) == len(self.timings_history)
        
        self.dt_simulated_history.append(dt_simulated * 1000)
        self.total_frames_counter += 1

        if self.frame_start_time is not None:
            self.total_frame_time = (
                time.perf_counter() - self.frame_start_time
            ) * 1000  # Convert to milliseconds
            self.total_frame_time_history.append(self.total_frame_time)

            self.timings_history.append(self.timings)
        
        self.frame_start_time = time.perf_counter()
        # self.timings.clear() # we cannot use .clear() as this would clear the entries in the deque
        self.timings = {}
        
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
