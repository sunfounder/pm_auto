
from enum import Enum

from ..libs.i2c import I2C
from ..libs.utils import hex_to_rgb

RGB_STYLES = [
    'solid', 'breathing', 'flow', 'flow_reverse', 'rainbow', 'rainbow_reverse', 'hue_cycle'
]

class SunFounderRGBLED():
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
        '''
        Set mode.

        Args:
            mode (Mode, str): Mode to set.
        '''
        if isinstance(mode, str):
            mode = self.Mode[mode.upper()]
        self.i2c.write_byte_data(self.Register.MODE.value, mode.value)

    def set_enable(self, enable: bool):
        '''
        Set enable.

        Args:
            enable (bool): Enable to set.
        '''
        self.enable = enable
        if enable:
            self.set_mode(self.style)
        else:
            self.set_mode(self.Mode.OFF)

    def set_style(self, style: (Mode, str)):
        '''
        Set style.

        Args:
            style (Mode, str): Style to set.
        '''
        if isinstance(style, self.Mode):
            style = style.name.lower()
        self.style = style
        if self.enable:
            self.set_mode(style)

    def set_num(self, num: int):
        '''
        Set LED number.

        Args:
            num (int): LED number to set.
        '''
        self.led_count = num
        self.i2c.write_byte_data(self.Register.NUM.value, num)

    def set_color(self, color: (tuple, str, list)):
        '''
        Set color.

        Args:
            color (tuple, str, list): Color to set.
        '''
        if isinstance(color, str):
            color = hex_to_rgb(color)
        elif isinstance(color, tuple):
            color = list(color)
        elif isinstance(color, list):
            pass
        else:
            raise Exception(f"Invalid color: {color}")
        self.color = color
        self.i2c.write_i2c_block_data(self.Register.RED.value, color)

    def set_brightness(self, brightness: int):
        '''
        Set brightness.

        Args:
            brightness (int): Brightness to set.
        '''
        self.brightness = brightness
        self.i2c.write_byte_data(self.Register.BRIGHTNESS.value, brightness)

    def set_speed(self, speed: int):
        '''
        Set speed.

        Args:
            speed (int): Speed to set.
        '''
        self.speed = speed
        self.i2c.write_byte_data(self.Register.SPEED.value, speed)
