import asyncio
import logging
from typing import Dict, Optional, List
from zlib import DEF_BUF_SIZE
from pm_auto.libs.utils import log_error
from pm_auto.libs.event_bus import EventBus

class Addon:
    """
    插件基类 - 异步版本
    """
    DEFAULT_CONFIG = {}

    def __init__(self, config=None, event: EventBus=None, device_info: Dict = None, peripherals: List[str] = None, log: Optional[logging.Logger] = None):
        self.log = log or logging.getLogger(__name__)
        self.device_info = device_info
        self._is_ready = False
        self.config = self.DEFAULT_CONFIG.copy()
        self.event = event
        self.running = False
        self.peripherals = peripherals or []
        self._task: Optional[asyncio.Task] = None
        self.update_config(config, init=True)

    @log_error
    def is_ready(self) -> bool:
        return self._is_ready
    
    @log_error
    def update_config(self, config: Dict, init: bool = False) -> Dict:
        '''
        Update config for addon.

        Args:
            config (Dict): Config dict.
            init (bool): Whether to update config for init.

        Returns:
            A dict of config patch to update the config file.
        '''
        return {}

    @log_error
    async def start(self) -> None:
        self._is_ready = True
        if self.running:
            self.log.warning(f"{self.__class__.__name__} service is already running")
            return
        await self._start()
        self._task = asyncio.create_task(self.main())
        self.log.info(f"{self.__class__.__name__} service started")
    
    @log_error
    async def stop(self) -> None:
        self._is_ready = False
        if self.running and self._task:
            self.running = False
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.log.debug(f"{self.__class__.__name__} stopping")
        await self._stop()
        self.log.info(f"{self.__class__.__name__} service stopped")
    
    @log_error
    async def main(self) -> None:
        self.running = True
        if not self.is_ready():
            self.log.error("%s Service not ready", self.__class__.__name__)
            return
        await self._main()

    async def _main(self) -> None:
        while self.running:
            await asyncio.sleep(1)

    async def _start(self) -> None:
        await asyncio.sleep(0)

    async def _stop(self) -> None:
        await asyncio.sleep(0)
