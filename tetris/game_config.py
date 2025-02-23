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
        """
        生成霓虹风格的颜色方案。
        """
        colors = []
        for i in range(num_colors):
            # 使用 HSV 颜色空间，固定高饱和度和高亮度
            hue = i / num_colors  # 色调在 0 到 1 之间变化
            saturation = 1.0  # 高饱和度
            value = 1.0  # 高亮度
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, saturation, value)]
            colors.append((r, g, b))
        return colors
    
    def _generate_colors(self, num_colors: int) -> List[Tuple[int, int, int]]:
        """
        生成糖果风格的颜色方案。
        """
        colors = []
        for i in range(num_colors):
            # 使用 HSV 颜色空间，调整饱和度和亮度
            hue = i / num_colors  # 色调在 0 到 1 之间变化
            saturation = 0.6  # 中等饱和度
            value = 0.9  # 高亮度
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, saturation, value)]
            colors.append((r, g, b))
        return colors
    