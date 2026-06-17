
from pm_auto.libs.addon import Addon
from pm_auto.libs.utils import map_value, log_error

# https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel_SPI
import board
import neopixel_spi as neopixel
from os import path

from math import cos, pi
import time
import asyncio


RGB_STYLES = [
    'solid', 'breathing', 'flow', 'flow_reverse', 'rainbow', 'rainbow_reverse', 'hue_cycle'
]

default_config = {
    'rgb_led_count': 4,
    'rgb_enable': True,
    'rgb_color': '#00ffff',
    'rgb_brightness': 100,  # 0-100
    'rgb_style': 'breath',
    'rgb_speed': 50,
}

class WS2812Addon(Addon):

    def __init__(self, *args, **kwargs):
        self.position = []
        super().__init__(*args, **kwargs)

        self.strip = None
        self.counter = 0
        self.counter_max = 100

        if not path.exists('/dev/spidev0.0'):
            self.log.error("SPI not enabled")
        else:
            try:
                self.init()
            except Exception as e:
                self.log.error("Failed to initialize WS2812 Service: %s" % e)

    @log_error
    def init(self):
        spi = board.SPI()
        PIXEL_ORDER = neopixel.GRB

        self.strip = neopixel.NeoPixel_SPI(
                spi, self.led_count, pixel_order=PIXEL_ORDER, auto_write=False
        )
        time.sleep(0.01)
        self.strip.fill(0)
        self.strip.show()
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
                if 'rgb_led_count_min' in self.config and _count < self.config['rgb_led_count_min']:
                    _count = self.config['rgb_led_count_min']
                    self.log.warning(f"rgb_led_count {_count} too small, available led count: >= {self.config['rgb_led_count_min']}")
                self.led_count = _count
                if len(self.position) == 0:
                    self.position = list(range(self.led_count))
                patch['rgb_led_count'] = self.led_count
                self.log.debug(f"Update LED count: {self.led_count}")
        if 'rgb_enable' in config:
            _enable = config['rgb_enable']
            if not isinstance(_enable, bool):
                self.log.error(f"Invalid rgb_enable: {_enable}")
            else:
                self.enable = _enable
                patch['rgb_enable'] = self.enable
                self.log.debug(f"Update RGB enable: {self.enable}")
        if 'rgb_color' in config:
            _color = config['rgb_color']
            if not isinstance(_color, str):
                self.log.error(f"Invalid rgb_color: {_color}")
            else:
                self.color = self.hex_to_rgb(_color)
                patch['rgb_color'] = _color
                self.log.debug(f"Update RGB color: {_color}")
        if 'rgb_brightness' in config:
            _brightness = config['rgb_brightness']
            if not isinstance(_brightness, int):
                self.log.error(f"Invalid rgb_brightness: {_brightness}")
            else:
                self.brightness = _brightness
                patch['rgb_brightness'] = self.brightness
                self.log.debug(f"Update RGB brightness: {self.brightness}")
        if 'rgb_speed' in config:
            _speed = config['rgb_speed']
            if not isinstance(_speed, int):
                self.log.error(f"Invalid rgb_speed: {_speed}")
            else:
                self.speed = _speed
                patch['rgb_speed'] = self.speed
                self.log.debug(f"Update RGB speed: {self.speed}")
        if 'rgb_style' in config:
            _style = config['rgb_style']
            if not isinstance(_style, str) or _style not in RGB_STYLES:
                self.log.error(f"Invalid rgb_style: {_style}")
            else:
                self.style = _style
                patch['rgb_style'] = self.style
                self.log.debug(f"Update RGB style: {self.style}")
        if 'rgb_position' in config:
            _position = config['rgb_position']
            if not isinstance(_position, list):
                self.log.error(f"Invalid rgb_position: {_position}")
            else:
                self.position = list(_position)
                if len(_position) != self.led_count:
                    self.position += [i for i in range(self.led_count) if i not in self.position]
                patch['rgb_position'] = self.position
                self.log.debug(f"Update RGB position: {self.position}")
        return patch


    @log_error
    def hex_to_rgb(self, hex):
        ''' str or hex, eg: 'ffffff', '#ffffff', '#FFFFFF' '''
        try:
            hex = hex.strip().replace('#', '')
            r = int(hex[0:2], 16)
            g = int(hex[2:4], 16)
            b = int(hex[4:6], 16)
            return [r, g, b]
        except Exception as e:
            self.log.error('Color parameter error:')
            self.log.exception(e)

    @log_error
    def hsl_to_rgb(self, hue, saturation=1, brightness=1):
        hue = hue % 360
        _hi = int((hue/60)%6)
        _f = hue / 60.0 - _hi
        _p = brightness * (1 - saturation)
        _q = brightness * (1 - _f * saturation)
        _t = brightness * (1 - (1 - _f) * saturation)
        
        if _hi == 0:
            _R_val = brightness
            _G_val = _t
            _B_val = _p
        if _hi == 1:
            _R_val = _q
            _G_val = brightness
            _B_val = _p
        if _hi == 2:
            _R_val = _p
            _G_val = brightness
            _B_val = _t
        if _hi == 3:
            _R_val = _p
            _G_val = _q
            _B_val = brightness
        if _hi == 4:
            _R_val = _t
            _G_val = _p
            _B_val = brightness
        if _hi == 5:
            _R_val = brightness
            _G_val = _p
            _B_val = _q
        
        r = int(_R_val * 255)
        g = int(_G_val * 255)
        b = int(_B_val * 255)
        return (r, g, b)

    @log_error
    def clear(self):
        self.strip.fill(0)

    @log_error
    def fill(self, color:str='#000000'):
        self.strip.fill(color)

    @log_error
    def fill_pattern(self, pattern):
        for i in range(self.led_count):
            self.strip[i] = pattern[i]
        self.strip.show()

    @log_error
    def create_rainbow_pattern(self, num, offset=0):
        '''
        Create a rainbow pattern with num LEDs.
        
        Args:
            num (int): Number of LEDs in the pattern.
            offset (float, optional): Offset for the hue value. Defaults to 0.
        
        Returns:
            list: A list of hue values for each LED in the pattern.
        '''
        pattern = []
        for i in range(num):
            hue = i * 360.0 / num
            hue += offset
            pattern.append(hue)
        return pattern

    @log_error
    def create_gradient_pattern(self, num, offset=0):
        pattern = []
        for i in range(num):
            x = i / num * 2 * pi - pi
            brightness = cos(x + offset) * 50 + 50
            brightness = int(brightness)
            pattern.append(brightness)
            
        return pattern

    @log_error
    async def _main(self):
        self.counter = 0
        self.counter_max = 100

        while self.running:
            if not self.enable:
                self.clear()
                self.strip.show()
                await asyncio.sleep(1)
                continue
            try:
                if self.style in RGB_STYLES:
                    style_func = getattr(self, self.style)
                    await style_func()
            except KeyError as e:
                self.log.error(f'Style error: {self.style}')
                await asyncio.sleep(5)
            except Exception as e:
                self.log.error(f'WS2812 Service error:')
                self.log.exception(e)
                await asyncio.sleep(5)
            self.counter += 1
            if self.counter >= self.counter_max:
                self.counter = 0

    @log_error
    async def _stop(self):
        self.clear()
        self.strip.show()

    # styles
    async def solid(self):

        # self.log.debug(f"WS2812 Solid, color: {self.color}, brightness: {self.brightness}")
        color = [int(x * self.brightness * 0.01) for x in self.color]
        self.strip.fill(color)
        self.strip.show()
        await asyncio.sleep(1)

    async def breathing(self):
        # self.log.debug(f"WS2812 Breathing, color: {self.color}, brightness: {self.brightness}, speed: {self.speed}")
        self.counter_max = 200
        if self.counter >= self.counter_max:
            self.counter = 0
        # Map speed(0-100) to delay
        delay = map_value(self.speed, 0, 100, 0.1, 0.001)
        # Re calculate color with nrightness
        color = [int(x * self.brightness * 0.01) for x in self.color]

        if self.counter < 100:
            i = self.counter
            r, g, b = [int(x * i * 0.01) for x in color]
        else:
            i = 200 - self.counter
            r, g, b = [int(x * i * 0.01) for x in color]
        self.strip.fill((r, g, b))
        self.strip.show()
        await asyncio.sleep(delay)

    async def flow(self, reverse=False):
        '''
        Flow effect.
        
        Args:
            reverse (bool, optional): Whether to reverse the flow direction. Defaults to False.
        '''
        # self.log.debug(f"WS2812 Flow, color: {self.color}, brightness: {self.brightness}, speed: {self.speed}")
        self.counter_max = self.led_count
        if self.counter >= self.counter_max:
            self.counter = 0
        delay = map_value(self.speed, 0, 100, 0.5, 0.1)
        color = [int(x * self.brightness * 0.01) for x in self.color]
        
        order = list(self.position)
        if reverse:
            order.reverse()

        self.strip.fill(0)
        index = order[self.counter]
        self.strip[index] = color
        self.strip.show()
        await asyncio.sleep(delay)

    async def flow_reverse(self):
        '''
        Flow effect in reverse direction.
        '''
        await self.flow(reverse=True)

    async def rainbow(self, reverse=False):
        '''
        Rainbow effect.
        
        Args:
            reverse (bool, optional): Whether to reverse the rainbow direction. Defaults to False.
        '''
        # self.log.debug(f"WS2812 Rainbow, color: {self.color}, brightness: {self.brightness}, speed: {self.speed}")
        self.counter_max = 360
        if self.counter >= self.counter_max:
            self.counter = 0
        delay = map_value(self.speed, 0, 100, 0.1, 0.005)

        rainbow_pattern = self.create_rainbow_pattern(self.led_count, self.counter)
        order = list(self.position)
        if reverse:
            order.reverse()
        for i, led in enumerate(order):
            hue = rainbow_pattern[i]
            color = self.hsl_to_rgb(hue, 1, self.brightness * 0.01)
            self.strip[led] = color
        self.strip.show()

        await asyncio.sleep(delay)

    async def rainbow_reverse(self):
        await self.rainbow(reverse=True)

    async def hue_cycle(self):
        # self.log.debug(f"WS2812 Hue Cycle, color: {self.color}, brightness: {self.brightness}, speed: {self.speed}")
        self.counter_max = 360
        if self.counter >= self.counter_max:
            self.counter = 0
        delay = map_value(self.speed, 0, 100, 0.1, 0.005)
        hue = self.counter
        color = self.hsl_to_rgb(hue, 1, self.brightness * 0.01)

        self.strip.fill(color)
        self.strip.show()
        await asyncio.sleep(delay)
