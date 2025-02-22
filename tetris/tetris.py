import colorsys
import pygame
import random
import os

class GameConfig:
    SCREEN_WIDTH = 300
    SCREEN_HEIGHT = 600
    BLOCK_SIZE = 30
    FALL_SPEED = 1.5
    FAST_FALL_SPEED = 15.0  # 加速下落的速度，数值越大，下落越快
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
    PREVIEW_X = 220  # 预览区域的 X 坐标
    PREVIEW_Y = 50   # 预览区域的 Y 坐标
    PREVIEW_SIZE = 4  # 预览区域的方块数量 (4x4)

    def __init__(self):
        num_colors = 12
        self.COLORS = self._generate_colors(num_colors)

    def _generate_colors(self, num_colors: int) -> list[tuple[int, int, int]]:
        """Generates a list of colors based on HSV values."""
        colors = []
        for i in range(num_colors):
            hue = i / num_colors
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 0.8, 0.8)]
            colors.append((r, g, b))
        return colors

class Tetromino:
    def __init__(self, config: GameConfig):
        self.shape = random.choice(config.SHAPES)
        self.color = random.choice(config.COLORS)
        self.x = 0
        self.y = 0
        self.rotations = self._calculate_rotations()  # 预先计算所有旋转
        self.rotation_index = 0  # 当前旋转的索引

    def _calculate_rotations(self) -> list[list[list[int]]]:
        """Calculates all possible rotations of the shape."""
        rotations = [self.shape]
        for _ in range(3):  # 计算 3 次旋转，总共 4 个方向
            rotations.append(list(zip(*rotations[-1][::-1])))
        return rotations

    def rotate(self):
        """Rotates the tetromino to the next pre-calculated rotation."""
        self.rotation_index = (self.rotation_index + 1) % len(self.rotations)
        self.shape = self.rotations[self.rotation_index]

