from pm_auto.libs.addon import Addon
from pm_auto.libs.rgb_matrix import RGB_Matrix
from pm_auto.libs.utils import log_error
from pm_auto.libs.color import Color

from .effects import get_effect, EFFECT_LIST, DEFAULT_EFFECT

import asyncio

class RGBMatrixAddon(Addon):

    DEFAULT_CONFIG = {
        'rgb_matrix_enable': True,
        'rgb_matrix_style': 'rainbow',
        'rgb_matrix_color': '#ff0000',
        'rgb_matrix_color2': '#0000ff',
        'rgb_matrix_brightness': 100,  # 0-100
        'rgb_matrix_speed': 50,
    }

    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.rgb_matrix = RGB_Matrix(0X74, width=8, height=4)
            self.rgb_matrix.clear()
            self.rgb_matrix.display()
        except Exception as e:
            self.log.error(f"Failed to initialize RGB Matrix")
            self.log.exception(e)
            return
        self._is_ready = True

    @log_error
    def update_config(self, config, init=False):
        '''
        Update config.

        Args:
            config (Dict): New config dict.

        Returns:
            A dict of config patch to update the config file.
        '''
        patch = {}
        if 'rgb_matrix_enable' in config:
            _enable = bool(config['rgb_matrix_enable'])
            self.enable = _enable
            patch['rgb_matrix_enable'] = _enable
            self.log.debug(f"Update RGB Matrix enable: {_enable}")
        if 'rgb_matrix_style' in config:
            _style = config['rgb_matrix_style']
            if not isinstance(_style, str) or _style not in EFFECT_LIST:
                self.log.error("Invalid rgb_matrix_style")
            else:
                self.style = _style
                patch['rgb_matrix_style'] = _style
                self.log.debug(f"Update RGB Matrix style: {self.style}")
        if 'rgb_matrix_color' in config:
            _color = config['rgb_matrix_color']
            if not isinstance(_color, str):
                self.log.error("Invalid rgb_matrix_color")
            else:
                # self.color = _color
                self.color = Color().hex_to_rgb(_color)
                patch['rgb_matrix_color'] = _color
                self.log.debug(f"Update RGB Matrix color: {self.color}")
        if 'rgb_matrix_color2' in config:
            _color2 = config['rgb_matrix_color2']
            if not isinstance(_color2, str):
                self.log.error("Invalid rgb_matrix_color2")
            else:
                # self.color2 = _color2
                self.color2 = Color().hex_to_rgb(_color2)
                patch['rgb_matrix_color2'] = _color2
                self.log.debug(f"Update RGB Matrix color2: {self.color2}")
        if 'rgb_matrix_brightness' in config:
            _brightness = config['rgb_matrix_brightness']
            if not isinstance(_brightness, int):
                self.log.error("Invalid rgb_matrix_brightness")
            else:
                self.brightness = _brightness
                patch['rgb_matrix_brightness'] = _brightness
                self.log.debug(f"Update RGB Matrix brightness: {self.brightness}")
        if 'rgb_matrix_speed' in config:
            _speed = config['rgb_matrix_speed']
            if not isinstance(_speed, int):
                self.log.error("Invalid rgb_matrix_speed")
            else:
                self.speed = _speed
                patch['rgb_matrix_speed'] = _speed
                self.log.debug(f"Update RGB Matrix speed: {self.speed}")
        return patch

    @log_error
    def init_effect(self):
        if self.style not in EFFECT_LIST:
            self.log.warning(f'RGB_Matrix Style error, change to default effect {DEFAULT_EFFECT}. Style {self.style} not found, Choose from {EFFECT_LIST}')
            return
        return get_effect(self.style)
    
    @log_error
    async def _main(self):

        self.running = True
        if not self.is_ready():
            self.log.error("RGB_Matrix Service not ready")
            return
        while self.running:
            if not self.enable:
                self.rgb_matrix.clear()
                self.rgb_matrix.display()
                await asyncio.sleep(1)
                continue
            try:
                if self.style not in EFFECT_LIST:
                    self.log.error(f'RGB_Matrix Style error: {self.style}')
                    await asyncio.sleep(5)
                    continue
                effect = self.init_effect()
                effect(self, self.rgb_matrix)
                await asyncio.sleep(.01)
            except Exception as e:
                self.log.error('RGB_Matrix Service error:')
                self.log.exception(e)
                await asyncio.sleep(5)

    @log_error
    async def _stop(self):
        self.rgb_matrix.clear()
        self.rgb_matrix.display()

