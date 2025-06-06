import math
import random
import utime
import asyncio
from app_components import clear_background

from ..comms import Comms
from ..drawing import Drawing
from ..focusable import Focusable
from .room import Room


class MultiPlayerReactionGameGame(Focusable):
    drawing: Drawing = Drawing()
    random_delay_ms: int
    react_set: bool = False
    start_ts: int
    reacted_in: str | None
    cleared_background: bool
    comms: Comms
    room: Room
    multiplayer: bool
    is_host: bool
    results: dict[bytes, int]
    start_ts = 0
    cleared_background = False
    waiting_for_host_to_start = True

    async def listen_for_scores(self) -> None:
        print("Listening for scores...")
        incoming = await self.comms.receive_scores()
        if incoming:
            print("Received scores from host or players.")
            sender, msg = incoming
            parts = msg.split()
            tag = parts[0]
            print(tag, parts)
            if tag == "TIME" and self.is_host:
                print(f"Received TIME from {sender.hex()}: {parts[3]}")
                # Host collects everyone’s TIME
                t = int(parts[3])
                self.results[sender] = t
                # once everyone (host + players) have sent
                expected = len(self.room.players) + 1
                if len(self.results) == expected:
                    # broadcast final scoreboard
                    self.comms.send_results(self.room, self.results)

            elif tag == "RESULT" and not self.is_host:
                # Client receives final RESULTS
                raw = parts[3]
                for pair in raw.split(","):
                    mac_hex, tstr = pair.split(":")
                    self.results[bytes.fromhex(mac_hex)] = int(tstr)
        else:
            print("No scores received")

    def __init__(
        self,
        comms: Comms,
        room: Room,
        is_host: bool = False,
    ):
        self.comms = comms
        self.room = room
        # self.multiplayer = bool(comms and room)
        self.multiplayer = True
        if is_host and not self.multiplayer:
            raise ValueError("Cannot be host without a multiplayer setup.")

        self.is_host = is_host
        self.results = {}
        self.reacted_in = None
        self.react_set = False
        self.start_ts = 0
        self.cleared_background = False

    def handle_button(self, button: str) -> None:
        if button in ["CONFIRM", "RIGHT", "DOWN"]:
            print(f"Button {button} pressed in game. reacted_in is {self.reacted_in}")
            if self.reacted_in is None:
                self.on_reaction()
            elif self.reacted_in:
                # reset game
                print("Reaction not set yet! Resetting game.")
                self.restart()

    async def start(self):
        self.results.clear()
        self.waiting_for_host_to_start = True
        self.reacted_in = None
        self.cleared_background = False

        if self.multiplayer:
            print(
                f"line 57: Starting multiplayer game in room {self.room.name} as {'host' if self.is_host else 'client'}"
            )
            if self.is_host:
                # Host picks & broadcasts delay
                self.random_delay_ms = random.randint(1000, 5000)
                asyncio.create_task(self.listen_for_scores())
                await self.comms.send_react_start(self.room, self.random_delay_ms)
                print(f"Host set random delay: {self.random_delay_ms}ms")
                await asyncio.sleep(self.random_delay_ms / 1000)
            else:
                # Client waits for host START
                incoming = await self.comms.receive_react(room=self.room)
                if incoming:
                    self.waiting_for_host_to_start = False
                    print(
                        f"Received REACT START from host in {self.room.name} with time {incoming}ms"
                    )
                    self.random_delay_ms = incoming
                    self.cleared_background = False
                    await asyncio.sleep(self.random_delay_ms / 1000)
                else:
                    print(
                        f"Failed to receive START from host in room {self.room.name}. Restarting game."
                    )
                    self.restart()
                    return
            # mark go-time
            self.start_ts = utime.ticks_ms()
            self.react_set = True

        else:
            # … your existing single-player start() …
            assert not self.react_set
            self.random_delay_ms = random.randint(700, 1000)
            await asyncio.sleep(self.random_delay_ms / 1000)
            self.start_ts = utime.ticks_ms()
            self.react_set = True

    def restart(self):
        print("Restarting game...")
        self.cleared_background = False
        self.reacted_in = None
        self.react_set = False
        self.start_ts = 0
        self.random_delay_ms = 0
        asyncio.create_task(self.start())

    def on_reaction(self):
        now = utime.ticks_ms()
        if not self.react_set:
            print("Too soon!")
            return
        elapsed = utime.ticks_diff(now, self.start_ts)
        self.reacted_in = f"{elapsed}"
        self.react_set = False

        print(f"Reaction time: {self.reacted_in}ms")

        if self.multiplayer:
            if self.is_host:
                # Host also records own time
                self.results[self.comms.mac] = elapsed
            else:
                # Client → host
                self.comms.send_react_time(self.room, elapsed)
                asyncio.create_task(self.listen_for_scores())

    def update(self, delta: int) -> bool:
        return True

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

        if self.multiplayer and self.results:
            y = 38
            height_of_box = 22 * len(self.results) + 10

            ctx.rgb(0.2, 0.2, 0.2).round_rectangle(
                -60,
                20,
                120,
                height_of_box,
                8,
            ).fill()

            for mac, t in self.results.items():
                prefix = "You" if mac == self.comms.mac else mac.hex()[6:]
                ctx.font_size = 20
                ctx.rgb(1, 1, 1).move_to(0, y).text(f"{prefix}: {t}ms")
                y += 22

        elif self.waiting_for_host_to_start and not self.is_host:
            self.drawing.draw_radial_box(
                ctx,
                base_color=(0, 0.4, 0),
                circle_size=80,
                box_size=120,
                custom_accent_color=(0.8, 0, 0.8),
            )

            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, -30).text(f"you have joined")
            ctx.font_size = 40 * (1 / 100)
            assert self.room is not None
            ctx.rgb(1, 1, 1).move_to(0, 0).text(self.room.name)
            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, 30).text("waiting for host to start")
            return
