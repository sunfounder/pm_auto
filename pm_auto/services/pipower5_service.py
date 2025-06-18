import threading
import time
from pipower5 import PiPower5


class PiPower5Service():

    LOOP_INTERVAL = 0.1 # 100ms

    def __init__(self):

        self.pipower5 = PiPower5()
        self._button_callback = None
        self._shutdown_callback = None
        self.running = False
        self._thread = None

    def set_button_callback(self, callback):
        self._button_callback = callback

    def set_shutdown_callback(self, callback):
        self._shutdown_callback = callback

    def loop(self):
        while self.running:
            button_status = self.pipower5.read_power_btn()
            shutdown_request = self.pipower5.read_shutdown_request()

            if self._button_callback is not None:
                self._button_callback(button_status)

            if self._shutdown_callback is not None:
                if button_status == 'long_press_2s':
                    self._shutdown_callback('button')
                elif shutdown_request == 1:
                    self._shutdown_callback('low battery')
                elif shutdown_request == 2:
                    self._shutdown_callback('button')

            time.sleep(self.LOOP_INTERVAL)

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self.loop)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self.running = False
        # self._thread.join()

