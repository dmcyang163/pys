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

class SoundPool:
    """声音池，用于管理多个声音副本。"""

    def __init__(self, sound_path, size):
        """
        初始化 SoundPool。

        Args:
            sound_path: 要复制的声音文件的路径。
            size: 声音池的大小（副本数量）。
        """
        self.sound_path = sound_path
        self.pool = [pygame.mixer.Sound(sound_path) for _ in range(size)]
        self.index = 0

    def play(self):
        """播放一个声音副本。"""
        if not self.pool:
            print("声音池为空！")  # 调试信息
            return
        sound = self.pool[self.index]
        sound.play()
        self.index = (self.index + 1) % len(self.pool)


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

        pygame.mixer.init(frequency=44100, size=-16, channels=8, buffer=512)  # 增加通道数量

        max_channels = pygame.mixer.get_num_channels()
        print(f"pygame.mixer 支持的最大通道数为：{max_channels}")

        # 初始化声音和声音池
        self._init_sounds_and_pools()

        # 初始化声音通道
        self._init_channels()

    def _init_joystick(self):
        """初始化手柄。"""
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)  # 使用第一个手柄
            self.joystick.init()
            print(f"手柄已连接: {self.joystick.get_name()}")
        else:
            print("未检测到手柄。")

    def _init_sounds_and_pools(self):
        """初始化游戏音效和声音池。"""
        # 加载爆炸音效
        self.explosion_sound_pool = self._load_sound_and_create_pool(
            "explosion.wav", 5)

        # 加载背景音乐
        music_path = ttools.get_resource_path(os.path.join("assets/sounds", "tetris_music.mp3"))
        if os.path.exists(music_path):
            self.tetris_sound = pygame.mixer.Sound(music_path)
        else:
            print("背景音乐文件未找到。")
            self.tetris_sound = None

        # 加载旋转音效
        self.rotate_success_sound_pool = self._load_sound_and_create_pool(
            "tick.wav", 10)
        self.rotate_fail_sound_pool = self._load_sound_and_create_pool(
            "kick_wall.wav", 5)

        # 加载加速下落音效
        self.fast_fall_sound_pool = self._load_sound_and_create_pool(
            "tick.wav", 10)

    def _load_sound_and_create_pool(self, sound_file, pool_size):
        """加载音效文件并创建声音池。"""
        sound_path = ttools.get_resource_path(os.path.join("assets/sounds", sound_file))
        if os.path.exists(sound_path):
            sound_pool = SoundPool(sound_path, pool_size)
            return sound_pool
        else:
            print(f"{sound_file} 音效文件未找到。")
            return None

    def _load_sound(self, sound_file):
        """加载音效文件。"""
        sound_path = ttools.get_resource_path(os.path.join("assets/sounds", sound_file))
        if os.path.exists(sound_path):
            return pygame.mixer.Sound(sound_path)
        else:
            print(f"{sound_file} 音效文件未找到。")
            return None

    def _init_channels(self):
        """初始化声音通道。"""
        self.music_channel = pygame.mixer.Channel(0)  # 背景音乐通道
        self.explosion_channel = pygame.mixer.Channel(1)  # 消除声音通道
        self.rotate_channel = pygame.mixer.Channel(2)  # 旋转声音通道
        self.fast_fall_channel = pygame.mixer.Channel(3)  # 加速下落声音通道

        # 设置背景音乐循环播放
        if self.tetris_sound:
            self.music_channel.play(self.tetris_sound, loops=-1)

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
                if self.down_key_pressed and self.fast_fall_sound_pool:  # 播放加速下落音效
                    self.fast_fall_channel.play(self.fast_fall_sound_pool.pool[self.fast_fall_sound_pool.index])  # 使用通道播放声音
                    self.fast_fall_sound_pool.play()
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

            # 播放爆炸声音
            if self.explosion_sound_pool:
                self.explosion_channel.play(self.explosion_sound_pool.pool[self.explosion_sound_pool.index])  # 使用通道播放声音
                self.explosion_sound_pool.play()

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
        elif self.game_state == GameState.PLAYING:
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
        self.renderer.render_game_over(self.game_board, self.current_tetromino, self.next_tetromino,
                                        self.score_manager, self.particle_system)

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
                if self.rotate_fail_sound_pool:
                    self.rotate_channel.play(self.rotate_fail_sound_pool.pool[self.rotate_fail_sound_pool.index])
                    self.rotate_fail_sound_pool.play()
                return False

        # 播放旋转成功音效
        if self.rotate_success_sound_pool:
            self.rotate_channel.play(self.rotate_success_sound_pool.pool[self.rotate_success_sound_pool.index])
            self.rotate_success_sound_pool.play()
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

if __name__ == "__main__":
    game = TetrisGame()
    game.game_loop()
