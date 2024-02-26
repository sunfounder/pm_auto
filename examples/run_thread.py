from pm_auto.pm_auto import PMAuto
import time

config = {
    "temperature_unit": "C",
    'rgb_led_count': 4,
    'rgb_enable': True,
    'rgb_color': '#ff00ff',
    'rgb_brightness': 100,
    'rgb_style': 'rainbow',
    'rgb_speed': 0,
    'gpio_fan_pin': 6,
}

peripherals = [
    'ws2812',
    'oled',
    'pwm_fan',
    'gpio_fan',
]

pm_auto = PMAuto(config, peripherals=peripherals)

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