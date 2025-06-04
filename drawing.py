import math
from .torch import LEDManager


class Drawing:
    def __init__(self):
        self.led_manager = LEDManager()

    def triangle(
        self,
        ctx,
        x: float,
        y: float,
        size: float,
        colour=(1, 0, 0),
        rotate: float = 0,
    ):
        """
        Draws a triangle whose center is at (x,y), pre-rotated by `rotate` radians,
        then stroked (no ctx.rotate()). Passing any x,y simply moves the triangle
        center to that point.
        """
        ctx.save()
        # 1) Define the three corner offsets *relative* to the triangle’s center.
        local_pts = [
            (-size, size),  # top-left corner
            (size, size),  # top-right corner
            (0, -size),  # bottom-center
        ]

        cos_r = math.cos(rotate)
        sin_r = math.sin(rotate)

        # 2) Rotate each local point around (0,0) then shift it to (x,y)
        world_pts = []
        for dx, dy in local_pts:
            # rotate around origin
            rx = dx * cos_r - dy * sin_r
            ry = dx * sin_r + dy * cos_r
            # translate so that (0,0)→(x,y)
            world_pts.append((rx + x, ry + y))

        # 3) Build and stroke path
        ctx.rgb(*colour).begin_path()
        ctx.move_to(*world_pts[0])
        ctx.line_to(*world_pts[1])
        ctx.line_to(*world_pts[2])
        ctx.close_path()
        ctx.rgb(colour[0], colour[1], colour[2]).fill()
        ctx.stroke()
        ctx.restore()

    def draw_radial_box(
        self, ctx, base_color: tuple, circle_size: float = 80, box_size: float = 120
    ):
        """
        Draws a square background filled with a radial gradient,
        plus an inner circle of radius circle_size.

        base_color: (r,g,b) for the circle
        circle_size: radius of the inner circle
        box_size: half-width/height of the square
        """
        # generate darker stops
        stop0 = tuple(float(max(0, c - 0.1)) for c in base_color)
        stop1 = tuple(float(max(0, c - 0.2)) for c in base_color)

        # radial gradient: from slightly outside circle back into it
        ctx.radial_gradient(0, 0, circle_size + 10, 0, 0, circle_size)
        ctx.add_stop(0, stop0, 1)
        ctx.add_stop(1, stop1, 1)

        # fill the square
        ctx.rectangle(-box_size, -box_size, 2 * box_size, 2 * box_size).fill()

        # draw inner circle
        ctx.rgb(*base_color).arc(0, 0, circle_size, 0, 2 * math.pi, True).fill()

    def toggle(self):
        self.color = (255, 255, 255) if self.color == (0, 0, 0) else (0, 0, 0)
        self.on = not self.on

        if self.color == (255, 255, 255):
            self.led_manager.on()
        else:
            self.led_manager.off()
