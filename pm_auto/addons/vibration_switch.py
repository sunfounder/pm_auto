from pm_auto.libs.addon import Addon
from pm_auto.libs.utils import log_error, softlink_gpiochip0_to_gpiochip4

class VibrationSwitchAddon(Addon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.device = None
        self.pin = None
        self.pull_up = True

        self.update_config(config)

    @log_error
    def update_config(self, config):
        '''
        Update config.

        Args:
            config (Dict): New config dict.

        Returns:
            A dict of config patch to update the config file.
        '''
        patch = {}
        updated = False
        _pin = None
        _pull_up = None
        if 'vibration_switch_pin' in config:
            _pin = config['vibration_switch_pin']
            updated = True
        if 'vibration_switch_pull_up' in config:
            _pull_up = config['vibration_switch_pull_up']
            updated = True
        if updated:
            if self.init_gpio(_pin, _pull_up):
                self._is_ready = True
                self.pin = _pin or self.pin
                self.pull_up = _pull_up or self.pull_up
                patch['vibration_switch_pin'] = self.pin
                patch['vibration_switch_pull_up'] = self.pull_up
                self.log.info(f"VibrationSwitch pin: {self.pin}, pull_up: {self.pull_up}")
            else:
                self._is_ready = False
                self.log.error(f"Failed to initialize VibrationSwitch on pin {_pin} with pull_up={_pull_up}")
        return patch

    @log_error
    def init_gpio(self, pin=None, pull_up=None):
        pin = pin or self.pin
        pull_up = pull_up or self.pull_up

        from gpiozero import DigitalInputDevice
        try:
            # Fix gpiozero reads gpiochip4 while new kernel changed to gpiochip0
            softlink_gpiochip0_to_gpiochip4()

            if self.device is not None:
                self.device.close()
                self.device = None
            if pin is None:
                return False
            self.log.info(f"Initializing VibrationSwitch on pin {pin} with pull_up={pull_up}")
            self.device = DigitalInputDevice(pin, pull_up=pull_up)
            self.device.when_activated = self.when_activated
            return True
        except Exception as e:
            self.log.error(f"Failed to initialize VibrationSwitch: {e}")
            return False

    @log_error
    def when_activated(self):
        self.event.publish('vibration_detected')

    @log_error
    async def start(self):
        # No need to start
        pass

    @log_error
    async def stop(self):
        if self.device is not None:
            self.device.close()
