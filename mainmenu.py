import math
from app_components import clear_background

from .focusable import Focusable
from .drawing import Drawing


class GameType:
    SINGLEPLAYER = "singleplayer"
    JOINING = "joining"
    JOINED = "joined"
    HOSTING = "hosting"
    PLAYINGMULTIPLAYER = "playingmultiplayer"


class MainMenu(Focusable):
    gametype: GameType | None = None
    drawing: Drawing = Drawing()
    cleared_background: bool = False

    # breathing settings
    breath_period: float = 4.0  # seconds per full in-and-out
    breath_amplitude: float = 5.0  # max px offset up/down
    _time: float = 0.0  # accumulated time

    text_vertical_offset: float = 0.0

    def __init__(self):
        pass

    def draw(self, ctx):
        if not self.cleared_background:
            clear_background(ctx)
            self.cleared_background = True

        # pull in our breathing offset
        offset = self.text_vertical_offset

        # background with a “floating” 3D look
        ctx.radial_gradient(
            0,
            -offset * 0.1,  # start circle moves opposite to simulate light
            70,
            0,
            offset * 0.1,  # end circle moves with offset to shift shadow
            55,
        )
        ctx.add_stop(0, (0.8, 0, 0.8), 1)
        ctx.add_stop(1, (0.25, 0.25, 0.25), 1)
        ctx.rectangle(-120, -120, 240, 240).fill()

        # shift the fill-circle down (shadow) as the top “lifts”
        ctx.rgb(0.7, 0.5, 0.7).arc(0, offset * 0.1, 55, 0, 2 * math.pi, True).fill()

        # # background
        # ctx.radial_gradient(0, 0, 70, 0, 0, 55)
        # ctx.add_stop(0, (0.45, 0.45, 0.45), 1)
        # ctx.add_stop(1, (0.25, 0.25, 0.25), 1)
        # ctx.rectangle(-120, -120, 240, 240).fill()  # .rgb(0.25, 0.25, 0.25)
        # ctx.rgb(0.5, 0.5, 0.5).arc(0, 0, 55, 0, 2 * math.pi, True).fill()

        # title
        ctx.font_size = 36
        ctx.rgb(1, 1, 1).move_to(0, 0 + self.text_vertical_offset * 0.5).text("React")

        ctx.font_size = 16
        ctx.rgb(1, 1, 1).move_to(0, 20 + self.text_vertical_offset * 0.2).text(
            "MULTIPLAYER"
        )

        ctx.font_size = 24
        ctx.rgb(1, 1, 1).move_to(0, 90).text("Singleplayer")

        ctx.font_size = 22
        ctx.save()
        ctx.rgb(1, 1, 1).move_to(5, -85).rotate(-1).text("HOST")
        ctx.restore()
        ctx.rgb(1, 1, 1).move_to(-5, -85).rotate(1).text("JOIN")
        ctx.restore()

        # now your pure-python triangle math will see a clean CTM again:
        triangle_colour = (1, 1, 1)
        # self.drawing.triangle(ctx, 50, -90, 20, triangle_colour, rotate=-0.7)
        self.drawing.triangle(ctx, 87, -62, 7, triangle_colour, rotate=1)
        self.drawing.triangle(ctx, -87, -62, 7, triangle_colour, rotate=-1)
        self.drawing.triangle(ctx, 0, 112, 7, triangle_colour, rotate=math.pi)

    async def start(self) -> None:
        print("Starting main menu")

    def update(self, delta: int) -> bool:
        """Delta is in milliseconds since last update."""

        # advance our time accumulator in seconds
        self._time += delta / 1000.0

        # ω = 2π / period
        omega = 2 * math.pi / self.breath_period

        # sine wave gives ease-in-out; offset swings between –amplitude and +amplitude
        self.text_vertical_offset = self.breath_amplitude * math.sin(omega * self._time)

        # return False to stay on this menu
        return False
