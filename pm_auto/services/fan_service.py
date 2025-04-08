import logging
import subprocess
import os
import time
import threading

from ..libs.utils import run_command, log_error

default_config = {
    "gpio_fan_pin": 6,
    "gpio_fan_led_pin": 5,
    "gpio_fan_led": 'follow',
    "gpio_fan_mode": 1,
}

FANS = [
    'pwm_fan', # Deprecated
    'gpio_fan', # Deprecated
    'spc_fan', # Deprecated
    'pwm_fan_speed',
    'gpio_fan_state',
    'gpio_fan_led',
    'spc_fan_power'
]
# 5个风扇驱动等级，从高到低
GPIO_FAN_MODES = ['Always On', 'Performance', 'Cool', 'Balanced', 'Quiet']
FAN_LEVELS = [
    {
        "name": "OFF",
        "low": -200,
        "high": 55,
        "percent": 0,
    }, {
        "name": "LOW",
        "low": 45,
        "high": 65,
        "percent": 40,
    }, {
        "name": "MEDIUM",
        "low": 55,
        "high": 75,
        "percent": 80,
    }, {
        "name": "HIGH",
        "low": 65,
        "high": 100,
        "percent": 100,
    },
]

INTERVAL = 1

class FanService:
    @log_error
    def __init__(self, config, fans=[], get_logger=None):
        if get_logger is None:
            get_logger = logging.getLogger
        self.log = get_logger(__name__)

        self.gpio_fan = Fan()
        self.spc_fan = Fan()
        self.pwm_fan = Fan()
        self.config = default_config

        self.temperature_unit = 'C'
        self.interval = 1
        self.update_config(config)

        if 'gpio_fan_state' in fans or 'gpio_fan' in fans: # gpio_fan is deprecated, use gpio_fan_state instead
            pin = self.config["gpio_fan_pin"]
            if 'gpio_fan_led' in fans:
                led_pin = self.config["gpio_fan_led_pin"]
                self.log.debug(f"Init GPIO Fan with pin: {pin}, led_pin: {led_pin}")
                self.gpio_fan = GPIOFan(pin, led_pin=led_pin, log=self.log)
                self.gpio_fan.set_led(self.config["gpio_fan_led"])
            else:
                self.log.debug(f"Init GPIO Fan with pin: {pin}")
                self.gpio_fan = GPIOFan(pin, log=self.log)
            if not self.gpio_fan.is_ready():
                self.log.warning("GPIO Fan init failed, disable gpio_fan control")
        if 'spc_fan_power' in fans or 'spc_fan' in fans: # spc_fan is deprecated, use spc_fan_power instead
            self.log.debug("Init SPC Fan")
            self.spc_fan = SPCFan(log=self.log)
            if not self.spc_fan.is_ready():
                self.log.warning("SPC Fan init failed, disable spc_fan control")
        if 'pwm_fan_speed' in fans or 'pwm_fan' in fans: # pwm_fan is deprecated, use pwm_fan_speed instead
            self.log.debug("Init PWM Fan")
            self.pwm_fan = PWMFan(log=self.log)
            if not self.pwm_fan.is_ready():
                self.log.warning("PWM Fan init failed, disable pwm_fan control")

        self.level = 0
        self.initial = True
        self.__on_state_changed__ = lambda x: None
        self.running = False
        self.thread = None

    def set_debug_level(self, level):
        self.log.setLevel(level)

    @log_error
    def set_on_state_changed(self, callback):
        self.__on_state_changed__ = callback

    @log_error
    def update_config(self, config):
        if "gpio_fan_pin" in config:
            self.log.debug(f"Update gpio_fan_pin to {config['gpio_fan_pin']}")
            self.config["gpio_fan_pin"] = config["gpio_fan_pin"]
            if self.gpio_fan.is_ready():
                self.gpio_fan.change_pin(config["gpio_fan_pin"])
        if "gpio_fan_mode" in config:
            self.log.debug(f"Update gpio_fan_mode to {config['gpio_fan_mode']}")
            self.config["gpio_fan_mode"] = config["gpio_fan_mode"]
        if "gpio_fan_led" in config:
            self.log.debug(f"Update gpio_fan_led to {config['gpio_fan_led']}")
            self.config["gpio_fan_led"] = config["gpio_fan_led"]
            if self.gpio_fan.is_ready():
                self.gpio_fan.set_led(config["gpio_fan_led"])
        if "gpio_fan_led_pin" in config:
            self.log.debug(f"Update gpio_fan_led_pin to {config['gpio_fan_led_pin']}")
            self.config["gpio_fan_led_pin"] = config["gpio_fan_led_pin"]
            if self.gpio_fan.is_ready():
                self.gpio_fan.change_led_pin(config["gpio_fan_led_pin"])

    @log_error
    def get_cpu_temperature(self):
        file = '/sys/class/thermal/thermal_zone0/temp'
        try:
            with open(file, 'r') as f:
                temp = int(f.read())
            return round(temp/1000, 2)
        except Exception as e:
            self.log.error(f'get_cpu_temperature error: {e}')
            return 0.0

    @log_error
    def run(self):
        state = {}
        if self.pwm_fan.is_ready() and self.pwm_fan.is_supported():
            if self.initial:
                self.log.info("PWM Fan is supported, sync all other fan with pwm fan")
                self.initial = False
            # Sync all other fan with pwm fan
            pwm_fan_speed = self.pwm_fan.get_speed()
            state["pwm_fan_speed"] = pwm_fan_speed
            pwm_fan_level = self.pwm_fan.get_state()
            if self.spc_fan.is_ready():
                spc_fan_power = FAN_LEVELS[pwm_fan_level]['percent']
                self.spc_fan.set_power(spc_fan_power)
                state["spc_fan_power"] = spc_fan_power
            if self.gpio_fan.is_ready():
                gpio_fan_state = pwm_fan_level >= self.config['gpio_fan_mode']
                state["gpio_fan_state"] = gpio_fan_state
                self.gpio_fan.set(gpio_fan_state)
        else:
            temperature = self.get_cpu_temperature()
            self.log.debug(f"cpu temperature: {temperature} \"C")
            changed = False
            direction = ""
            if temperature < FAN_LEVELS[self.level]["low"]:
                self.level -= 1
                changed = True
                direction = "low"
            elif temperature > FAN_LEVELS[self.level]["high"]:
                self.level += 1
                changed = True
                direction = "high"
            
            self.level = max(0, min(self.level, len(FAN_LEVELS) - 1))
            power = FAN_LEVELS[self.level]['percent']

            if self.gpio_fan.is_ready():
                gpio_fan_state = self.level >= self.config['gpio_fan_mode']
                state['gpio_fan_state'] = gpio_fan_state
                self.gpio_fan.set(gpio_fan_state)
            if self.spc_fan.is_ready():
                self.spc_fan.set_power(power)
                state['spc_fan_power'] = power
            if self.pwm_fan.is_ready():
                self.pwm_fan.set_state(self.level)
                state['pwm_fan_speed'] = self.pwm_fan.get_speed()

            if changed:
                self.log.info(f"set fan level: {FAN_LEVELS[self.level]['name']}")
                self.log.info(f"set fan power: {power}")
                self.log.info(
                    f"cpu temperature: {temperature} \"C, {direction}er than {FAN_LEVELS[self.level][direction]}")
            elif self.initial:
                self.log.info(f"cpu temperature: {temperature} \"C")
                self.initial = False
        
        self.__on_state_changed__(state)

    @log_error
    def loop(self):
        while self.running:
            self.run()
            time.sleep(self.interval)

    @log_error
    def off(self):
        if self.gpio_fan.is_ready():
            self.gpio_fan.off()
        if self.spc_fan.is_ready():
            self.spc_fan.off()
        if self.pwm_fan.is_ready():
            self.pwm_fan.off()

    @log_error
    def close(self):
        if self.gpio_fan.is_ready():
            self.gpio_fan.close()
        if self.spc_fan.is_ready():
            self.spc_fan.close()
        if self.pwm_fan.is_ready():
            self.pwm_fan.close()
        self.log.debug("FanService closed")

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
        self.off()
        self.close()

