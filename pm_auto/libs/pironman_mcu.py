# Pironman MCU Library
#
# This is a library for Pironman MCU. Some model of Pironman have a build in MCU onboard to control the hardware.
# This library is used to control the hardware of Pironman MCU.
#

from .i2c import I2C

PM_MCU_I2C_ADDR = 0x6A

FIRMWARE_VERSION_REG_ADDR = 0x00
DEFAULT_ON_REG_ADDR = 0x01
PWR_BTN_REG_ADDR = 0x02
SHUTDOWN_REQ_REG_ADDR = 0x03

class PironmanMCU:
    def __init__(self):
        self.i2c = I2C(PM_MCU_I2C_ADDR)

    def get_firmware_version(self):
        data = self.i2c.read_i2c_block_data(FIRMWARE_VERSION_REG_ADDR, 1)[0]
        major = data >> 6 & 0x03
        minor = data >> 3 & 0x07
        patch = data & 0x07
        return (major, minor, patch)

    def get_button_wakeup(self):
        data = self.i2c.read_i2c_block_data(PWR_BTN_REG_ADDR, 1)[0]
        if data == 1: 
            self.i2c.write_byte_data(PWR_BTN_REG_ADDR, 0)
            return True
        return False

    def get_shutdown_request(self):
        data = self.i2c.read_i2c_block_data(SHUTDOWN_REQ_REG_ADDR, 1)[0]
        if data!= 0:
            self.i2c.write_byte_data(SHUTDOWN_REQ_REG_ADDR, 0)
            return True
        return False

    def get_default_on(self):
        data = self.i2c.read_i2c_block_data(DEFAULT_ON_REG_ADDR, 1)[0]
        return data!= 0

    def close(self):
        pass