import sys
import pygame
import os
import random
from typing import List

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
    """俄罗斯方块游戏主类。"""

    def __init__(self):
        """初始化 TetrisGame。"""
        pygame.init()
        pygame.display.init()

        # 解决DirectX驱动问题
        if pygame.display.get_driver() == "directx":
            pygame.display.quit()
            os.environ['SDL_VIDEODRIVER'] = 'windib'
            pygame.display.init()

        self.config = GameConfig()
        self.game_board = Board(self.config)
        self.score_manager = ScoreManager(self.config)
        self.renderer = GameRenderer(self.config)

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
        self.particle_system = ParticleSystem(self.particle_pool, self.config)  # 传递 config
        self.joystick = None
        self._init_joystick()
        self.input_handler = InputHandler(self)

        # 初始化音效
        self._init_sounds()

    def _init_joystick(self):
        """初始化手柄。"""
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)  # 使用第一个手柄
            self.joystick.init()
            print(f"手柄已连接: {self.joystick.get_name()}")
        else:
            print("未检测到手柄。")

    def _init_sounds(self):
        """初始化游戏音效。"""
        sound_path = ttools.get_resource_path(os.path.join("assets/sounds", "explosion.wav"))
        if os.path.exists(sound_path):
            self.explosion_sound = pygame.mixer.Sound(sound_path)
        else:
            print("爆炸音效文件未找到。")

        music_path = ttools.get_resource_path(os.path.join("assets/sounds", "tetris_music.mp3"))
        if os.path.exists(music_path):
            self.tetris_sound = pygame.mixer.Sound(music_path)
            self.tetris_sound.play(loops=-1)  # 循环播放背景音乐
        else:
            print("背景音乐文件未找到。")

        # 加载旋转音效
        self.rotate_success_sound = None
        rotate_success_path = ttools.get_resource_path(os.path.join("assets/sounds", "rotating-switch.wav"))
        if os.path.exists(rotate_success_path):
            self.rotate_success_sound = pygame.mixer.Sound(rotate_success_path)
        else:
            print("旋转成功音效文件未找到。")

        self.rotate_fail_sound = None
        rotate_fail_path = ttools.get_resource_path(os.path.join("assets/sounds", "kick_wall.wav"))
        if os.path.exists(rotate_fail_path):
            self.rotate_fail_sound = pygame.mixer.Sound(rotate_fail_path)
        else:
            print("旋转失败音效文件未找到。")

    def _create_new_piece(self) -> Tetromino:
        """创建一个新的俄罗斯方块。"""
        return Tetromino(self.config)

    def new_piece(self) -> bool:
        """生成新的俄罗斯方块，并检查是否游戏结束。"""
        self.current_tetromino = self.next_tetromino
        self.next_tetromino = self._create_new_piece()
        self.current_tetromino.x = self.config.SCREEN_WIDTH // self.config.BLOCK_SIZE // 2 - len(
            self.current_tetromino.shape[0]) // 2
        self.current_tetromino.y = 0
        if self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x,
                                            self.current_tetromino.y):
            self.score_manager.update_high_score()
            self.game_state = GameState.GAME_OVER
            return False
        return True

    def _handle_clearing_animation(self, current_time: int, animation_duration: int) -> None:
        """处理消除行的动画。"""
        self.clearing_animation_progress = min(1.0, self.clearing_animation_progress + (
                current_time - self.last_frame_time) / animation_duration)
        if self.clearing_animation_progress >= 1.0:
            self.game_board.remove_lines(self.cleared_lines)
            self.is_clearing = False
            if not self.new_piece():
                self.game_state = GameState.GAME_OVER
                self.running = False  # 游戏结束

    def _handle_piece_movement(self, current_time: int) -> None:
        """处理方块的左右移动和下落。"""
        self._move_piece_horizontally(current_time)
        self._move_piece_down(current_time)

    def _move_piece_horizontally(self, current_time: int) -> None:
        """处理方块的左右移动。"""
        time_since_last_move = current_time - self.last_move_time
        if time_since_last_move > self.move_delay:
            if self.left_key_pressed:
                if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x - 1,
                                                    self.current_tetromino.y):
                    self.current_tetromino.x -= 1
                    self.last_move_time = current_time
            if self.right_key_pressed:
                if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x + 1,
                                                     self.current_tetromino.y):
                    self.current_tetromino.x += 1
                    self.last_move_time = current_time

    def _move_piece_down(self, current_time: int) -> None:
        """处理方块的下落。"""
        base_speed = self.config.FAST_FALL_SPEED if self.down_key_pressed else self.config.FALL_SPEED
        current_speed = base_speed * self.score_manager.increase_fall_speed()

        if current_time - self.last_fall_time > 1000 / current_speed:
            if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x,
                                                self.current_tetromino.y + 1):
                self.current_tetromino.y += 1
                self.last_fall_time = current_time
            else:
                self._handle_piece_landed()

    def _handle_piece_landed(self) -> None:
        """处理方块落地后的逻辑。"""
        if not self.game_board.check_collision(self.current_tetromino, self.current_tetromino.x,
                                            self.current_tetromino.y):
            self.game_board.merge_piece(self.current_tetromino)
            self.cleared_lines = self.game_board.clear_lines()

        if self.cleared_lines:
            self.is_clearing = True
            self.clearing_animation_progress = 0.0
            score_increase = self.score_manager.add_score(len(self.cleared_lines))

            # 显示消除行得分
            self.score_manager.show_score_popup(score_increase)  # 调用 show_score_popup

            # 等级提升判断
            if self.score_manager.should_level_up():
                self.score_manager.level_up()
                print(f"升级！当前等级：{self.score_manager.level}")

            if hasattr(self, 'explosion_sound'):
                self.explosion_sound.play()

            # 生成消除行的粒子效果
            for line in self.cleared_lines:
                self.particle_system.create_line_clearing_particles(line, self.game_board.grid)

        else:
            if not self.new_piece():
                self.game_state = GameState.GAME_OVER
        self.last_fall_time = pygame.time.get_ticks()

    def toggle_pause(self) -> None:
        """切换游戏暂停状态。"""
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            print("游戏已暂停")
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING
            print("游戏已恢复")

    def _render_game_state(self):
        """根据当前游戏状态渲染相应的界面。"""
        if self.game_state == GameState.PLAYING:
            self.renderer.render_game(self.game_board, self.current_tetromino, self.next_tetromino,
                                      self.score_manager, self.particle_system)
        elif self.game_state == GameState.PAUSED:
            self.renderer.render_pause_screen(self.game_board, self.current_tetromino, self.next_tetromino,
                                               self.score_manager, self.particle_system)
        elif self.game_state == GameState.GAME_OVER:
            self.renderer.render_game_over(self.game_board, self.current_tetromino, self.next_tetromino,
                                            self.score_manager, self.particle_system)

    def _handle_game_over(self):
        """处理游戏结束状态。"""
        print("Game Over state detected, rendering game over screen...")
        self.renderer.render_game_over(self.game_board, self.current_tetromino, self.next_tetromino, self.score_manager, self.particle_system)

        # 处理游戏结束时的输入事件
        self.input_handler.handle_input()

    def game_loop(self) -> None:
        """游戏主循环。"""
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
                self._render_game_state()

            elif self.game_state == GameState.PAUSED:
                self._render_game_state()

            elif self.game_state == GameState.GAME_OVER:
                self._handle_game_over()

            pygame.display.flip()
            self.last_frame_time = current_time
            clock.tick(30)

    def handle_rotate(self) -> bool:
        """
        处理方块的旋转，并播放相应的音效。
        返回旋转是否成功
        """
        original_x = self.current_tetromino.x
        original_y = self.current_tetromino.y
        self.current_tetromino.rotate()

        # 检查旋转后的碰撞
        if self.game_board.check_collision(
            self.current_tetromino,
            self.current_tetromino.x,
            self.current_tetromino.y
        ):
            # 如果发生碰撞，尝试平移方块来解决碰撞
            if not self._try_wall_kick():
                # 如果平移也无法解决碰撞，则撤销旋转
                self.current_tetromino.x = original_x
                self.current_tetromino.y = original_y
                for _ in range(3):
                    self.current_tetromino.rotate()
                # 播放旋转失败音效
                self._play_rotate_sound(False)
                return False

        # 播放旋转成功音效
        self._play_rotate_sound(True)
        return True

    def _try_wall_kick(self) -> bool:
        """
        尝试通过平移方块来解决旋转后的碰撞（墙踢）。
        """
        # 定义墙踢的偏移量（可以根据需要调整）
        wall_kick_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for offset_x, offset_y in wall_kick_offsets:
            new_x = self.current_tetromino.x + offset_x
            new_y = self.current_tetromino.y + offset_y

            if not self.game_board.check_collision(self.current_tetromino, new_x, new_y):
                # 如果平移后没有碰撞，则应用平移
                self.current_tetromino.x = new_x
                self.current_tetromino.y = new_y
                return True  # 成功解决碰撞

        return False  # 无法通过平移解决碰撞

    def _play_rotate_sound(self, success: bool) -> None:
        """
        播放旋转音效。

        Args:
            success:  如果旋转成功，则为 True；如果旋转失败，则为 False。
        """
        if success:
            if self.rotate_success_sound:
                self.rotate_success_sound.play()
        else:
            if self.rotate_fail_sound:
                self.rotate_fail_sound.play()


if __name__ == "__main__":
    game = TetrisGame()
    game.game_loop()
