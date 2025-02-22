import pygame
import random

# 初始化pygame
pygame.init()

# 设置屏幕大小
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("打砖块")

# 颜色定义
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# 设置时钟
clock = pygame.time.Clock()

# 挡板
paddle_width = 100
paddle_height = 20
paddle_x = (SCREEN_WIDTH - paddle_width) // 2
paddle_y = SCREEN_HEIGHT - paddle_height - 10
paddle_speed = 10

# 球
ball_radius = 10
ball_x = SCREEN_WIDTH // 2
ball_y = SCREEN_HEIGHT // 2
ball_speed_x = 5
ball_speed_y = -5

# 砖块
brick_width = 75
brick_height = 30
brick_rows = 5
brick_cols = SCREEN_WIDTH // brick_width
bricks = []

for row in range(brick_rows):
    for col in range(brick_cols):
        brick = pygame.Rect(col * brick_width, row * brick_height, brick_width, brick_height)
        bricks.append(brick)

# 游戏循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 控制挡板
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and paddle_x > 0:
        paddle_x -= paddle_speed
    if keys[pygame.K_RIGHT] and paddle_x < SCREEN_WIDTH - paddle_width:
        paddle_x += paddle_speed

    # 更新球的位置
    ball_x += ball_speed_x
    ball_y += ball_speed_y

    # 球与墙的碰撞检测
    if ball_x - ball_radius <= 0 or ball_x + ball_radius >= SCREEN_WIDTH:
        ball_speed_x = -ball_speed_x
    if ball_y - ball_radius <= 0:
        ball_speed_y = -ball_speed_y

    # 球与挡板的碰撞检测
    if ball_y + ball_radius >= paddle_y and paddle_x <= ball_x <= paddle_x + paddle_width:
        ball_speed_y = -ball_speed_y

    # 球与砖块的碰撞检测
    for brick in bricks[:]:
        if brick.collidepoint(ball_x, ball_y):
            bricks.remove(brick)
            ball_speed_y = -ball_speed_y
            break

    # 游戏结束条件
    if ball_y + ball_radius >= SCREEN_HEIGHT:
        running = False

    # 清屏
    screen.fill(BLACK)

    # 绘制挡板
    pygame.draw.rect(screen, WHITE, (paddle_x, paddle_y, paddle_width, paddle_height))

    # 绘制球
    pygame.draw.circle(screen, RED, (ball_x, ball_y), ball_radius)

    # 绘制砖块
    for brick in bricks:
        pygame.draw.rect(screen, GREEN, brick)

    # 更新屏幕
    pygame.display.flip()

    # 控制帧率
    clock.tick(60)

# 退出游戏
pygame.quit()