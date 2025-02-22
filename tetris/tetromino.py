import random
from typing import List
from game_config import GameConfig

class Tetromino:
    def __init__(self, config: GameConfig):
        self.shape = random.choice(config.SHAPES)
        self.color = random.choice(config.COLORS)
        self.x = 0
        self.y = 0
        self.rotations = self._calculate_rotations()
        self.rotation_index = 0

    def _calculate_rotations(self) -> List[List[List[int]]]:
        rotations = [self.shape]
        for _ in range(3):
            rotations.append(list(zip(*rotations[-1][::-1])))
        return rotations

    def rotate(self) -> None:
        self.rotation_index = (self.rotation_index + 1) % len(self.rotations)
        self.shape = self.rotations[self.rotation_index]