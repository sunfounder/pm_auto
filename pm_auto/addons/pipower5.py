from pm_auto.libs.utils import log_error
from pm_auto.libs.addon import Addon
from pm_auto.libs.task_scheduler import TaskScheduler
import asyncio

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

class PiPower5Addon(Addon):
    LOOP_INTERVAL = 0.1 # 100ms

    REG_PWR_BTN_STATE= 154
    REG_WRITE_POWER_BTN_STATE = 12

    @log_error
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tasks = TaskScheduler()
        from pipower5.pipower5 import PiPower5
        self.pipower5 = PiPower5()
        if not self.pipower5.is_ready():
            self._is_ready = False
            return

        self._button_callback = None
        self._shutdown_callback = None

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def set_button_callback(self, callback):
        self._button_callback = callback

    @log_error
    def set_shutdown_callback(self, callback):
        self._shutdown_callback = callback

    @log_error
    def read_power_btn(self):
        val = self.pipower5.i2c.read_byte_data(self.REG_PWR_BTN_STATE)
        self.pipower5.i2c.write_byte_data(self.REG_WRITE_POWER_BTN_STATE, 0) # reset state

        if val in BUTTON_MAP:
            return BUTTON_MAP[val]
        else:
            return val
              
    @log_error
    def read_shutdown_request(self):
        val = self.pipower5.read_shutdown_request()
        if val in SHUTDOWN_REQUEST_MAP:
            return SHUTDOWN_REQUEST_MAP[val]
        else:
            return val

    @log_error
    def publish_data(self):
        data = self.pipower5.read_all()
        self.event.publish("data_changed", data)

    @log_error
    async def _main(self):
        self.tasks.run_periodically(self.publish_data, 1)

        while self.running:
            button_status = self.read_power_btn()
            shutdown_request = self.read_shutdown_request()

            if button_status == 'single_click':
                self.event.publish('pipower5_button_single_click', 'single_click')
            elif button_status == 'double_click':
                self.event.publish('pipower5_button_double_click', 'double_click')

            if self._shutdown_callback is not None:
                if button_status == 'long_press_2s':
                    self.event.publish('pipower5_button_long_click', 'long_click')
                elif shutdown_request == 'low_battery':
                    self.event.publish('pipower5_low_battery', 'low_battery')
                elif shutdown_request == 'button':
                    self.event.publish('pipower5_button_shutdown', 'button')

            await asyncio.sleep(self.LOOP_INTERVAL)
        
