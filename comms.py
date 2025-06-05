from typing import Callable
import espnow
from .multiplayergame.room import MACAddress, Room
from .wifi_reset import wifi_reset


class Comms:
    broadcast_setup: bool = False

    def __init__(self):
        # A WLAN interface must be active to send()/recv()
        self.sta = wifi_reset()  # Reset wifi to AP off, STA on and disconnected

        self.e = espnow.ESPNow()
        self.e.active(True)

    def reset(self) -> None:
        self.__init__()

    def setup_broadcast(self) -> None:
        self.broadcast_setup = True
        peer_mac: bytes = b"\xff\xff\xff\xff\xff\xff"
        self.e.add_peer(peer_mac)  # Must add_peer() before send()
        print("Added broadcast peer")

    def send(self, addr: bytes, message: bytes | str) -> None:
        if isinstance(message, str):
            message = message.encode()

        encoded_reactz = "REACTZ ".encode()
        message = encoded_reactz + message
        self.e.send(addr, message)

    def broadcast(
        self,
        message: str,
        on_join: Callable[[MACAddress], None] | None = None,
    ) -> None:
        if self.broadcast_setup == False:
            self.setup_broadcast()
        bcast: bytes = b"\xff\xff\xff\xff\xff\xff"
        print(f"Sending {message} to broadcast")
        try:
            self.send(bcast, message)
        except OSError as e:
            # if code -12393, it means the peer is not available
            if e.args[0] == -12393:
                print("No peers available")
            raise
        print(f"Sent message {message} to broadcast")
        join_requests = self.receive(100)
        if join_requests:
            mac, msg = join_requests
            if msg.startswith("JOIN "):
                room_name = msg.split(" ", 1)[1]
                print(f"Join request received from {mac} for room {room_name}")
                self.e.add_peer(mac)
                self.send(mac, f"JOINED {room_name}")
                if on_join:
                    on_join(mac)

    def receive(self, timeout: int = 500) -> tuple[bytes, str] | None:
        """Receive a message from a peer.
        Args:
            timeout_ms: int (Optional): May have the following values.
                0: No timeout. Return immediately if no data is available;
                > 0: Specify a timeout value in milliseconds;
                < 0: Do not timeout, ie. wait forever for new messages; or
                None (or not provided): Use the default timeout value set with ESPNow.config().
        Returns:
            tuple[bytes, str] | None: A tuple containing the host's MAC address and the message string,
            or None if no message was received within the timeout.
        """
        host, msg = self.e.recv(timeout)
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

    def join_room(
        self,
        room: Room,
        on_join: Callable[[], None],
    ) -> None:
        # This method could be used to join a specific room
        print(f"Joining room: {room.name}")
        self.e.add_peer(room.host_mac)  # Ensure the host is added as a peer
        self.send(room.host_mac, f"JOIN {room.name}")
        print(
            f"Peered and sent JOIN request to {room.host_mac.hex()} for room {room.name}"
        )
        join_ack: tuple[bytes, str] | None = None
        while join_ack is None:
            # Wait for a JOINED message from the host
            print(f"Waiting for join acknowledgment from {room.host_mac.hex()}")
            join_ack = self.receive(1000)
            if join_ack:
                mac, msg = join_ack
                if msg.startswith("REACTZ JOINED "):
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

    def send_react_start(self, room: Room, delay_ms: int) -> None:
        """Host → everyone: when to start"""
        self.broadcast(f"REACTZ START {room.name} {delay_ms}")

    def send_react_time(self, room: Room, time_ms: int) -> None:
        """Client → host: your reaction time"""
        self.send(room.host_mac, f"REACTZ TIME {room.name} {time_ms}")

    def send_results(
        self, player_mac: bytes, room: Room, results: dict[bytes, int]
    ) -> None:
        """Host → each player: final scoreboard"""
        payload = ",".join(f"{mac.hex()}:{t}" for mac, t in results.items())
        self.send(player_mac, f"REACTZ RESULT {room.name} {payload}")

    def receive_react(self, timeout: int = 500) -> tuple[bytes, str] | None:
        """Filter only REACTZ-prefixed messages"""
        incoming = self.receive(timeout)
        if incoming:
            mac, msg = incoming
            if msg.startswith("REACTZ "):
                return mac, msg
        return None
