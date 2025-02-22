import pygame
import random

class Paddle(pygame.sprite.Sprite):
    """挡板类."""

    WIDTH = 100
    HEIGHT = 20
    SPEED = 10
    COLOR = (255, 255, 255)  # WHITE

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([self.WIDTH, self.HEIGHT])
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.speed = self.SPEED

    def update(self):
        """更新挡板位置."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.x > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.x < Game.SCREEN_WIDTH - self.width:
            self.rect.x += self.speed

    def draw(self, surface):
        """绘制挡板."""
        surface.blit(self.image, self.rect)


class Ball(pygame.sprite.Sprite):
    """球类."""

    RADIUS = 10
    SPEED_X = 5
    SPEED_Y = -5
    COLOR = (255, 0, 0)  # RED

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([self.RADIUS * 2, self.RADIUS * 2], pygame.SRCALPHA)  # Make it transparent
        pygame.draw.circle(self.image, self.COLOR, (self.RADIUS, self.RADIUS), self.RADIUS)
        self.rect = self.image.get_rect()
        self.rect.x = x - self.RADIUS
        self.rect.y = y - self.RADIUS
        self.radius = self.RADIUS
        self.speed_x = self.SPEED_X
        self.speed_y = self.SPEED_Y

    def update(self):
        """更新球的位置并处理与墙的碰撞."""
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.left <= 0 or self.rect.right >= Game.SCREEN_WIDTH:
            self.speed_x = -self.speed_x
        if self.rect.top <= 0:
            self.speed_y = -self.speed_y

    def draw(self, surface):
        """绘制球."""
        surface.blit(self.image, self.rect)


class Brick(pygame.sprite.Sprite):
    """砖块类."""

    WIDTH = 75
    HEIGHT = 30
    COLOR = (0, 255, 0)  # GREEN

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([self.WIDTH, self.HEIGHT])
        self.image.fill(self.COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.WIDTH
        self.height = self.HEIGHT

    def draw(self, surface):
        """绘制砖块."""
        surface.blit(self.image, self.rect)


class Game:
    """游戏类."""

    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    FONT_SIZE = 36
    FPS = 60  # 帧率
    BRICK_ROWS = 5

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("打砖块")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, self.FONT_SIZE)

        self.paddle = Paddle((self.SCREEN_WIDTH - Paddle.WIDTH) // 2,
                             self.SCREEN_HEIGHT - Paddle.HEIGHT - 10)
        self.ball = Ball(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2)
        self.bricks = pygame.sprite.Group()
        self.create_bricks()

        self.score = 0
        self.game_state = "running"  # "running", "game_over", "win"

    def create_bricks(self):
        """创建砖块."""
        brick_cols = self.SCREEN_WIDTH // Brick.WIDTH
        for row in range(self.BRICK_ROWS):
            for col in range(brick_cols):
                brick = Brick(col * Brick.WIDTH, row * Brick.HEIGHT)
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
            self.clock.tick(self.FPS)

        pygame.quit()

    def update(self):
        """更新游戏元素."""
        self.paddle.update()
        self.ball.update()
        self.check_collisions()

    def draw(self):
        """绘制游戏元素."""
        self.screen.fill(self.BLACK)
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        for brick in self.bricks:
            brick.draw(self.screen)

        score_text = self.font.render(f"Score: {self.score}", True, self.WHITE)
        self.screen.blit(score_text, (10, 10))

    def check_game_state(self):
        """检查游戏状态（游戏结束或胜利）. """
        if self.ball.rect.bottom >= self.SCREEN_HEIGHT:
            self.game_state = "game_over"

        if not self.bricks:
            self.game_state = "win"

    def draw_game_over(self):
        """绘制游戏结束画面."""
        self.screen.fill(self.BLACK)
        game_over_text = self.font.render("Game Over!", True, self.RED)
        restart_text = self.font.render("Press R to Restart, Q to Quit", True, self.WHITE)
        score_text = self.font.render(f"Final Score: {self.score}", True, self.WHITE)

        game_over_rect = game_over_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 50))
        restart_rect = restart_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 50))
        score_rect = score_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))

        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(score_text, score_rect)

    def draw_win(self):
        """绘制胜利画面."""
        self.screen.fill(self.BLACK)
        win_text = self.font.render("You Win!", True, self.GREEN)
        restart_text = self.font.render("Press R to Restart, Q to Quit", True, self.WHITE)
        score_text = self.font.render(f"Final Score: {self.score}", True, self.WHITE)

        win_rect = win_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 50))
        restart_rect = restart_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 50))
        score_rect = score_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))

        self.screen.blit(win_text, win_rect)
        self.screen.blit(restart_text, restart_rect)
        self.screen.blit(score_text, score_rect)

    def reset(self):
        """重置游戏状态."""
        self.paddle = Paddle((self.SCREEN_WIDTH - Paddle.WIDTH) // 2,
                             self.SCREEN_HEIGHT - Paddle.HEIGHT - 10)
        self.ball = Ball(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2)
        self.bricks = pygame.sprite.Group()
        self.create_bricks()
        self.score = 0
        self.game_state = "running"


if __name__ == "__main__":
    game = Game()
    game.run()
