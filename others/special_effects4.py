import pygame
import random
import numpy as np
from scipy.ndimage import gaussian_filter

# 初始化 Pygame
pygame.init()

# 屏幕尺寸
width, height = 400, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("逼真玻璃积木俄罗斯方块")

# 颜色
black = (0, 0, 0)
white = (255, 255, 255)
colors = [
    (255, 50, 50),    # 红色
    (50, 255, 50),    # 绿色
    (50, 50, 255),    # 蓝色
    (255, 255, 50),  # 黄色
    (255, 50, 255),  # 紫色
    (50, 255, 255),  # 青色
]

# 方块大小
block_size = 40

# 游戏区域尺寸 (列数和行数)
grid_width = width // block_size
grid_height = height // block_size

# 俄罗斯方块形状 (示例)
shapes = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 1, 0]],  # T
]

# 模糊半径 (用于反射效果)
blur_radius = 3

def draw_block(surface, x, y, color):
    """绘制具有逼真玻璃效果的方块."""
    # 基本颜色
    base_color = color

    # 高光颜色 (更亮)
    highlight_color = tuple(min(c + 80, 255) for c in base_color)

    # 阴影颜色 (更暗)
    shadow_color = tuple(max(c - 80, 0) for c in base_color)

    # 透明度 (RGBA)
    alpha = 150  # 调整这个值来改变透明度 (0-255)

    # 创建一个 Surface 来绘制方块
    block_surface = pygame.Surface((block_size, block_size), pygame.SRCALPHA)

    # 绘制主体 (带透明度)
    pygame.draw.rect(block_surface, base_color + (alpha,), (0, 0, block_size, block_size))

    # 绘制高光 (使用渐变)
    for i in range(block_size // 2):
        c = tuple(int(base_color[j] + (highlight_color[j] - base_color[j]) * (i / (block_size // 2))) for j in range(3))
        pygame.draw.line(block_surface, c + (alpha,), (i, 0), (0, i), 2)

    # 绘制阴影 (使用渐变)
    for i in range(block_size // 2):
        c = tuple(int(base_color[j] + (shadow_color[j] - base_color[j]) * (i / (block_size // 2))) for j in range(3))
        pygame.draw.line(block_surface, c + (alpha,), (block_size - i, block_size), (block_size, block_size - i), 2)

    # 绘制边缘高光
    pygame.draw.line(block_surface, highlight_color + (200,), (1, 0), (block_size - 1, 0), 1)
    pygame.draw.line(block_surface, highlight_color + (200,), (0, 1), (0, block_size - 1), 1)

    # 模拟反射 (模糊背景) - 简化版本
    # 获取方块区域的屏幕截图
    block_rect = pygame.Rect(x * block_size, y * block_size, block_size, block_size)
    subsurface = screen.subsurface(block_rect).copy()

    # 模糊处理
    pixel_array = pygame.surfarray.array3d(subsurface)
    blurred_array = gaussian_filter(pixel_array, sigma=blur_radius)
    blurred_surface = pygame.surfarray.make_surface(blurred_array.astype(np.uint8))
    blurred_surface = blurred_surface.convert_alpha()

    # 绘制模糊后的背景
    block_surface.blit(blurred_surface, (0, 0))

    # 叠加方块颜色
    pygame.draw.rect(block_surface, base_color + (alpha,), (0, 0, block_size, block_size), 0)


    # 将方块绘制到屏幕上
    surface.blit(block_surface, (x * block_size, y * block_size))


def new_block():
    """创建一个新的俄罗斯方块."""
    shape = random.choice(shapes)
    color = random.choice(colors)
    x = grid_width // 2 - len(shape[0]) // 2
    y = 0
    return shape, color, x, y


# 游戏状态
current_shape, current_color, current_x, current_y = new_block()
grid = [[0] * grid_width for _ in range(grid_height)]  # 游戏区域

# 绘制背景 (简单的渐变)
background = pygame.Surface((width, height))
for y in range(height):
    c = int(y / height * 50)
    pygame.draw.line(background, (c, c, c), (0, y), (width, y))
screen.blit(background, (0, 0))


# 游戏循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 绘制背景
    screen.blit(background, (0, 0))

    # 绘制游戏区域
    for y in range(grid_height):
        for x in range(grid_width):
            if grid[y][x] != 0:
                draw_block(screen, x, y, grid[y][x])

    # 绘制当前方块
    for row in range(len(current_shape)):
        for col in range(len(current_shape[row])):
            if current_shape[row][col] == 1:
                draw_block(screen, current_x + col, current_y + row, current_color)

    # 更新屏幕
    pygame.display.flip()
    pygame.time.delay(1000)

    # 简单地让方块下落 (实际游戏需要更复杂的逻辑)
    current_y += 1
    if current_y + len(current_shape) > grid_height:
        # 方块到底部了，固定到游戏区域
        for row in range(len(current_shape)):
            for col in range(len(current_shape[row])):
                if current_shape[row][col] == 1:
                    grid[current_y + row - 1][current_x + col] = current_color
        current_shape, current_color, current_x, current_y = new_block()


# 退出 Pygame
pygame.quit()
