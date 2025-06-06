from app import App
import asyncio
import time

from app_components import clear_background
from events.input import Buttons, BUTTON_TYPES
from system.eventbus import eventbus
from system.scheduler.events import RequestStopAppEvent

from .multiplayergame.multiplayergamesetup import MultiPlayerReactionGameSetup
from .mainmenu import GameType, MainMenu
from .focusable import Focusable
from .singleplayergame import SinglePlayerReactionGame


class Reactz(App):
    focus: Focusable | None = None
    menuTask: asyncio.Task | None = None
    cleared: bool = False
    request_fast_updates: bool = False  # for SASPPU firmware

    def __init__(self):
        self.button_states = Buttons(self)
        self.focus = MainMenu()

    async def run(self, render_update):
        last_time = time.ticks_ms()  # type: ignore

        # first draw
        await render_update()

        # start background task
        if self.focus:
            asyncio.create_task(self.focus.start())  # type: ignore

        while True:
            # yield to the event loop for 50 ms so button events get delivered
            # await asyncio.sleep_ms(50)
            await render_update()

            if self.button_states.get(BUTTON_TYPES["CANCEL"]):
                if self.focus and isinstance(self.focus, MainMenu):
                    # host a new reaction game
                    self.focus = MultiPlayerReactionGameSetup(gameType=GameType.HOSTING)
                    self.menuTask = asyncio.create_task(self.focus.start())
                elif self.focus:
                    self.focus.handle_button("CANCEL")

            if self.button_states.get(BUTTON_TYPES["LEFT"]):
                if self.focus and isinstance(self.focus, MainMenu):
                    # if we are in the main menu, exit the app
                    self.focus = None
                    self.quit()
                elif self.focus:
                    # if we are in a game, return to the main menu
                    self.focus.close()
                    if self.menuTask:
                        self.menuTask.cancel()
                    self.focus = MainMenu()
                    asyncio.create_task(self.focus.start())

            elif self.button_states.get(BUTTON_TYPES["RIGHT"]):
                if self.focus and isinstance(self.focus, MainMenu):
                    # join an existing reaction game
                    self.focus = MultiPlayerReactionGameSetup(gameType=GameType.JOINING)
                    self.menuTask = asyncio.create_task(self.focus.start())
                elif self.focus:
                    self.focus.handle_button("RIGHT")

            elif self.button_states.get(BUTTON_TYPES["CONFIRM"]):
                if self.focus:
                    self.focus.handle_button("CONFIRM")

            elif self.button_states.get(BUTTON_TYPES["UP"]):
                if self.focus:
                    self.focus.handle_button("UP")

            elif self.button_states.get(BUTTON_TYPES["DOWN"]):
                if self.focus and isinstance(self.focus, MainMenu):
                    # start a new reaction game
                    self.focus = SinglePlayerReactionGame()
                    asyncio.create_task(self.focus.start())
                elif self.focus:
                    self.focus.handle_button("DOWN")

            self.button_states.clear()

            # update & redraw
            cur_time = time.ticks_ms()  # type: ignore
            delta = time.ticks_diff(cur_time, last_time)  # type: ignore
            self.update(delta)
            await render_update()
            last_time = cur_time

    def quit(self):
        eventbus.emit(RequestStopAppEvent(self))

    def draw(self, ctx):
        if not self.cleared:
            clear_background(ctx)
            self.cleared = True

        ctx.font_size = 36
        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.save()

        if self.focus:
            self.focus.draw(ctx)
        ctx.restore()

    def update(self, delta: int):
        if self.focus:
            self.focus.update(delta)
        else:
            self.focus = MainMenu()
            asyncio.create_task(self.focus.start())


__app_export__ = Reactz
