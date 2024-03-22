from pm_auto.fan_control import FanControl
import time

peripherals = [
    'pwm_fan',
    'gpio_fan',
]

config = {
    'gpio_fan_pin': 6,
}

fc = FanControl(config, fans=peripherals)

while True:
    fc.run()
    time.sleep(2)

    for i in range(0, 100, 10):
        fc.get_cpu_temperature = lambda: i
        fc.run()
        time.sleep(2)
    for i in range(100, 0, -10):
        fc.get_cpu_temperature = lambda: i
        fc.run()
        time.sleep(2)
