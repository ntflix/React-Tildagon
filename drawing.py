import math


class Drawing:
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
