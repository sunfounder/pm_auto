import time
import threading
from sf_rpi_status import shutdown

from .utils import has_common_items, log_error

from .fan_control import FanControl, FANS
from .vibration_switch import VibrationSwitch

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
        if 'oled' in peripherals:
            from .oled import OLED
            self.log.debug("Initializing OLED")
            self.oled = OLED(config, get_logger=get_logger)
            if not self.oled.is_ready():
                self.log.error("Failed to initialize OLED")
            else:
                self.log.debug("OLED initialized")            
        if 'ws2812' in peripherals:
            from .ws2812 import WS2812  
            self.ws2812 = WS2812(config, get_logger=get_logger)
            if not self.ws2812.is_ready():
                self.log.error("Failed to initialize WS2812")
            else:
                self.log.debug("WS2812 initialized")
                self.ws2812.start()
        # if FANS in peripherals:
        if self.fan_enabled() or 'spc' in peripherals:
            self.fan = FanControl(config, fans=peripherals, get_logger=get_logger)
        if 'spc' in peripherals:
            self.spc = SPCAuto(get_logger=get_logger)
        if 'vibration_switch' in peripherals:
            self.vibration_switch = VibrationSwitch(config, get_logger=get_logger)
            self.vibration_switch.set_on_vabration_detected(self.on_vabration_detected)

        self.interval = 1
    
        self.thread = None
        self.running = False

        self.__on_state_changed__ = None

    @log_error
    def on_vabration_detected(self):
        self.log.info("Vibration detected")
        self.oled.wake()

    @log_error
    def fan_enabled(self):
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

    @log_error
    def loop(self):
        while self.running:
            if self.oled is not None and self.oled.is_ready():
                self.oled.run()
            if self.fan is not None:
                self.fan.run()
            if self.spc is not None and self.spc.is_ready():
                self.spc.run()
            time.sleep(self.interval)

    @log_error
    def start(self):
        if self.running:
            self.log.warning("Already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()
        self.log.info("PM Auto Start")

    @log_error
    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
        if self.oled is not None and self.oled.is_ready():
            self.oled.close()
        if self.ws2812 is not None and self.ws2812.is_ready():
            self.ws2812.stop()
        if self.fan is not None:
            self.fan.close()
        self.log.info("PM Auto stoped")


class SPCAuto():
    @log_error
    def __init__(self, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        from spc.spc import SPC
        self.spc = SPC(get_logger=get_logger)
        if not self.spc.is_ready():
            self._is_ready = False
            return

        self._is_ready = True
        self.shutdown_request = 0
        self.is_plugged_in = False

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def handle_shutdown(self):
        if self.spc is None or not self.spc.is_ready():
            return

        shutdown_request = self.spc.read_shutdown_request()
        if shutdown_request != self.shutdown_request:
            self.shutdown_request = shutdown_request
            self.log.debug(f"Shutdown request: {shutdown_request}")
        if shutdown_request in self.spc.SHUTDOWN_REQUESTS:
            if shutdown_request == self.spc.SHUTDOWN_REQUEST_LOW_POWER:
                self.log.info('Low power shutdown.')
            elif shutdown_request == self.spc.SHUTDOWN_REQUEST_BUTTON:
                self.log.info('Button shutdown.')
            shutdown()

    @log_error
    def handle_external_input(self):
        if self.spc is None or not self.spc.is_ready():
            return

        if 'external_input' not in self.spc.device.peripherals:
            return

        if 'battery' not in self.spc.device.peripherals:
            return

        is_plugged_in = self.spc.read_is_plugged_in()
        if is_plugged_in != self.is_plugged_in:
            self.is_plugged_in = is_plugged_in
            if is_plugged_in == True:
                self.log.info(f"External input plug in")
            else:
                self.log.info(f"External input unplugged")
        if is_plugged_in == False:
            shutdown_pct = self.spc.read_shutdown_battery_pct()
            current_pct= self.spc.read_battery_percentage()
            if current_pct < shutdown_pct:
                self.log.info(f"Battery is below {shutdown_pct}, shutdown!", level="INFO")
                shutdown()

    @log_error
    def run(self):
        self.handle_external_input()
        self.handle_shutdown()
