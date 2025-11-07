from abc import ABC, abstractmethod
from typing import List, Tuple, Any, Dict
import math

import pygame

from ppe.frontend.input import InputState
from ppe.utils.profiler import Profiler
from ppe.frontend.controller import AbstractController


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


class PGAbstractUIElement(AbstractUIElement):
    def __init__(self, position, width, height):
        super().__init__(position, width, height)

    def _resolve_position(
        self, position: Tuple[int, int], surface: pygame.Surface
    ) -> Tuple[int, int]:
        """Resolves the given position to be within the screen bounds.
        This is especially useful for definig distances from the right or bottom of the screen
        by using negative numbers.

        Args:
            position (Tuple[int, int]): The position to resolve.
            surface (pygame.Surface): The surface to check against.

        Returns:
            Tuple[int, int]: The resolved position.
        """
        x, y = position
        if x < 0:
            x = surface.get_width() + position[0]
        if y < 0:
            y = surface.get_height() + position[1]
        return (x, y)


class PGProfilerWidget(PGAbstractUIElement):
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
        position = self._resolve_position(self.position, surface)
        row_position = (
            position[0],
            position[1] + row_idx * (self.bar_height + self.bar_spacing),
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


class PGTextPanelWidget(PGAbstractUIElement):
    """
    A simple UI widget that renders text strings.
    """

    def __init__(
        self,
        position: Tuple[int, int],
        text: str,
        font: pygame.font.Font = None,
        text_color: Tuple[int, int, int] = (0, 0, 0),
        line_spacing: int = 4,
        max_width: int = math.inf,
    ):
        """
        Initializes the TextPanelWidget.

        Args:
            position (Tuple[int, int]): The position of the widget.
            font (pygame.font.Font): The font to use for rendering text. Defaults to Arial.
            text_color (Tuple[int, int, int]): The color of the text. Defaults to black.
            line_spacing (int): The spacing between lines of text. Defaults to 4.
            max_width (int): The maximum width of the widget. If the text exceeds this width, it will wrap to the next line.
                If None, no wrapping will occur. Defaults to None.
        """
        super().__init__(position, 0, 0)
        self.font = font if font else pygame.font.SysFont("Arial", 12)
        self.text_color = text_color
        self.line_spacing = line_spacing
        self.max_width = max_width
        self._text = text
        self.lines = self._linebreak_text(text)

    def _linebreak_text(self, text: str) -> List[str]:
        lines = text.split("\n")

        splitted_lines = []

        for line in lines:
            if self.max_width is not None:
                words = line.split(" ")
                current_line = ""
                for word in words:
                    if self.font.size(current_line + word)[0] > self.max_width:
                        splitted_lines.append(current_line)
                        current_line = ""
                    current_line += word + " "
                if current_line:
                    splitted_lines.append(current_line)
            else:
                splitted_lines.append(line)

        return splitted_lines

    def update_text(self, text: str):
        self._text = text
        self.lines = self._linebreak_text(text)

    def update(self, input_state: InputState, dt: float) -> None:
        """This widget is non-interactive."""
        pass

    def render(self, surface: pygame.Surface) -> None:
        """Draws the list of text strings."""
        position = self._resolve_position(self.position, surface)
        for i_line, line in enumerate(self.lines):
            text_surf = self.font.render(line, True, self.text_color)
            surface.blit(
                text_surf,
                (
                    position[0],
                    position[1] + i_line * (self.font.get_height() + self.line_spacing),
                ),
            )


class PGControllerInfoWidget(PGTextPanelWidget):
    """
    A specialized text panel that automatically displays the
    action_description from a list of controllers.
    """

    def __init__(
        self,
        position: Tuple[int, int],
        controllers: List[AbstractController],
        font: pygame.font.Font = None,
        text_color: Tuple[int, int, int] = (0, 0, 0),
        line_spacing: int = 4,
    ):
        """
        Initializes the widget.

        Args:
            position (Tuple[int, int]): The position of the widget.
            controllers (List[AbstractController]): The list of controllers to get descriptions from.
            font (pygame.font.Font): The font to use for rendering. Defaults to Arial.
            text_color (Tuple): The color of the text.
            line_spacing (int): The vertical spacing between lines.
        """
        self.controllers = controllers
        super().__init__(
            position=position,
            text="\n".join(c.action_description for c in self.controllers),
            font=font,
            text_color=text_color,
            line_spacing=line_spacing,
        )

    def update(self, input_state: InputState, dt: float) -> None:
        """
        Updates the widget's text lines from the controllers.
        This widget is non-interactive, so it doesn't process input.
        """
        # This is the logic we successfully moved out of the main loop
        self.update_text("\n".join(c.action_description for c in self.controllers))

    # The 'draw' method is inherited from TextPanelWidget and works perfectly
