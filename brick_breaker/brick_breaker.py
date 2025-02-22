import pygame
import random

# 常量定义
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_SPEED = 10
BALL_RADIUS = 10
BALL_SPEED_X = 5
BALL_SPEED_Y = -5
BRICK_WIDTH = 75
BRICK_HEIGHT = 30
BRICK_ROWS = 5
BRICK_COLS = SCREEN_WIDTH // BRICK_WIDTH
FONT_SIZE = 36
FPS = 60  # 帧率


class Paddle(pygame.sprite.Sprite):
    """挡板类."""

    def __init__(self, x, y, width, height, speed):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = width
        self.height = height
        self.speed = speed

    def update(self):
        """更新挡板位置."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.x > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.x < SCREEN_WIDTH - self.width:
            self.rect.x += self.speed

    def draw(self, surface):
        """绘制挡板."""
        surface.blit(self.image, self.rect)


class Ball(pygame.sprite.Sprite):
    """球类."""

    def __init__(self, x, y, radius, speed_x, speed_y):
        super().__init__()
        self.image = pygame.Surface([radius * 2, radius * 2], pygame.SRCALPHA)  # Make it transparent
        pygame.draw.circle(self.image, RED, (radius, radius), radius)
        self.rect = self.image.get_rect()
        self.rect.x = x - radius
        self.rect.y = y - radius
        self.radius = radius
        self.speed_x = speed_x
        self.speed_y = speed_y

    def update(self):
        """更新球的位置并处理与墙的碰撞."""
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.speed_x = -self.speed_x
        if self.rect.top <= 0:
            self.speed_y = -self.speed_y

    def draw(self, surface):
        """绘制球."""
        surface.blit(self.image, self.rect)


class Brick(pygame.sprite.Sprite):
    """砖块类."""

    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = width
        self.height = height

    def draw(self, surface):
        """绘制砖块."""
        surface.blit(self.image, self.rect)


class Game:
    """游戏类."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("打砖块")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, FONT_SIZE)

        self.paddle = Paddle((SCREEN_WIDTH - PADDLE_WIDTH) // 2, SCREEN_HEIGHT - PADDLE_HEIGHT - 10,
                             PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED)
        self.ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_RADIUS, BALL_SPEED_X, BALL_SPEED_Y)
        self.bricks = pygame.sprite.Group()
        self.create_bricks()

        self.score = 0
        self.game_state = "running"  # "running", "game_over", "win"

    def create_bricks(self):
        """创建砖块."""
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                brick = Brick(col * BRICK_WIDTH, row * BRICK_HEIGHT, BRICK_WIDTH, BRICK_HEIGHT)
                self.bricks.add(brick)

    def check_collisions(self):
        """检测碰撞."""
        # 球与挡板的碰撞
        if self.ball.rect.bottom >= self.paddle.rect.top and \
           self.paddle.rect.left <= self.ball.rect.centerx <= self.paddle.rect.right:
            self.ball.speed_y = -abs(self.ball.speed_y)

        # 球与砖块的碰撞
        brick_collisions = pygame.sprite.spritecollide(self.ball, self.bricks, True)
        if brick_collisions:
            self.ball.speed_y = -self.ball.speed_y
            self.score += 10

    def run(self):
        """游戏主循环."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.game_state == "game_over" or self.game_state == "win":
                        if event.key == pygame.K_r:
                            self.reset()
                        elif event.key == pygame.K_q:
                            running = False

            if self.game_state == "running":
                self.update()
                self.draw()
                self.check_game_state()

            elif self.game_state == "game_over":
                self.draw_game_over()

            elif self.game_state == "win":
                self.draw_win()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

    def update(self):
        """更新游戏元素."""
        self.paddle.update()
        self.ball.update()
        self.check_collisions()

    def draw(self):
        """绘制游戏元素."""
        self.screen.fill(BLACK)
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        for brick in self.bricks:
            brick.draw(self.screen)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

    def check_game_state(self):
        """检查游戏状态（游戏结束或胜利）. """
        if self.ball.rect.bottom >= SCREEN_HEIGHT:
            self.game_state = "game_over"

        if not self.bricks:
            self.game_state = "win"

    def draw_game_over(self):
        """绘制游戏结束画面."""
        self.screen.fill(BLACK)
        game_over_text = self.font.render("Game Over!", True, RED)
        restart_text = self.font.render("Press R to Restart, Q to Quit", True, WHITE)
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)

        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(score_text, score_rect)

    def draw_win(self):
        """绘制胜利画面."""
        self.screen.fill(BLACK)
        win_text = self.font.render("You Win!", True, GREEN)
        restart_text = self.font.render("Press R to Restart, Q to Quit", True, WHITE)
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)

        win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        self.screen.blit(win_text, win_rect)
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(score_text, score_rect)

    def reset(self):
        """重置游戏状态."""
        self.paddle = Paddle((SCREEN_WIDTH - PADDLE_WIDTH) // 2, SCREEN_HEIGHT - PADDLE_HEIGHT - 10,
                             PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED)
        self.ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_RADIUS, BALL_SPEED_X, BALL_SPEED_Y)
        self.bricks = pygame.sprite.Group()
        self.create_bricks()
        self.score = 0
        self.game_state = "running"


if __name__ == "__main__":
    game = Game()
    game.run()
