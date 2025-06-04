import math
from typing import TYPE_CHECKING

from .focusable import Focusable
from .drawing import Drawing

if TYPE_CHECKING:
    from app import Reactz  # Avoid circular import issues


class GameType:
    SINGLEPLAYER = "singleplayer"
    JOINING = "joining"
    HOSTING = "hosting"


class MainMenu(Focusable):
    gametype: GameType | None = None
    drawing: Drawing = Drawing()

    def __init__(self):
        pass

    def draw(self, ctx):
        # background
        ctx.radial_gradient(0, 0, 70, 0, 0, 55)
        ctx.add_stop(0, (0.45, 0.45, 0.45), 1)
        ctx.add_stop(1, (0.25, 0.25, 0.25), 1)
        ctx.rectangle(-120, -120, 240, 240).fill()  # .rgb(0.25, 0.25, 0.25)
        ctx.rgb(0.5, 0.5, 0.5).arc(0, 0, 55, 0, 2 * math.pi, True).fill()

        # title
        ctx.font_size = 36
        ctx.rgb(1, 1, 1).move_to(0, 0).text("React")

        # menu options (no CTM bleed-over!)
        ctx.font_size = 24
        ctx.rgb(1, 1, 1).move_to(0, 90).text("Singleplayer")

        ctx.font_size = 18
        ctx.save()
        ctx.rgb(1, 1, 1).rotate(0).move_to(-60, -40).text("Host game…")
        ctx.restore()
        ctx.rgb(1, 1, 1).rotate(0).move_to(60, -40).text("Join game…")
        ctx.restore()

        # now your pure-python triangle math will see a clean CTM again:
        triangle_colour = (1, 1, 1)
        # self.drawing.triangle(ctx, 50, -90, 20, triangle_colour, rotate=-0.7)
        self.drawing.triangle(ctx, 87, -62, 7, triangle_colour, rotate=1)
        self.drawing.triangle(ctx, -87, -62, 7, triangle_colour, rotate=-1)
        self.drawing.triangle(ctx, 0, 112, 7, triangle_colour, rotate=math.pi)

    async def start(self) -> None:
        print("Starting main menu")
