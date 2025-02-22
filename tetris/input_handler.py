import pygame
from game_state import GameState

class InputHandler:
    def __init__(self, game):
        self.game = game

    def handle_input(self) -> bool:
        if self.game.game_state == GameState.GAME_OVER:
            pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.TEXTINPUT])
        else:
            pygame.event.set_allowed(None)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.game.game_state == GameState.PLAYING:
                self._handle_playing_event(event)
            elif self.game.game_state == GameState.GAME_OVER:
                self._handle_game_over_event(event)

        return True

    def _handle_playing_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.game.left_key_pressed = True
            elif event.key == pygame.K_RIGHT:
                self.game.right_key_pressed = True
            elif event.key == pygame.K_DOWN:
                self.game.down_key_pressed = True
            elif event.key == pygame.K_UP:
                self._handle_rotate()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.game.left_key_pressed = False
            elif event.key == pygame.K_RIGHT:
                self.game.right_key_pressed = False
            elif event.key == pygame.K_DOWN:
                self.game.down_key_pressed = False

    def _handle_rotate(self) -> None:
        self.game.current_tetromino.rotate()
        if self.game.game_board.check_collision(
            self.game.current_tetromino,
            self.game.current_tetromino.x,
            self.game.current_tetromino.y
        ):
            for _ in range(3):
                self.game.current_tetromino.rotate()

    def _handle_game_over_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            self._handle_game_over_key(event.key)
        elif event.type == pygame.TEXTINPUT:
            self._handle_game_over_text(event.text)

    def _handle_game_over_key(self, key) -> None:
        key_name = pygame.key.name(key).lower()
        if key_name in ['r', 'ｒ']:
            self.game.__init__()
            self.game.game_state = GameState.PLAYING
            self.game.new_piece()
        elif key_name in ['q', 'ｑ']:
            self.game.running = False

    def _handle_game_over_text(self, text) -> None:
        text = text.lower()
        if text in ['r', 'ｒ']:
            self.game.__init__()
            self.game.game_state = GameState.PLAYING
            self.game.new_piece()
        elif text in ['q', 'ｑ']:
            self.game.running = False