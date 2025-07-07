import time
import threading
from ..libs.rgb_matrix import RGB_Matrix
from ..libs.utils import log_error
from ..libs.color import Color
import logging
from ..rgb_matrix_effects import get_effect, EFFECT_LIST, DEFAULT_EFFECT

RGB_MATRIX_DEFAULT_CONFIG = {
    'rgb_matrix_enable': True,
    'rgb_matrix_style': 'rainbow',
    'rgb_matrix_color': '#00ffff',
    'rgb_matrix_brightness': 100,  # 0-100
    'rgb_matrix_speed': 50,
}

class RGBMatrixService():

    @log_error
    def __init__(self, config, log=None):
        self.log = log or logging.getLogger(__name__)

        self._is_ready = False
        try:
            self.rgb_matrix = RGB_Matrix(0X74, width=8, height=4)
            self.rgb_matrix.clear()
            self.rgb_matrix.display()
        except Exception as e:
            self.log.error(f"Failed to initialize RGB Matrix")
            self.log.exception(e)
            return
        self._is_ready = True


        self.config = RGB_MATRIX_DEFAULT_CONFIG.copy()
        self.update_config(config)

        self.enable = self.config['rgb_matrix_enable']
        self.style = self.config['rgb_matrix_style']
        self.color = self.config['rgb_matrix_color']
        self.brightness = self.config['rgb_matrix_brightness']
        self.speed = self.config['rgb_matrix_speed']

        self.running = False
        self.thread = None

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def update_config(self, config):
        if 'rgb_matrix_enable' in config:
            _enable = bool(config['rgb_matrix_enable'])
            self.config['rgb_matrix_enable'] = _enable
            self.log.debug(f"Update RGB Matrix enable: {_enable}")
        if 'rgb_matrix_style' in config:
            if not isinstance(config['rgb_matrix_style'], str) or config['rgb_matrix_style'] not in EFFECT_LIST:
                self.log.error("Invalid rgb_matrix_style")
                return
            self.config['rgb_matrix_style'] = config['rgb_matrix_style']
            self.log.debug(f"Update RGB Matrix style: {self.config['rgb_matrix_style']}")
        if 'rgb_matrix_color' in config:
            if not isinstance(config['rgb_matrix_color'], str):
                self.log.error("Invalid rgb_matrix_color")
                return
            self.config['rgb_matrix_color'] = Color.hex_to_rgb(config['rgb_matrix_color'])
            self.log.debug(f"Update RGB Matrix color: {self.config['rgb_matrix_color']}")
        if 'rgb_matrix_brightness' in config:
            if not isinstance(config['rgb_matrix_brightness'], int):
                self.log.error("Invalid rgb_matrix_brightness")
                return
            self.config['rgb_matrix_brightness'] = config['rgb_matrix_brightness']
            self.log.debug(f"Update RGB Matrix brightness: {self.config['rgb_matrix_brightness']}")
        if 'rgb_matrix_speed' in config:
            if not isinstance(config['rgb_matrix_speed'], int):
                self.log.error("Invalid rgb_matrix_speed")
                return
            self.config['rgb_matrix_speed'] = config['rgb_matrix_speed']
            self.log.debug(f"Update RGB Matrix speed: {self.config['rgb_matrix_speed']}")


    @log_error
    def init_effect(self):
        if self.style not in EFFECT_LIST:
            self.log.warning(f'RGB_Matrix Style error, change to default effect {DEFAULT_EFFECT}. Style {self.style} not found, Choose from {EFFECT_LIST}')
            return
        return get_effect(self.style)
    
    @log_error
    def loop(self):
        effect = self.init_effect()

        self.running = True
        if not self.is_ready():
            self.log.error("RGB_Matrix Service not ready")
            return
        while self.running:
            if not self.enable:
                self.rgb_matrix.clear()
                self.rgb_matrix.display()
                time.sleep(1)
                continue
            try:
                if self.style not in EFFECT_LIST:
                    self.log.error(f'RGB_Matrix Style error: {self.style}')
                    time.sleep(5)
                    continue
                effect(self.rgb_matrix, self.config)
                time.sleep(.01)
            except Exception as e:
                self.log.error('RGB_Matrix Service error:')
                self.log.exception(e)
                time.sleep(5)

    @log_error
    def start(self):
        if self.running:
            self.log.warning("Already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    @log_error
    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
        self.rgb_matrix.clear()
        self.rgb_matrix.display()
        self.log.debug("RGB_Matrix Service stoped")

