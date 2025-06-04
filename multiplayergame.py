import math
import utime

from .mainmenu import GameType
from .constants import (
    get_random_waiting_message,
    get_room_name,
)
from .focusable import Focusable


class MultiPlayerReactionGame(Focusable):
    room_name: str = ""
    gameType: str = ""
    waiting_message: str = get_random_waiting_message()
    total_delta: int = 0

    def __init__(self, gameType: str):
        self.gameType = gameType
        if gameType == GameType.HOSTING:
            self.room_name = get_room_name()
        print(f"Multiplayer game initialized as {gameType}")
        pass

    def handle_button(self, button: str) -> None:
        print(f"Button pressed: {button}")

    async def start(self):
        print("start called")

    def on_reaction(self):
        print("Reaction received!")
        if self.react_set:
            now_ms = utime.ticks_ms()
            elapsed_ms = utime.ticks_diff(now_ms, self.start_ts)
            print(f"Reaction time: {elapsed_ms:.0f} ms")
            self.reacted_in = f"{elapsed_ms:.0f}"
            # reset so next round can start
            self.react_set = False
            self.start_ts = 0
        else:
            print("Reaction not set yet!")

    def draw(self, ctx) -> None:
        if self.gameType == GameType.JOINING:
            ctx.rgb(0.2, 0.1, 0.25).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(0.4, 0.2, 0.5).arc(0, 0, 80, 0, 2 * math.pi, True).fill()
            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, -30).text(f"searching for rooms…")
            ctx.font_size = 40
            ctx.rgb(1, 1, 1).move_to(0, 0).text(self.waiting_message)
        elif self.gameType == GameType.HOSTING:
            ctx.rgb(0, 0.2, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.rgb(0, 0.4, 0).arc(0, 0, 80, 0, 2 * math.pi, True).fill()
            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, -30).text(f"your room name is")
            ctx.font_size = 40
            ctx.rgb(1, 1, 1).move_to(0, 0).text(self.room_name)
            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, 30).text("players can join now")

    def update(self, delta: int) -> bool:
        self.total_delta += delta
        if self.total_delta > 3000:
            self.waiting_message = get_random_waiting_message()
            self.total_delta = 0
        return True
