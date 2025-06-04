class Focusable:
    def __init__(self): ...

    def draw(self, ctx) -> None: ...

    def handle_button(self, button: str) -> None: ...

    def update(self, delta: int) -> bool:
        return True

    def close(self) -> None:
        pass

    async def start(self) -> None: ...
