import pygame
import os
from typing import Tuple, List
from game_config import GameConfig
from tetromino import Tetromino
from board import Board
from score_manager import ScoreManager
from particle import Particle
import ttools


class GameRenderer:
    def __init__(self, config: GameConfig):
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - 分数显示版")
        # pygame.font.init()
        self.font = pygame.font.Font(ttools.get_resource_path(os.path.join("fonts", "MI_LanTing_Regular.ttf")), int(config.SCREEN_WIDTH * 0.08))
        self.block_surface = pygame.Surface((self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), pygame.SRCALPHA)
        self.grid_line_color = config.GRID_LINE_COLOR
        self.background_color = config.BACKGROUND_COLOR
        self.grid_surface = self._create_grid_surface()
        self.score_surface = None
        self.high_score_surface = None

        # 加载玻璃纹理图片
        # 加载玻璃纹理图片并缩放到方块大小
        # 加载玻璃纹理图片并缩放到方块大小
        texture_path = os.path.join("textures", "block.png")
        if os.path.exists(texture_path):
            print(f"纹理图片路径正确: {texture_path}")
            self.glass_texture = pygame.image.load(texture_path).convert()
            self.glass_texture = pygame.transform.scale(self.glass_texture, (self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
            print(f"纹理缩放后尺寸: {self.glass_texture.get_size()}")
        else:
            print(f"纹理图片路径错误: {texture_path}")
            self.glass_texture = pygame.Surface((self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
            self.glass_texture.fill((255, 0, 0))  # 使用红色占位符

        # 调试：直接绘制纹理到屏幕
        # self.screen.blit(self.glass_texture, (0, 0))
        # pygame.display.flip()
        # pygame.time.wait(2000)  # 等待 2 秒，观察纹理是否正确显示

        
    def draw_block(self, x: int, y: int, color: Tuple[int, int, int], alpha: int = 255) -> None:
        self.block_surface.fill((0, 0, 0, 0))
        pygame.draw.rect(self.block_surface, color + (alpha,), (0, 0, self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
        pygame.draw.rect(self.block_surface, (40, 40, 40), (0, 0, self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), 1)
        self.screen.blit(self.block_surface, (x * self.config.BLOCK_SIZE, y * self.config.BLOCK_SIZE))

    # def draw_block(self, x: int, y: int, color: Tuple[int, int, int], alpha: int = 255) -> None:
    #     block_size = self.config.BLOCK_SIZE
    #     rect = pygame.Rect(x * block_size, y * block_size, block_size, block_size)

    #     # 创建一个新的 Surface 用于绘制方块
    #     surface = pygame.Surface((block_size, block_size), pygame.SRCALPHA)

    #     # 绘制渐变背景
    #     for i in range(block_size):
    #         ratio = i / block_size
    #         gradient_color = (
    #             int(color[0] * (1 - ratio) + color[0] * 0.8 * ratio),
    #             int(color[1] * (1 - ratio) + color[1] * 0.8 * ratio),
    #             int(color[2] * (1 - ratio) + color[2] * 0.8 * ratio),
    #             alpha
    #         )
    #         pygame.draw.line(surface, gradient_color, (i, 0), (i, block_size))

    #     # 添加纹理
    #     texture_surface = self.glass_texture.copy()
    #     texture_surface.fill(color + (alpha,), special_flags=pygame.BLEND_RGBA_MULT)
    #     surface.blit(texture_surface, (0, 0))  # 将纹理绘制到 Surface 的左上角

    #     # 调试：绘制纹理边框
    #     # pygame.draw.rect(surface, (255, 0, 0), (0, 0, block_size, block_size), 1)  # 红色边框

    #     # 将 Surface 绘制到屏幕上
    #     self.screen.blit(surface, rect.topleft)

    #     # 绘制边框
    #     border_color = (max(0, color[0] - 50), max(0, color[1] - 50), max(0, color[2] - 50))
    #     pygame.draw.rect(self.screen, border_color, rect, 1)

   
    def draw_board(self, game_board: Board) -> None:
        for y, row in enumerate(game_board.grid):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(x, y, cell)

    def draw_piece(self, tetromino: Tetromino) -> None:
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(tetromino.x + x, tetromino.y + y, tetromino.color)

    def _create_grid_surface(self) -> pygame.Surface:
        grid_surface = pygame.Surface((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in range(0, self.config.SCREEN_WIDTH, self.config.BLOCK_SIZE):
            pygame.draw.line(grid_surface, self.grid_line_color, (x, 0), (x, self.config.SCREEN_HEIGHT))
        for y in range(0, self.config.SCREEN_HEIGHT, self.config.BLOCK_SIZE):
            pygame.draw.line(grid_surface, self.grid_line_color, (0, y), (self.config.SCREEN_WIDTH, y))
        return grid_surface

    def draw_grid(self) -> None:
        self.screen.blit(self.grid_surface, (0, 0))

    def draw_score(self, score_manager: ScoreManager) -> None:
        if score_manager.score_changed:
            formatted_score = f"{score_manager.score:,}"
            self.score_surface = self.font.render(f"分数: {formatted_score}", True, (255, 255, 255))
            score_manager.score_changed = False

        if score_manager.high_score_changed:
            formatted_high_score = f"{score_manager.high_score:,}"
            self.high_score_surface = self.font.render(f"最高分: {formatted_high_score}", True, (255, 255, 255))
            score_manager.high_score_changed = False

        if self.score_surface:
            self.screen.blit(self.score_surface, (10, 10))
        if self.high_score_surface:
            self.screen.blit(self.high_score_surface, (10, 10 + int(self.config.SCREEN_WIDTH * 0.08)))

    def draw_next_piece(self, tetromino: Tetromino) -> None:
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    block_x = self.config.PREVIEW_X // self.config.BLOCK_SIZE + x
                    block_y = self.config.PREVIEW_Y // self.config.BLOCK_SIZE + y
                    self.draw_block(block_x, block_y, tetromino.color)