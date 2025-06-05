MACAddress = bytes


class Room:
    name: str
    host_mac: MACAddress
    players: list[MACAddress] = []

    def __str__(self) -> str:
        return f"Room(name={self.name}, host_mac={self.host_mac.hex()})"

    def __init__(self, name: str, host_mac: bytes):
        self.name = name
        self.host_mac = host_mac

    def add_player(self, player_mac: MACAddress) -> None:
        if player_mac not in self.players:
            self.players.append(player_mac)
            print(f"Player {player_mac.hex()} added to room {self.name}")
        else:
            print(f"Player {player_mac.hex()} is already in room {self.name}")
