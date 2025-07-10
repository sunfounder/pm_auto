from pm_auto.libs.addon import Addon
from pm_auto.libs.utils import log_error
from pm_auto.libs.task_scheduler import TaskScheduler

from sf_rpi_status import \
    get_cpu_temperature, \
    get_gpu_temperature, \
    get_cpu_percent, \
    get_cpu_freq, \
    get_cpu_count, \
    get_memory_info, \
    get_disks, \
    get_disk_info, \
    get_disks_info, \
    get_boot_time, \
    get_ips, \
    get_macs, \
    get_network_connection_type, \
    get_network_speed

import time
import asyncio

class SystemAddon(Addon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event.subscribe('shutdown', self._on_shutdown)
        self.tasks = TaskScheduler()
        self._is_ready = True

    @log_error
    def _on_shutdown(self, reason):
        if reason != 'None' or reason != None or reason != 0:
            self.log.info(f"Shutdown reason: {reason}")
            self.event.publish('before_shutdown', reason)
            time.sleep(2)

            try:
                from sf_rpi_status import shutdown
                shutdown()
            except Exception as e:
                self.log.error(f"Failed to shutdown: {e}")
                from os import system
                system("sudo shutdown -h now")

    @log_error
    def task_once(self):
        data = {}
        data['cpu_count'] = int(get_cpu_count())
        macs = get_macs()
        for name in macs:
            data[f'mac_{name}'] = macs[name]
        self.event.publish('data_changed', data)

    @log_error
    def task_1s(self):
        data = {}
        data['boot_time'] = float(get_boot_time())

        data['cpu_temperature'] = float(get_cpu_temperature()) if get_cpu_temperature() is not None else None
        data['gpu_temperature'] = float(get_gpu_temperature()) if get_gpu_temperature() is not None else None
        cpu_percent = get_cpu_percent()
        data['cpu_percent'] = float(cpu_percent)
        cpu_percents = get_cpu_percent(percpu=True)
        for i, percent in enumerate(cpu_percents):
            data[f'cpu_{i}_percent'] = float(percent)

        cpu_freq = get_cpu_freq()
        data['cpu_freq'] = float(cpu_freq.current)
        data['cpu_freq_min'] = float(cpu_freq.min)
        data['cpu_freq_max'] = float(cpu_freq.max)

        memory = get_memory_info()
        data['memory_total'] = int(memory.total)
        data['memory_available'] = int(memory.available)
        data['memory_percent'] = float(memory.percent)
        data['memory_used'] = int(memory.used)
    
        network_speed = get_network_speed()
        data['network_upload_speed'] = int(network_speed.upload)
        data['network_download_speed'] = int(network_speed.download)
    
        self.event.publish('data_changed', data)

    @log_error
    def task_3s(self):
        data = {}
        ips = get_ips()
        data['ips'] = ips
        for name in ips:
            data[f'ip_{name}'] = ips[name]
        
        network_connection_type = get_network_connection_type()
        data['network_type'] = "&".join(network_connection_type)

        self.event.publish('data_changed', data)

    @log_error
    def task_5s(self):
        data = {}
        data['disk_list'] = get_disks()
        disks = get_disks_info(temperature=True)
        data['disks'] = disks
        for disk_name in disks:
            disk = disks[disk_name]
            data[f'disk_{disk_name}_mounted'] = int(disk.mounted)
            data[f'disk_{disk_name}_total'] = int(disk.total)
            data[f'disk_{disk_name}_used'] = int(disk.used)
            data[f'disk_{disk_name}_free'] = int(disk.free)
            data[f'disk_{disk_name}_percent'] = float(disk.percent)
        
        self.event.publish('data_changed', data)

    @log_error
    async def _main(self):
        self.log.debug("SystemAddon main loop started")
        await self.tasks.run_once(self.task_once, 1)
        await self.tasks.run_periodically(self.task_1s, 1)
        await self.tasks.run_periodically(self.task_3s, 3)
        await self.tasks.run_periodically(self.task_5s, 5)
        while self.running:
            await asyncio.sleep(1)

    @log_error
    async def _stop(self):
        await self.tasks.stop()
