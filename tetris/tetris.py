import sys
import pygame
import os
from game_config import GameConfig
from tetromino import Tetromino
from board import Board
from score_manager import ScoreManager
from particle import ParticlePool, ParticleSystem
from renderer import GameRenderer
from input_handler import InputHandler
from game_state import GameState

import ttools


    
class TetrisGame:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        if pygame.display.get_driver() == "directx":
            pygame.display.quit()
            os.environ['SDL_VIDEODRIVER'] = 'windib'
            pygame.display.init()
        self.config = GameConfig()
        self.game_board = Board(self.config)
        self.renderer = GameRenderer(self.config)
        self.score_manager = ScoreManager()
        self.current_tetromino = self._create_new_piece()
        self.next_tetromino = self._create_new_piece()
        self.last_fall_time = pygame.time.get_ticks()
        self.down_key_pressed = False
        self.left_key_pressed = False
        self.right_key_pressed = False
        self.last_move_time = 0
        self.move_delay = 100
        self.cleared_lines = []
        self.clearing_animation_progress = 0.0
        self.is_clearing = False
        self.explosion_particles = []
        self.game_state = GameState.PLAYING

        self.game_over_surface = None  # game_over 的 Surface
        self.pause_surface = None  # 暂停界面的 Surface

        pygame.mixer.music.load(ttools.get_resource_path(os.path.join("sounds", "tetris_music.mp3")))
        pygame.mixer.music.play(-1)
        self.explosion_sound = pygame.mixer.Sound(ttools.get_resource_path(os.path.join("sounds", "explosion.wav")))
        self.particle_pool = ParticlePool(max_particles=1000)
        self.particle_system = ParticleSystem(self.particle_pool)

        # 初始化手柄
        self.joystick = None
        self._init_joystick()

        self.input_handler = InputHandler(self)
    def _init_joystick(self):
            """
            初始化手柄。
            """
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)  # 使用第一个手柄
                self.joystick.init()
                print(f"手柄已连接: {self.joystick.get_name()}")
                print(f"摇杆数量: {self.joystick.get_numaxes()}")  # 打印摇杆数量
                print(f"按钮数量: {self.joystick.get_numbuttons()}")  # 打印按钮数量
                for i in range(self.joystick.get_numbuttons()):
                    print(f"按钮 {i}: {self.joystick.get_button(i)}")

                for i in range(self.joystick.get_numaxes()):
                    print(f"摇杆 {i}: {self.joystick.get_axis(i)}")
            else:
                print("未检测到手柄。")

    def _create_new_piece(self) -> Tetromino:
        return Tetromino(self.config)

    def new_piece(self) -> bool:
        self.current_tetromino = self.next_tetromino
        self.next_tetromino = self._create_new_piece()
        self.current_tetromino.x = self.config.SCREEN_WIDTH // self.config.BLOCK_SIZE // 2 - len(self.current_tetromino.shape[0]) // 2
        self.current_tetromino.y = 0
        if self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x, self.current_tetromino.y):
            self.score_manager.update_high_score()
            self.game_state = GameState.GAME_OVER
            return False
        return True

    def _handle_clearing_animation(self, current_time: int, animation_duration: int) -> None:
        self.clearing_animation_progress = min(1.0, self.clearing_animation_progress + (current_time - self.last_frame_time) / animation_duration)
        if self.clearing_animation_progress >= 1.0:
            self.game_board.remove_lines(self.cleared_lines)
            self.is_clearing = False
            if not self.new_piece():
                self.running = False  # Game over

    def _handle_piece_movement(self, current_time: int) -> None:
        """
        处理方块的左右移动和下落。
        """
        self._move_piece_horizontally(current_time)
        self._move_piece_down(current_time)

    def _move_piece_horizontally(self, current_time: int) -> None:
        """
        处理方块的左右移动。
        """
        time_since_last_move = current_time - self.last_move_time
        if time_since_last_move > self.move_delay:
            if self.left_key_pressed:
                if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x - 1, self.current_tetromino.y):
                    self.current_tetromino.x -= 1
                    self.last_move_time = current_time
            if self.right_key_pressed:
                if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x + 1, self.current_tetromino.y):
                    self.current_tetromino.x += 1
                    self.last_move_time = current_time

    def _move_piece_down(self, current_time: int) -> None:
        """
        处理方块的下落。
        """
        current_speed = self.config.FAST_FALL_SPEED if self.down_key_pressed else self.config.FALL_SPEED
        if current_time - self.last_fall_time > 1000 / current_speed:
            if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x, self.current_tetromino.y + 1):
                self.current_tetromino.y += 1
                self.last_fall_time = current_time
            else:
                self._handle_piece_landed()

    def _handle_piece_landed(self) -> None:
        if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x, self.current_tetromino.y):
            self.game_board.merge_piece(self.current_tetromino)
            # 检测满行但不删除
            self.cleared_lines = self.game_board.clear_lines()


        if self.cleared_lines:
            self.is_clearing = True
            self.clearing_animation_progress = 0.0
            self.score_manager.add_score(len(self.cleared_lines))
            self.explosion_sound.play()

            # 触发粒子效果
            for line in self.cleared_lines:
                for x in range(len(self.game_board.grid[0])):
                    if self.game_board.grid[line][x]:
                        self.particle_system.add_particles(
                            x * self.config.BLOCK_SIZE + self.config.BLOCK_SIZE // 2,
                            line * self.config.BLOCK_SIZE + self.config.BLOCK_SIZE // 2,
                            self.game_board.grid[line][x],
                            count=10
                        )
        else:
            if not self.new_piece():
                self.game_state = GameState.GAME_OVER
        self.last_fall_time = pygame.time.get_ticks()
    
    
    def _render_game(self) -> None:
        self.renderer.screen.fill(self.renderer.background_color)
        self.renderer.draw_grid()
        self.renderer.draw_board(self.game_board)

        if not self.is_clearing:
            self.renderer.draw_piece(self.current_tetromino)

        self.particle_system.draw(self.renderer.screen)
        self.renderer.draw_next_piece(self.next_tetromino)
        self.renderer.draw_score(self.score_manager)
        pygame.display.update()

    def toggle_pause(self) -> None:
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            print("游戏已暂停")
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING
            print("游戏已恢复")

    def _create_pause_surface(self) -> None:
        """
        创建暂停界面的 Surface。
        """
        self.pause_surface = pygame.Surface((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA)
        self.pause_surface.fill((0, 0, 0, 128))  # 黑色半透明覆盖层 (RGBA: 0, 0, 0, 128)

        # 绘制“游戏暂停中”文字
        pause_text = self.renderer.font.render("游戏暂停中", True, (255, 255, 255))  # 白色文字
        text_rect = pause_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2))

        # 将文字绘制到 Surface 上
        self.pause_surface.blit(pause_text, text_rect)

    def _render_pause_screen(self) -> None:
        """
        渲染暂停界面：在当前画面上覆盖一个半透明的遮罩，并显示“游戏暂停中”。
        """
        if not self.is_paused_rendered:
            if self.pause_surface is None:
                self._create_pause_surface()  # 如果 Surface 未创建，则先创建

            # 先绘制当前游戏画面
            self._render_game()

            self.renderer.screen.blit(self.pause_surface, (0, 0))

            # 更新屏幕显示
            pygame.display.flip()

            # 设置标志位，表示已经绘制了暂停界面
            self.is_paused_rendered = True

    def _render_game_over(self) -> None:
        """
        渲染游戏结束界面。
        """
        if not hasattr(self, 'game_over_surface'):
            self.game_over_surface = pygame.Surface((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA)
            background_color = (0, 0, 0, 30)
            pygame.draw.rect(self.game_over_surface, background_color, (0, 0, self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT))

            game_over_text = self.renderer.font.render("游戏结束", True, (255, 255, 255))
            score_text = self.renderer.font.render(f"分数: {self.score_manager.score:,}", True, (255, 255, 255))
            high_score_text = self.renderer.font.render(f"最高分: {self.score_manager.high_score:,}", True, (255, 255, 255))
            restart_text = self.renderer.font.render("按 R 重新开始", True, (255, 255, 255))
            quit_text = self.renderer.font.render("按 Q 退出游戏", True, (255, 255, 255))

            self.game_over_surface.blit(game_over_text, (self.config.SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, self.config.SCREEN_HEIGHT // 3))
            self.game_over_surface.blit(score_text, (self.config.SCREEN_WIDTH // 2 - score_text.get_width() // 2, self.config.SCREEN_HEIGHT // 2))
            self.game_over_surface.blit(high_score_text, (self.config.SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, self.config.SCREEN_HEIGHT // 2 + 50))
            self.game_over_surface.blit(restart_text, (self.config.SCREEN_WIDTH // 2 - restart_text.get_width() // 2, self.config.SCREEN_HEIGHT // 2 + 100))
            self.game_over_surface.blit(quit_text, (self.config.SCREEN_WIDTH // 2 - quit_text.get_width() // 2, self.config.SCREEN_HEIGHT // 2 + 150))

        self.renderer.screen.blit(self.game_over_surface, (0, 0))
        pygame.display.flip()

    def game_loop(self) -> None:
        """
        主游戏循环。
        """
        try:
            clock = pygame.time.Clock()
            self.running = True
            self.new_piece()

            while self.running:
                current_time = pygame.time.get_ticks()
                self.running = self.input_handler.handle_input()

                if self.game_state == GameState.PLAYING:
                    # 重置暂停界面绘制标志
                    self.is_paused_rendered = False

                    if self.is_clearing:
                        self._handle_clearing_animation(current_time, self.config.ANIMATION_DURATION)
                    else:
                        self._handle_piece_movement(current_time)

                    self.particle_system.update()
                    self._render_game()

                elif self.game_state == GameState.PAUSED:
                    self._render_pause_screen()  # 渲染暂停界面

                elif self.game_state == GameState.GAME_OVER:
                    self._render_game_over()
                    pygame.event.clear()
                    waiting_for_restart = True
                    while waiting_for_restart:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                self.running = False
                                waiting_for_restart = False
                            if event.type == pygame.KEYDOWN:
                                key = pygame.key.name(event.key).lower()
                                if key in ['r', 'ｒ']:
                                    self.__init__()
                                    waiting_for_restart = False
                                    self.game_state = GameState.PLAYING
                                    self.new_piece()
                                elif key in ['q', 'ｑ']:
                                    self.running = False
                                    waiting_for_restart = False
                
                # 统一调用 pygame.display.flip()
                if self.game_state != GameState.PAUSED:
                    pygame.display.flip()

                self.last_frame_time = current_time
                clock.tick(30)

        finally:
            pygame.mixer.music.stop()
            pygame.quit()
            self.particle_pool = None
            self.particle_system = None

if __name__ == "__main__":
    game = TetrisGame()
    game.game_loop()