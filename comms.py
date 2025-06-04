import espnow
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

    def broadcast(self, message: str) -> None:
        if self.broadcast_setup == False:
            self.setup_broadcast()
        bcast: bytes = b"\xff\xff\xff\xff\xff\xff"
        print(f"Sending {message} to broadcast")
        try:
            self.e.send(bcast, message)
        except OSError as e:
            # if code -12393, it means the peer is not available
            if e.args[0] == -12393:
                print("No peers available")
            raise
        print(f"Sent message {message} to broadcast")

    def receive(self) -> tuple[bytes, str] | None:
        host, msg = self.e.recv(500)
        if msg:
            msg_str = msg.decode()
            print(f"Received message from {host}: {msg_str}")
            return host, msg_str
        else:
            print("Timeout")
            return None
