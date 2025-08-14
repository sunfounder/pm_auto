
import time
from os import path
from evdev import InputDevice, ecodes
import threading
from enum import IntEnum
import re
import json

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

def parse_input_devices_to_json():
    """
    Parse /proc/bus/input/devices file into structured JSON, extracting clean field values
    
    Returns:
        str: Formatted JSON string
        None: Returns None if parsing fails
    """
    with open("/proc/bus/input/devices", "r") as f:
        content = f.read()
    
    # Split by device (each device starts with "I: Bus=")
    device_blocks = re.split(r'\n(?=I: Bus=)', content.strip())
    devices = {}
    
    for block in device_blocks:
        device_info = {}
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        for line in lines:
            # Extract type identifier (e.g., I, N, P, etc.)
            match = re.match(r'^([A-Z]): (.*)$', line)
            if not match:
                continue
                
            key = match.group(1)
            value_str = match.group(2)
            
            # Parse different field types
            if key == 'I':  # Bus information
                # Extract Bus, Vendor, Product, Version
                bus_info = {}
                for item in value_str.split():
                    if '=' in item:
                        k, v = item.split('=', 1)
                        bus_info[k.lower()] = v
                device_info['bus'] = bus_info
                
            elif key == 'N':  # Device name
                # Extract name from quotes (e.g., Name="Power Button" → Power Button)
                name_match = re.search(r'Name="([^"]+)"', value_str)
                if name_match:
                    device_info['name'] = name_match.group(1)
                    
            elif key == 'P':  # Physical location
                phys_match = re.search(r'Phys=([^ ]+)', value_str)
                if phys_match:
                    device_info['phys'] = phys_match.group(1)
                    
            elif key == 'S':  # sysfs path
                sysfs_match = re.search(r'Sysfs=([^ ]+)', value_str)
                if sysfs_match:
                    device_info['sysfs'] = sysfs_match.group(1)
                    
            elif key == 'U':  # Unique identifier
                uniq_match = re.search(r'Uniq=([^ ]*)', value_str)
                if uniq_match:
                    device_info['uniq'] = uniq_match.group(1)
                    
            elif key == 'H':  # Handlers
                handlers_match = re.search(r'Handlers=(.*)', value_str)
                if handlers_match:
                    device_info['handlers'] = handlers_match.group(1).split()
                for handler in device_info['handlers']:
                    if handler.startswith('event'):
                        device_info['path'] = f"/dev/input/{handler}"
                        break

                    
            elif key == 'B':  # Properties field
                prop_parts = value_str.split('=', 1)
                if len(prop_parts) == 2:
                    prop_name = prop_parts[0].strip()
                    prop_value = prop_parts[1].strip()
                    if 'properties' not in device_info:
                        device_info['properties'] = {}
                    device_info['properties'][prop_name] = prop_value
        
        devices[device_info['name']] = device_info
    
    return json.dumps(devices, indent=2, ensure_ascii=False)

def find_device_path(name):
    """
    Find the path corresponding to the device name
    
    Args:
        name (str): Device name
        
    Returns:
        str: Device path, e.g., "/dev/input/event0"
        None: If device is not found
    """
    devices = parse_input_devices_to_json()
    if not devices:
        return None
    
    devices = json.loads(devices)
    for dev_name, dev_info in devices.items():
        if dev_name == name:
            return dev_info.get('path')
    return None

class Pi5PowerButton():

    EVENT_CODE = ecodes.KEY_POWER # usually 116

    DOUBLE_CLICK_INTERVAL = 0.25 # 250ms
    STATUS_RESET_TIMEOUT = 2 # 2s

    READ_INTERVAL = 0.1 # 100ms

    def __init__(self, grab=True, debug=False):
        device_path = find_device_path('pwr_button')
        if not device_path:
            raise Exception(f'Power button device not found')
        
        self.dev = InputDevice(device_path)
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
    
