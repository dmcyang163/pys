import pygame
import random
import math

# 初始化Pygame
pygame.init()

# 设置屏幕尺寸
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("鼠标触发烟花效果")

# 定义颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 165, 0)]

# 烟花粒子类
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(2, 5)
        self.radius = random.randint(2, 4)
        self.color = random.choice(COLORS)
        self.life = 100  # 粒子的生命值

    def update(self):
        # 更新粒子的位置
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        self.life -= 1  # 减少生命值

    def draw(self, screen):
        # 绘制粒子
        if self.life > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

# 主循环
running = True
clock = pygame.time.Clock()
particles = []

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:  # 监听鼠标点击事件
            # 在鼠标点击位置生成烟花粒子
            x, y = pygame.mouse.get_pos()
            for _ in range(100):  # 生成100个粒子
                particles.append(Particle(x, y))

    # 更新屏幕
    screen.fill(BLACK)

    # 更新和绘制粒子
    for particle in particles[:]:  # 使用切片来复制列表，以便在迭代时修改原列表
        particle.update()
        particle.draw(screen)
        if particle.life <= 0:
            particles.remove(particle)  # 移除生命值为0的粒子

    pygame.display.flip()
    clock.tick(60)  # 控制帧率

pygame.quit()
