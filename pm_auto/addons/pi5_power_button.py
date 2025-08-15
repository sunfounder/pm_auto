from pm_auto.libs.addon import Addon
from pm_auto.libs.pi5_power_button import Pi5PowerButton, ShutdownReason, ButtonStatus
from pm_auto.libs.utils import log_error

class Pi5PowerButtonAddon(Addon):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.button = Pi5PowerButton()
        self.button.set_button_callback(self.button_callback)
        # self.button.set_shutdown_callback(self.shutdown_callback)
        self._is_ready = True

    @log_error
    def button_callback(self, state):
        if state == ButtonStatus.CLICK:
            self.log.debug("Pi5 power button click")
            self.event.publish('pi5_power_button_click', state)
        elif state == ButtonStatus.DOUBLE_CLICK:
            self.log.debug("Pi5 power button double click")
            self.event.publish('pi5_power_button_double_click', state)
        elif state == ButtonStatus.LONG_PRESS_2S:
            self.log.debug("Pi5 power button long press")
            self.event.publish('pi5_power_button_long_press', 'button_long_press')
        elif state == ButtonStatus.LONG_PRESS_2S_RELEASED:
            self.log.debug("Pi5 power button long press released")
            self.event.publish('pi5_power_button_long_press_released', 'button_long_press_released')


    @log_error
    # def shutdown_callback(self, reason):
    #     if reason == ShutdownReason.BUTTON:
    #         self.log.debug("Pi5 power button shutdown")
    #         self.event.publish('pi5_power_button_shutdown', reason)

    @log_error
    async def _start(self):
        self.button.start()

    @log_error
    async def _stop(self):
        self.button.stop()
    

