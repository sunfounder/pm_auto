# Pironman MCU Service
#
# This is a service for Pironman MCU. Some model of Pironman have a build in MCU onboard to control the hardware.
# This service is used to control the hardware of Pironman MCU.
#
import threading
import time
from enum import IntEnum

from ..libs.utils import log_error
from ..libs.pironman_mcu import PironmanMCU, ShutdownReason
from sf_rpi_status import shutdown

INTERVAL = 0.1

class PironmanMCUService:
    def __init__(self, config, get_logger=None):
        if get_logger is None:
            import logging
            get_logger = logging.getLogger
        self.log = get_logger(__name__)
        self._is_ready = False
        try:
            self.mcu = PironmanMCU()
            self._is_ready = True
        except Exception as e:
            self.log.error(f"Failed to initialize PironmanMCU: {e}")
            return
        self.__on_wakeup__ = lambda: None
        self.__on_shutdown__ = lambda reason: None
        self.running = False
        self.thread = None
    
    @log_error
    def set_debug_level(self, level):
        self.log.setLevel(level)

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def update_config(self, config):
        # No config to update for now
        pass

    @log_error
    def set_on_wakeup(self, on_wakeup):
        self.__on_wakeup__ = on_wakeup

    @log_error
    def set_on_shutdown(self, on_shutdown):
        self.__on_shutdown__ = on_shutdown

    @log_error
    def loop(self):
        if not self._is_ready:
            self.log.error("PironmanMCUService is not ready")
            return
        while self.running:
            wakeup_button = self.mcu.get_button()
            shutdown_request = self.mcu.get_shutdown_request()
            if wakeup_button:
                self.__on_wakeup__(wakeup_button)
            if shutdown_request != ShutdownReason.NONE:
                self.log.info(f"Shutdown request {ShutdownReason(shutdown_request).name}")
                self.__on_shutdown__(shutdown_request)
                time.sleep(3)
                shutdown()
            time.sleep(INTERVAL)

    @log_error
    def start(self):
        if self.running:
            self.log.warning("Already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    @log_error
    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
        if self.mcu is not None:
            self.mcu.close()
