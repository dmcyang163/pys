class ScoreManager:
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.score_changed = True
        self.high_score_changed = True
        self.level = 1  # 初始化等级
        self.level_changed = True  # 初始化等级改变标志
        self.highest_level = 1 # 初始化最高等级
        self.highest_level_changed = True # 初始化最高等级改变标志
        self.load_high_score()

    def load_high_score(self) -> None:
        try:
            with open("high_score.txt", "r") as f:
                lines = f.readlines()
                self.high_score = int(lines[0].strip())
                self.highest_level = int(lines[1].strip()) # 读取最高等级
        except (FileNotFoundError, ValueError, IndexError):
            self.high_score = 0
            self.highest_level = 1

    def update_high_score(self) -> None:
        if self.score > self.high_score:
            self.high_score = self.score
            self.high_score_changed = True
        if self.level > self.highest_level:
            self.highest_level = self.level
            self.highest_level_changed = True
        with open("high_score.txt", "w") as f:
            f.write(str(self.high_score) + '\n')
            f.write(str(self.highest_level)) # 保存最高等级

    def add_score(self, lines_cleared: int) -> None:
        self.score += 100 * lines_cleared ** 2
        self.score_changed = True

    def level_up(self) -> None:
        self.level += 1
        self.level_changed = True  # 设置等级改变标志
