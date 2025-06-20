import asyncio
import random
import math
import utime
from app_components import clear_background

from .focusable import Focusable


class SinglePlayerReactionGame(Focusable):
    random_delay_ms: int = 0
    react_set: bool = False
    start_ts: int = 0
    reacted_in: str | None = None
    cleared_background: bool = False

    def __init__(self):
        pass

    def handle_button(self, button: str) -> None:
        if button in ["CONFIRM", "RIGHT", "DOWN"]:
            if self.reacted_in is None:
                self.on_reaction()
            elif self.reacted_in:
                # reset game
                print("Reaction not set yet! Resetting game.")
                self.restart()

    async def start(self):
        self.reacted_in = None
        assert not self.react_set, "Reaction already set!"
        self.random_delay_ms = random.randint(700, 1000)
        print(f"Reaction set! Wait {self.random_delay_ms} ms to react.")
        await asyncio.sleep(self.random_delay_ms / 1000)
        # mark the moment the player should react
        self.start_ts = utime.ticks_ms()
        self.react_set = True
        print("Go!")

    def restart(self):
        print("Restarting game...")
        self.cleared_background = False
        self.reacted_in = None
        self.react_set = False
        self.start_ts = 0
        self.random_delay_ms = 0
        asyncio.create_task(self.start())

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
        if not self.cleared_background:
            clear_background(ctx)
            self.cleared_background = True

        if self.react_set:
            ctx.rgb(1, 0, 0).arc(0, 0, 60, 0, 2 * math.pi, True).fill()
        else:
            if self.reacted_in is not None:
                ctx.rgb(0, 0.6, 0).arc(0, 0, 60, 0, 2 * math.pi, True).fill()
                ctx.rgb(1, 1, 1).move_to(0, 0).text(f"{self.reacted_in}ms")
            else:
                ctx.rgb(0.5, 0, 0.5).arc(0, 0, 40, 0, 2 * math.pi, True).fill()
