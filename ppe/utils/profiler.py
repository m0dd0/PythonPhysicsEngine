import time
from contextlib import contextmanager
from typing import Dict

class Profiler:
    """A simple profiler to time different sections of a game loop."""

    def __init__(self):
        self.timings: Dict[str, float] = {}
        self.frame_start_time: float = 0.0
        self.total_frame_time: float = 0.0

    def start_frame(self):
        """Marks the beginning of a new frame."""
        self.frame_start_time = time.perf_counter()
        self.timings.clear()

    def end_frame(self):
        """Marks the end of a frame and calculates total time."""
        self.total_frame_time = time.perf_counter() - self.frame_start_time

    @contextmanager
    def time(self, name: str):
        """A context manager to time a block of code."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.timings[name] = self.timings.get(name, 0) + duration

    def get_percentages(self) -> Dict[str, float]:
        """Returns the timing data as percentages of the total frame time."""
        if self.total_frame_time == 0:
            return {name: 0 for name in self.timings}
            
        return {
            name: (duration / self.total_frame_time) * 100
            for name, duration in self.timings.items()
        }