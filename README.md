# PM Auto

Pironman Auto — Python library for controlling all peripherals on Pironman devices.

## Installation

```bash
# System dependencies
apt-get -y install python3 python3-pip python3-venv git liblgpio-dev libfreetype6-dev libjpeg-dev libopenjp2-7

# From GitHub (tagged release)
pip install git+https://github.com/sunfounder/pm_auto.git@2.0.0

# Or from v2 branch (auto bug fixes, backward-compatible)
pip install git+https://github.com/sunfounder/pm_auto.git@v2
```

## Usage

```python
from pm_auto.pm_auto import PMAuto

config = {
    "peripherals": ["oled", "ws2812"],
    "temperature_unit": "C",
    "rgb_led_count": 4,
    "rgb_enable": True,
    "rgb_color": "#0a1aff",
    "rgb_brightness": 50,
    "rgb_style": "breathing",
    "rgb_speed": 50,
}

pm = PMAuto(config)
pm.start()
```

## Supported Peripherals

| Key | Addon | Description |
|-----|-------|-------------|
| `oled` | OLED | SSD1306 I2C display |
| `ws2812` | WS2812 | SPI addressable RGB LEDs |
| `sf_rgb_led` | SunFounder RGB | I2C RGB LEDs via CH32V003 MCU |
| `gpio_fan_state` | Fan | GPIO fan speed control |
| `pwm_fan_speed` | Fan | PWM fan control |
| `vibration_switch` | Vibration | GPIO vibration sensor |
| `system` | System | CPU/memory/disk monitoring |
| `rgb_matrix` | RGB Matrix | LED matrix display |

## Versioning

Follow [Semantic Versioning](https://semver.org/):
- `A.B.C` — A = breaking changes, B = new features, C = bug fixes
- Each release is tagged (e.g. `2.0.0`)
- `v2` branch is the active development line (backward-compatible within v2)

## About SunFounder

SunFounder is a company focused on STEAM education with products like open source robots, development boards, STEAM kit, modules, tools and other smart devices distributed globally.

## Contact

- Website: [www.sunfounder.com](https://www.sunfounder.com)
- Email: service@sunfounder.com
