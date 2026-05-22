
from typing import Dict, List, Type
from pm_auto.libs.addon import Addon
from pm_auto.libs.utils import has_common_items

import logging
import asyncio

def get_addons(peripherals: List[str]) -> List[Type[Addon]]:
    addons = []
    from .fan import FANS
    if has_common_items(peripherals, FANS):
        from .fan import FanAddon
        addons.append(FanAddon)
    if 'oled' in peripherals:
        from .oled import OLEDAddon
        addons.append(OLEDAddon)
    if 'pi5_power_button' in peripherals:
        from .pi5_power_button import Pi5PowerButtonAddon
        addons.append(Pi5PowerButtonAddon)
    if 'pipower5' in peripherals:
        from .pipower5 import PiPower5Addon
        addons.append(PiPower5Addon)
    if 'pironman_mcu' in peripherals:
        from .pironman_mcu import PironmanMcuAddon
        addons.append(PironmanMcuAddon)
    if 'rgb_matrix' in peripherals:
        from .rgb_matrix import RGBMatrixAddon
        addons.append(RGBMatrixAddon)
    if 'system' in peripherals:
        from .system import SystemAddon
        addons.append(SystemAddon)
    if 'vibration_switch' in peripherals:
        from .vibration_switch import VibrationSwitchAddon
        addons.append(VibrationSwitchAddon)
    if 'ws2812' in peripherals:
        from .ws2812 import WS2812Addon
        addons.append(WS2812Addon)
    if 'sf_rgb_led' in peripherals:
        from .sunfounder_rgb_led import SunFounderRGBLEDAddon
        addons.append(SunFounderRGBLEDAddon)
    
    return addons

class Addons:
    """
    插件管理器 - 异步版本
    """
    def __init__(self, peripherals=None, config=None, device_info=None, event=None, log=None):
        self.log = log or logging.getLogger(__name__)
        self._is_ready = False
        # 创建全局事件总线实例
        self.event = event
        self.config = config
        self.peripherals = peripherals or []

        # Initialize addons
        self.addons = {}
        addons = get_addons(peripherals)
        self.log.info(f"Addons: {', '.join([addon.__name__ for addon in addons])}")
        for Addon in addons:
            name = Addon.__name__.replace('Addon', '').lower()
            addon = Addon(config=self.config, event=self.event, device_info=device_info, peripherals=peripherals, log=log)
            if addon.is_ready():
                self.log.info("%s service initialized", Addon.__name__)
                self.addons[name] = addon
            else:
                self.log.error("Failed to initialize %s service", Addon.__name__)

    def __getattr__(self, name: str):
        if name in self.addons:
            return self.addons[name]
        raise AttributeError(f"'Addons' object has no attribute '{name}'")

    def update_config(self, config: Dict) -> Dict:
        '''
        Update config.

        Args:
            config (Dict): Config dict.

        Returns:
            A dict of config patch to update the config file.
        '''
        patch = {}
        for addon in self.addons.values():
            new_patch = addon.update_config(config)
            if new_patch is not None:
                patch.update(new_patch)
        return patch

    async def start(self) -> None:
        # 并行启动所有插件
        await asyncio.gather(*[addon.start() for addon in self.addons.values()])
        self.log.info("Addons started")

    async def stop(self) -> None:
        # 并行停止所有插件
        await asyncio.gather(*[addon.stop() for addon in self.addons.values()])
        self.log.info("Addons stopped")
