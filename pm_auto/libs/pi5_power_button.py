
import time
from os import path
from evdev import InputDevice, ecodes
import threading
from enum import IntEnum

# https://raspberrypi.stackexchange.com/questions/149209/execute-custom-script-raspberry-pi-5-using-the-build-in-power-button
# https://forums.raspberrypi.com/viewtopic.php?t=364002

class ButtonStatus(IntEnum):
    RELEASED = 0
    PRESSED = 1
    CLICK = 2
    DOUBLE_CLICK = 3
    LONG_PRESS_2S = 4
    LONG_PRESS_2S_RELEASED = 5
    LONG_PRESS_5S = 6
    LONG_PRESS_5S_RELEASED = 7

class ShutdownReason(IntEnum):
    NONE = 0
    BUTTON = 1

class Pi5PowerButton():

    DEV_PATH = '/dev/input/event0'
    EVENT_CODE = ecodes.KEY_POWER # usually 116

    DOUBLE_CLICK_INTERVAL = 0.25 # 250ms
    STATUS_RESET_TIMEOUT = 2 # 2s

    READ_INTERVAL = 0.1 # 100ms

    def __init__(self, grab=True, debug=False):
        if not path.exists(self.DEV_PATH):
            raise Exception(f'Power button device not found at {self.DEV_PATH}')
   
        self.dev = InputDevice(self.DEV_PATH)
        # grab the device to prevent other programs from reading it
        if grab:
            self.dev.grab()

        self.status = ButtonStatus.RELEASED
        self.last_key_down_time = 0
        self.last_key_up_time = 0
        self.is_pressed = False
        self.doule_clik_ready = False
        self._watch_thread = None
        self._process_thread = None
        self._button_callback = None
        self._shutdown_callback = None
        self.running = False
        self._debug = debug

    def start_pwr_btn_watcher(self):
        if self._watch_thread is None or not self._watch_thread.is_alive():
            self._watch_thread = threading.Thread(target=self.watch_loop)
            self._watch_thread.daemon = True
            self._watch_thread.start()

    def watch_loop(self):
        for event in self.dev.read_loop():
            if event.type == ecodes.EV_KEY and event.code == self.EVENT_CODE:
                _event_time = event.timestamp()
                if event.value == 0: # up
                    # print('-------------------up-----------------')
                    self.is_pressed = False
                    
                    self.last_key_up_time = time.time()

                    if self.doule_clik_ready:
                        self.status = ButtonStatus.DOUBLE_CLICK
                        self.doule_clik_ready = False
                        continue
                    
                    _interval = _event_time - self.last_key_down_time
                    if _interval > 5:
                        self.status = ButtonStatus.LONG_PRESS_5S_RELEASED
                    elif _interval > 2:
                        self.status = ButtonStatus.LONG_PRESS_2S_RELEASED
                    else:
                        self.status = ButtonStatus.CLICK

                elif event.value == 1: # down
                    # print('-------------------down-----------------')
                    self.is_pressed = True

                    if _event_time - self.last_key_down_time < self.DOUBLE_CLICK_INTERVAL:
                        self.doule_clik_ready = True

                    self.status = ButtonStatus.PRESSED
                    self.last_key_down_time = _event_time
                    
    def read(self):
        _status = self.status
        if self.is_pressed:
            if time.time() - self.last_key_down_time > 5:
                _status = ButtonStatus.LONG_PRESS_5S
            elif time.time() - self.last_key_down_time > 2:
                _status = ButtonStatus.LONG_PRESS_2S
        else:
            if self.status == ButtonStatus.CLICK:
                if time.time() - self.last_key_up_time > self.DOUBLE_CLICK_INTERVAL:
                    _status = ButtonStatus.CLICK
                    self.status = ButtonStatus.RELEASED
                else:
                    _status = ButtonStatus.RELEASED
            else:
                self.status = ButtonStatus.RELEASED

        return _status
    
    def set_button_callback(self, callback):
        self._button_callback = callback

    def set_shutdown_callback(self, callback):
        self._shutdown_callback = callback

    def process_loop(self):
        self.start_pwr_btn_watcher()
        while self.running:
            state = self.read()
            # print(state)
            if self._debug and state != ButtonStatus.RELEASED:
                print(state)
            if self._button_callback is not None:
                self._button_callback(state)
            # if self._shutdown_callback is not None and state == ButtonStatus.LONG_PRESS_2S:
            #     self._shutdown_callback(ShutdownReason.BUTTON)
            time.sleep(self.READ_INTERVAL)

    def start(self):
        self.running = True
        self._process_thread = threading.Thread(target=self.process_loop)
        self._process_thread.daemon = True
        self._process_thread.start()

    def stop(self):
        self.running = False
    
