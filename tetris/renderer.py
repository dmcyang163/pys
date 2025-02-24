import pygame
import os
from typing import Tuple, List
from game_config import GameConfig
from tetromino import Tetromino
from board import Board
from score_manager import ScoreManager
from particle import Particle
import ttools
from particle import ParticleSystem


class GameRenderer:
    def __init__(self, config: GameConfig):
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - 分数显示版")
        
        # 加载字体，启用抗锯齿
        self.font = pygame.font.Font(ttools.get_resource_path(os.path.join("fonts", "MI_LanTing_Regular.ttf")), int(config.SCREEN_WIDTH * 0.08))
        
        self.block_surface = pygame.Surface((self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), pygame.SRCALPHA)
        self.grid_line_color = config.GRID_LINE_COLOR
        self.background_color = config.BACKGROUND_COLOR
        self.grid_surface = self._create_grid_surface()
        self.score_surface = None
        self.high_score_surface = None

        # 加载玻璃纹理图片
        texture_path = os.path.join("textures", "block.png")
        if os.path.exists(texture_path):
            self.glass_texture = pygame.image.load(texture_path).convert()
            self.glass_texture = pygame.transform.scale(self.glass_texture, (self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
        else:
            self.glass_texture = pygame.Surface((self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
            self.glass_texture.fill((255, 0, 0))  # 使用红色占位符

        # 初始化暂停界面和游戏结束界面的 Surface
        self.pause_surface = None
        self.game_over_surface = None
        self._init_pause_surface()
        self._init_game_over_surface()

    def _init_pause_surface(self) -> None:
        # 创建暂停界面的 Surface
        self.pause_surface = pygame.Surface((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA)
        self.pause_surface.fill((0, 0, 0, 128))  # 黑色半透明遮罩

        # 绘制静态文字（不需要动态更新的部分）
        pause_text = self.font.render("游戏暂停中", True, (255, 255, 255))  # 启用抗锯齿
        text_rect = pause_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2))
        self.pause_surface.blit(pause_text, text_rect)

    def _init_game_over_surface(self) -> None:
        # 创建游戏结束界面的 Surface
        self.game_over_surface = pygame.Surface((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA)
        self.game_over_surface.fill((0, 0, 0, 128))  # 黑色半透明遮罩

        # 绘制静态文字
        self._draw_static_text()

    def _draw_static_text(self) -> None:
        """绘制游戏结束界面的静态文字"""
        game_over_text = self.font.render("游戏结束", True, (255, 255, 255))  # 启用抗锯齿
        restart_text = self.font.render("按 R 重新开始", True, (255, 255, 255))  # 启用抗锯齿
        quit_text = self.font.render("按 Q 退出游戏", True, (255, 255, 255))  # 启用抗锯齿

        # 将静态文字绘制到 Surface 上
        self.game_over_surface.blit(game_over_text, (self.config.SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, self.config.SCREEN_HEIGHT // 3))
        self.game_over_surface.blit(restart_text, (self.config.SCREEN_WIDTH // 2 - restart_text.get_width() // 2, self.config.SCREEN_HEIGHT // 2 + 100))
        self.game_over_surface.blit(quit_text, (self.config.SCREEN_WIDTH // 2 - quit_text.get_width() // 2, self.config.SCREEN_HEIGHT // 2 + 150))

    def draw_block(self, x: int, y: int, color: Tuple[int, int, int], alpha: int = 255) -> None:
        self.block_surface.fill((0, 0, 0, 0))
        pygame.draw.rect(self.block_surface, color + (alpha,), (0, 0, self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
        pygame.draw.rect(self.block_surface, (40, 40, 40), (0, 0, self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), 1)
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
            self.score_surface = self.font.render(f"分数: {formatted_score}", True, (255, 255, 255))  # 启用抗锯齿
            score_manager.score_changed = False

        if score_manager.high_score_changed:
            formatted_high_score = f"{score_manager.high_score:,}"
            self.high_score_surface = self.font.render(f"最高分: {formatted_high_score}", True, (255, 255, 255))  # 启用抗锯齿
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

    def render_game(self, game_board: Board, current_tetromino: Tetromino, next_tetromino: Tetromino, score_manager: ScoreManager, particle_system: ParticleSystem) -> None:
        """
        渲染游戏画面。
        """
        self.screen.fill(self.background_color)
        self.draw_grid()
        self.draw_board(game_board)
        self.draw_piece(current_tetromino)
        particle_system.draw(self.screen)
        self.draw_next_piece(next_tetromino)
        self.draw_score(score_manager)

    def render_pause_screen(self, game_board: Board, current_tetromino: Tetromino, next_tetromino: Tetromino, score_manager: ScoreManager, particle_system: ParticleSystem) -> None:
        # 先绘制当前游戏画面
        self.render_game(game_board, current_tetromino, next_tetromino, score_manager, particle_system)

        # 最后绘制暂停界面（遮罩和文字）
        self.screen.blit(self.pause_surface, (0, 0))

    def render_game_over(self, game_board: Board, current_tetromino: Tetromino, next_tetromino: Tetromino, score_manager: ScoreManager, particle_system: ParticleSystem) -> None:
        print("Rendering game over screen...")

        # 先绘制当前游戏画面
        self.render_game(game_board, current_tetromino, next_tetromino, score_manager, particle_system)

        # 清空 game_over_surface，避免文字叠加
        self.game_over_surface.fill((0, 0, 0, 128))  # 重新填充半透明黑色遮罩

        # 绘制静态文字
        self._draw_static_text()

        # 动态更新分数
        score_text = self.font.render(f"分数: {score_manager.score:,}", True, (255, 255, 255))  # 启用抗锯齿
        high_score_text = self.font.render(f"最高分: {score_manager.high_score:,}", True, (255, 255, 255))  # 启用抗锯齿

        # 将动态文字绘制到 Surface 上
        self.game_over_surface.blit(score_text, (self.config.SCREEN_WIDTH // 2 - score_text.get_width() // 2, self.config.SCREEN_HEIGHT // 2))
        self.game_over_surface.blit(high_score_text, (self.config.SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, self.config.SCREEN_HEIGHT // 2 + 50))

        # 最后绘制游戏结束界面（遮罩和文字）
        self.screen.blit(self.game_over_surface, (0, 0))
        print("Game Over Surface drawn at (0, 0)")