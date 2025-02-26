import pygame
import os
import ttools
from game_config import GameConfig

class ScoreManager:
    """分数管理类，负责管理游戏中的分数、最高分、等级和最高等级。"""

    def __init__(self, config: GameConfig):
        """初始化 ScoreManager。"""
        self.config = config
        self.score = 0  # 当前分数
        self.high_score = 0  # 最高分
        self.score_changed = True  # 分数是否改变的标志
        self.high_score_changed = True  # 最高分是否改变的标志
        self.level = 1  # 当前等级
        self.level_changed = True  # 等级是否改变的标志
        self.highest_level = 1  # 最高等级
        self.highest_level_changed = True  # 最高等级是否改变的标志
        self.level_up_score = 1000  # 升级所需的分数
        self.fall_speed_increase = 0.1  # 每次升级增加的下落速度百分比
        self.load_high_score()  # 加载最高分和最高等级

        # 新增属性：消除行得分显示
        self.score_popup_text = None  # 显示的文本
        self.score_popup_position = (self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2)  # 文本位置
        self.score_popup_start_time = 0  # 文本开始显示的时间
        self.score_popup_duration = 2000  # 文本显示持续时间（毫秒）
        self.score_popup_alpha = 255  # 文本透明度
        self.font = pygame.font.Font(ttools.get_resource_path(os.path.join("assets", "fonts", "MI_LanTing_Regular.ttf")), int(config.SCREEN_WIDTH * 0.08))

    def load_high_score(self) -> None:
        """从文件中加载最高分和最高等级。"""
        try:
            with open("high_score.txt", "r") as f:
                lines = f.readlines()
                self.high_score = int(lines[0].strip())  # 读取最高分
                self.highest_level = int(lines[1].strip())  # 读取最高等级
        except (FileNotFoundError, ValueError, IndexError):
            # 如果文件不存在或格式错误，使用默认值
            self.high_score = 0
            self.highest_level = 1

    def save_high_score(self) -> None:
        """将最高分和最高等级保存到文件中。"""
        try:
            with open("high_score.txt", "w") as f:
                f.write(f"{self.high_score}\n")  # 保存最高分
                f.write(f"{self.highest_level}")  # 保存最高等级
        except IOError as e:
            print(f"保存最高分和最高等级时出错: {e}")

    def update_high_score(self) -> None:
        """更新最高分和最高等级。"""
        if self.score > self.high_score:
            self.high_score = self.score
            self.high_score_changed = True
        if self.level > self.highest_level:
            self.highest_level = self.level
            self.highest_level_changed = True
        self.save_high_score()  # 保存最高分和最高等级

    def add_score(self, lines_cleared: int) -> None:
        """根据消除的行数增加分数。"""
        score_increase = 100 * lines_cleared ** 2
        self.score += score_increase
        self.score_changed = True
        return score_increase

    def level_up(self) -> None:
        """提升等级。"""
        self.level += 1
        self.level_changed = True  # 设置等级改变标志

    def should_level_up(self) -> bool:
        """检查是否应该升级。"""
        return self.score >= self.level_up_score * self.level

    def increase_fall_speed(self) -> float:
        """根据等级计算当前的下落速度倍数。"""
        return 1 + (self.level - 1) * self.fall_speed_increase

    def show_score_popup(self, score: int) -> None:
        """显示消除行得分。"""
        self.score_popup_text = self.font.render(f"+{score}", True, (255, 255, 255))
        self.score_popup_start_time = pygame.time.get_ticks()
        self.score_popup_alpha = 255  # 重置透明度
