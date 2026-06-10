
from pm_auto.libs.addon import Addon
from ..libs.sunfounder_rgb_led import SunFounderRGBLED, RGB_STYLES, MAX_LEDS
from ..libs.utils import log_error

class SunFounderRGBLEDAddon(Addon):

    def __init__(self, *args, **kwargs):
        self.enable = False
        self.style = ""
        self.color = ""
        self.brightness = 0
        self.count = 0
        self.speed = 0

        super().__init__(*args, **kwargs)

        try:
            self.rgb = SunFounderRGBLED()
            self._is_ready = True
        except Exception as e:
            self.log.error(f"Failed to initialize SunFounderRGBLEDAddon: {e}")
            return

    @log_error
    def update_config(self, config, init=False):
        patch = {}
        if 'rgb_led_count' in config:
            _count = config['rgb_led_count']
            if not isinstance(_count, int):
                self.log.error("Invalid rgb_led_count")
            else:
                if _count < 1:
                    _count = 1
                if not init:
                    self.rgb.set_num(_count)
                self.count = _count
                patch['rgb_led_count'] = _count
                self.log.debug(f"Update LED count: {_count}")
        if 'rgb_enable' in config:
            _enable = config['rgb_enable']
            if not isinstance(_enable, bool):
                self.log.error(f"Invalid rgb_enable: {_enable}")
            else:
                if not init:
                    self.rgb.set_enable(_enable)
                self.enable = _enable
                patch['rgb_enable'] = _enable
                self.log.debug(f"Update RGB enable: {_enable}")
        if 'rgb_color' in config:
            _color = config['rgb_color']
            if not isinstance(_color, str):
                self.log.error(f"Invalid rgb_color: {_color}")
            else:
                if not init:
                    self.rgb.set_color(_color)
                self.color = _color
                patch['rgb_color'] = _color
                self.log.debug(f"Update RGB color: {_color}")
        if 'rgb_brightness' in config:
            _brightness = config['rgb_brightness']
            if not isinstance(_brightness, int):
                self.log.error(f"Invalid rgb_brightness: {_brightness}")
            else:
                if _brightness < 0:
                    _brightness = 0
                elif _brightness > 100:
                    _brightness = 100
                if not init:
                    self.rgb.set_brightness(_brightness)
                self.brightness = _brightness
                patch['rgb_brightness'] = _brightness
                self.log.debug(f"Update RGB brightness: {_brightness}")
        if 'rgb_speed' in config:
            _speed = config['rgb_speed']
            if not isinstance(_speed, int):
                self.log.error(f"Invalid rgb_speed: {_speed}")
            else:
                if _speed < 0:
                    _speed = 0
                elif _speed > 100:
                    _speed = 100
                if not init:
                    self.rgb.set_speed(_speed)
                self.speed = _speed
                patch['rgb_speed'] = _speed
                self.log.debug(f"Update RGB speed: {_speed}")
        if 'rgb_style' in config:
            _style = config['rgb_style']
            if not isinstance(_style, str) or _style not in RGB_STYLES:
                self.log.error(f"Invalid rgb_style: {_style}")
            else:
                if not init:
                    self.rgb.set_style(_style)
                self.style = _style
                patch['rgb_style'] = _style
                self.log.debug(f"Update RGB style: {_style}")
        return patch

    @log_error
    async def _start(self) -> None:
        self.log.info("RGB LED started")
        from ..libs.utils import hex_to_rgb
        import asyncio
        self.rgb.set_num(self.count)
        await asyncio.sleep(0.002)
        self.rgb.color = hex_to_rgb(self.color) if isinstance(self.color, str) else self.color
        self.rgb.brightness = self.brightness
        self.rgb.speed = self.speed
        self.rgb._write_rgb_block()
        await asyncio.sleep(0.002)
        self.rgb.set_style(self.style)
        self.rgb.set_enable(self.enable)

    @log_error
    async def _stop(self) -> None:
        self.rgb.set_enable(False)
        self.log.info("RGB LED stopped")
