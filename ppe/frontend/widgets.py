from abc import ABC, abstractmethod
from typing import List, Tuple, Any, Dict

import pygame

from ppe.frontend.input import InputState
from ppe.utils.profiler import Profiler


class AbstractUIElement(ABC):
    """
    An abstract, backend-agnostic base class for all UI elements.

    It defines the element's state and behavior using generic types,
    allowing concrete implementations for different rendering backends.
    """

    def __init__(self, position: Tuple[int, int], width: int, height: int):
        """
        Initializes the UI element with its screen-space position and dimensions.

        Args:
            position: The screen-space position of the top-left corner.
            width: The width of the element in pixels.
            height: The height of the element in pixels.
        """
        # Store generic, primitive state
        self.position = position
        self.width = width
        self.height = height

        self.is_visible = True
        self.is_enabled = True

    @abstractmethod
    def update(self, input_state: InputState, dt: float) -> None:
        """
        Processes user input and updates the element's internal state.

        Args:
            input_state (InputState): The current input state for the frame.
            dt (float): The time elapsed since the last frame in seconds.
        """
        pass

    @abstractmethod
    def render(self, surface: Any) -> None:
        """
        Draws the element to the screen.

        Args:
            surface: The rendering surface/context of the specific backend
                     (e.g., a pygame.Surface, an HTML5 canvas context, etc.).
        """
        pass


class PGProfilerWidget(AbstractUIElement):
    """
    A UI widget that visualizes data from a Profiler object.

    This class draws the profiler data as a series of stacked, color-coded
    bars, including labels for each section. It's non-interactive and
    updates its display automatically based on the profiler data.
    """

    def __init__(
        self,
        position: Tuple[int, int],
        profiler: Profiler,
        font: pygame.font.Font = None,
        label_font: pygame.font.Font = None,
        subsection_keys: List[str] = None,
        width: int = 400,
        bar_height: int = 12,
        bar_spacing: int = 4,
        horizontal_bar_offset: int = 70,
        pixels_per_ms: float = 10.0,
        smoothing_frames: int = 30,
        colors: List[Tuple[int, int, int]] = None,
    ):
        """
        Initializes the ProfilerWidget.

        Args:
            x (int): The screen-space x-coordinate of the top-left corner.
            y (int): The screen-space y-coordinate of the top-left corner.
            profiler (Profiler): The Profiler instance (the "model") to read data from.
            font (pygame.font.Font): The font used for headings (e.g., "total").
                Defaults to Arial.
            label_font (pygame.font.Font): The (often smaller) font for labels inside the bars.
                Defaults to Arial.
            subsection_keys (List[str], optional): A list of top-level timing keys
                (like "physics") to display as separate, detailed bars.
            width (int): The total width of the widget area.
            horizontal_bar_offset (int): The horizontal space reserved for headings.
            pixels_per_ms (float): The scale of the bars (e.g., 10 pixels per 1ms).
            smoothing_frames (int): The number of frames to average over for smoothing.
            colors (List[Tuple]): A list of colors to cycle through for bar segments.
        """
        # We can calculate the total height based on the subsections
        num_rows = 1 + (len(subsection_keys) if subsection_keys else 0)
        total_height = (num_rows * bar_height) + ((num_rows - 1) * bar_spacing)
        super().__init__(position, width, total_height)

        self.profiler = profiler

        self.font = font if font else pygame.font.SysFont("Arial", 12)
        self.label_font = label_font if label_font else pygame.font.SysFont("Arial", 10)
        self.subsection_keys = subsection_keys if subsection_keys else []
        self.bar_height = bar_height
        self.bar_spacing = bar_spacing
        self.horizontal_bar_offset = horizontal_bar_offset
        self.pixels_per_ms = pixels_per_ms
        self.smoothing_frames = smoothing_frames

        # Define default colors if none are provided
        self.colors = (
            colors
            if colors
            else [
                (255, 141, 133),  # Red
                (133, 219, 255),  # Blue
                (133, 255, 141),  # Green
                (255, 204, 133),  # Orange
                (204, 133, 255),  # Purple
            ]
        )

    def update(self, input_state: InputState, dt: float) -> None:
        """The ProfilerWidget is non-interactive."""
        pass

    def render(self, surface: pygame.Surface) -> None:
        """Draws the complete profiler UI to the given surface."""

        # Get the number of frames to average over
        frames_used = min(
            len(self.profiler.total_frame_time_history), self.smoothing_frames
        )
        if frames_used == 0:
            return

        # compute the average frame time and timings
        frame_time = (
            sum(list(self.profiler.total_frame_time_history)[-frames_used:])
            / frames_used
        )
        if frame_time == 0:
            return

        timings_history = list(self.profiler.timings_history)[-frames_used:]
        timings = {
            name: sum(timing.get(name, 0) for timing in timings_history) / frames_used
            for name in timings_history[0].keys()
        }

        # Render the top-level bar (all timings without a '/')
        self._draw_bar(
            surface=surface,
            row_idx=0,
            timings={k: v for k, v in timings.items() if "/" not in k},
            heading=f"total ({int(frame_time):03d}ms)",
            total_frame_time=frame_time,
        )

        # Render all requested subsection bars
        for i_subsection, subsection_key in enumerate(self.subsection_keys):
            # Filter for keys like "physics/solver", "physics/narrow"
            subsection_timings = {
                k.split("/")[1]: v
                for k, v in timings.items()
                if k.startswith(f"{subsection_key}/")
            }
            if not subsection_timings:
                continue

            heading = (
                f"{subsection_key} ({int(sum(subsection_timings.values())):03d}ms)"
            )
            self._draw_bar(
                surface=surface,
                row_idx=i_subsection + 1,
                timings=subsection_timings,
                heading=heading,
            )

    def _draw_bar(
        self,
        surface: pygame.Surface,
        row_idx: int,
        timings: Dict[str, float],
        heading: str,
        total_frame_time: float = None,
    ) -> None:
        """Renders a single horizontal bar for the profiler."""

        # Draw the header text
        row_position = (
            self.position[0],
            self.position[1] + row_idx * (self.bar_height + self.bar_spacing),
        )
        surface.blit(self.font.render(heading, True, (0, 0, 0)), row_position)

        total_time = sum(timings.values())
        if total_frame_time is not None:
            timings["_idle_"] = total_frame_time - total_time
            total_time = total_frame_time

        accumulated_section_width = 0
        for i_segment, (key, value) in enumerate(timings.items()):
            width = int(value * self.pixels_per_ms)
            if width == 0:
                continue

            color = self.colors[i_segment % len(self.colors)]
            section_position = (
                row_position[0]
                + self.horizontal_bar_offset
                + accumulated_section_width,
                row_position[1],
            )
            accumulated_section_width += width

            # Draw the colored segment
            pygame.draw.rect(
                surface,
                color,
                (section_position[0], section_position[1], width, self.bar_height),
            )

            # Prepare and truncate the label to fit
            label = f"{key} ({int(value):02d}ms / {int(value / total_time * 100):02d}%)"
            for i in range(len(label)):
                if self.label_font.size(label[:i])[0] > width:
                    label = label[: i - 1]
                    break
            label_rect = self.label_font.render(label, True, (0, 0, 0))
            surface.blit(
                label_rect,
                (
                    section_position[0] + (width - label_rect.get_width()) // 2,
                    section_position[1]
                    + (self.bar_height - label_rect.get_height()) // 2,
                ),
            )
