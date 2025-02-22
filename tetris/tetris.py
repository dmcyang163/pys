import colorsys
import pygame
import random
import os
from typing import List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

@dataclass
class GameConfig:
    SCREEN_WIDTH: int = 300
    SCREEN_HEIGHT: int = 600
    BLOCK_SIZE: int = 30
    FALL_SPEED: float = 1.5
    FAST_FALL_SPEED: float = 15.0
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
        根据 HSV 值生成颜色列表。

        Args:
            num_colors (int): 要生成的颜色数量。

        Returns:
            list[tuple[int, int, int]]: 颜色列表，每个颜色都是一个 RGB 元组。
        """
        colors = []
        for i in range(num_colors):
            hue = i / num_colors
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 0.8, 0.8)]
            colors.append((r, g, b))
        return colors

class Tetromino:
    """
    表示一个俄罗斯方块，包含形状、颜色、位置和旋转信息。
    """
    def __init__(self, config: GameConfig):
        """
        初始化俄罗斯方块。

        Args:
            config (GameConfig): 游戏配置对象。
        """
        self.shape = random.choice(config.SHAPES)
        self.color = random.choice(config.COLORS)
        self.x = 0
        self.y = 0
        self.rotations = self._calculate_rotations()
        self.rotation_index = 0

    def _calculate_rotations(self) -> List[List[List[int]]]:
        """
        计算形状的所有可能旋转。

        Returns:
            list[list[list[int]]]: 旋转列表，每个旋转都是一个形状（二维列表）。
        """
        rotations = [self.shape]
        for _ in range(3):
            rotations.append(list(zip(*rotations[-1][::-1])))
        return rotations

    def rotate(self) -> None:
        """
        将俄罗斯方块旋转到下一个预先计算的旋转。
        """
        self.rotation_index = (self.rotation_index + 1) % len(self.rotations)
        self.shape = self.rotations[self.rotation_index]

class Board:
    """
    表示游戏面板，包含网格和碰撞检测逻辑。
    """
    def __init__(self, config: GameConfig):
        """
        初始化游戏面板。

        Args:
            config (GameConfig): 游戏配置对象。
        """
        self.config = config
        self.grid = [[0 for _ in range(config.SCREEN_WIDTH // config.BLOCK_SIZE)]
                     for _ in range(config.SCREEN_HEIGHT // config.BLOCK_SIZE)]

    def check_collision(self, tetromino: Tetromino, piece_x: int, piece_y: int) -> bool:
        """
        检查方块是否与面板或其他方块发生碰撞。

        Args:
            tetromino (Tetromino): 要检查的方块。
            piece_x (int): 方块的 X 坐标。
            piece_y (int): 方块的 Y 坐标。

        Returns:
            bool: 如果发生碰撞，则返回 True，否则返回 False。
        """
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece_x + x
                    new_y = piece_y + y
                    if (new_x < 0 or new_x >= len(self.grid[0]) or new_y >= len(self.grid) or
                            (new_y >= 0 and self.grid[new_y][new_x])):
                        return True
        return False

    def merge_piece(self, tetromino: Tetromino) -> None:
        """
        将方块合并到面板中。

        Args:
            tetromino (Tetromino): 要合并的方块。
        """
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[tetromino.y + y][tetromino.x + x] = tetromino.color

    def clear_lines(self) -> List[int]:  # 返回被清除的行的索引列表
        """
        清除面板上的任何完整行，并返回已清除的行数。

        Returns:
            list[int]: 包含被清除行索引的列表。
        """
        lines_to_clear = [i for i, row in enumerate(self.grid) if all(row)]
        self.remove_lines(lines_to_clear)  # 直接调用 remove_lines
        return lines_to_clear

    def remove_lines(self, lines_to_clear: List[int]) -> None:
        """
        从面板中移除指定的行。

        Args:
            lines_to_clear (list[int]): 要移除的行索引列表。
        """
        for i in sorted(lines_to_clear, reverse=True):  # 从后往前删除，避免索引问题
            del self.grid[i]
            self.grid.insert(0, [0 for _ in range(len(self.grid[0]))])

class ScoreManager:
    """
    管理游戏得分和高分。
    """
    def __init__(self):
        """
        初始化得分管理器。
        """
        self.score = 0
        self.high_score = 0
        self.load_high_score()

    def load_high_score(self) -> None:
        """
        从文件中加载高分。
        """
        try:
            with open("high_score.txt", "r") as f:
                self.high_score = int(f.read())
        except FileNotFoundError:
            self.high_score = 0
        except ValueError:
            self.high_score = 0

    def update_high_score(self) -> None:
        """
        如果当前得分高于高分，则更新高分。
        """
        if self.score > self.high_score:
            self.high_score = self.score
            with open("high_score.txt", "w") as f:
                f.write(str(self.high_score))

class Particle:
    """
    表示爆炸效果中的一个粒子。
    """
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        """
        初始化粒子。

        Args:
            x (int): 粒子的 X 坐标。
            y (int): 粒子的 Y 坐标。
            color (tuple[int, int, int]): 粒子的颜色 (RGB)。
        """
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(6, 12)  # 粒子大小范围
        self.speed_x = random.uniform(-3, 3)  # 粒子水平速度范围
        self.speed_y = random.uniform(-7, -2)  # 粒子垂直速度范围
        self.lifetime = random.randint(30, 60)  # 粒子生命周期范围
        self.original_color = color  # 记录原始颜色
        self.fade_speed = random.uniform(0.02, 0.05)  # 颜色淡化速度

    def update(self) -> None:
        """
        更新粒子的位置、大小、颜色和生命周期。
        """
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += 0.1  # 重力
        self.lifetime -= 1

        # 粒子大小逐渐缩小
        self.size = max(1, self.size - 0.2)

        # 粒子颜色逐渐淡化
        r, g, b = self.color
        fade_amount = int(255 * self.fade_speed)
        r = max(0, r - fade_amount)
        g = max(0, g - fade_amount)
        b = max(0, b - fade_amount)
        self.color = (r, g, b)

    def draw(self, screen: pygame.Surface) -> None:
        """
        在屏幕上绘制粒子。

        Args:
            screen (pygame.Surface): 要绘制的屏幕 Surface 对象。
        """
        pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), int(self.size), int(self.size)))

class GameRenderer:
    """
    负责渲染游戏界面，包括面板、方块、网格和得分。
    """
    def __init__(self, config: GameConfig):
        """
        初始化游戏渲染器。

        Args:
            config (GameConfig): 游戏配置对象。
        """
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - 分数显示版")
        self.font = pygame.font.Font(os.path.join("fonts", "MI_LanTing_Regular.ttf"), int(config.SCREEN_WIDTH * 0.08))
        self.block_surface = pygame.Surface((self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), pygame.SRCALPHA)  # 创建一个 block_surface
        self.grid_line_color = config.GRID_LINE_COLOR # 使用常量
        self.background_color = config.BACKGROUND_COLOR # 使用常量

    def draw_block(self, x: int, y: int, color: Tuple[int, int, int], alpha: int = 255) -> None:
        """
        在屏幕上绘制一个单独的方块，可以选择设置透明度。

        Args:
            x (int): 方块的 X 坐标。
            y (int): 方块的 Y 坐标。
            color (tuple[int, int, int]): 方块的颜色 (RGB)。
            alpha (int, optional): 方块的透明度 (0-255)。默认为 255 (不透明)。
        """
        self.block_surface.fill((0, 0, 0, 0))  # 清空 surface
        pygame.draw.rect(self.block_surface, color + (alpha,), (0, 0, self.config.BLOCK_SIZE, self.config.BLOCK_SIZE))
        self.screen.blit(self.block_surface, (x * self.config.BLOCK_SIZE, y * self.config.BLOCK_SIZE))
        pygame.draw.rect(self.screen, (50, 50, 50), (x * self.config.BLOCK_SIZE,
                         y * self.config.BLOCK_SIZE,
                         self.config.BLOCK_SIZE,
                         self.config.BLOCK_SIZE), 1)

    def draw_board(self, game_board: Board) -> None:
        """
        在屏幕上绘制整个游戏面板。

        Args:
            game_board (Board): 要绘制的游戏面板对象。
        """
        for y, row in enumerate(game_board.grid):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(x, y, cell)

    def draw_piece(self, tetromino: Tetromino) -> None:
        """
        在屏幕上绘制当前的俄罗斯方块。

        Args:
            tetromino (Tetromino): 要绘制的俄罗斯方块对象。
        """
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(tetromino.x + x, tetromino.y + y, tetromino.color)

    def draw_grid(self) -> None:
        """
        在屏幕上绘制网格线。
        """
        for x in range(0, self.config.SCREEN_WIDTH, self.config.BLOCK_SIZE):
            pygame.draw.line(self.screen, self.grid_line_color, (x, 0), (x, self.config.SCREEN_HEIGHT)) # 使用常量
        for y in range(0, self.config.SCREEN_HEIGHT, self.config.BLOCK_SIZE):
            pygame.draw.line(self.screen, self.grid_line_color, (0, y), (self.config.SCREEN_WIDTH, y)) # 使用常量

    def draw_score(self, score_manager: ScoreManager) -> None:
        """
        在屏幕上绘制得分和高分。

        Args:
            score_manager (ScoreManager): 得分管理器对象。
        """
        formatted_score = f"{score_manager.score:,}"
        formatted_high_score = f"{score_manager.high_score:,}"
        score_text = self.font.render(f"分数: {formatted_score}", True, (255, 255, 255))
        high_score_text = self.font.render(f"最高分: {formatted_high_score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(high_score_text, (10, 10 + int(self.config.SCREEN_WIDTH * 0.08)))

    def draw_next_piece(self, tetromino: Tetromino, config: GameConfig) -> None:
        """
        在预览区域绘制下一个俄罗斯方块。

        Args:
            tetromino (Tetromino): 要绘制的下一个俄罗斯方块对象。
            config (GameConfig): 游戏配置对象。
        """
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    block_x = config.PREVIEW_X // config.BLOCK_SIZE + x
                    block_y = config.PREVIEW_Y // config.BLOCK_SIZE + y
                    self.draw_block(block_x, block_y, tetromino.color)

    def draw_explosion(self, x: int, y: int, color: Tuple[int, int, int], explosion_particles: List[Particle]) -> None:
        """
        在指定位置创建爆炸效果。

        Args:
            x (int): 爆炸中心的 X 坐标。
            y (int): 爆炸中心的 Y 坐标。
            color (tuple[int, int, int]): 爆炸粒子的颜色 (RGB)。
            explosion_particles (list[Particle]): 存储爆炸粒子的列表。
        """
        num_particles = 30  # 增加粒子数量
        for _ in range(num_particles):
            particle = Particle(x * self.config.BLOCK_SIZE + self.config.BLOCK_SIZE // 2,
                                y * self.config.BLOCK_SIZE + self.config.BLOCK_SIZE // 2,
                                color)
            explosion_particles.append(particle)

        # 添加闪光效果
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (x * self.config.BLOCK_SIZE + self.config.BLOCK_SIZE // 2,
                            y * self.config.BLOCK_SIZE + self.config.BLOCK_SIZE // 2),
                           self.config.BLOCK_SIZE // 2)

    def draw_clearing_animation(self, game_board: Board, lines_to_clear: List[int], animation_progress: float, explosion_particles: List[Particle]) -> None:
        """
        绘制指定行的清除动画（爆炸效果）。

        Args:
            game_board (Board): 游戏面板对象。
            lines_to_clear (list[int]): 要清除的行索引列表。
            animation_progress (float): 动画进度 (0.0 到 1.0)。
            explosion_particles (list[Particle]): 存储爆炸粒子的列表。
        """
        for i in lines_to_clear:
            for x in range(len(game_board.grid[0])):
                if game_board.grid[i][x]:
                    self.draw_explosion(x, i, game_board.grid[i][x], explosion_particles)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3

class InputHandler:
    def __init__(self, game):
        self.game = game

    def handle_input(self) -> bool:
        """
        处理用户输入事件。

        Returns:
            bool: 如果游戏应该继续运行，则返回 True，否则返回 False (退出游戏)。
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if self.game.game_state == GameState.PLAYING:
                self._handle_key_event(event)
        return True

    def _handle_key_event(self, event) -> None:
        """
        处理键盘事件。

        Args:
            event: Pygame 事件对象。
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.game.left_key_pressed = True
            if event.key == pygame.K_RIGHT:
                self.game.right_key_pressed = True
            if event.key == pygame.K_DOWN:
                self.game.down_key_pressed = True
            if event.key == pygame.K_UP:
                self.game.current_tetromino.rotate()
                if self.game.game_board.check_collision(
                    self.game.current_tetromino,
                    self.game.current_tetromino.x,
                    self.game.current_tetromino.y
                ):
                    # 如果旋转后发生碰撞，则撤销旋转
                    for _ in range(3):
                        self.game.current_tetromino.rotate()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.game.left_key_pressed = False
            if event.key == pygame.K_RIGHT:
                self.game.right_key_pressed = False
            if event.key == pygame.K_DOWN:
                self.game.down_key_pressed = False

class TetrisGame:
    """
    主游戏类，包含游戏循环、输入处理和游戏逻辑。
    """
    def __init__(self):
        """
        初始化游戏。
        """
        pygame.init()
        pygame.display.init()
        if pygame.display.get_driver() == "directx":
            pygame.display.quit()
            os.environ['SDL_VIDEODRIVER'] = 'windib'
            pygame.display.init()
        self.config = GameConfig()
        self.game_board = Board(self.config)
        self.renderer = GameRenderer(self.config)
        self.score_manager = ScoreManager()
        self.current_tetromino = self._create_new_piece()
        self.next_tetromino = self._create_new_piece()
        self.last_fall_time = pygame.time.get_ticks()
        self.down_key_pressed = False
        self.left_key_pressed = False
        self.right_key_pressed = False
        self.last_move_time = 0
        self.move_delay = 150

        self.cleared_lines = []  # 需要清除的行
        self.clearing_animation_progress = 0.0  # 清除动画的进度 (0.0 到 1.0)
        self.is_clearing = False  # 是否正在清除动画
        self.explosion_particles = []  # 存储爆炸粒子
        self.game_state = GameState.PLAYING

        # 加载背景音乐
        pygame.mixer.music.load(os.path.join("sounds", "tetris_music.mp3"))
        pygame.mixer.music.play(-1)

        # 加载爆炸音效
        self.explosion_sound = pygame.mixer.Sound(os.path.join("sounds", "explosion.wav"))

        # 初始化 InputHandler
        self.input_handler = InputHandler(self)


    def _create_new_piece(self) -> Tetromino:
        """
        创建一个新的俄罗斯方块，并将其放置在面板顶部。

        Returns:
            Tetromino: 新创建的俄罗斯方块对象。
        """
        tetromino = Tetromino(self.config)
        return tetromino

    def handle_input(self) -> bool:
        """
        处理用户输入事件。

        Returns:
            bool: 如果游戏应该继续运行，则返回 True，否则返回 False (退出游戏)。
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if self.game_state == GameState.PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.left_key_pressed = True
                    if event.key == pygame.K_RIGHT:
                        self.right_key_pressed = True
                    if event.key == pygame.K_DOWN:
                        self.down_key_pressed = True
                    if event.key == pygame.K_UP:
                        self.current_tetromino.rotate()
                        if self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x, self.current_tetromino.y):
                            # 如果旋转后发生碰撞，则撤销旋转
                            for _ in range(3):
                                self.current_tetromino.rotate()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.left_key_pressed = False
                    if event.key == pygame.K_RIGHT:
                        self.right_key_pressed = False
                    if event.key == pygame.K_DOWN:
                        self.down_key_pressed = False
        return True    
    def new_piece(self) -> bool:
        """
        创建一个新的俄罗斯方块，并将其放置在面板顶部。

        如果无法放置新的俄罗斯方块（游戏结束），则返回 False。

        Returns:
            bool: 如果成功创建了新的俄罗斯方块，则返回 True，否则返回 False (游戏结束)。
        """
        self.current_tetromino = self.next_tetromino
        self.next_tetromino = self._create_new_piece()
        self.current_tetromino.x = self.config.SCREEN_WIDTH // self.config.BLOCK_SIZE // 2 - len(self.current_tetromino.shape[0]) // 2
        self.current_tetromino.y = 0
        if self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x, self.current_tetromino.y):
            # 游戏结束
            self.score_manager.update_high_score()
            self.game_state = GameState.GAME_OVER
            return False
        return True

    def _handle_clearing_animation(self, current_time: int, animation_duration: int) -> None:
        """
        处理清除动画。

        Args:
            current_time (int): 当前时间（毫秒）。
            animation_duration (int): 动画持续时间（毫秒）。
        """
        self.clearing_animation_progress = min(1.0, self.clearing_animation_progress + (current_time - self.last_frame_time) / animation_duration)
        self.renderer.draw_clearing_animation(self.game_board, self.cleared_lines, self.clearing_animation_progress, self.explosion_particles)
        if self.clearing_animation_progress >= 1.0:
            # 动画完成，移除行并创建新方块
            self.game_board.remove_lines(self.cleared_lines)
            self.is_clearing = False
            self.explosion_particles = []  # 清空爆炸粒子
            if not self.new_piece():
                self.running = False  # Game over

    def _handle_piece_movement(self, current_time: int) -> None:
        """
        处理方块的左右移动和下落。

        Args:
            current_time (int): 当前时间（毫秒）。
        """
        self._move_piece_horizontally(current_time)
        self._move_piece_down(current_time)

    def _move_piece_horizontally(self, current_time: int) -> None:
        """
        处理方块的左右移动。

        Args:
            current_time (int): 当前时间（毫秒）。
        """
        if current_time - self.last_move_time > self.move_delay:
            if self.left_key_pressed:
                if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x - 1, self.current_tetromino.y):
                    self.current_tetromino.x -= 1
                    self.last_move_time = current_time
            if self.right_key_pressed:
                if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x + 1, self.current_tetromino.y):
                    self.current_tetromino.x += 1
                    self.last_move_time = current_time

    def _move_piece_down(self, current_time: int) -> None:
        """
        处理方块的下落。

        Args:
            current_time (int): 当前时间（毫秒）。
        """
        current_speed = self.config.FAST_FALL_SPEED if self.down_key_pressed else self.config.FALL_SPEED
        if current_time - self.last_fall_time > 1000 / current_speed:
            if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x, self.current_tetromino.y + 1):
                self.current_tetromino.y += 1
                self.last_fall_time = current_time  # 更新 last_fall_time
            else:
                self._handle_piece_landed()

    def _handle_piece_landed(self) -> None:
        """
        处理方块落地的情况。
        """
        self.game_board.merge_piece(self.current_tetromino)
        self.cleared_lines = self.game_board.clear_lines()
        if self.cleared_lines:
            self.is_clearing = True
            self.clearing_animation_progress = 0.0
            self.score_manager.score += 100 * len(self.cleared_lines) ** 2
            self.explosion_sound.play()  # 播放爆炸音效
        else:
            if not self.new_piece():
                # 游戏结束，设置游戏状态为 GAME_OVER
                self.game_state = GameState.GAME_OVER
        self.last_fall_time = pygame.time.get_ticks()

    def _update_explosion_particles(self) -> None:
        """
        更新和移除爆炸粒子。
        """
        for particle in self.explosion_particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.explosion_particles.remove(particle)

    def _render_game(self) -> None:
        """
        渲染游戏界面。
        """
        self.renderer.screen.fill(self.renderer.background_color)
        self.renderer.draw_grid()
        self.renderer.draw_board(self.game_board)

        if not self.is_clearing:
            # 绘制当前方块
            self.renderer.draw_piece(self.current_tetromino)

        # 绘制爆炸粒子
        for particle in self.explosion_particles:
            particle.draw(self.renderer.screen)

        self.renderer.draw_next_piece(self.next_tetromino, self.config)
        self.renderer.draw_score(self.score_manager)
        pygame.display.flip()

    def game_loop(self) -> None:
        """
        主游戏循环。
        """
        clock = pygame.time.Clock()
        self.running = True
        self.new_piece()

        while self.running:
            current_time = pygame.time.get_ticks()
            # 使用 InputHandler 处理输入
            self.running = self.input_handler.handle_input()

            if self.game_state == GameState.PLAYING:
                if self.is_clearing:
                    self._handle_clearing_animation(current_time, self.config.ANIMATION_DURATION)
                else:
                    self._handle_piece_movement(current_time)

                self._update_explosion_particles()
                self._render_game()

            elif self.game_state == GameState.GAME_OVER:
                # 显示游戏结束界面
                self.renderer.screen.fill((0, 0, 0))
                game_over_text = self.renderer.font.render("游戏结束", True, (255, 255, 255))
                score_text = self.renderer.font.render(f"分数: {self.score_manager.score:,}", True, (255, 255, 255))
                high_score_text = self.renderer.font.render(f"最高分: {self.score_manager.high_score:,}", True, (255, 255, 255))
                restart_text = self.renderer.font.render("按 R 重新开始", True, (255, 255, 255))
                quit_text = self.renderer.font.render("按 Q 退出游戏", True, (255, 255, 255))

                game_over_rect = game_over_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 3))
                score_rect = score_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2))
                high_score_rect = high_score_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2 + 50))
                restart_rect = restart_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2 + 100))
                quit_rect = quit_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2 + 150))

                self.renderer.screen.blit(game_over_text, game_over_rect)
                self.renderer.screen.blit(score_text, score_rect)
                self.renderer.screen.blit(high_score_text, high_score_rect)
                self.renderer.screen.blit(restart_text, restart_rect)
                self.renderer.screen.blit(quit_text, quit_rect)

                pygame.display.flip()

                # 清空事件队列
                pygame.event.clear()

                # 等待用户按下 R 键重新开始游戏或 Q 键退出游戏
                waiting_for_restart = True
                while waiting_for_restart:
                    for event in pygame.event.get():
                        print("Event:", event)  # 打印事件信息
                        if event.type == pygame.QUIT:
                            self.running = False
                            waiting_for_restart = False
                        if event.type == pygame.KEYDOWN:
                            key = pygame.key.name(event.key).lower()  # 将按键值转换为小写
                            print("Key pressed:", key)  # 打印按下的键
                            if key == 'r':
                                # 重新初始化游戏
                                self.__init__()
                                waiting_for_restart = False
                                self.game_state = GameState.PLAYING
                                self.new_piece()
                            elif key == 'q':
                                # 退出游戏
                                self.running = False
                                waiting_for_restart = False
                        elif event.type == pygame.TEXTEDITING:
                            # 处理文本输入事件
                            print("TextEditing event:", event.text)  # 打印文本输入事件
                            if event.text.lower() == 'r':
                                # 重新初始化游戏
                                self.__init__()
                                waiting_for_restart = False
                                self.game_state = GameState.PLAYING
                                self.new_piece()
                            elif event.text.lower() == 'q':
                                # 退出游戏
                                self.running = False
                                waiting_for_restart = False

            self.last_frame_time = current_time
            # print(f"FPS: {clock.get_fps()}")

            # 限制帧率为 30 FPS
            clock.tick(30)

        pygame.mixer.music.stop()
        pygame.quit()

if __name__ == "__main__":
    game = TetrisGame()
    game.game_loop()
