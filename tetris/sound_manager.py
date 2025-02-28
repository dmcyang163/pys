import pygame
import os
import util.ttools as ttools
from enum import Enum

class SoundType(Enum):
    EXPLOSION = "explosion"
    ROTATE_SUCCESS = "rotate_success"
    ROTATE_FAIL = "rotate_fail"
    FAST_FALL = "fast_fall"
    FAST_FALL_LOOP = "fast_fall_loop"  # 添加这个
    MOVE_HORIZONTAL = "move_horizontal" # 添加这个
    LEVEL_UP = "level_up" # 添加这个

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
        try:
            self.pool = [pygame.mixer.Sound(sound_path) for _ in range(size)]
        except pygame.error as e:
            print(f"创建声音池失败：{sound_path}, 错误信息：{e}")
            self.pool = []
        self.index = 0

    def get_sound(self):
        """获取一个声音副本。"""
        if not self.pool:
            print("声音池为空！")  # 调试信息
            return None
        sound = self.pool[self.index]
        self.index = (self.index + 1) % len(self.pool)
        return sound

class SoundManager:
    """管理游戏中的所有声音和声音池。"""

    def __init__(self, config):
        """初始化 SoundManager。"""
        self.config = config
        self.sound_pools = {}  # 使用字典存储声音池

        # 初始化声音通道
        pygame.mixer.init(frequency=44100, size=-16, channels=8, buffer=512)  # 重新初始化 Pygame 音频系统
        self.music_channel = pygame.mixer.Channel(0)  # 背景音乐通道
        self.effect_channel = pygame.mixer.Channel(1)  # 音效通道
        self.fast_fall_channel = pygame.mixer.Channel(2) # 加速下落音效通道
        self.level_up_channel = pygame.mixer.Channel(3)  # 升级音效通道

        # 初始化声音和声音池
        self._init_sounds_and_pools()

        # 设置音量
        self.set_volume(0.5)  # 设置所有通道的音量为 0.5

    def set_volume(self, volume):
        """设置所有通道的音量。"""
        self.music_channel.set_volume(volume)
        self.effect_channel.set_volume(volume)
        self.fast_fall_channel.set_volume(volume)
        self.level_up_channel.set_volume(volume)

    def _init_sounds_and_pools(self):
        """初始化游戏音效和声音池。"""
        # 加载爆炸音效
        self._load_sound_and_create_pool(SoundType.EXPLOSION, "explosion.wav", 5)

        # 加载背景音乐
        music_path = ttools.get_resource_path(os.path.join("assets/sounds", "no~.mp3")) #tetris_music
        if os.path.exists(music_path):
            try:
                self.tetris_sound = pygame.mixer.Sound(music_path)
            except pygame.error as e:
                print(f"加载背景音乐失败：{music_path}, 错误信息：{e}")
                self.tetris_sound = None
        else:
            print("背景音乐文件未找到。")
            self.tetris_sound = None

        # 加载旋转音效
        self._load_sound_and_create_pool(SoundType.ROTATE_SUCCESS, "bobo.wav", 10)
        self._load_sound_and_create_pool(SoundType.ROTATE_FAIL, "kick_wall.wav", 2)

        # 加载加速下落音效
        self._load_sound_and_create_pool(SoundType.FAST_FALL, "kick_wall.wav", 2)
        self._load_sound_and_create_pool(SoundType.FAST_FALL_LOOP, "bobo.wav", 18)  # 添加这个

        # 加载左右移动音效
        self._load_sound_and_create_pool(SoundType.MOVE_HORIZONTAL, "bobo.wav", 10) # 添加这个

        # 加载升级音效
        self._load_sound_and_create_pool(SoundType.LEVEL_UP, "level_up.wav", 2) # 添加这个

        # 设置背景音乐循环播放
        if self.tetris_sound:
            self.music_channel.play(self.tetris_sound, loops=-1)

    def _load_sound_and_create_pool(self, sound_type: SoundType, sound_file, pool_size):
        """加载音效文件并创建声音池。"""
        sound_path = ttools.get_resource_path(os.path.join("assets/sounds", sound_file))
        print(f"尝试加载音效文件：{sound_path}")  # 调试信息
        if os.path.exists(sound_path):
            try:
                self.sound_pools[sound_type] = SoundPool(sound_path, pool_size)
                print(f"成功加载音效文件：{sound_path}")  # 调试信息
            except pygame.error as e:
                print(f"加载音效文件失败：{sound_path}, 错误信息：{e}")  # 调试信息
        else:
            print(f"{sound_file} 音效文件未找到。")

    def play_sound(self, sound_type: SoundType):
        """播放指定类型的音效。"""
        print(f"尝试播放音效：{sound_type}")  # 调试信息
        if sound_type in self.sound_pools:
            sound_pool = self.sound_pools[sound_type]
            sound = sound_pool.get_sound()
            if sound:
                if sound_type == SoundType.FAST_FALL_LOOP:
                    self.fast_fall_channel.play(sound, loops=-1)  # 循环播放，使用单独的通道
                elif sound_type == SoundType.LEVEL_UP:
                    self.level_up_channel.play(sound)  # 使用单独的通道播放升级音效
                else:
                    self.effect_channel.play(sound)  # 使用统一的音效通道
                print(f"成功播放音效：{sound_type}")  # 调试信息
            else:
                print(f"无法获取音效：{sound_type}")  # 调试信息
        else:
            print(f"音效类型未找到：{sound_type}")  # 调试信息

    def stop_sound(self, sound_type: SoundType):
        """停止播放指定类型的音效"""
        if sound_type == SoundType.FAST_FALL_LOOP:
            self.fast_fall_channel.stop()  # 停止播放加速下落音效
        # else:  # 其他音效不需要手动停止，因为它们是短音效
        #     if sound_type in self.sound_pools:
        #         sound_pool = self.sound_pools[sound_type]
        #         for sound in sound_pool.pool:
        #             sound.stop()
