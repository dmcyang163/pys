from dataclasses import dataclass
from typing import List, Tuple
import colorsys

@dataclass
class GameConfig:
    SCREEN_WIDTH: int = 300
    SCREEN_HEIGHT: int = 600
    BLOCK_SIZE: int = 30
    FALL_SPEED: float = 1.5
    FAST_FALL_SPEED: float = 21.0
    COLORS: List[Tuple[int, int, int]] = None
    SHAPES: List[List[List[int]]] = None
    PREVIEW_X: int = 220
    PREVIEW_Y: int = 50
    PREVIEW_SIZE: int = 4
    NUM_COLORS: int = 12
    GRID_LINE_COLOR: Tuple[int, int, int] = (50, 50, 50)
    BACKGROUND_COLOR: Tuple[int, int, int] = (30, 30, 30)
    EXPLOSION_PARTICLE_COUNT: int = 30
    ANIMATION_DURATION: int = 300

    def __post_init__(self):
        self.SHAPES = [
            [[1, 1, 1, 1]],
            [[1, 1, 1], [0, 1, 0]],
            [[1, 1], [1, 1]],
            [[0, 1, 1], [1, 1, 0]],
            [[1, 1, 0], [0, 1, 1]],
            [[1, 0, 0], [1, 1, 1]],
            [[0, 0, 1], [1, 1, 1]]
        ]
        self.COLORS = self._generate_colors(self.NUM_COLORS)

    def _generate_colors(self, num_colors: int) -> List[Tuple[int, int, int]]:
        colors = []
        for i in range(num_colors):
            hue = i / num_colors
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 0.8, 0.8)]
            colors.append((r, g, b))
        return colors