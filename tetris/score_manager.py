class ScoreManager:
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.score_changed = True
        self.high_score_changed = True
        self.load_high_score()

    def load_high_score(self) -> None:
        try:
            with open("high_score.txt", "r") as f:
                self.high_score = int(f.read())
        except (FileNotFoundError, ValueError):
            self.high_score = 0

    def update_high_score(self) -> None:
        if self.score > self.high_score:
            self.high_score = self.score
            self.high_score_changed = True
            with open("high_score.txt", "w") as f:
                f.write(str(self.high_score))

    def add_score(self, lines_cleared: int) -> None:
        self.score += 100 * lines_cleared ** 2
        self.score_changed = True