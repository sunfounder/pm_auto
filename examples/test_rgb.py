from pm_auto.ws2812 import WS2812
import time
import logging

def get_logger(name):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)
    return log


if __name__ == "__main__":
    try:
        strip = WS2812({
            'rgb_led_count': 4,
            'rgb_enable': True,
            'rgb_color': '#ff00ff',
            'rgb_brightness': 100,
            'rgb_style': 'rainbow',
            'rgb_speed': 100,
        }, get_logger)  # LED_COUNT, LED_PIN
        strip.start()
        while True:
            time.sleep(3)
    finally:
        strip.stop()
