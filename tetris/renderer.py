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
    """渲染游戏元素到屏幕上。"""

    # 常量
    TEXT_COLOR = (255, 255, 255)  # 文本颜色
    GAME_OVER_TEXT_OFFSET = -50  # 游戏结束界面文本偏移量
    FONT_SIZE_RATIO = 0.08  # 字体大小比例
    GRID_LINE_COLOR = (40, 40, 40)  # 网格线颜色
    BLOCK_BORDER_COLOR = (40, 40, 40)  # 方块边框颜色
    BLOCK_ALPHA = 255  # 方块透明度

    def __init__(self, config: GameConfig):
        """初始化。"""
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块")

        # 加载字体
        font_size = int(config.SCREEN_WIDTH * self.FONT_SIZE_RATIO)
        self.font = pygame.font.Font(ttools.get_resource_path(os.path.join("assets", "fonts", "MI_LanTing_Regular.ttf")), font_size)

        # 初始化方块缓存
        self.block_cache = {}  # 缓存不同颜色的方块 Surface

        # 初始化网格 Surface
        self.grid_surface = self._init_grid_surface()

        # 初始化分数、最高分和等级 Surface
        self.score_surface = None
        self.high_score_surface = None
        self.level_surface = None

        # 加载玻璃纹理
        texture_path = os.path.join("assets/textures", "block.png")
        if os.path.exists(texture_path):
            self.glass_texture = pygame.image.load(texture_path).convert()
            self.glass_texture = pygame.transform.scale(self.glass_texture, (self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
        else:
            self.glass_texture = pygame.Surface((self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
            self.glass_texture.fill((255, 0, 0))  # 占位符

        # 初始化暂停和游戏结束界面
        self.pause_surface = self._init_pause_surface()
        self.game_over_surface = self._init_game_over_surface()

    def _init_pause_surface(self) -> pygame.Surface:
        """初始化暂停界面。"""
        pause_surface = pygame.Surface((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA)
        pause_surface.fill((0, 0, 0, 128))  # 黑色半透明遮罩

        # 绘制静态文本
        pause_text = self.font.render("游戏暂停中", True, self.TEXT_COLOR)
        text_rect = pause_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2))
        pause_surface.blit(pause_text, text_rect)

        return pause_surface

    def _init_game_over_surface(self) -> pygame.Surface:
        """初始化游戏结束界面。"""
        game_over_surface = pygame.Surface((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA)
        game_over_surface.fill((0, 0, 0, 160))  # 黑色半透明遮罩

        # 绘制静态文本
        self._draw_static_text(game_over_surface)

        return game_over_surface

    def _draw_static_text(self, surface: pygame.Surface) -> None:
        """绘制静态文本。"""
        game_over_text = self.font.render("游戏结束", True, self.TEXT_COLOR)
        restart_text = self.font.render("按 R 重新开始", True, self.TEXT_COLOR)
        quit_text = self.font.render("按 Q 退出游戏", True, self.TEXT_COLOR)

        # 绘制文本
        text_y = self.config.SCREEN_HEIGHT // 2 + 100
        self._draw_text(surface, game_over_text, self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 3)
        self._draw_text(surface, restart_text, self.config.SCREEN_WIDTH // 2, text_y)
        self._draw_text(surface, quit_text, self.config.SCREEN_WIDTH // 2, text_y + 50)

    def _draw_text(self, surface: pygame.Surface, text: pygame.Surface, x: int, y: int, center_x: bool = True, center_y: bool = True) -> None:
        """绘制文本。"""
        text_rect = text.get_rect()
        if center_x:
            text_rect.centerx = x
        else:
            text_rect.x = x
        if center_y:
            text_rect.centery = y
        else:
            text_rect.y = y
        surface.blit(text, text_rect)

    def draw_block(self, x: int, y: int, color: Tuple[int, int, int], alpha: int = BLOCK_ALPHA) -> None:
        """绘制方块。"""
        if color not in self.block_cache:
            block_surface = pygame.Surface((self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(block_surface, color + (alpha,), (0, 0, self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
            pygame.draw.rect(block_surface, self.BLOCK_BORDER_COLOR, (0, 0, self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), 1)
            self.block_cache[color] = block_surface
        self.screen.blit(self.block_cache[color], (x * self.config.BLOCK_SIZE, y * self.config.BLOCK_SIZE))

    def draw_board(self, game_board: Board) -> None:
        """绘制游戏面板。"""
        for y, row in enumerate(game_board.grid):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(x, y, cell)

    def draw_piece(self, tetromino: Tetromino) -> None:
        """绘制俄罗斯方块。"""
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(tetromino.x + x, tetromino.y + y, tetromino.color)

    def _init_grid_surface(self) -> pygame.Surface:
        """初始化网格。"""
        grid_surface = pygame.Surface((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in range(0, self.config.SCREEN_WIDTH, self.config.BLOCK_SIZE):
            pygame.draw.line(grid_surface, self.GRID_LINE_COLOR, (x, 0), (x, self.config.SCREEN_HEIGHT))
        for y in range(0, self.config.SCREEN_HEIGHT, self.config.BLOCK_SIZE):
            pygame.draw.line(grid_surface, self.GRID_LINE_COLOR, (0, y), (self.config.SCREEN_WIDTH, y))
        return grid_surface

    def draw_grid(self) -> None:
        """绘制网格。"""
        self.screen.blit(self.grid_surface, (0, 0))

    def draw_score(self, score_manager: ScoreManager) -> None:
        """绘制分数。"""
        if score_manager.score_changed:
            formatted_score = f"{score_manager.score:,}"
            self.score_surface = self.font.render(f"分数: {formatted_score}", True, self.TEXT_COLOR)
            score_manager.score_changed = False

        if score_manager.high_score_changed:
            formatted_high_score = f"{score_manager.high_score:,}"
            self.high_score_surface = self.font.render(f"最高分: {formatted_high_score}", True, self.TEXT_COLOR)
            score_manager.high_score_changed = False

        if score_manager.level_changed:
            formatted_level = f"{score_manager.level:,}"
            self.level_surface = self.font.render(f"等级: {formatted_level}", True, self.TEXT_COLOR)
            score_manager.level_changed = False

        text_y = 10
        text_spacing = int(self.config.SCREEN_WIDTH * self.FONT_SIZE_RATIO)
        if self.score_surface:
            self._draw_text(self.screen, self.score_surface, 10 + self.score_surface.get_width() // 2, text_y + self.score_surface.get_height() // 2)
            text_y += text_spacing
        if self.high_score_surface:
            self._draw_text(self.screen, self.high_score_surface, 10 + self.high_score_surface.get_width() // 2, text_y + self.high_score_surface.get_height() // 2)
            text_y += text_spacing
        if self.level_surface:
            self._draw_text(self.screen, self.level_surface, 10 + self.level_surface.get_width() // 2, text_y + self.level_surface.get_height() // 2)

    def draw_next_piece(self, tetromino: Tetromino) -> None:
        """绘制下一个俄罗斯方块。"""
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    block_x = self.config.PREVIEW_X // self.config.BLOCK_SIZE + x
                    block_y = self.config.PREVIEW_Y // self.config.BLOCK_SIZE + y
                    self.draw_block(block_x, block_y, tetromino.color)

    def render_game(self, game_board: Board, current_tetromino: Tetromino, next_tetromino: Tetromino, score_manager: ScoreManager, particle_system: ParticleSystem) -> None:
        """渲染游戏。"""
        self.screen.fill(self.config.BACKGROUND_COLOR)
        self.draw_grid()
        self.draw_board(game_board)
        self.draw_piece(current_tetromino)
        particle_system.draw(self.screen)
        self.draw_next_piece(next_tetromino)
        self.draw_score(score_manager)

        # 绘制消除行得分
        self.draw_score_popup(score_manager)

    def render_pause_screen(self, game_board: Board, current_tetromino: Tetromino, next_tetromino: Tetromino, score_manager: ScoreManager, particle_system: ParticleSystem) -> None:
        """渲染暂停界面。"""
        self.render_game(game_board, current_tetromino, next_tetromino, score_manager, particle_system)
        self.screen.blit(self.pause_surface, (0, 0))

    def render_game_over(self, game_board: Board, current_tetromino: Tetromino, next_tetromino: Tetromino, score_manager: ScoreManager, particle_system: ParticleSystem) -> None:
        """渲染游戏结束界面。"""
        self.render_game(game_board, current_tetromino, next_tetromino, score_manager, particle_system)
        self._draw_game_over_screen(score_manager)

    def _draw_game_over_screen(self, score_manager: ScoreManager) -> None:
        """绘制游戏结束界面。"""
        self.game_over_surface.fill((0, 0, 0, 160))  # 黑色半透明遮罩
        self._draw_static_text(self.game_over_surface)

        # 渲染动态文本
        score_text = self.font.render(f"分数: {score_manager.score:,}", True, self.TEXT_COLOR)
        high_score_text = self.font.render(f"最高分: {score_manager.high_score:,}", True, self.TEXT_COLOR)
        level_text = self.font.render(f"等级: {score_manager.level:,}", True, self.TEXT_COLOR)

        # 绘制动态文本
        offset = self.GAME_OVER_TEXT_OFFSET
        text_y = self.config.SCREEN_HEIGHT // 2 + offset
        self._draw_text(self.game_over_surface, score_text, self.config.SCREEN_WIDTH // 2, text_y)
        text_y += 50
        self._draw_text(self.game_over_surface, high_score_text, self.config.SCREEN_WIDTH // 2, text_y)
        text_y += 50
        self._draw_text(self.game_over_surface, level_text, self.config.SCREEN_WIDTH // 2, text_y)

        # 绘制游戏结束界面
        self.screen.blit(self.game_over_surface, (0, 0))

    def draw_score_popup(self, score_manager: ScoreManager) -> None:
        """绘制消除行得分。"""
        if score_manager.score_popup_text is None:
            return

        elapsed_time = pygame.time.get_ticks() - score_manager.score_popup_start_time
        if elapsed_time > score_manager.score_popup_duration:
            score_manager.score_popup_text = None  # 结束显示
            return

        # 计算透明度
        alpha = max(0, 255 - (elapsed_time / score_manager.score_popup_duration) * 255)
        score_manager.score_popup_alpha = alpha

        # 创建带透明度的文本 Surface
        text_surface = pygame.Surface(score_manager.score_popup_text.get_size(), pygame.SRCALPHA)
        text_surface.blit(score_manager.score_popup_text, (0, 0))
        text_surface.set_alpha(int(alpha))

        # 绘制文本
        text_rect = text_surface.get_rect(center=score_manager.score_popup_position)
        self.screen.blit(text_surface, text_rect)
