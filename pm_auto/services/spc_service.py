from ..libs.utils import log_error
from sf_rpi_status import shutdown
import time
import threading

class SPCService():
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
        self.shutdown_request = 0
        self.is_plugged_in = False
        self.interval = 1
        self.running = False
        self.thread = None

    @log_error
    def is_ready(self):
        return self._is_ready

    @log_error
    def set_debug_level(self, level):
        self.log.setLevel(level)

    @log_error
    def handle_shutdown(self):
        if self.spc is None or not self.spc.is_ready():
            return

        shutdown_request = self.spc.read_shutdown_request()
        if shutdown_request != self.shutdown_request:
            self.shutdown_request = shutdown_request
            self.log.debug(f"Shutdown request: {shutdown_request}")
        if shutdown_request in self.spc.SHUTDOWN_REQUESTS:
            if shutdown_request == self.spc.SHUTDOWN_REQUEST_LOW_POWER:
                self.log.info('Low power shutdown.')
            elif shutdown_request == self.spc.SHUTDOWN_REQUEST_BUTTON:
                self.log.info('Button shutdown.')
            shutdown()

    @log_error
    def handle_external_input(self):
        if self.spc is None or not self.spc.is_ready():
            return

        if 'external_input' not in self.spc.device.peripherals:
            return

        if 'battery' not in self.spc.device.peripherals:
            return

        is_plugged_in = self.spc.read_is_plugged_in()
        if is_plugged_in != self.is_plugged_in:
            self.is_plugged_in = is_plugged_in
            if is_plugged_in == True:
                self.log.info(f"External input plug in")
            else:
                self.log.info(f"External input unplugged")
        if is_plugged_in == False:
            shutdown_pct = self.spc.read_shutdown_battery_pct()
            current_pct= self.spc.read_battery_percentage()
            if current_pct < shutdown_pct:
                self.log.info(f"Battery is below {shutdown_pct}, shutdown!", level="INFO")
                shutdown()

    @log_error
    def loop(self):
        if self.spc is None or not self.spc.is_ready():
            return
        while self.running:
            self.handle_external_input()
            self.handle_shutdown()
            time.sleep(self.interval)

    @log_error
    def start(self):
        if self.thread is not None:
            self.log.warning("Already running")
            return
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.log.info("SPC Service Start")
        self.thread.start()

    def stop(self):
        if self.thread is not None:
            self.running = False
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                self.log.warning("Thread termination timeout")
            self.thread = None
        self.log.info("SPC Service Stop")
