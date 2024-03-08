from pm_auto.pm_auto import PMAuto
import time
import logging

config = {
    "temperature_unit": "C",
    'shutdown_battery_percentage': 10,
}

peripherals = [
    'spc',
]

def get_logger(name):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)
    return log

pm_auto = PMAuto(config, peripherals=peripherals, get_logger=get_logger)

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