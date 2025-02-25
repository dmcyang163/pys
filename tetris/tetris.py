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
        self.particle_pool = ParticlePool(max_particles=1000)
        self.particle_system = ParticleSystem(self.particle_pool)
        self.joystick = None
        self._init_joystick()
        self.input_handler = InputHandler(self)

        # 初始化音效
        self.explosion_sound = pygame.mixer.Sound(ttools.get_resource_path(os.path.join("sounds", "explosion.wav")))  # 加载爆炸音效
        self.tetris_sound = pygame.mixer.Sound(ttools.get_resource_path(os.path.join("sounds", "tetris_music.mp3")))  # 加载爆炸音效
        self.tetris_sound.play(loops=-1)  # 循环播放背景音乐
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
            self.cleared_lines = self.game_board.clear_lines()

        if self.cleared_lines:
            self.is_clearing = True
            self.clearing_animation_progress = 0.0
            self.score_manager.add_score(len(self.cleared_lines))
            # 播放爆炸音效
            if hasattr(self, 'explosion_sound'):  # 确保 explosion_sound 存在
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

    def toggle_pause(self) -> None:
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            print("游戏已暂停")
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING
            print("游戏已恢复")

    def game_loop(self) -> None:
        clock = pygame.time.Clock()
        self.running = True
        self.new_piece()

        while self.running:
            current_time = pygame.time.get_ticks()
            self.running = self.input_handler.handle_input()

            if self.game_state == GameState.PLAYING:
                if self.is_clearing:
                    self._handle_clearing_animation(current_time, self.config.ANIMATION_DURATION)
                else:
                    self._handle_piece_movement(current_time)

                self.particle_system.update()
                self.renderer.render_game(self.game_board, self.current_tetromino, self.next_tetromino, self.score_manager, self.particle_system)

            elif self.game_state == GameState.PAUSED:
                # 渲染暂停界面
                self.renderer.render_pause_screen(self.game_board, self.current_tetromino, self.next_tetromino, self.score_manager, self.particle_system)

            elif self.game_state == GameState.GAME_OVER:
                # 渲染游戏结束界面
                print("Game Over state detected, rendering game over screen...")
                self.renderer.render_game_over(self.game_board, self.current_tetromino, self.next_tetromino, self.score_manager, self.particle_system)
                
                pygame.event.clear()
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        waiting_for_restart = False
                    if event.type == pygame.KEYDOWN:
                        key = pygame.key.name(event.key).lower()
                        if key in ['r', 'ｒ']:
                            self.__init__()
                            
                            self.game_state = GameState.PLAYING
                            self.new_piece()
                        elif key in ['q', 'ｑ']:
                            self.running = False
                                

            # 统一调用 pygame.display.flip()
            pygame.display.flip()
            self.last_frame_time = current_time
            clock.tick(30)

if __name__ == "__main__":
    game = TetrisGame()
    game.game_loop()
