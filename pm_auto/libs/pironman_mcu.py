# Pironman MCU Library
#
# This is a library for Pironman MCU. Some model of Pironman have a build in MCU onboard to control the hardware.
# This library is used to control the hardware of Pironman MCU.
#

from enum import IntEnum
from .i2c import I2C

# Pironman MCU I2C Address
PM_MCU_I2C_ADDR = 0x6A

BUTTON_MAP = {
    0: 'released',
    1: 'single_click',
    2: 'double_click',
    3: 'long_press_2s',
    4: 'long_press_2s_released',
    5: 'long_press_5s',
    6: 'long_press_5s_released',
}

# Register Address
class RegisterAddress(IntEnum):
    FIRMWARE_VERSION = 0x00
    DEFAULT_ON       = 0x01
    PWR_BTN          = 0x02
    SHUTDOWN_REQ     = 0x03

class ButtonStatus(IntEnum):
    RELEASED = 0
    PRESSED = 1

# Shutdown Reason
class ShutdownReason(IntEnum):
    NONE = 0
    BUTTON = 1

class PironmanMCU:
    def __init__(self):
        self.i2c = I2C(PM_MCU_I2C_ADDR)

    def get_firmware_version(self):
        data = self.i2c.read_i2c_block_data(RegisterAddress.FIRMWARE_VERSION, 1)[0]
        major = data >> 6 & 0x03
        minor = data >> 3 & 0x07
        patch = data & 0x07
        return (major, minor, patch)

    def get_button(self):

        data = self.i2c.read_i2c_block_data(RegisterAddress.PWR_BTN, 1)[0]
        self.i2c.write_byte_data(RegisterAddress.PWR_BTN, 0)

        if data in BUTTON_MAP:
            return BUTTON_MAP[data]
        else:
            return data
    
    def get_shutdown_request(self):
        data = self.i2c.read_i2c_block_data(RegisterAddress.SHUTDOWN_REQ, 1)[0]
        if data!= 0:
            self.i2c.write_byte_data(RegisterAddress.SHUTDOWN_REQ, 0)
        return data

    def get_default_on(self):
        data = self.i2c.read_i2c_block_data(RegisterAddress.DEFAULT_ON, 1)[0]
        return data!= 0

    def close(self):
        pass