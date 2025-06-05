import math
import utime
import asyncio
from app_components import clear_background

from ..comms import Comms
from ..drawing import Drawing
from ..mainmenu import GameType
from ..constants import get_random_waiting_message, get_room_name
from ..focusable import Focusable
from .multiplayergamegame import MultiPlayerReactionGameGame
from .room import Room


class MultiPlayerReactionGameSetup(Focusable):
    gameType: str = ""
    searching_message: str = "searching for rooms…"
    waiting_message: str = "Searching…"
    total_delta: int = 0
    drawing: Drawing = Drawing()
    joining_task: asyncio.Task | None = None
    listening_for_rooms: bool = False
    cleared_background: bool = False
    accent: tuple[float, float, float] | None = None
    color_override: tuple[float, float, float] | None = None
    subtitle: str | None = None
    game: MultiPlayerReactionGameGame | None = None

    room: Room | None = None

    # breathing settings
    breath_period: float = 4.0  # seconds per full in-and-out
    breath_amplitude: float = 3.0  # max px offset up/down
    _time: float = 0.0  # accumulated time
    breath_offset: float = 0.0

    def __init__(self, gameType: str):
        self.gameType = gameType
        if gameType == GameType.HOSTING:
            room_name = get_room_name()
            self.room = Room(name=room_name, host_mac=b"")
            if "banana" in self.room.name:
                self.accent = (1, 1, 0)
            else:
                self.accent = (0.396, 0, 0.4)
        print(f"Multiplayer game initialized as {gameType}")
        asyncio.create_task(self.reset_comms())

    async def reset_comms(self) -> None:
        self.comms = Comms()

    def handle_button(self, button: str) -> None:
        print(f"Button pressed: {button}")
        if self.gameType == GameType.PLAYINGMULTIPLAYER:
            if self.game:
                self.game.handle_button(button)
            return
        if button == "DOWN" and self.gameType == GameType.JOINING:
            if self.room:
                self.join_room()
        elif button == "DOWN" and self.gameType == GameType.HOSTING:
            if self.room and len(self.room.players) > 0:
                if self.joining_task:
                    # Cancel the task that is advertising the room
                    print("Cancelling joining task")
                    self.joining_task.cancel()
                self.joining_task = None
                self.start_multiplayer_game_as_host()

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

    def start_multiplayer_game_as_host(self) -> None:
        assert self.room is not None, "Room must be initialized before starting game"
        print("Starting game with players:", self.room.players)
        self.gameType = GameType.PLAYINGMULTIPLAYER
        self.game = MultiPlayerReactionGameGame(
            comms=self.comms,
            room=self.room,
            is_host=True,
        )
        asyncio.create_task(self.game.start())

    async def adverstise_room(self) -> None:
        assert self.room is not None, "Room must be initialized before advertising"
        print(f"Advertising room: {self.room.name}")
        while True:
            try:
                self.comms.broadcast(
                    f"HOST {self.room.name}",
                    on_join=self.add_player_to_room,
                )
            except asyncio.CancelledError:
                print("Advertise room cancelled")
                raise
            except OSError as e:
                if e.args[0] == -12393:
                    print("No peers available, retrying...")
            await asyncio.sleep(3)

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
            room_name = msg[5:]  # Extract room name after "HOST "
            print(f"Found room: {room_name} from {host}")
            self.searching_message = "Found room!"
            self.room = Room(name=room_name, host_mac=host)

            self.waiting_message = room_name
            if "banana" in self.room.name:
                self.accent = (1, 1, 0)
            if self.room.name == "banana banana":
                self.color_override = (0.9, 0.9, 0)

    def join_room(self) -> None:
        assert self.room is not None, "Room must be initialized before joining"
        print(f"Joining room: {self.room.name}")
        self.comms.join_room(self.room, self.on_joined)
        # self.gameType = GameType.PLAYINGMULTIPLAYER

    def on_joined(self) -> None:
        assert self.room is not None
        print(f"Joined the room {self.room.name}")
        self.gameType = GameType.PLAYINGMULTIPLAYER
        self.game = MultiPlayerReactionGameGame(
            comms=self.comms,
            room=self.room,
            is_host=False,
        )
        asyncio.create_task(self.game.start())

    def add_player_to_room(self, player_mac: bytes) -> None:
        if self.room:
            print(f"Adding player {player_mac.hex()} to room {self.room.name}")
            self.room.add_player(player_mac)
            self.subtitle = f"{len(self.room.players)} player{'' if len(self.room.players) == 1 else 's'} joined"
        else:
            print("No room to add player to!")

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
        if not self.cleared_background:
            clear_background(ctx)
            self.cleared_background = True

        if self.gameType == GameType.PLAYINGMULTIPLAYER:
            if self.game:
                self.game.draw(ctx)
            return

        elif self.gameType == GameType.JOINING:
            base_color = self.color_override
            if not self.room:
                if not self.color_override:
                    base_color = (0.4, 0.2, 0.5)
                self.drawing.draw_radial_box(
                    ctx, base_color=base_color, circle_size=80, box_size=120  # type: ignore
                )
            else:
                base_color = self.color_override
                if not self.color_override:
                    base_color = (0, 0.4, 0)

                self.drawing.draw_radial_box(
                    ctx,
                    base_color=base_color,  # type: ignore
                    circle_size=80,
                    box_size=120,
                    custom_accent_color=self.accent,
                )

            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, -30).text(self.searching_message)
            ctx.font_size = 40
            ctx.rgb(1, 1, 1).move_to(0, 0).text(self.waiting_message)
            if self.room:
                ctx.font_size = 22
                ctx.rgb(1, 1, 1).move_to(0, 90).text("join room")

                triangle_colour = (1, 1, 1)
                self.drawing.triangle(
                    ctx,
                    0,
                    112 + self.breath_offset * -0.5,
                    7,
                    triangle_colour,
                    rotate=math.pi,
                )
            return

        elif self.gameType == GameType.JOINED:
            self.drawing.draw_radial_box(
                ctx,
                base_color=(0, 0.4, 0),
                circle_size=80,
                box_size=120,
                custom_accent_color=self.accent,
            )

            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, -30).text(f"you have joined")
            ctx.font_size = 40 * (1 + self.breath_offset / 100)
            assert self.room is not None
            ctx.rgb(1, 1, 1).move_to(0, 0 + self.breath_offset).text(self.room.name)
            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, 30).text("waiting for host to start")
            return

        elif self.gameType == GameType.HOSTING:

            self.drawing.draw_radial_box(
                ctx,
                base_color=(0, 0.4, 0),
                circle_size=80,
                box_size=120,
                custom_accent_color=self.accent,
            )

            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, -30).text(f"your room name is")
            ctx.font_size = 40 * (1 + self.breath_offset / 100)
            assert self.room is not None
            ctx.rgb(1, 1, 1).move_to(0, 0 + self.breath_offset).text(self.room.name)
            ctx.font_size = 22
            ctx.rgb(1, 1, 1).move_to(0, 30).text(
                self.subtitle or "players can join now"
            )
            if len(self.room.players) > 0:
                ctx.font_size = 22
                ctx.rgb(1, 1, 1).move_to(0, 90).text("start")

                triangle_colour = (1, 1, 1)
                self.drawing.triangle(
                    ctx,
                    0,
                    112 + self.breath_offset * -0.5,
                    7,
                    triangle_colour,
                    rotate=math.pi,
                )
            return

    def update(self, delta: int) -> bool:
        if self.gameType == GameType.PLAYINGMULTIPLAYER:
            if self.game:
                return self.game.update(delta)

        if not self.room:
            self.total_delta += delta
            if self.total_delta > 3000:
                self.waiting_message = get_random_waiting_message()
                self.total_delta = 0
                """Delta is in milliseconds since last update."""

        # advance our time accumulator in seconds
        self._time += delta / 1000.0

        # ω = 2π / period
        omega = 2 * math.pi / self.breath_period

        # sine wave gives ease-in-out; offset swings between –amplitude and +amplitude
        self.breath_offset = self.breath_amplitude * math.sin(omega * self._time)

        return True
