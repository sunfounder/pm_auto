"""Regression test: the patch returned by update_config() must reach self.config.

Covers sunfounder/pm_auto#3.  Addon.__init__ used to call
``self.update_config(config, init=True)`` and throw the returned patch away,
so every subclass that reads ``self.config`` in its own ``__init__`` kept
seeing DEFAULT_CONFIG.  FanAddon takes the fan pin and the fan-LED pin/mode
from there, so a configured ``gpio_fan_led: "off"`` ran as the default
``"follow"`` (LEDs tracking the fan) and ``gpio_fan_led_pin`` was ignored at
every service start.

Runs without GPIO hardware: ``pm_auto.libs.pin`` is replaced with a fake
module before FanAddon is constructed.
"""

import logging
import sys
import types

from pm_auto.libs.addon import Addon


class FakePin:
    """Records what each Pin pokes at, instead of touching real GPIO."""

    instances = []

    def __init__(self, pin, mode):
        self.pin = pin
        self.mode = mode
        self.state = None
        FakePin.instances.append(self)

    def set_value(self, value):
        self.state = bool(value)

    def on(self):
        self.state = True

    def off(self):
        self.state = False

    def close(self):
        pass


class FakePinMode:
    IN = 0
    OUT = 1


def install_fake_pin_module():
    fake = types.ModuleType("pm_auto.libs.pin")
    fake.Pin = FakePin
    fake.PinMode = FakePinMode
    sys.modules["pm_auto.libs.pin"] = fake
    FakePin.instances = []


def make_fan_addon(config):
    install_fake_pin_module()
    from pm_auto.addons.fan import FanAddon

    return FanAddon(
        config=config,
        peripherals=["gpio_fan_state", "gpio_fan_led"],
        log=logging.getLogger("fan-config-test"),
    )


class DummyAddon(Addon):
    DEFAULT_CONFIG = {"alpha": 1, "beta": 2}

    @property
    def mutated_in_init(self):
        return getattr(self, "_mutated", False)

    def update_config(self, config, init=False):
        patch = {}
        if "alpha" in config:
            patch["alpha"] = config["alpha"]
        return patch


def test_init_patch_is_merged_into_self_config():
    addon = DummyAddon(config={"alpha": 9})
    assert addon.config["alpha"] == 9, addon.config
    # Untouched keys keep their default.
    assert addon.config["beta"] == 2, addon.config


def test_fan_uses_configured_led_and_pin():
    addon = make_fan_addon(
        {
            "gpio_fan_pin": 12,
            "gpio_fan_mode": 0,
            "gpio_fan_led": "off",
            "gpio_fan_led_pin": 26,
        }
    )
    pins = [pin.pin for pin in FakePin.instances]
    assert pins == [12, 26], pins  # fan pin, then fan-LED pin
    assert addon.gpio_fan.led_follow is False
    assert addon.gpio_fan.led.state is False
    assert addon.config["gpio_fan_led"] == "off", addon.config
    assert addon.config["gpio_fan_led_pin"] == 26, addon.config


def test_fan_led_on_and_follow():
    on_addon = make_fan_addon({"gpio_fan_led": "on"})
    assert on_addon.gpio_fan.led_follow is False
    assert on_addon.gpio_fan.led.state is True

    follow_addon = make_fan_addon({"gpio_fan_led": "follow"})
    assert follow_addon.gpio_fan.led_follow is True


def test_fan_defaults_survive_missing_keys():
    addon = make_fan_addon({"gpio_fan_mode": 0})
    assert [pin.pin for pin in FakePin.instances] == [6, 5]
    assert addon.gpio_fan.led_follow is True
    assert addon.config["gpio_fan_led"] == "follow", addon.config


def test_fan_invalid_values_are_not_stored():
    addon = make_fan_addon({"gpio_fan_led": "blink", "gpio_fan_led_pin": 26})
    assert addon.config["gpio_fan_led"] == "follow", addon.config
    assert addon.config["gpio_fan_led_pin"] == 26, addon.config


if __name__ == "__main__":
    test_init_patch_is_merged_into_self_config()
    test_fan_uses_configured_led_and_pin()
    test_fan_led_on_and_follow()
    test_fan_defaults_survive_missing_keys()
    test_fan_invalid_values_are_not_stored()
    print("all addon config merge tests passed")
