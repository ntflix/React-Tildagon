import math
import random
import utime
import asyncio
from app_components import clear_background

from ..comms import Comms
from ..focusable import Focusable
from .room import Room


class MultiPlayerReactionGameGame(Focusable):
    random_delay_ms: int
    react_set: bool
    start_ts: int
    reacted_in: str | None
    cleared_background: bool
    comms: Comms
    room: Room
    multiplayer: bool
    is_host: bool
    results: dict[bytes, int]
    react_set = False
    start_ts = 0
    cleared_background = False

    def __init__(
        self,
        comms: Comms,
        room: Room,
        is_host: bool = False,
    ):
        self.comms = comms
        self.room = room
        self.multiplayer = bool(comms and room)
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
            if self.reacted_in is None:
                self.on_reaction()
            elif self.reacted_in:
                # reset game
                print("Reaction not set yet! Resetting game.")
                self.restart()

    async def start(self):
        self.results.clear()
        self.reacted_in = None
        self.cleared_background = False

        if self.multiplayer:
            print(
                f"line 57: Starting multiplayer game in room {self.room.name} as {'host' if self.is_host else 'client'}"
            )
            if self.is_host:
                # Host picks & broadcasts delay
                self.random_delay_ms = random.randint(1000, 5000)
                self.comms.send_react_start(self.room, self.random_delay_ms)
                print(f"Host set random delay: {self.random_delay_ms}ms")
                await asyncio.sleep(self.random_delay_ms / 1000)
            else:
                # Client waits for host START
                incoming = self.comms.receive_react(room=self.room, timeout=20000)
                if incoming:
                    print(
                        f"Received REACT START from host in {self.room.name} with time {incoming}ms"
                    )
                    self.random_delay_ms = incoming
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

        if self.multiplayer:
            if self.is_host:
                # Host also records own time
                self.results[self.comms.mac] = elapsed
            else:
                # Client → host
                self.comms.send_react_time(self.room, elapsed)

    def update(self, delta: int) -> bool:
        if self.multiplayer:
            incoming = self.comms.receive_scores(1500)
            if incoming:
                sender, msg = incoming
                parts = msg.split()
                tag = parts[1]
                if tag == "TIME" and self.is_host:
                    # Host collects everyone’s TIME
                    t = int(parts[3])
                    self.results[sender] = t
                    # once everyone (host + players) have sent
                    expected = len(self.room.players) + 1
                    if len(self.results) == expected:
                        # broadcast final scoreboard
                        for p in [self.comms.mac] + self.room.players:
                            self.comms.send_results(p, self.room, self.results)

                elif tag == "RESULT" and not self.is_host:
                    # Client receives final RESULTS
                    raw = parts[3]
                    for pair in raw.split(","):
                        mac_hex, tstr = pair.split(":")
                        self.results[bytes.fromhex(mac_hex)] = int(tstr)

        return True

    def draw(self, ctx) -> None:
        if not self.cleared_background:
            clear_background(ctx)
            self.cleared_background = True

        print("drawing")
        if self.react_set:
            print("drawing react set")
            ctx.rgb(1, 0, 0).arc(0, 0, 60, 0, 2 * math.pi, True).fill()
        else:
            print("drawing react set not set")
            if self.reacted_in is not None:
                print("drawing reacted in")
                ctx.rgb(0, 0.6, 0).arc(0, 0, 60, 0, 2 * math.pi, True).fill()
                ctx.rgb(1, 1, 1).move_to(0, 0).text(f"{self.reacted_in}ms")
            else:
                print("drawing reacted in not set")
                ctx.rgb(0.5, 0, 0.5).arc(0, 0, 40, 0, 2 * math.pi, True).fill()

        if self.multiplayer and self.results:
            y = 100
            for mac, t in self.results.items():
                prefix = "You" if mac == self.comms.mac else mac.hex()[:4]
                ctx.font_size = 18
                ctx.rgb(1, 1, 1).move_to(-60, y).text(f"{prefix}: {t}ms")
                y += 24
