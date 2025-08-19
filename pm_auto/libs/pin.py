# To fix raspberry Pi chaos pin library

from enum import Enum

class PinMode(Enum):
    IN = 0
    OUT = 1

class Pin:
    def __init__(self, pin: int, mode: PinMode):
        self._pin = pin
        self._mode = mode
        self._value = None

        from RPi import GPIO
        self.gpio = GPIO

        self.gpio.setmode(self.gpio.BCM)
        if self._mode == PinMode.OUT:
            self.gpio.setup(self._pin, self.gpio.OUT)
        elif self._mode == PinMode.IN:
            self.gpio.setup(self._pin, self.gpio.IN)
        else:
            pass



    @property
    def value(self):
        if self.mode == PinMode.OUT:
            return self._value
        elif self.mode == PinMode.IN:
            return self.gpio.input(self._pin)
        else:
            # auto setmode to input
            self.gpio.setup(self._pin, self.gpio.IN)
            self.mode = PinMode.IN
            return self.gpio.input(self._pin)

    @value.setter
    def value(self, value):
        if self.mode == PinMode.OUT:
            self._value = value
            self.gpio.output(self._pin, value)
        else:
            # auto setmode to output
            self.gpio.setup(self._pin, self.gpio.OUT)
            self.mode = PinMode.OUT
            self.gpio.output(self._pin, value)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        if value == PinMode.OUT:
            self.gpio.setup(self._pin, self.gpio.OUT)
        elif value == PinMode.IN:
            self.gpio.setup(self._pin, self.gpio.IN)
        else:
            pass
        self._mode = value

    @property
    def pin(self):
        return self._pin

    @pin.setter
    def pin(self, value):
        self._pin = value
        self.gpio.setmode(self.gpio.BCM)
        if self.mode == PinMode.OUT:
            self.gpio.setup(self.pin, self.gpio.OUT)
        elif self.mode == PinMode.IN:
            self.gpio.setup(self.pin, self.gpio.IN)
        else:
            pass

    def set_value(self, value):
        self.value = value

    def on(self):
        self.value = 1

    def off(self):
        self.value = 0

    def high(self):
        self.value = 1

    def low(self):
        self.value = 0

    def toggle(self):
        self.value = not self.value

    def close(self):
        if self._mode and self._mode == PinMode.OUT:
            self.off()
        if self.gpio and self._pin:
            self.gpio.cleanup(self._pin)

    def __del__(self):
        self.close()
