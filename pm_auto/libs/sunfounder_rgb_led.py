
from enum import Enum

from ..libs.i2c import I2C
from ..libs.utils import hex_to_rgb

# I2C register map size (matches CH32V003 firmware registerMap[255])
REGISTER_SIZE = 255
# Hardware limit: DMA buffer holds max 23 LEDs (WS2812_MAX_LEDS in firmware)
MAX_LEDS = 23

RGB_STYLES = [
    'solid', 'breathing', 'flow', 'flow_reverse', 'rainbow', 'rainbow_reverse', 'hue_cycle'
]

class SunFounderRGBLED():
    """I2C driver for CH32V003-based RGB LED controller (Pironman 5 UPS RGB firmware).

    Communicates via I2C at address 0x6A. The firmware acts as an I2C slave with a
    255-byte register map. First byte of each write = register address, subsequent bytes
    are written sequentially with auto-increment. See register_map.h in firmware source.
    """
    ADDRESS = 0x6A

    class Mode(Enum):
        OFF = 0x00
        SOLID = 0x01
        BREATHING = 0x02
        FLOW = 0x03
        FLOW_REVERSE = 0x04
        RAINBOW = 0x05
        RAINBOW_REVERSE = 0x06
        HUE_CYCLE = 0x07

    class Register(Enum):
        MODE = 0x00
        NUM = 0x01

        RED = 0x10
        GREEN = 0x11
        BLUE = 0x12
        BRIGHTNESS = 0x13
        SPEED = 0x14

    def __init__(self, *args, **kwargs):
        self.led_count = 0
        self.enable = False
        self.color = (0, 0, 0)
        self.brightness = 0
        self.speed = 0
        self.style = 'solid'
        self.i2c = I2C(self.ADDRESS)

    def set_mode(self, mode: (Mode, str)):
        if isinstance(mode, str):
            mode = self.Mode[mode.upper()]
        self.i2c.write_byte_data(self.Register.MODE.value, mode.value)

    def set_enable(self, enable: bool):
        self.enable = enable
        if enable:
            self.set_mode(self.style)
        else:
            self.set_mode(self.Mode.OFF)

    def set_style(self, style: (Mode, str)):
        if isinstance(style, self.Mode):
            style = style.name.lower()
        self.style = style
        if self.enable:
            self.set_mode(style)

    def set_num(self, num: int):
        if num < 0:
            num = 0
        self.led_count = num
        self.i2c.write_byte_data(self.Register.NUM.value, num)

    def set_color(self, color: (tuple, str, list)):
        if isinstance(color, str):
            color = hex_to_rgb(color)
        elif isinstance(color, tuple):
            color = list(color)
        elif isinstance(color, list):
            pass
        else:
            raise Exception(f"Invalid color: {color}")
        self.color = color
        self._write_rgb_block()

    def set_brightness(self, brightness: int):
        if brightness < 0:
            brightness = 0
        elif brightness > 100:
            brightness = 100
        self.brightness = brightness
        self._write_rgb_block()

    def set_speed(self, speed: int):
        if speed < 0:
            speed = 0
        elif speed > 100:
            speed = 100
        self.speed = speed
        self._write_rgb_block()

    def _write_rgb_block(self):
        """Write R, G, B, brightness, speed with retry for I2C bus contention.

        The CH32V003 firmware disables IRQs during WS2812 DMA transfers (~750us),
        causing I2C writes to fail with EREMOTEIO if they land in this window.
        Retry up to 3 times with jittered delays to find a non-contended window.
        """
        import time
        import random
        for attempt in range(3):
            try:
                self.i2c.write_byte_data(self.Register.RED.value, self.color[0])
                time.sleep(0.005)
                self.i2c.write_byte_data(self.Register.GREEN.value, self.color[1])
                time.sleep(0.005)
                self.i2c.write_byte_data(self.Register.BLUE.value, self.color[2])
                time.sleep(0.005)
                self.i2c.write_byte_data(self.Register.BRIGHTNESS.value, self.brightness)
                time.sleep(0.005)
                self.i2c.write_byte_data(self.Register.SPEED.value, self.speed)
                return
            except OSError:
                if attempt < 2:
                    time.sleep(0.01 + random.uniform(0, 0.005))
        raise
