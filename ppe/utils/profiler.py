import time
from contextlib import contextmanager
from typing import Dict
from collections import deque


class Profiler:
    """A simple profiler to time different sections of a game loop."""

    def __init__(self, smoothing_frames: int = 30):
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
        """Marks the beginning of a new frame."""
        self.frame_start_time = time.perf_counter()
        self.timings.clear()

    def end_frame(self):
        """Marks the end of a frame and calculates total time."""
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
        """A context manager to time a block of code."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = (time.perf_counter() - start) * 1000  # Convert to milliseconds
            self.timings[name] = self.timings.get(name, 0) + duration

    def get_percentages(self) -> Dict[str, float]:
        """Returns the timing data as percentages of the total frame time."""
        if self.total_frame_time == 0:
            return {name: 0 for name in self.timings}

        return {
            name: (duration / self.total_frame_time) * 100
            for name, duration in self.timings.items()
        }
