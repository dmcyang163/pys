import colorsys
import pygame
import random
import os

class GameConfig:
    """
    配置游戏参数，例如屏幕尺寸、方块大小、颜色和形状。
    """
    SCREEN_WIDTH = 300
    SCREEN_HEIGHT = 600
    BLOCK_SIZE = 30
    FALL_SPEED = 1.5
    FAST_FALL_SPEED = 21.0
    COLORS = []
    SHAPES = [
        [[1, 1, 1, 1]],
        [[1, 1, 1], [0, 1, 0]],
        [[1, 1], [1, 1]],
        [[0, 1, 1], [1, 1, 0]],
        [[1, 1, 0], [0, 1, 1]],
        [[1, 0, 0], [1, 1, 1]],
        [[0, 0, 1], [1, 1, 1]]
    ]
    PREVIEW_X = 220
    PREVIEW_Y = 50
    PREVIEW_SIZE = 4

    def __init__(self):
        num_colors = 12
        self.COLORS = self._generate_colors(num_colors)

    def _generate_colors(self, num_colors: int) -> list[tuple[int, int, int]]:
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

    def _calculate_rotations(self) -> list[list[list[int]]]:
        """
        计算形状的所有可能旋转。

        Returns:
            list[list[list[int]]]: 旋转列表，每个旋转都是一个形状（二维列表）。
        """
        rotations = [self.shape]
        for _ in range(3):
            rotations.append(list(zip(*rotations[-1][::-1])))
        return rotations

    def rotate(self):
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

    def check_collision(self, piece: Tetromino, piece_x: int, piece_y: int) -> bool:
        """
        检查方块是否与面板或其他方块发生碰撞。

        Args:
            piece (Tetromino): 要检查的方块。
            piece_x (int): 方块的 X 坐标。
            piece_y (int): 方块的 Y 坐标。

        Returns:
            bool: 如果发生碰撞，则返回 True，否则返回 False。
        """
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece_x + x
                    new_y = piece_y + y
                    if (new_x < 0 or new_x >= len(self.grid[0]) or new_y >= len(self.grid) or
                            (new_y >= 0 and self.grid[new_y][new_x])):
                        return True
        return False

    def merge_piece(self, piece: Tetromino):
        """
        将方块合并到面板中。

        Args:
            piece (Tetromino): 要合并的方块。
        """
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[piece.y + y][piece.x + x] = piece.color

    def clear_lines(self) -> list[int]:  # 返回被清除的行的索引列表
        """
        清除面板上的任何完整行，并返回已清除的行数。

        Returns:
            list[int]: 包含被清除行索引的列表。
        """
        lines_to_clear = [i for i, row in enumerate(self.grid) if all(row)]
        return lines_to_clear

    def remove_lines(self, lines_to_clear: list[int]):
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

    def load_high_score(self):
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

    def update_high_score(self):
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
    def __init__(self, x: int, y: int, color: tuple[int, int, int]):
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

    def update(self):
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

    def draw(self, screen: pygame.Surface):
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
        self.font = pygame.font.Font("MI_LanTing_Regular.ttf", int(config.SCREEN_WIDTH * 0.08))
        self.block_surface = pygame.Surface((self.config.BLOCK_SIZE, self.config.BLOCK_SIZE), pygame.SRCALPHA)  # 创建一个 block_surface

    def draw_block(self, x: int, y: int, color: tuple[int, int, int], alpha: int = 255):
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

    def draw_board(self, board: Board):
        """
        在屏幕上绘制整个游戏面板。

        Args:
            board (Board): 要绘制的游戏面板对象。
        """
        for y, row in enumerate(board.grid):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(x, y, cell)

    def draw_piece(self, piece: Tetromino):
        """
        在屏幕上绘制当前的俄罗斯方块。

        Args:
            piece (Tetromino): 要绘制的俄罗斯方块对象。
        """
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(piece.x + x, piece.y + y, piece.color)

    def draw_grid(self):
        """
        在屏幕上绘制网格线。
        """
        for x in range(0, self.config.SCREEN_WIDTH, self.config.BLOCK_SIZE):
            pygame.draw.line(self.screen, (50, 50, 50), (x, 0), (x, self.config.SCREEN_HEIGHT))
        for y in range(0, self.config.SCREEN_HEIGHT, self.config.BLOCK_SIZE):
            pygame.draw.line(self.screen, (50, 50, 50), (0, y), (self.config.SCREEN_WIDTH, y))

    def draw_score(self, score_manager: ScoreManager):
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

    def draw_next_piece(self, piece: Tetromino, config: GameConfig):
        """
        在预览区域绘制下一个俄罗斯方块。

        Args:
            piece (Tetromino): 要绘制的下一个俄罗斯方块对象。
            config (GameConfig): 游戏配置对象。
        """
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    block_x = config.PREVIEW_X // config.BLOCK_SIZE + x
                    block_y = config.PREVIEW_Y // config.BLOCK_SIZE + y
                    self.draw_block(block_x, block_y, piece.color)

    def draw_explosion(self, x: int, y: int, color: tuple[int, int, int], explosion_particles: list[Particle]):
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

    def draw_clearing_animation(self, board: Board, lines_to_clear: list[int], animation_progress: float, explosion_particles: list[Particle]):
        """
        绘制指定行的清除动画（爆炸效果）。

        Args:
            board (Board): 游戏面板对象。
            lines_to_clear (list[int]): 要清除的行索引列表。
            animation_progress (float): 动画进度 (0.0 到 1.0)。
            explosion_particles (list[Particle]): 存储爆炸粒子的列表。
        """
        for i in lines_to_clear:
            for x in range(len(board.grid[0])):
                if board.grid[i][x]:
                    self.draw_explosion(x, i, board.grid[i][x], explosion_particles)

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
        self.board = Board(self.config)
        self.renderer = GameRenderer(self.config)
        self.score_manager = ScoreManager()
        self.current_piece = self._create_new_piece()
        self.next_piece = self._create_new_piece()
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

        pygame.mixer.music.load('tetris_music.mp3')
        pygame.mixer.music.play(-1)

        # 加载爆炸音效
        self.explosion_sound = pygame.mixer.Sound("explosion.wav")

    def _create_new_piece(self) -> Tetromino:
        """
        创建一个新的俄罗斯方块，并将其放置在面板顶部。

        Returns:
            Tetromino: 新创建的俄罗斯方块对象。
        """
        piece = Tetromino(self.config)
        return piece

    def handle_input(self) -> bool:
        """
        处理用户输入事件。

        Returns:
            bool: 如果游戏应该继续运行，则返回 True，否则返回 False (退出游戏)。
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.left_key_pressed = True
                elif event.key == pygame.K_RIGHT:
                    self.right_key_pressed = True
                elif event.key == pygame.K_UP:
                    original_rotation_index = self.current_piece.rotation_index
                    self.current_piece.rotate()
                    if self.board.check_collision(self.current_piece, self.current_piece.x, self.current_piece.y):
                        self.current_piece.rotation_index = original_rotation_index
                        self.current_piece.shape = self.current_piece.rotations[original_rotation_index]
                elif event.key == pygame.K_DOWN:
                    self.down_key_pressed = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.left_key_pressed = False
                elif event.key == pygame.K_RIGHT:
                    self.right_key_pressed = False
                elif event.key == pygame.K_DOWN:
                    self.down_key_pressed = False
        return True

    def new_piece(self) -> bool:
        """
        创建一个新的俄罗斯方块，并检查游戏是否结束。

        Returns:
            bool: 如果可以创建新的方块（游戏未结束），则返回 True，否则返回 False。
        """
        self.current_piece = self.next_piece
        self.current_piece.x = len(self.board.grid[0]) // 2 - len(self.current_piece.shape[0]) // 2
        self.current_piece.y = 0
        self.next_piece = self._create_new_piece()
        return not self.board.check_collision(self.current_piece, self.current_piece.x, self.current_piece.y)

    def game_loop(self):
        """
        主游戏循环。
        """
        running = True
        clock = pygame.time.Clock()
        animation_duration = 300  # 动画持续时间（毫秒）
        self.last_frame_time = pygame.time.get_ticks()
        self.last_fall_time = pygame.time.get_ticks()  # 初始化 last_fall_time

        while running:
            current_time = pygame.time.get_ticks()
            running = self.handle_input()

            if self.is_clearing:
                # 清除动画进行中
                self.clearing_animation_progress = min(1.0, self.clearing_animation_progress + (current_time - self.last_frame_time) / animation_duration)
                self.renderer.draw_clearing_animation(self.board, self.cleared_lines, self.clearing_animation_progress, self.explosion_particles)
                if self.clearing_animation_progress >= 1.0:
                    # 动画完成，移除行并创建新方块
                    self.board.remove_lines(self.cleared_lines)
                    self.is_clearing = False
                    self.explosion_particles = []  # 清空爆炸粒子
                    if not self.new_piece():
                        running = False  # Game over
            else:
                # 左右移动逻辑
                if current_time - self.last_move_time > self.move_delay:
                    if self.left_key_pressed:
                        if not self.board.check_collision(self.current_piece, self.current_piece.x - 1, self.current_piece.y):
                            self.current_piece.x -= 1
                            self.last_move_time = current_time
                    if self.right_key_pressed:
                        if not self.board.check_collision(self.current_piece, self.current_piece.x + 1, self.current_piece.y):
                            self.current_piece.x += 1
                            self.last_move_time = current_time

                # 下落逻辑
                current_speed = self.config.FAST_FALL_SPEED if self.down_key_pressed else self.config.FALL_SPEED
                if current_time - self.last_fall_time > 1000 / current_speed:
                    if not self.board.check_collision(self.current_piece, self.current_piece.x, self.current_piece.y + 1):
                        self.current_piece.y += 1
                        self.last_fall_time = current_time  # 更新 last_fall_time
                    else:
                        self.board.merge_piece(self.current_piece)
                        self.cleared_lines = self.board.clear_lines()  # 获取需要清除的行
                        if self.cleared_lines:
                            self.is_clearing = True  # 启动清除动画
                            self.clearing_animation_progress = 0.0  # 重置动画进度

                            # 播放爆炸音效
                            self.explosion_sound.play()
                        else:
                            if not self.new_piece():
                                running = False  # Game over
                        # self.last_fall_time = current_time  # 移除此行，因为它已经在上面更新了
                        self.score_manager.score += len(self.cleared_lines) * 100
                        self.score_manager.update_high_score()

            # 更新和绘制爆炸粒子
            for particle in self.explosion_particles[:]:
                particle.update()
                if particle.lifetime <= 0 or particle.size <= 1:  # 添加大小判断
                    self.explosion_particles.remove(particle)

            # 渲染
            self.renderer.screen.fill((30, 30, 30))
            self.renderer.draw_grid()
            self.renderer.draw_board(self.board)

            if not self.is_clearing:
                # 绘制当前方块
                self.renderer.draw_piece(self.current_piece)

            # 绘制爆炸粒子
            for particle in self.explosion_particles:
                particle.draw(self.renderer.screen)

            self.renderer.draw_next_piece(self.next_piece, self.config)
            self.renderer.draw_score(self.score_manager)
            pygame.display.flip()

            self.last_frame_time = current_time  # 记录当前帧的时间

            # 调试信息
            print(f"current_time: {current_time}, last_fall_time: {self.last_fall_time}, current_speed: {current_speed}")
            print(f"clearing_animation_progress: {self.clearing_animation_progress}, is_clearing: {self.is_clearing}")
            print(f"FPS: {clock.get_fps()}")

            # 限制帧率为 30 FPS
            clock.tick(30)

        pygame.mixer.music.stop()
        pygame.quit()


if __name__ == "__main__":
    game = TetrisGame()
    game.game_loop()
