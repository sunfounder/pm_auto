# CLAUDE.md

## Project Overview

PM Auto is a Python library for controlling Raspberry Pi peripherals (OLED, WS2812 RGB LEDs, fans, power management) on Pironman devices. Built as an addon-based plugin system.

## Build & Package

```bash
pip install .
```

- Package: `pm_auto`
- Config: `pyproject.toml` (setuptools, version from `pm_auto.__version__`)
- No test suite currently

## Architecture

```
pm_auto/
  __init__.py          # re-exports __version__
  version.py           # single source of truth for version
  pm_auto.py           # PMAuto orchestrator
  libs/
    addon.py           # base Addon class
    i2c.py             # I2C wrapper (SMBus)
    sunfounder_rgb_led.py  # I2C driver for CH32V003 RGB firmware (addr 0x6A)
    utils.py           # helpers: hex_to_rgb, log_error, map_value
  addons/
    __init__.py        # addon loader/dispatcher
    ws2812.py          # SPI neopixel addon (Pironman 5)
    sunfounder_rgb_led.py  # I2C RGB LED addon (older hardware, sf_rgb_led peripheral)
    oled/              # SSD1306 OLED display pages
    fan.py             # GPIO fan control
    ...
```

## RGB LED: Two addons, two protocols

| Addon | Peripheral Key | Bus | Hardware |
|-------|---------------|-----|----------|
| `ws2812.py` | `ws2812` | SPI (neopixel_spi) | Pironman 5 Max/Mini |
| `sunfounder_rgb_led.py` | `sf_rgb_led` | I2C (0x6A) | Older Pironman + CH32V003 MCU |

Both share the same config keys: `rgb_led_count`, `rgb_enable`, `rgb_color`, `rgb_brightness`, `rgb_speed`, `rgb_style`.

The I2C driver targets the CH32V003 firmware at `pironman5-ups-rgb-firmware`. Protocol: first byte = register address, subsequent bytes auto-increment through `registerMap[255]`. Hardware limit: 23 LEDs (`WS2812_MAX_LEDS`).

## Version & Branching

Follow the **multi-version mode** branching spec:
- `v1` — frozen, historical
- `v2` — active development, default branch
- Tag every release: `2.0.0`, `2.0.1`, ...
- No breaking changes on a version branch

## Code Style

- Python with type hints where practical
- Addons extend `pm_auto.libs.addon.Addon`
- Async `_start()` / `_stop()` lifecycle
- `update_config(config, init)` returns a patch dict
- Minimal docstrings — only for non-obvious behavior
