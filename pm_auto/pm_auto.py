import time
import threading

from .libs.utils import has_common_items, log_error


app_name = 'pm_auto'

DEFAULT_CONFIG = {
    'rgb_led_count': 4,
    'rgb_enable': True,
    'rgb_color': '#ff00ff',
    'rgb_brightness': 100,
    'rgb_style': 'rainbow',
    'rgb_speed': 0,
    'oled_rotation': 0,
    'oled_disk': 'total',  # 'total' or the name of the disk, normally 'mmcblk0' for SD Card, 'nvme0n1' for NVMe SSD
    'oled_network_interface': 'all',  # 'all' or the name of the interface, normally 'wlan0' for WiFi, 'eth0' for Ethernet
    'oled_sleep': False,
    'oled_sleep_timeout': 10,
    'temperature_unit': 'C',
    'gpio_fan_mode': 1,
    'gpio_fan_led_pin': 5,
    "gpio_fan_pin": 6,
    'vibration_switch_pin': 26,
    'vibration_switch_pull_up': False,
}

class PMAuto():
    @log_error
    def __init__(self, config=DEFAULT_CONFIG, peripherals=[], get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False
        self.peripherals = peripherals

        self.oled = None
        self.ws2812 = None
        self.fan = None
        self.spc = None
        self.vibration_switch = None
        self.pironman_mcu = None

        if 'oled' in peripherals:
            from .services.oled_service import OLEDService
            self.log.debug("Initializing OLED service")
            self.oled = OLEDService(config, get_logger=get_logger)
            if not self.oled.is_ready():
                self.log.error("Failed to initialize OLED")
            else:
                self.log.debug("OLED service initialized")            
        if 'ws2812' in peripherals:
            self.log.debug("Initializing WS2812 service")
            from .services.ws2812_service import WS2812Service
            self.ws2812 = WS2812Service(config, get_logger=get_logger)
            if not self.ws2812.is_ready():
                self.log.error("Failed to initialize WS2812 service")
            else:
                self.log.debug("WS2812 service initialized")
        # if FANS in peripherals:
        if self.fan_enabled() or 'spc' in peripherals:
            self.log.debug("Initializing Fan service")
            from .services.fan_service import FanService
            self.fan = FanService(config, fans=peripherals, get_logger=get_logger)
            self.log.debug("Fan service initialized")
        if 'spc' in peripherals:
            self.log.debug("Initializing SPC service")
            from .services.spc_service import SPCService
            self.spc = SPCService(get_logger=get_logger)
            self.log.debug("SPC service initialized")
        if 'vibration_switch' in peripherals:
            self.log.debug("Initializing Vibration switch service")
            from .services.vibration_switch_service import VibrationSwitchService
            self.vibration_switch = VibrationSwitchService(config, get_logger=get_logger)
            self.vibration_switch.set_on_vabration_detected(self.wake_oled)
            self.log.debug("Vibration switch service initialized")
        if 'pironman_mcu' in peripherals:
            self.log.debug("Initializing Pironman MCU service")
            from.services.pironman_mcu_service import PironmanMCUService
            self.pironman_mcu = PironmanMCUService(config, get_logger=get_logger)
            self.pironman_mcu.set_on_wakeup(self.oled_button)
            self.pironman_mcu.set_on_shutdown(self.on_shutdown)
            self.log.debug("Pironman MCU service initialized")
        if 'pi5_pwr_btn' in peripherals:
            self.log.debug("Initializing Power button service")
            from .services.pi5_pwr_btn_service import Pi5PwrBtn
            self.pwr_btn = Pi5PwrBtn(grab=True)
            self.pwr_btn.set_button_callback(self.oled_button)
            self.pwr_btn.start()
            self.log.debug("Power button service initialized")

        self.__on_state_changed__ = None

    # @log_error
    # def wake_oled(self):
    #     self.log.info("Wake OLED")
    #     self.oled.wake()
    #     self.oled.button()

    @log_error
    def oled_button(self, button_state):
        self.oled.set_button(button_state)    

    @log_error
    def on_shutdown(self, reason):
        self.log.info(f"Auto Shutdown reason: {reason}")
        self.oled.show_shutdown_screen(reason)

    @log_error
    def fan_enabled(self):
        from .services.fan_service import FANS
        return has_common_items(FANS, self.peripherals)

    @log_error
    def set_debug_level(self, level):
        self.log.setLevel(level)
        if self.oled is not None:
            self.oled.set_debug_level(level)
        if self.ws2812 is not None:
            self.ws2812.set_debug_level(level)
        if self.fan is not None:
            self.fan.set_debug_level(level)
        if self.spc is not None:
            self.spc.set_debug_level(level)
        if self.vibration_switch is not None:
            self.vibration_switch.set_debug_level(level)
        if self.pironman_mcu is not None:
            self.pironman_mcu.set_debug_level(level)

    @log_error
    def set_on_state_changed(self, callback):
        self.__on_state_changed__ = callback
        self.fan.set_on_state_changed(callback)

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def update_config(self, config):
        self.log.debug(f"Update config: {config}")
        if 'oled' in self.peripherals:
            self.oled.update_config(config)
        if 'ws2812' in self.peripherals:
            self.ws2812.update_config(config)
        if self.fan_enabled():
            self.fan.update_config(config)
        if 'vibration_switch' in self.peripherals:
            self.vibration_switch.update_config(config)
        if 'pironman_mcu' in self.peripherals:
            self.pironman_mcu.update_config(config)

    @log_error
    def start(self):
        if self.oled is not None and self.oled.is_ready():
            self.oled.start()
        if self.ws2812 is not None and self.ws2812.is_ready():
            self.ws2812.start()
        if self.fan is not None:
            self.fan.start()
        if self.spc is not None and self.spc.is_ready():
            self.spc.start()
        if self.vibration_switch is not None:
            self.vibration_switch.start()
        if self.pironman_mcu is not None:
            self.pironman_mcu.start()

        self.log.info("PM Auto Start")

    @log_error
    def stop(self):
        if self.oled is not None and self.oled.is_ready():
            self.oled.stop()
        if self.ws2812 is not None and self.ws2812.is_ready():
            self.ws2812.stop()
        if self.fan is not None:
            self.fan.stop()
        if self.spc is not None and self.spc.is_ready():
            self.spc.stop()
        if self.vibration_switch is not None:
            self.vibration_switch.stop()
        if self.pironman_mcu is not None:
            self.pironman_mcu.stop()
        self.log.info("PM Auto stoped")

