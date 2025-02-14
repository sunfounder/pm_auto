from gpiozero import DigitalInputDevice

class VibrationSwitch:
    def __init__(self, config, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        self.device = None
        self.pin = None
        self.pull_up = True

        self.update_config(config)

    def set_debug_level(self, level):
        self.log.setLevel(level)

    def is_ready(self):
        return self._is_ready

    def update_config(self, config):
        if 'vibration_switch_pin' in config:
            self.pin = config['vibration_switch_pin']
        if 'vibration_switch_pull_up' in config:
            self.pull = config['vibration_switch_pull_up']
        if self.init_gpio():
            self._is_ready = True
        else:
            self._is_ready = False

    def init_gpio(self):
        if self.device is not None:
            self.device.close()
            self.device = None
        if self.pin is None:
            return False
        self.device = DigitalInputDevice(self.pin, pull_up=self.pull_up)
        return True

    def set_on_vabration_detected(self, func):
        self.device.when_activated = func

def test():
    import time
    vibration_switch = DigitalInputDevice(26, pull_up=False, bounce_time=0.01)
    vibration_switch.when_activated = lambda: print('Vibration detected')

    while True:
        time.sleep(1)

def test1():
    import time

    config = {
        'vibration_switch_pin': 26,
        'vibration_switch_pull_up': True
    }

    vibration_switch = VibrationSwitch(config)

    def on_vabration_detected():
        print('Vibration detected')

    vibration_switch.set_on_vabration_detected(on_vabration_detected)

    while True:
        time.sleep(1)


if __name__ == '__main__':
    test1()