def check_ready(func):
    def wrapper(self, *args, **kwargs):
        if not self.is_ready():
            self.log.warning(f"{self.__class__.__name__} is not ready")
            return
        return func(self, *args, **kwargs)
    return wrapper

class Fan():
    def __init__(self, log=None):
        self.log = log
        self._is_ready = False

    def is_ready(self):
        return self._is_ready
    
    # Decorator to check if the fan is ready
class GPIOFan(Fan):
    def __init__(self, pin, *args, led_pin=None, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            import gpiozero
            self.pin = pin
            self.fan = gpiozero.DigitalOutputDevice(pin)
            self.led = None
            self.led_follow = False
            if led_pin is not None:
                self.led = gpiozero.DigitalOutputDevice(led_pin)
                self.led.value = 0
            self._is_ready = True
        except Exception as e:
            self.log.error(f"GPIO Fan init error: {e}")
            self._is_ready = False

    def change_pin(self, pin):
        self.fan.close()
        self.pin = pin
        try:
            import gpiozero
            self.fan = gpiozero.DigitalOutputDevice(pin)
            self._is_ready = True
        except Exception as e:
            self.log.error(f"Change pin error: {e}")
            self._is_ready = False

    def change_led_pin(self, led_pin):
        self.led.close()
        self.led_pin = led_pin
        try:
            import gpiozero
            self.led = gpiozero.DigitalOutputDevice(led_pin)
            self.led.off()
            self._is_ready = True
        except Exception as e:
            self.log.error(f"Change led pin error: {e}")
            self._is_ready = False

    @log_error
    @check_ready
    def set(self, value: bool):
        self.fan.value = value
        if self.led_follow:
            self.led.value = value

    @log_error
    @check_ready
    def set_led(self, value: str):
        self.log.debug(f"Set led to {value}")
        if value == 'follow':
            self.led_follow = True
        else:
            self.led_follow = False
            if value == 'on':
                self.led.value = 1
            elif value == 'off':
                self.led.value = 0
            else:
                self.log.warning(f"Invalid led value: {value}")

    @log_error
    @check_ready
    def on(self):
        self.set(True)

    @log_error
    @check_ready
    def off(self):
        self.set(False)

    @log_error
    @check_ready
    def close(self):
        self.off()
        self._is_ready = False
        self.fan.close()
        self.log.debug("GPIO Fan closed")

class SPCFan(Fan):
    I2C_ADDRESS = 0x5A
    GET_FAN_SPEED = 0x21
    SET_FAN_SPEED = 0x00

    def __init__(self, *args, **kwargs):
        from spc.spc import SPC
        super().__init__(*args, **kwargs)
        self.spc = SPC()
        if 'fan' in self.spc.device.peripherals:
            self._is_ready = self.spc.is_ready()

    @log_error
    @check_ready
    def on(self):
        self.set_power(self.power)

    @log_error
    @check_ready
    def off(self):
        self.set_power(0)

    @log_error
    @check_ready
    def set_power(self, power: int):
        '''
        power: 0 ~ 100
        '''
        if not isinstance(power, int):
            raise ValueError("Invalid power")
        
        power = max(0, min(100, power))
        self.spc.set_fan_power(power)
        return power

    @log_error
    @check_ready
    def get_power(self):
        return self.spc.get_fan_power()

    @log_error
    @check_ready
    def close(self):
        self.off()
        self._is_ready = False
        self.log.debug("SPC Fan closed")

class PWMFan(Fan):
    # Systems that need to replace system pwm fan control
    # Please use all lowercase
    TEMP_CONTROL_INTERVENE_OS = [
        
    ]

    @log_error
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not PWMFan.pwm_fan_supported():
            self.log.warning("PWM Fan is not supported")
            self._is_ready = False
            return

        # Check if system support pwm fan control
        _, os_id = run_command("lsb_release -a |grep ID | awk -F ':' '{print $2}'")
        os_id = os_id.strip()
        _, os_code_name = run_command("lsb_release -a |grep Codename | awk -F ':' '{print $2}'")
        os_code_name = os_code_name.strip()

        self.enable_control = False
        if os_id.lower() in self.TEMP_CONTROL_INTERVENE_OS or os_code_name.lower() in self.TEMP_CONTROL_INTERVENE_OS:
            self.log.warning("System do not support pwm fan control")
            self.enable_control = True
        self._is_ready = True

    @staticmethod
    def pwm_fan_supported():
        from os import path
        return path.exists('/sys/class/thermal/cooling_device0/cur_state') and path.exists('/sys/devices/platform/cooling_fan')

    @log_error
    @check_ready
    def is_supported(self):
        return not self.enable_control

    @log_error
    @check_ready
    def get_state(self):
        path = '/sys/class/thermal/cooling_device0/cur_state'
        try:
            with open(path, 'r') as f:
                cur_state = int(f.read())
            return cur_state
        except Exception as e:
            self.log.error(f'read pwm fan state error: {e}')
            return 0

    @log_error
    @check_ready
    def set_state(self, level: int):
        '''
        level: 0 ~ 3
        '''
        if (isinstance(level, int)):
            if level > 3:
                level = 3
            elif level < 0:
                level = 0

            cmd = f"echo '{level}' | sudo tee -a /sys/class/thermal/cooling_device0/cur_state"
            result = subprocess.check_output(cmd, shell=True)

            return result

    @log_error
    @check_ready
    def get_speed(self):
        '''
        path =  '/sys/devices/platform/cooling_fan/hwmon/*/fan1_input'
        '''
        dir = '/sys/devices/platform/cooling_fan/hwmon/'
        secondary_dir = os.listdir(dir)
        path = f'{dir}/{secondary_dir[0]}/fan1_input'

        os.listdir
        try:
            with open(path, 'r') as f:
                speed = int(f.read())
            return speed
        except Exception as e:
            self.log.error(f'read fan1 speed error: {e}')
            return 0

    @log_error
    @check_ready
    def off(self):
        if not self.is_supported():
            self.set_state(0)

    @log_error
    @check_ready
    def close(self):
        self.off()
        self._is_ready = False
        self.log.debug("PWM Fan closed")