from pm_auto.pm_auto import PMAuto
import time
import logging

config = {
    'temperature_unit': 'F',
    # 'shutdown_battery_percentage': 10,
    'gpio_fan_pin': 6,
    'oled_rotation': 180,
    'rgb_led_count': 12,
}

peripherals = [
    # 'spc',
    'gpio_fan',
    'pwm_fan',
    'oled',
]

def get_logger(name):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)
    return log

pm_auto = PMAuto(config, peripherals=peripherals, get_logger=get_logger)
# pm_auto.set_on_state_changed(lambda state: print(state))

def main():
    try:
        pm_auto.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt, terminating...")
    finally:
        pm_auto.stop()
        print("Goodbye")

if __name__ == "__main__":
    main()