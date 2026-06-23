import logging

from .libs.utils import log_error
from .libs.event_bus import EventBus
from .addons import Addons

from typing import Dict
import threading
import asyncio

DEFAULT_CONFIG = {
    'temperature_unit': 'C',
    'rgb_led_count': 4,
    'rgb_enable': True,
    'rgb_color': '#ff00ff',
    'rgb_brightness': 100,
    'rgb_style': 'rainbow',
    'rgb_speed': 0,
    'oled_rotation': 0,
    'oled_disk': 'total',  # 'total' or the name of the disk, normally 'mmcblk0' for SD Card, 'nvme0n1' for NVMe SSD
    'oled_network_interface': 'all',  # 'all' or the name of the interface, normally 'wlan0' for WiFi, 'eth0' for Ethernet
    'oled_sleep': False,
    'oled_sleep_timeout': 10,
    'oled_pages': [
        'performance',
        'ips',
        'disk',
    ],
    'rgb_matrix_enable': True,
    'rgb_matrix_style': 'rainbow',
    'rgb_matrix_color': '#ff0000',
    'rgb_matrix_color2': '#0000ff',
    'rgb_matrix_brightness': 100,  # 0-100
    'rgb_matrix_speed': 50,
}

class PMAuto:
    def __init__(self, config=DEFAULT_CONFIG, device_info=None, peripherals=None, event_map=None, log=None):
        self.log = log or logging.getLogger(__name__)
        self._is_ready = False
        self.device_info = device_info
        # 创建全局事件总线实例
        self.event = EventBus(log=log)
        self.peripherals = peripherals or []
        self.data = {}
        self.thread = None  # 添加线程属性
        self.loop = None    # 添加事件循环属性

        # Add system addon for all device
        self.peripherals.append('system')

        # Initialize addons
        self.addons = Addons(
            peripherals=self.peripherals,
            device_info=self.device_info,
            config=config,
            event=self.event,
            log=self.log)

        # Initialize event map
        self.event_map = event_map or {}
        # Connect events
        for pub_event_name, sub_event_name in self.event_map.items():
            self.event.connect(pub_event_name, sub_event_name)
        
        self.event.subscribe("before_shutdown", self.handle_before_shutdown)
        self.event.subscribe("data_changed", self.handle_data_changed)

    @log_error
    def test_smtp(self):
        return self.addons.pipower5.test_smtp()

    @log_error
    def play_pipower5_buzzer(self, event):
        return self.addons.pipower5.play_pipower5_buzzer(event)

    @log_error
    def power_failure_simulation(self, test_time=60):
        return self.addons.pipower5.power_failure_simulation(test_time)

    @log_error
    def handle_data_changed(self, data: Dict, delete_keys: list = []) -> None:
        # Delete old data
        for key in delete_keys:
            if key in self.data:
                del self.data[key]

        self.data.update(data)

    @log_error
    def handle_before_shutdown(self, reason):
        pass

    @log_error
    def read(self) -> Dict:
        return self.data

    @log_error
    def get_ip_data(self):
        return self.addons.system.fetch_ip_data()

    @log_error
    def is_ready(self) -> bool:
        return self._is_ready

    @log_error
    def update_config(self, config: Dict) -> Dict:
        '''
        Update config.

        Args:
            config (Dict): Config dict.

        Returns:
            A dict of config patch to update the config file.
        '''
        self.log.info(f"PM Auto new config: {config}")
        patch = self.addons.update_config(config)
        if 'temperature_unit' in config:
            patch['temperature_unit'] = config['temperature_unit']
        if len(patch) > 0:
            self.log.info(f"PM Auto Update config patch: {patch}")
        return patch

    @log_error
    def start(self) -> None:
        def run_event_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.create_task(self.addons.start())
            try:
                self.loop.run_forever()
            except KeyboardInterrupt:
                self.log.info("Received shutdown signal")
            finally:
                self.loop.run_until_complete(self.addons.stop())
                self.loop.close()
            self.log.info("PM Auto started")
        
        # 创建并启动线程
        self.thread = threading.Thread(target=run_event_loop, daemon=True)
        self.thread.start()

    @log_error
    def stop(self) -> None:
        if self.loop and self.loop.is_running():
            # 线程安全地停止事件循环
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread and self.thread.is_alive():
            # 等待线程结束
            self.thread.join()
        self.log.info("PM Auto stopped")
