# Pironman MCU Service
#
# This is a service for Pironman MCU. Some model of Pironman have a build in MCU onboard to control the hardware.
# This service is used to control the hardware of Pironman MCU.
#
from pm_auto.libs.addon import Addon
from pm_auto.libs.utils import log_error
from pm_auto.libs.pironman_mcu import PironmanMCU, ShutdownReason, ButtonStatus

import asyncio

INTERVAL = 0.1

class PironmanMcuAddon(Addon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcu = None
        try:
            self.mcu = PironmanMCU()
            self._is_ready = True
        except Exception as e:
            self.log.error(f"Failed to initialize PironmanMCU: {e}")

    @log_error
    async def _main(self):
        while self.running:
            mcu_button = self.mcu.get_button()
            # shutdown_request = self.mcu.get_shutdown_request()
            if mcu_button == ButtonStatus.CLICK:
                self.log.debug("Pironman MCU button click")
                self.event.publish("pironman_mcu_button_click")
            elif mcu_button == ButtonStatus.DOUBLE_CLICK:
                self.log.debug("Pironman MCU button double click")
                self.event.publish("pironman_mcu_button_double_click")
            elif mcu_button == ButtonStatus.LONG_PRESS_2S:
                self.log.debug("Pironman MCU button long press 2s")
                self.event.publish("pironman_mcu_button_long_press", 'button_long_press')
            elif mcu_button == ButtonStatus.LONG_PRESS_2S_RELEASED:
                self.log.debug("Pironman MCU button long press 2s released")
                self.event.publish("pironman_mcu_button_long_press_released", 'button_long_press_released')
            # if shutdown_request == ShutdownReason.BUTTON:
            #     self.log.info("Pironman MCU button shutdown request")
            #     self.event.publish("pironman_mcu_shutdown_request_button", "button")
            await asyncio.sleep(INTERVAL)

    @log_error
    async def _stop(self):
        if self.mcu is not None and self._is_ready:
            self.mcu.close()
