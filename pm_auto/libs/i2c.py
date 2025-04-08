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
    def scan(busnum=1, force=False):
        devices = []
        for addr in range(0x03, 0x77 + 1):
            read = SMBus.read_byte, (addr,), {'force':force}
            write = SMBus.write_byte, (addr, 0), {'force':force}
            for func, args, kwargs in (read, write):
                try:
                    with SMBus(busnum) as bus:
                        data = func(bus, *args, **kwargs)
                        devices.append(addr)
                        break
                except OSError as expt:
                    if expt.errno == 16:
                        # just busy, maybe permanent by a kernel driver or just temporary by some user code
                        pass
        return devices

