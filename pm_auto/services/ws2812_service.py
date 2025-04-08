import time
import threading

# https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel_SPI
import board
import neopixel_spi as neopixel
from os import path

from ..libs.utils import map_value
from math import cos, pi

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

class WS2812Service():

    def __init__(self, config=default_config, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        self.led_count = 8
        self.color = None
        self.speed = None
        self.style = None
        self.enable = None
        self.brightness = None

        self.strip = None
        self.running = False
        self.thread = None
        self.counter = 0
        self.counter_max = 100

        if not path.exists('/dev/spidev0.0'):
            self.log.error("SPI not enabled")
        else:
            try:
                self.update_config(config)
                self.init()
            except Exception as e:
                self.log.error("Failed to initialize WS2812 Service: %s" % e)

    def set_debug_level(self, level):
        self.log.setLevel(level)

    def is_ready(self):
        return self._is_ready

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

    def update_config(self, config):
        if 'rgb_led_count' in config:
            if not isinstance(config['rgb_led_count'], int):
                self.log.error("Invalid rgb_led_count")
                return
            self.led_count = config['rgb_led_count']
            self.log.debug(f"Update LED count: {self.led_count}")
        if 'rgb_enable' in config:
            if not isinstance(config['rgb_enable'], bool):
                self.log.error("Invalid rgb_enable")
                return
            self.enable = config['rgb_enable']
            self.log.debug(f"Update RGB enable: {self.enable}")
        if 'rgb_color' in config:
            if not isinstance(config['rgb_color'], str):
                self.log.error("Invalid rgb_color")
                return
            self.color = self.hex_to_rgb(config['rgb_color'])
            self.log.debug(f"Update RGB color: {self.color}")
        if 'rgb_brightness' in config:
            if not isinstance(config['rgb_brightness'], int):
                self.log.error("Invalid rgb_brightness")
                return
            self.brightness = config['rgb_brightness']
            self.log.debug(f"Update RGB brightness: {self.brightness}")
        if 'rgb_speed' in config:
            if not isinstance(config['rgb_speed'], int):
                self.log.error("Invalid rgb_speed")
                return
            self.speed = config['rgb_speed']
            self.log.debug(f"Update RGB speed: {self.speed}")
        if 'rgb_style' in config:
            if not isinstance(config['rgb_style'], str) or config['rgb_style'] not in RGB_STYLES:
                self.log.error("Invalid rgb_style")
                return
            self.style = config['rgb_style']
            self.log.debug(f"Update RGB style: {self.style}")

    # str or hex, eg: 'ffffff', '#ffffff', '#FFFFFF'
    def hex_to_rgb(self, hex):
        try:
            hex = hex.strip().replace('#', '')
            r = int(hex[0:2], 16)
            g = int(hex[2:4], 16)
            b = int(hex[4:6], 16)
            return [r, g, b]
        except Exception as e:
            self.log('color parameter error: \n%s' % e)

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

    def clear(self):
        self.strip.fill(0)

    def fill(self, color:str='#000000'):
        self.strip.fill(color)

    def fill_pattern(self, pattern):
        for i in range(self.led_count):
            self.strip[i] = pattern[i]
        self.strip.show()

    def create_rainbow_pattern(self, num, offset=0):
        pattern = []
        for i in range(num):
            hue = i * 360.0 / num
            hue += offset
            pattern.append(hue)
        return pattern

    def create_gradient_pattern(self, num, offset=0):
        pattern = []
        for i in range(num):
            x = i / num * 2 * pi - pi
            brightness = cos(x + offset) * 50 + 50
            brightness = int(brightness)
            pattern.append(brightness)
            
        return pattern

    def loop(self):
        self.running = True
        self.counter = 0
        self.counter_max = 100
        if not self.is_ready():
            self.log.error("WS2812 Service not ready")
            return
        while self.running:
            if not self.enable:
                self.clear()
                self.strip.show()
                time.sleep(1)
                continue
            try:
                # self.log.debug(f"WS2812 style: {self.style}")
                if self.style in RGB_STYLES:
                    style_func = getattr(self, self.style)
                    style_func()
            except KeyError as e:
                self.log.error(f'Style error: {e}')
                time.sleep(5)
            except Exception as e:
                self.log.error(f'WS2812 Service error: {type(e)} {e}')
                time.sleep(5)
            self.counter += 1
            if self.counter >= self.counter_max:
                self.counter = 0

    def start(self):
        if self.running:
            self.log.warning("Already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
        self.clear()
        self.strip.show()
        self.log.debug("WS2812 Service stoped")

    # styles
    def solid(self):
        # self.log.debug(f"WS2812 Solid, color: {self.color}, brightness: {self.brightness}")
        color = [int(x * self.brightness * 0.01) for x in self.color]
        self.strip.fill(color)
        self.strip.show()
        time.sleep(1)

    def breathing(self):
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
        time.sleep(delay)

    def flow(self, order=None):
        # self.log.debug(f"WS2812 Flow, color: {self.color}, brightness: {self.brightness}, speed: {self.speed}")
        self.counter_max = self.led_count
        if self.counter >= self.counter_max:
            self.counter = 0
        delay = map_value(self.speed, 0, 100, 0.5, 0.1)
        color = [int(x * self.brightness * 0.01) for x in self.color]
        
        if order is None:
            order = range(self.led_count)

        self.strip.fill(0)
        index = order[self.counter]
        self.strip[index] = color
        self.strip.show()
        time.sleep(delay)

    def flow_reverse(self, order=None):
        if order is None:
            order = range(self.led_count)

        order = order[::-1]
        self.flow(order)

    def rainbow(self, reverse=False):
        # self.log.debug(f"WS2812 Rainbow, color: {self.color}, brightness: {self.brightness}, speed: {self.speed}")
        self.counter_max = 360
        if self.counter >= self.counter_max:
            self.counter = 0
        delay = map_value(self.speed, 0, 100, 0.1, 0.005)

        rainbow_pattern = self.create_rainbow_pattern(16, self.counter)
        leds = list(range(self.led_count))
        if reverse:
            leds.reverse()
        for i in leds:
            hue = rainbow_pattern[i]
            color = self.hsl_to_rgb(hue, 1, self.brightness * 0.01)
            self.strip[i] = color
        self.strip.show()

        time.sleep(delay)

    def rainbow_reverse(self):
        self.rainbow(reverse=True)

    def hue_cycle(self):
        # self.log.debug(f"WS2812 Hue Cycle, color: {self.color}, brightness: {self.brightness}, speed: {self.speed}")
        self.counter_max = 360
        if self.counter >= self.counter_max:
            self.counter = 0
        delay = map_value(self.speed, 0, 100, 0.1, 0.005)
        hue = self.counter
        color = self.hsl_to_rgb(hue, 1, self.brightness * 0.01)

        self.strip.fill(color)
        self.strip.show()
        time.sleep(delay)
