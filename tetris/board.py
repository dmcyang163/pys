from typing import List
from game_config import GameConfig
from tetromino import Tetromino

class Board:
    def __init__(self, config: GameConfig):
        self.config = config
        self.grid = [[0 for _ in range(config.SCREEN_WIDTH // config.BLOCK_SIZE)]
                     for _ in range(config.SCREEN_HEIGHT // config.BLOCK_SIZE)]

    def check_collision(self, tetromino: Tetromino, piece_x: int, piece_y: int) -> bool:
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
        for y, row in enumerate(tetromino.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[tetromino.y + y][tetromino.x + x] = tetromino.color

    def clear_lines(self) -> List[int]:
        lines_to_clear = [i for i, row in enumerate(self.grid) if all(row)]
        self.remove_lines(lines_to_clear)
        return lines_to_clear

    def remove_lines(self, lines_to_clear: List[int]) -> None:
        for i in sorted(lines_to_clear, reverse=True):
            del self.grid[i]
            self.grid.insert(0, [0 for _ in range(len(self.grid[0]))])