import pygame
from game_state import GameState


class InputHandler:
    def __init__(self, game):
        self.game = game

    def handle_input(self) -> bool:
        """处理输入事件，包括键盘和手柄。"""
        if self.game.game_state == GameState.GAME_OVER:
            pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.TEXTINPUT])
        else:
            pygame.event.set_allowed(None)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.game.game_state == GameState.PLAYING:
                self._handle_playing_event(event)
            elif self.game.game_state == GameState.PAUSED:
                self._handle_paused_event(event)  # 处理暂停状态下的输入
            elif self.game.game_state == GameState.GAME_OVER:
                self._handle_game_over_event(event)

        # 处理手柄输入
        if self.game.joystick:
            self._handle_joystick_input()

        return True

    def _handle_playing_event(self, event) -> None:
        """处理游戏进行中的键盘事件。"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.game.left_key_pressed = True
            elif event.key == pygame.K_RIGHT:
                self.game.right_key_pressed = True
            elif event.key == pygame.K_DOWN:
                self.game.down_key_pressed = True
            elif event.key == pygame.K_UP:
                # 旋转
                self._handle_rotate()
            elif event.key == pygame.K_p:  # 使用键值检测 P 键
                self.game.toggle_pause()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.game.left_key_pressed = False
            elif event.key == pygame.K_RIGHT:
                self.game.right_key_pressed = False
            elif event.key == pygame.K_DOWN:
                self.game.down_key_pressed = False

    def _handle_paused_event(self, event) -> None:
        """处理暂停状态下的输入事件。"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:  # 使用键值检测 P 键
                self.game.toggle_pause()
            elif event.key == pygame.K_q:  # 使用键值检测 Q 键
                self.game.running = False

    def _handle_joystick_input(self) -> None:
        """处理手柄输入。"""
        # 获取手柄的摇杆和按钮状态
        axis_x = self.game.joystick.get_axis(0)  # 左摇杆的水平轴
        axis_y = self.game.joystick.get_axis(1)  # 左摇杆的垂直轴
        button_a = self.game.joystick.get_button(0)  # A 按钮
        button_b = self.game.joystick.get_button(1)  # B 按钮
        button_start = self.game.joystick.get_button(7)  # START 按钮

        # 处理左右移动
        if axis_x < -0.5:  # 左摇杆向左
            self.game.left_key_pressed = True
            self.game.right_key_pressed = False
        elif axis_x > 0.5:  # 左摇杆向右
            self.game.right_key_pressed = True
            self.game.left_key_pressed = False
        else:
            self.game.left_key_pressed = False
            self.game.right_key_pressed = False

        # 处理快速下落
        if axis_y > 0.5:  # 左摇杆向下
            self.game.down_key_pressed = True
        else:
            self.game.down_key_pressed = False

        # 处理旋转
        if button_a:  # A 按钮旋转
            # 旋转
            self._handle_rotate()

        # 处理暂停
        if button_start:  # START 按钮暂停
            self.game.toggle_pause()

    def _handle_rotate(self) -> None:
        """处理方块的旋转。"""
        self.game.handle_rotate()

    def _handle_game_over_event(self, event) -> None:
        """处理游戏结束时的输入事件。"""
        if event.type == pygame.KEYDOWN:
            self._handle_game_over_key(event.key)
        elif event.type == pygame.TEXTINPUT:
            self._handle_game_over_text(event.text)

    def _handle_game_over_key(self, key) -> None:
        """处理游戏结束时的键盘输入。"""
        key_name = pygame.key.name(key).lower()
        if key_name in ['r', 'ｒ']:
            self.game.__init__()
            self.game.game_state = GameState.PLAYING
            self.game.new_piece()
        elif key_name in ['q', 'ｑ']:
            self.game.running = False

    def _handle_game_over_text(self, text) -> None:
        """处理游戏结束时的文本输入。"""
        text = text.lower()
        if text in ['r', 'ｒ']:
            self.game.__init__()
            self.game.game_state = GameState.PLAYING
            self.game.new_piece()
        elif text in ['q', 'ｑ']:
            self.game.running = False
