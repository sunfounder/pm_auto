from pm_auto.ws2812 import WS2812
import time

if __name__ == "__main__":
    try:
        strip = WS2812({
            'rgb_led_count': 4,
            'rgb_enable': True,
            'rgb_color': '#ff00ff',
            'rgb_brightness': 100,
            'rgb_style': 'rainbow',
            'rgb_speed': 100,
        })  # LED_COUNT, LED_PIN
        strip.start()
        while True:
            time.sleep(3)

    finally:
        strip.stop()