class Board:
    def __init__(self, config: GameConfig):
        self.config = config
        self.grid = [[0 for _ in range(config.SCREEN_WIDTH // config.BLOCK_SIZE)]
                     for _ in range(config.SCREEN_HEIGHT // config.BLOCK_SIZE)]

    def check_collision(self, piece: Tetromino, piece_x: int, piece_y: int) -> bool:
        """Checks if the piece collides with the board or other pieces."""
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
        """Merges the piece into the board."""
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[piece.y + y][piece.x + x] = piece.color

    def clear_lines(self) -> int:
        """Clears any full lines on the board and returns the number of lines cleared."""
        lines_to_clear = [i for i, row in enumerate(self.grid) if all(row)]
        if lines_to_clear:
            for i in lines_to_clear:
                del self.grid[i]
                self.grid.insert(0, [0 for _ in range(len(self.grid[0]))])
            return len(lines_to_clear)
        return 0

class ScoreManager:
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.load_high_score()

    def load_high_score(self):
        """Loads the high score from a file."""
        try:
            with open("high_score.txt", "r") as f:
                self.high_score = int(f.read())
        except FileNotFoundError:
            self.high_score = 0  # Handle the case where the file doesn't exist
        except ValueError:
            self.high_score = 0  # Handle the case where the file contains invalid data

    def update_high_score(self):
        """Updates the high score if the current score is higher."""
        if self.score > self.high_score:
            self.high_score = self.score
            with open("high_score.txt", "w") as f:
                f.write(str(self.high_score))

class GameRenderer:
    def __init__(self, config: GameConfig):
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - 分数显示版")
        self.font = pygame.font.Font("MI_LanTing_Regular.ttf", int(config.SCREEN_WIDTH * 0.08))

    def draw_block(self, x: int, y: int, color: tuple[int, int, int]):
        """Draws a single block on the screen."""
        pygame.draw.rect(self.screen, color, (x * self.config.BLOCK_SIZE,
                         y * self.config.BLOCK_SIZE,
                         self.config.BLOCK_SIZE,
                         self.config.BLOCK_SIZE))
        pygame.draw.rect(self.screen, (50, 50, 50), (x * self.config.BLOCK_SIZE,
                         y * self.config.BLOCK_SIZE,
                         self.config.BLOCK_SIZE,
                         self.config.BLOCK_SIZE), 1)

    def draw_board(self, board: Board):
        """Draws the entire board on the screen."""
        for y, row in enumerate(board.grid):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(x, y, cell)

    def draw_piece(self, piece: Tetromino):
        """Draws the current piece on the screen."""
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(piece.x + x, piece.y + y, piece.color)

    def draw_grid(self):
        """Draws the grid lines on the screen."""
        for x in range(0, self.config.SCREEN_WIDTH, self.config.BLOCK_SIZE):
            pygame.draw.line(self.screen, (50, 50, 50), (x, 0), (x, self.config.SCREEN_HEIGHT))
        for y in range(0, self.config.SCREEN_HEIGHT, self.config.BLOCK_SIZE):
            pygame.draw.line(self.screen, (50, 50, 50), (0, y), (self.config.SCREEN_WIDTH, y))

    def draw_score(self, score_manager: ScoreManager):
        """Draws the score and high score on the screen."""
        formatted_score = f"{score_manager.score:,}"
        formatted_high_score = f"{score_manager.high_score:,}"
        score_text = self.font.render(f"分数: {formatted_score}", True, (255, 255, 255))
        high_score_text = self.font.render(f"最高分: {formatted_high_score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(high_score_text, (10, 10 + int(self.config.SCREEN_WIDTH * 0.08)))

    def draw_next_piece(self, piece: Tetromino, config: GameConfig):
        """Draws the next piece in the preview area."""
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    block_x = config.PREVIEW_X // config.BLOCK_SIZE + x
                    block_y = config.PREVIEW_Y // config.BLOCK_SIZE + y
                    self.draw_block(block_x, block_y, piece.color)

class TetrisGame:
    def __init__(self):
        pygame.init()
        self.config = GameConfig()
        self.board = Board(self.config)
        self.renderer = GameRenderer(self.config)
        self.score_manager = ScoreManager()
        self.current_piece = self._create_new_piece()
        self.next_piece = self._create_new_piece() # 创建下一个方块
        self.last_fall_time = pygame.time.get_ticks()
        self.down_key_pressed = False
        self.left_key_pressed = False
        self.right_key_pressed = False
        self.last_move_time = 0  # 上次移动的时间
        self.move_delay = 150  # 移动延迟（毫秒）
        pygame.mixer.music.load('tetris_music.mp3')
        pygame.mixer.music.play(-1)

    def _create_new_piece(self) -> Tetromino:
        """Creates a new tetromino and positions it at the top of the board."""
        piece = Tetromino(self.config)
        #piece.x = len(self.board.grid[0]) // 2 - len(piece.shape[0]) // 2 # 初始位置由new_piece控制
        #piece.y = 0
        return piece

    def handle_input(self) -> bool:
        """Handles user input events."""
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
        """Creates a new piece and checks for game over."""
        self.current_piece = self.next_piece  # 将下一个方块变为当前方块
        self.current_piece.x = len(self.board.grid[0]) // 2 - len(self.current_piece.shape[0]) // 2
        self.current_piece.y = 0
        self.next_piece = self._create_new_piece()  # 创建新的下一个方块
        return not self.board.check_collision(self.current_piece, self.current_piece.x, self.current_piece.y)

    def game_loop(self):
        """The main game loop."""
        running = True
        clock = pygame.time.Clock()

        while running:
            current_time = pygame.time.get_ticks()
            running = self.handle_input()

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
                else:
                    self.board.merge_piece(self.current_piece)
                    lines_cleared = self.board.clear_lines()
                    self.score_manager.score += lines_cleared * 100
                    self.score_manager.update_high_score()
                    if not self.new_piece():
                        running = False  # Game over
                self.last_fall_time = current_time

            # 渲染
            self.renderer.screen.fill((30, 30, 30))
            self.renderer.draw_grid()
            self.renderer.draw_board(self.board)
            self.renderer.draw_piece(self.current_piece)
            self.renderer.draw_next_piece(self.next_piece, self.config)  # 绘制下一个方块
            self.renderer.draw_score(self.score_manager)
            pygame.display.flip()
            clock.tick(30)

        pygame.mixer.music.stop()
        pygame.quit()

if __name__ == "__main__":
    game = TetrisGame()
    game.game_loop()
