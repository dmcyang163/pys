import random
from typing import Tuple, List, Optional
from collections import deque
import pygame  # 添加 pygame 导入

class Particle:
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(6, 12)
        self.speed_x = random.uniform(-3, 3)
        self.speed_y = random.uniform(-7, -2)
        self.lifetime = random.randint(30, 60)
        self.original_color = color
        self.fade_speed = random.uniform(0.02, 0.05)

    def update(self) -> None:
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += 0.1  # 重力
        self.lifetime -= 1
        self.size = max(1, self.size - 0.2)
        r, g, b = self.color
        fade_amount = int(255 * self.fade_speed)
        r = max(0, r - fade_amount)
        g = max(0, g - fade_amount)
        b = max(0, b - fade_amount)
        self.color = (r, g, b)

    def draw(self, screen: pygame.Surface) -> None:
        """
        在屏幕上绘制粒子。
        """
        pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), int(self.size), int(self.size)))

class ParticlePool:
    def __init__(self, max_particles: int):
        self.max_particles = max_particles
        self.pool = [Particle(0, 0, (0, 0, 0)) for _ in range(max_particles)]
        self.available = list(self.pool)

    def get_particle(self, x: int, y: int, color: Tuple[int, int, int]) -> Optional[Particle]:
        if self.available:
            particle = self.available.pop()
            particle.x = x
            particle.y = y
            particle.color = color
            particle.size = random.randint(6, 12)
            particle.speed_x = random.uniform(-3, 3)
            particle.speed_y = random.uniform(-7, -2)
            particle.lifetime = random.randint(30, 60)
            particle.original_color = color
            particle.fade_speed = random.uniform(0.02, 0.05)
            return particle
        return None

    def return_particle(self, particle: Particle) -> None:
        self.available.append(particle)

class ParticleSystem:
    def __init__(self, particle_pool: ParticlePool, config):
        self.particles = deque()
        self.particle_pool = particle_pool
        self.config = config

    def add_particles(self, x: int, y: int, color: Tuple[int, int, int], count: int = 30) -> None:
        for _ in range(count):
            particle = self.particle_pool.get_particle(x, y, color)
            if particle:
                self.particles.append(particle)

    def create_line_clearing_particles(self, line, game_board):
        """为消除的行创建粒子效果"""
        for x in range(len(game_board[0])):
            if game_board[line][x]:
                self.add_particles(
                    x * self.config.BLOCK_SIZE + self.config.BLOCK_SIZE // 2,
                    line * self.config.BLOCK_SIZE + self.config.BLOCK_SIZE // 2,
                    game_board[line][x],
                    count=10
                )

    def update(self) -> None:
        for particle in list(self.particles):
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)
                self.particle_pool.return_particle(particle)

    def draw(self, screen: pygame.Surface) -> None:
        for particle in self.particles:
            particle.draw(screen)
