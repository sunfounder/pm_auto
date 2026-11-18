from pm_auto.libs.addon import Addon
from pm_auto.libs.pi5_power_button import Pi5PowerButton, ShutdownReason, ButtonStatus
from pm_auto.libs.utils import log_error

class Pi5PowerButtonAddon(Addon):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.button = Pi5PowerButton(log=self.log)
        self.button.set_button_callback(self.button_callback)
        # self.button.set_shutdown_callback(self.shutdown_callback)
        self._is_ready = True
        # The button still works without an exclusive grab, so a failed grab is
        # a degraded state, not a dead addon. Surface it instead of only
        # writing a log line, so status APIs and the UI can tell the difference.
        self.grabbed = self.button.grabbed
        if not self.grabbed:
            self.log.warning(
                "Pi5 power button is shared with another process: "
                "control is degraded (no exclusive grab)")
            if self.event is not None:
                self.event.publish('pi5_power_button_degraded', {'grabbed': False})

    def is_grabbed(self) -> bool:
        return self.grabbed

    def get_status(self) -> dict:
        return {'ready': self._is_ready, 'grabbed': self.grabbed}

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
    

