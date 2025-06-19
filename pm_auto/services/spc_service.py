from ..libs.utils import log_error
import time
import threading

BUTTON_MAP = {
    0: 'released',
    1: 'single_click',
    2: 'double_click',
    3: 'long_press_2s',
    4: 'long_press_2s_released',
    5: 'long_press_5s',
    6: 'long_press_5s_released',
}

SHUTDOWN_REQUEST_MAP = {
    0: 'none',
    1: 'low_battery',
    2: 'button',
}

class SPCService():
    LOOP_INTERVAL = 0.1 # 100ms

    REG_PWR_BTN_STATE= 154
    REG_WRITE_POWER_BTN_STATE = 12

    @log_error
    def __init__(self, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False

        from spc.spc import SPC
        self.spc = SPC(get_logger=get_logger)
        if not self.spc.is_ready():
            self._is_ready = False
            return

        self._is_ready = True
        self.running = False
        self._thread = None
        self._button_callback = None
        self._shutdown_callback = None

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def set_debug_level(self, level):
        self.log.setLevel(level)

    @log_error
    def set_button_callback(self, callback):
        self._button_callback = callback

    @log_error
    def set_shutdown_callback(self, callback):
        self._shutdown_callback = callback

    @log_error
    def read_power_btn(self):
        val = self.spc.i2c.read_byte_data(self.REG_PWR_BTN_STATE)
        self.spc.i2c.write_byte_data(self.REG_WRITE_POWER_BTN_STATE, 0) # reset state

        if val in BUTTON_MAP:
            return BUTTON_MAP[val]
        else:
            return val
              
    @log_error
    def read_shutdown_request(self):
        val = self.spc.read_shutdown_request()
        if val in SHUTDOWN_REQUEST_MAP:
            return SHUTDOWN_REQUEST_MAP[val]
        else:
            return val

    @log_error
    def loop(self):
        if self.spc is None or not self.spc.is_ready():
            return
        while self.running:
            button_status = self.read_power_btn()
            shutdown_request = self.read_shutdown_request()

            if self._button_callback is not None:
                self._button_callback(button_status)

            if self._shutdown_callback is not None:
                if button_status == 'long_press_2s':
                    self._shutdown_callback('button')
                elif shutdown_request == 'low_battery':
                    self._shutdown_callback('low battery')
                elif shutdown_request == 'button':
                    self._shutdown_callback('button')

            time.sleep(self.LOOP_INTERVAL)

    @log_error
    def start(self):
        if self._thread is not None:
            self.log.warning("Already running")
            return
        self.running = True
        self._thread = threading.Thread(target=self.loop, daemon=True)
        self.log.info("SPC Service Start")
        self._thread.start()

    def stop(self):
        self.running = False
        self.log.info("SPC Service Stop")
