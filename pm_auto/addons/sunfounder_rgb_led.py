
from enum import Enum

from pm_auto.libs.addon import Addon
from ..libs.i2c import I2C
from ..libs.utils import hex_to_rgb

RGB_STYLES = [
    'solid', 'breathing', 'flow', 'flow_reverse', 'rainbow', 'rainbow_reverse', 'hue_cycle'
]



class SunFounderRGBLEDAddon(Addon):
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
        super().__init__(*args, **kwargs)

        self.i2c = I2C(self.ADDRESS)
        if self.i2c.is_ready():
            self._is_ready = True
        
    @log_error
    def update_config(self, config, init=False):

        '''
        Update config.

        Args:
            config (Dict): New config dict.
            init (bool): True if init, False otherwise.

        Returns:
            A dict of config patch to update the config file.
        '''
        patch = {}
        if 'rgb_led_count' in config:
            _count = config['rgb_led_count']
            if not isinstance(_count, int):
                self.log.error("Invalid rgb_led_count")
            else:
                self.led_count = _count
                self.set_num(self.led_count)
                patch['rgb_led_count'] = self.led_count
                self.log.debug(f"Update LED count: {self.led_count}")
        if 'rgb_enable' in config:
            _enable = config['rgb_enable']
            if not isinstance(_enable, bool):
                self.log.error(f"Invalid rgb_enable: {_enable}")
            else:
                self.enable = _enable
                if not self.enable:
                    self.set_mode(self.style)
                else:
                    self.set_mode(self.Mode.OFF)
                patch['rgb_enable'] = self.enable
                self.log.debug(f"Update RGB enable: {self.enable}")
        if 'rgb_color' in config:
            _color = config['rgb_color']
            if not isinstance(_color, str):
                self.log.error(f"Invalid rgb_color: {_color}")
            else:
                self.color = self.hex_to_rgb(_color)
                self.set_color(self.color)
                patch['rgb_color'] = _color
                self.log.debug(f"Update RGB color: {_color}")
        if 'rgb_brightness' in config:
            _brightness = config['rgb_brightness']
            if not isinstance(_brightness, int):
                self.log.error(f"Invalid rgb_brightness: {_brightness}")
            else:
                self.brightness = _brightness
                self.set_brightness(self.brightness)
                patch['rgb_brightness'] = self.brightness
                self.log.debug(f"Update RGB brightness: {self.brightness}")
        if 'rgb_speed' in config:
            _speed = config['rgb_speed']
            if not isinstance(_speed, int):
                self.log.error(f"Invalid rgb_speed: {_speed}")
            else:
                self.speed = _speed
                self.set_speed(self.speed)
                patch['rgb_speed'] = self.speed
                self.log.debug(f"Update RGB speed: {self.speed}")
        if 'rgb_style' in config:
            _style = config['rgb_style']
            if not isinstance(_style, str) or _style not in RGB_STYLES:
                self.log.error(f"Invalid rgb_style: {_style}")
            else:
                self.style = _style
                self.set_mode(self.Mode[self.style.upper()])
                patch['rgb_style'] = self.style
                self.log.debug(f"Update RGB style: {self.style}")
        return patch

    def set_mode(self, mode: Mode):
        '''
        Set mode.

        Args:
            mode (Mode): Mode to set.
        '''
        self.i2c.write_byte_data(self.Register.MODE.value, mode.value)

    def set_num(self, num: int):
        '''
        Set LED number.

        Args:
            num (int): LED number to set.
        '''
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
        self.i2c.write_i2c_block_data(self.Register.RED.value, color)

    def set_brightness(self, brightness: int):
        '''
        Set brightness.

        Args:
            brightness (int): Brightness to set.
        '''
        self.i2c.write_byte_data(self.Register.BRIGHTNESS.value, brightness)
