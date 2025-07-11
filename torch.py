from tildagonos import tildagonos
from system.patterndisplay.events import *
from system.eventbus import eventbus


class LEDManager:
    __color: tuple[int, int, int] = (0, 0, 0)

    def do_color(self):
        # asyncio.sleep(0.5)
        for i in range(1, 13):
            tildagonos.leds[i] = self.color
        tildagonos.leds.write()

    def __init__(self):
        pass

    def on(self):
        eventbus.emit(PatternDisable())
        self.__color = (255, 255, 255)
        self.do_color()

    def off(self):
        self.__color = (0, 0, 0)
        self.do_color()

    def toggle(self):
        if self.__color == (255, 255, 255):
            self.off()
        else:
            self.on()

    @property
    def color(self):
        return self.__color
