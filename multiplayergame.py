import utime
import asyncio

from .comms import Comms
from .drawing import Drawing
from .mainmenu import GameType
from .constants import (
    get_random_waiting_message,
    get_room_name,
)
from .focusable import Focusable


class MultiPlayerReactionGame(Focusable):
    room_name: str = ""
    gameType: str = ""
    searching_message: str = "searching for rooms…"
    waiting_message: str = "Searching…"
    total_delta: int = 0
    drawing: Drawing = Drawing()
    joining_task: asyncio.Task | None = None
    listening_for_rooms: bool = False
    found_room: bool = False

    def __init__(self, gameType: str):
        self.gameType = gameType
        if gameType == GameType.HOSTING:
            self.room_name = get_room_name()
        print(f"Multiplayer game initialized as {gameType}")
        asyncio.create_task(self.reset_comms())

    async def reset_comms(self) -> None:
        self.comms = Comms()

    def handle_button(self, button: str) -> None:
        print(f"Button pressed: {button}")

    async def start(self):
        if self.joining_task:
            self.joining_task.cancel()
        print("start called")
        asyncio.create_task(self.reset_comms())
        await asyncio.sleep(1)
        if self.gameType == GameType.HOSTING:
            self.joining_task = asyncio.create_task(self.adverstise_room())
        elif self.gameType == GameType.JOINING:
            self.joining_task = None
            # self.broadcast_task = asyncio.create_task(self.comms.broadcast("JOIN"))
            await self.listen_for_rooms()
            # self.joining_task = asyncio.create_task(self.listen_for_rooms())

    async def adverstise_room(self) -> None:
        print(f"Advertising room: {self.room_name}")
        while True:
            try:
                self.comms.broadcast(f"HOST {self.room_name}")
            except asyncio.CancelledError:
                print("Advertise room cancelled")
                raise
            except OSError as e:
                if e.args[0] == -12393:
                    print("No peers available, retrying...")
            await asyncio.sleep(0.5)

    async def listen_for_rooms(self) -> None:
        print("Listening for rooms...")
        no_message_received = True
        while no_message_received:
            receive = self.comms.receive()
            if receive:
                host, msg = receive
                no_message_received = False
                print(f"Received message from {host}: {msg}")
            await asyncio.sleep(1)
        if msg and msg.startswith("HOST "):
            room_name = msg.split(" ", 1)[1]
            self.found_room = True
            print(f"Found room: {room_name} from {host}")
            # Here you could add logic to display the room name or join it
            self.searching_message = "Found room!"
            self.waiting_message = room_name

    def close(self) -> None:
        if self.joining_task:
            self.joining_task.cancel()
            self.joining_task = None
        print("Cancelled multiplayer game")

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
            if not self.found_room:
                self.drawing.draw_radial_box(
                    ctx, base_color=(0.4, 0.2, 0.5), circle_size=80, box_size=120
                )
            else:
                self.drawing.draw_radial_box(
                    ctx, base_color=(0, 0.4, 0), circle_size=80, box_size=120
                )

            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, -30).text(self.searching_message)
            ctx.font_size = 40
            ctx.rgb(1, 1, 1).move_to(0, 0).text(self.waiting_message)
        elif self.gameType == GameType.HOSTING:
            self.drawing.draw_radial_box(
                ctx, base_color=(0, 0.4, 0), circle_size=80, box_size=120
            )

            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, -30).text(f"your room name is")
            ctx.font_size = 40
            ctx.rgb(1, 1, 1).move_to(0, 0).text(self.room_name)
            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, 30).text("players can join now")

    def update(self, delta: int) -> bool:
        if not self.found_room:
            self.total_delta += delta
            if self.total_delta > 3000:
                self.waiting_message = get_random_waiting_message()
                self.total_delta = 0
        return True
