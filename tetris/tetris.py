import colorsys
import pygame
import random
import os

class GameConfig:
    SCREEN_WIDTH = 300
    SCREEN_HEIGHT = 600
    BLOCK_SIZE = 30
    FALL_SPEED = 1.5
    FAST_FALL_SPEED = 5.0
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
    
    def __init__(self):
        num_colors = 12
        for i in range(num_colors):
            hue = i / num_colors
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(hue, 0.8, 0.8)]
            self.COLORS.append((r, g, b))

class Tetromino:
    def __init__(self, config):
        self.shape = random.choice(config.SHAPES)
        self.color = random.choice(config.COLORS)
        self.x = 0
        self.y = 0

    def rotate(self):
        self.shape = list(zip(*self.shape[::-1]))

class Board:
    def __init__(self, config):
        self.config = config
        self.grid = [[0 for _ in range(config.SCREEN_WIDTH // config.BLOCK_SIZE)] 
                    for _ in range(config.SCREEN_HEIGHT // config.BLOCK_SIZE)]
    
    def check_collision(self, piece, px, py):
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = px + x
                    new_y = py + y
                    if (new_x < 0 
                        or new_x >= len(self.grid[0]) 
                        or new_y >= len(self.grid) 
                        or (new_y >= 0 and self.grid[new_y][new_x])):
                        return True
        return False
    
    def merge_piece(self, piece):
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[piece.y + y][piece.x + x] = piece.color
    
    def clear_lines(self):
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
        if os.path.exists("high_score.txt"):
            with open("high_score.txt", "r") as f:
                try:
                    self.high_score = int(f.read())
                except ValueError:
                    pass
    
    def update_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open("high_score.txt", "w") as f:
                f.write(str(self.high_score))

class GameRenderer:
    def __init__(self, config):
        self.config = config
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - 分数显示版")
        self.font = pygame.font.Font("MI_LanTing_Regular.ttf", int(config.SCREEN_WIDTH * 0.08))
    
    def draw_block(self, x, y, color):
        pygame.draw.rect(self.screen, color, (x * self.config.BLOCK_SIZE, 
                         y * self.config.BLOCK_SIZE, 
                         self.config.BLOCK_SIZE, 
                         self.config.BLOCK_SIZE))
        pygame.draw.rect(self.screen, (50, 50, 50), (x * self.config.BLOCK_SIZE, 
                         y * self.config.BLOCK_SIZE, 
                         self.config.BLOCK_SIZE, 
                         self.config.BLOCK_SIZE), 1)
    
    def draw_board(self, board):
        for y, row in enumerate(board.grid):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(x, y, cell)
    
    def draw_piece(self, piece):
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.draw_block(piece.x + x, piece.y + y, piece.color)
    
    def draw_grid(self):
        for x in range(0, self.config.SCREEN_WIDTH, self.config.BLOCK_SIZE):
            pygame.draw.line(self.screen, (50, 50, 50), (x, 0), (x, self.config.SCREEN_HEIGHT))
        for y in range(0, self.config.SCREEN_HEIGHT, self.config.BLOCK_SIZE):
            pygame.draw.line(self.screen, (50, 50, 50), (0, y), (self.config.SCREEN_WIDTH, y))
    
    def draw_score(self, score_manager):
        formatted_score = f"{score_manager.score:,}"
        formatted_high_score = f"{score_manager.high_score:,}"
        score_text = self.font.render(f"分数: {formatted_score}", True, (255, 255, 255))
        high_score_text = self.font.render(f"最高分: {formatted_high_score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(high_score_text, (10, 10 + int(self.config.SCREEN_WIDTH * 0.08)))

class TetrisGame:
    def __init__(self):
        pygame.init()
        self.config = GameConfig()
        self.board = Board(self.config)
        self.renderer = GameRenderer(self.config)
        self.score_manager = ScoreManager()
        self.current_piece = Tetromino(self.config)
        self.current_piece.x = len(self.board.grid[0]) // 2 - len(self.current_piece.shape[0]) // 2
        self.last_fall_time = pygame.time.get_ticks()
        self.down_key_pressed = False
        pygame.mixer.music.load('tetris_music.mp3')
        pygame.mixer.music.play(-1)
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if not self.board.check_collision(self.current_piece, self.current_piece.x - 1, self.current_piece.y):
                        self.current_piece.x -= 1
                elif event.key == pygame.K_RIGHT:
                    if not self.board.check_collision(self.current_piece, self.current_piece.x + 1, self.current_piece.y):
                        self.current_piece.x += 1
                elif event.key == pygame.K_UP:
                    original_shape = self.current_piece.shape
                    self.current_piece.rotate()
                    if self.board.check_collision(self.current_piece, self.current_piece.x, self.current_piece.y):
                        self.current_piece.shape = original_shape
                elif event.key == pygame.K_DOWN:
                    self.down_key_pressed = True
            elif event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
                self.down_key_pressed = False
        return True
    
    def new_piece(self):
        self.current_piece = Tetromino(self.config)
        self.current_piece.x = len(self.board.grid[0]) // 2 - len(self.current_piece.shape[0]) // 2
        self.current_piece.y = 0
        return not self.board.check_collision(self.current_piece, self.current_piece.x, self.current_piece.y)
    
    def game_loop(self):
        running = True
        clock = pygame.time.Clock()
        
        while running:
            current_time = pygame.time.get_ticks()
            running = self.handle_input()
            
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
                        running = False
                self.last_fall_time = current_time
            
            # 渲染
            self.renderer.screen.fill((30, 30, 30))
            self.renderer.draw_grid()
            self.renderer.draw_board(self.board)
            self.renderer.draw_piece(self.current_piece)
            self.renderer.draw_score(self.score_manager)
            pygame.display.flip()
            clock.tick(30)
        
        pygame.mixer.music.stop()
        pygame.quit()

if __name__ == "__main__":
    game = TetrisGame()
    game.game_loop()