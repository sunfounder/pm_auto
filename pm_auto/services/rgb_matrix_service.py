import time
import threading

from ..libs.rgb_matrix import RGB_Matrix

RGB_MATRIX_STYLES = [
    'solid', 'breathing', 'rainbow', 'rotate', 'rotate_dual', 'rotate_hsv', 'rotate_hsv_2'
]

default_config = {
    'rgb_matrix_enable': True,
    'rgb_matrix_color': '#00ffff',
    'rgb_matrix_brightness': 100,  # 0-100
    'rgb_matrix_style': 'rainbow',
    'rgb_matrix_speed': 50,
}

class RGBMatrixService():

    def __init__(self, config=default_config, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        self.color = None
        self.speed = None
        self.style = None
        self.enable = None
        self.brightness = None

        self.rgb_matrix = None

        self.running = False
        self.thread = None

        try:
            # self.update_config(config)
            self.enable = True
            self.color = '00ffff'
            self.brightness = 100
            self.speed = 50
            self.style = 'rainbow'
            self.init()
        except Exception as e:
            self.log.error(f"Failed to init RGB Matrix: {e}")

    def set_debug_level(self, level):
        self.log.setLevel(level)

    def is_ready(self):
        return self._is_ready

    # def update_config(self, config):
    #     if 'rgb_enable' in config:
    #         if not isinstance(config['rgb_enable'], bool):
    #             self.log.error("Invalid rgb_enable")
    #             return
    #         self.enable = config['rgb_enable']
    #         self.log.debug(f"Update RGB enable: {self.enable}")
    #     if 'rgb_color' in config:
    #         if not isinstance(config['rgb_color'], str):
    #             self.log.error("Invalid rgb_color")
    #             return
    #         self.color = self.hex_to_rgb(config['rgb_color'])
    #         self.log.debug(f"Update RGB color: {self.color}")
    #     if 'rgb_brightness' in config:
    #         if not isinstance(config['rgb_brightness'], int):
    #             self.log.error("Invalid rgb_brightness")
    #             return
    #         self.brightness = config['rgb_brightness']
    #         self.log.debug(f"Update RGB brightness: {self.brightness}")
    #     if 'rgb_speed' in config:
    #         if not isinstance(config['rgb_speed'], int):
    #             self.log.error("Invalid rgb_speed")
    #             return
    #         self.speed = config['rgb_speed']
    #         self.log.debug(f"Update RGB speed: {self.speed}")
    #     if 'rgb_style' in config:
    #         if not isinstance(config['rgb_style'], str) or config['rgb_style'] not in RGB_STYLES:
    #             self.log.error("Invalid rgb_style")
    #             return
    #         self.style = config['rgb_style']
    #         self.log.debug(f"Update RGB style: {self.style}")

    def init(self):
        self.rgb_matrix = RGB_Matrix(0X74, width=8, height=4)
        self.rgb_matrix.clear()
        self.rgb_matrix.display()
        self._is_ready = True

    def loop(self):
        from ..rgb_matrix_effects.solid import solid
        from ..rgb_matrix_effects.breathing import breathing
        from ..rgb_matrix_effects.rainbow import rainbow
        from ..rgb_matrix_effects.rotate import roate
        from ..rgb_matrix_effects.rotate_dual import roate_dual
        from ..rgb_matrix_effects.rotate_hsv import roate_hsv
        from ..rgb_matrix_effects.rotate_hsv_2 import roate_hsv_2

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
                if self.style not in RGB_MATRIX_STYLES:
                    self.log.error(f'RGB_Matrix Style error: {self.style}')
                    time.sleep(5)
                    continue
                if self.style == 'solid':
                    solid(self.rgb_matrix, self.color)
                elif self.style == 'breathing':
                    breathing(self.rgb_matrix, self.color, 0.001)
                elif self.style == 'rainbow':
                    rainbow(self.rgb_matrix)
                elif self.style == 'rotate':
                    roate(self.rgb_matrix)
                elif self.style == 'rotate_dual':
                    roate_dual(self.rgb_matrix)
                elif self.style == 'rotate_hsv':
                    roate_hsv(self.rgb_matrix)
                elif  self.style == 'rotate_hsv_2':
                    roate_hsv_2(self.rgb_matrix)
                time.sleep(.01)
            except Exception as e:
                self.log.error(f'RGB_Matrix Service error: {type(e)} {e}')
                time.sleep(5)

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
        self.rgb_matrix.clear()
        self.rgb_matrix.display()
        self.log.debug("RGB_Matrix Service stoped")

