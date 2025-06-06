import asyncio
from typing import Callable
import aioespnow
from .multiplayergame.room import MACAddress, Room
from .wifi_reset import wifi_reset


class Comms:
    broadcast_setup: bool = False

    def __init__(self):
        # A WLAN interface must be active to send()/recv()
        self.sta = wifi_reset()  # Reset wifi to AP off, STA on and disconnected

        self.e = aioespnow.AIOESPNow()
        self.e.active(True)

    def reset(self) -> None:
        self.__init__()

    def setup_broadcast(self) -> None:
        self.broadcast_setup = True
        peer_mac: bytes = b"\xff\xff\xff\xff\xff\xff"
        self.e.add_peer(peer_mac)  # Must add_peer() before send()
        print("Added broadcast peer")

    def get_size_of_message(self, message: bytes | str) -> int:
        """Get the size of the message in bytes."""
        if isinstance(message, str):
            message = message.encode()
        return len(message)

    async def send_async(self, addr: bytes, message: bytes | str) -> None:
        if isinstance(message, str):
            message = message.encode()

        encoded_reactz = "REACTZ ".encode()
        message = encoded_reactz + message
        print(f"Sending message {message} to {addr.hex()} async")
        if self.get_size_of_message(message) > 250:
            raise ValueError(
                f"Oops! Message size {self.get_size_of_message(message)} exceeds maximum allowed size of 250 bytes."
            )
        await self.e.asend(addr, message)

    def send_sync(self, addr: bytes, message: bytes | str) -> None:
        """Send a message to a peer synchronously."""
        if isinstance(message, str):
            message = message.encode()

        encoded_reactz = "REACTZ ".encode()
        message = encoded_reactz + message
        print(f"Sending message {message} to {addr.hex()} sync")
        if self.get_size_of_message(message) > 250:
            raise ValueError(
                f"Oops! Message size {self.get_size_of_message(message)} exceeds maximum allowed size of 250 bytes."
            )
        self.e.send(addr, message)

    async def broadcast(
        self,
        message: str,
        broadcast_async: bool = True,
    ) -> None:
        if self.broadcast_setup == False:
            self.setup_broadcast()
        bcast: bytes = b"\xff\xff\xff\xff\xff\xff"
        print(f"Sending {message} to broadcast")
        try:
            if broadcast_async:
                await self.send_async(bcast, message)
            else:
                self.send_sync(bcast, message)
        except OSError as e:
            # if code -12393, it means the peer is not available
            if e.args[0] == -12393:
                print("No peers available")
            raise
        print(f"Sent message {message} to broadcast")

    async def receive_join_requests(
        self,
        on_join: Callable[[MACAddress], None] | None = None,
    ) -> None:
        join_requests = await self.receive()
        print(f"Received incoming message: {join_requests} - broadcast")
        if join_requests:
            mac, msg = join_requests
            if msg.startswith("JOIN "):
                room_name = msg.split(" ", 1)[1]
                print(f"Join request received from {mac} for room {room_name}")
                self.e.add_peer(mac)
                self.send_sync(mac, f"JOINED {room_name}")
                if on_join:
                    on_join(mac)

    async def receive(self, recv_async: bool = True) -> tuple[bytes, str] | None:
        """Receive a message from a peer.
        Returns:
            tuple[bytes, str] | None: A tuple containing the host's MAC address and the message string,
            or None if no message was received within the timeout.
        """
        host: bytes
        msg: bytes | None = None

        if recv_async:
            host, msg = await self.e.arecv()
        else:
            host, msg = self.e.recv()

        if msg:
            msg_str = msg.decode()
            # If the message is prefixed with "REACTZ ", strip it
            if not msg_str.startswith("REACTZ "):
                print(
                    f"`comms.py`: Received message from {host}: {msg_str}, but it does not start with 'REACTZ '. Ignoring."
                )
                return None
            msg_str = msg_str[7:]
            print(f"`comms.py`: Received message from {host}: {msg_str}")
            return host, msg_str
        else:
            print("Timeout")
            return None

    async def join_room(
        self,
        room: Room,
        on_join: Callable[[], None],
    ) -> None:
        # This method could be used to join a specific room
        print(f"Joining room: {room.name}")
        self.e.add_peer(room.host_mac)  # Ensure the host is added as a peer
        await self.send_async(room.host_mac, f"JOIN {room.name}")
        print(
            f"Peered and sent JOIN request to {room.host_mac.hex()} for room {room.name}"
        )
        join_ack: tuple[bytes, str] | None = None
        while join_ack is None:
            # Wait for a JOINED message from the host
            print(f"Waiting for join acknowledgment from {room.host_mac.hex()}")
            join_ack = await self.receive()
            print(f"Received incoming message: {join_ack} - join_room")
            if join_ack:
                mac, msg = join_ack
                if msg.startswith("JOINED "):
                    print(f"Joined room {room.name} successfully from {mac}")
                    on_join()
                else:
                    # ignore, HOST message, don't need
                    join_ack = None
            else:
                print(
                    f"No response from host {room.host_mac.hex()} when trying to join room {room.name}"
                )

    @property
    def mac(self) -> bytes:
        """Local MAC address"""
        return self.sta.config("mac")

    async def send_react_start(self, room: Room, delay_ms: int) -> None:
        """Host → everyone: when to start"""
        await self.broadcast(f"START {room.name} {delay_ms}")

    def send_react_time(self, room: Room, time_ms: int) -> None:
        """Client → host: your reaction time"""
        asyncio.create_task(
            self.send_async(room.host_mac, f"TIME {room.name} {time_ms}")
        )

    def send_results(self, room: Room, results: dict[bytes, int]) -> None:
        """Host → everyone: final scoreboard"""
        payload = ",".join(f"{mac.hex()}:{t}" for mac, t in results.items())
        asyncio.create_task(self.broadcast(f"RESULT {room.name} {payload}"))

    async def receive_react(self, room: Room) -> int | None:
        """Filter only REACTZ-prefixed messages"""
        incoming = await self.receive()
        print(f"Received incoming message: {incoming} - receive_react")
        if incoming:
            mac, msg = incoming
            msg = msg.split(" ", 1)
            print(f"Received message from {mac.hex()}: {msg}")
            if msg[0] not in ["START"]:
                print(f"Message {msg[0]} is not a valid reaction message. Ignoring.")
                return None
            if msg[1].startswith(room.name):
                msg = msg[1][len(room.name) + 1 :]  # Strip room name and space
                return int(msg)
        return None

    async def receive_scores(self) -> tuple[bytes, str] | None:
        """Receive scores from host or players.
        Returns:
            tuple[bytes, str] | None: A tuple containing the sender's MAC address and the message string,
            or None if no message was received within the timeout.
        """
        incoming = await self.receive(recv_async=True)
        print(f"Received incoming message: {incoming} - receive_scores")
        if incoming:
            mac, msg = incoming
            print(f"Received {mac.hex()}: {msg}")
            if msg.startswith("TIME ") or msg.startswith("RESULT "):
                return mac, msg
        return None
