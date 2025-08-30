"""
Color scheme definitions for the physics engine visualization.

This module contains various color palettes that can be used throughout
the physics engine for consistent and visually appealing rendering.
"""

from typing import List, Tuple

# Type alias for RGB color tuples
Color = Tuple[int, int, int]

V1_COLORS =  ["#ffbe0b", "#fb5607", "#ff006e", "#8338ec", "#3a86ff"]

# Matplotlib's Tab10 color palette - good for categorical data
TAB10_COLORS: List[Color] = [
    (31, 119, 180),   # blue
    (255, 127, 14),   # orange
    (44, 160, 44),    # green
    (214, 39, 40),    # red
    (148, 103, 189),  # purple
    (140, 86, 75),    # brown
    (227, 119, 194),  # pink
    (127, 127, 127),  # gray
    (188, 189, 34),   # olive
    (23, 190, 207),   # cyan
]

# Classic primary colors
PRIMARY_COLORS: List[Color] = [
    (255, 0, 0),      # red
    (0, 255, 0),      # green
    (0, 0, 255),      # blue
    (255, 255, 0),    # yellow
    (255, 0, 255),    # magenta
    (0, 255, 255),    # cyan
]

# Grayscale palette
GRAYSCALE_COLORS: List[Color] = [
    (0, 0, 0),        # black
    (64, 64, 64),     # dark gray
    (128, 128, 128),  # medium gray
    (192, 192, 192),  # light gray
    (255, 255, 255),  # white
]

# Warm colors palette
WARM_COLORS: List[Color] = [
    (255, 69, 0),     # red-orange
    (255, 140, 0),    # dark orange
    (255, 165, 0),    # orange
    (255, 215, 0),    # gold
    (255, 255, 0),    # yellow
    (173, 255, 47),   # green-yellow
]

# Cool colors palette
COOL_COLORS: List[Color] = [
    (0, 255, 255),    # cyan
    (0, 191, 255),    # deep sky blue
    (30, 144, 255),   # dodger blue
    (0, 0, 255),      # blue
    (138, 43, 226),   # blue-violet
    (75, 0, 130),     # indigo
]

# High contrast colors for accessibility
HIGH_CONTRAST_COLORS: List[Color] = [
    (0, 0, 0),        # black
    (255, 255, 255),  # white
    (255, 0, 0),      # red
    (0, 255, 0),      # green
    (0, 0, 255),      # blue
    (255, 255, 0),    # yellow
]