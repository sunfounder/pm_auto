from smbus2 import SMBus

class I2C():

    def __init__(self, address, bus=1):     
        self._bus = bus
        self._address = address
        self._smbus = SMBus(self._bus)
        if not I2C.enabled(self._bus):
            raise ValueError("I2C bus {} not enabled".format(self._bus))
        if not self.is_ready():
            raise ValueError("I2C device not found at address 0x{:02X}".format(self._address))

    def write_byte(self, data):
        return self._smbus.write_byte(self._address, data)

    def write_byte_data(self, reg, data):
        return self._smbus.write_byte_data(self._address, reg, data)

    def write_word_data(self, reg, data):
        return self._smbus.write_word_data(self._address, reg, data)

    def write_i2c_block_data(self, reg, data):
        return self._smbus.write_i2c_block_data(self._address, reg, data)

    def read_byte(self):
        return self._smbus.read_byte(self._address)

    def read_i2c_block_data(self, reg, num):
        return self._smbus.read_i2c_block_data(self._address, reg, num)

    def is_ready(self):
        addresses = self.scan(self._bus)
        if self._address in addresses:
            return True
        else:
            return False

    @staticmethod
    def enabled(bus=1):
        import os
        return os.path.exists("/dev/i2c-{}".format(bus))

    @staticmethod
    def scan(bus: int = 1, force: bool = False) -> list:
        """Scan the I2C bus for devices

        Args:
            bus (int, optional): I2C bus number, default is 1
            force (bool, optional): True if force to access the I2C bus, False otherwise, default is False

        Returns:
            list: List of I2C addresses of devices found
        """
        devices = []
        for addr in range(0x03, 0x77 + 1):
            try:
                with SMBus(bus) as smbus:
                    # Read a byte from the address
                    smbus.write_quick(addr)
                    devices.append(addr)
            except OSError as expt:
                # Ignore device busy or unresponsive errors
                if expt.errno == 16:  # Device or resource busy
                    # print(f"Address 0x{addr:02X} busy")
                    pass
                # Other errors continue to try
                continue
        return devices

