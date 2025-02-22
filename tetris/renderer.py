import pygame
import os
from typing import Tuple, List
from game_config import GameConfig
from tetromino import Tetromino
from board import Board
from score_manager import ScoreManager
from particle import Particle

class GameRenderer:
    def __init__(self, config: GameConfig):
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - 分数显示版")
        self.font = pygame.font.Font(os.path.join("fonts", "MI_LanTing_Regular.ttf"), int(config.SCREEN_WIDTH * 0.08))
        self.block_surface = pygame.Surface((self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), pygame.SRCALPHA)
        self.grid_line_color = config.GRID_LINE_COLOR
        self.background_color = config.BACKGROUND_COLOR
        self.grid_surface = self._create_grid_surface()
        self.score_surface = None
        self.high_score_surface = None

    def draw_block(self, x: int, y: int, color: Tuple[int, int, int], alpha: int = 255) -> None:
        self.block_surface.fill((0, 0, 0, 0))
        pygame.draw.rect(self.block_surface, color + (alpha,), (0, 0, self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
        pygame.draw.rect(self.block_surface, (50, 50, 50), (0, 0, self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), 1)
        self.screen.blit(self.block_surface, (x * self.config.BLOCK_SIZE, y * self.config.BLOCK_SIZE))

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