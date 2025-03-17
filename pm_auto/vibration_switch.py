from gpiozero import DigitalInputDevice
from .utils import log_error

class VibrationSwitch:
    def __init__(self, config, get_logger=None):

        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        self.log.info("Initializing VibrationSwitch")

        self.device = None
        self.pin = None
        self.pull_up = True

        self.update_config(config)
        self.log.info("VibrationSwitch initialized")

        self.when_activated = None

    @log_error
    def set_debug_level(self, level):
        self.log.setLevel(level)

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def update_config(self, config):
        updated = False
        if 'vibration_switch_pin' in config:
            self.pin = config['vibration_switch_pin']
            updated = True
        if 'vibration_switch_pull_up' in config:
            self.pull = config['vibration_switch_pull_up']
            updated = True
        if updated:
            if self.init_gpio():
                self._is_ready = True
            else:
                self._is_ready = False

    @log_error
    def init_gpio(self):
        if self.device is not None:
            self.device.close()
            self.device = None
        if self.pin is None:
            return False
        self.log.info(f"Initializing VibrationSwitch on pin {self.pin} with pull_up={self.pull_up}")
        self.device = DigitalInputDevice(self.pin, pull_up=self.pull_up)
        if self.when_activated is not None:
            self.device.when_activated = self.when_activated
        return True

    @log_error
    def set_on_vabration_detected(self, func):
        self.when_activated = func
        self.device.when_activated = func
