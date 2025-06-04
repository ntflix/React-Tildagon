from typing import Callable
import espnow
from .wifi_reset import wifi_reset


class Comms:
    def __init__(self):
        # A WLAN interface must be active to send()/recv()
        self.sta = wifi_reset()  # Reset wifi to AP off, STA on and disconnected

        self.e = espnow.ESPNow()
        self.e.active(True)
        self.setup_broadcast()

    def reset(self) -> None:
        self.__init__()

    def setup_broadcast(self) -> None:
        peer_mac: bytes = b"\xff\xff\xff\xff\xff\xff"

        try:
            self.e.add_peer(peer_mac)  # Must add_peer() before send()
            print("Added broadcast peer")
        except OSError as e:
            if "ESP_ERR_ESPNOW_EXIST" in str(e):
                print("Peer already added")
            else:
                raise e

    async def broadcast(
        self,
        message: str,
    ) -> None:
        bcast: bytes = b"\xff\xff\xff\xff\xff\xff"
        print(f"Sending {message} to broadcast")
        try:
            self.e.send(bcast, message)
        except OSError as e:
            if "ETIMEDOUT" in str(e):
                print(f"Timeout while sending message {message}")

        print(f"Sent message {message} to broadcast")

    async def receive(self, on_receive: Callable[[bytes, str], None]):
        host, msg = await self.e.arecv()
        if msg:  # msg == None if timeout in recv()
            # convert message to string
            msg_str: str = msg.decode()
            print(host, msg_str)
            on_receive(host, msg_str)
