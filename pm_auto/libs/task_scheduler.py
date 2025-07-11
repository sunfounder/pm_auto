import asyncio
import time
from typing import Callable

class TaskScheduler:
    """极简异步任务调度系统，通过回调暴露关键节点"""
    
    def __init__(self):
        self.tasks = {}  # 存储所有任务
        self._stop_event = asyncio.Event()
        self._callbacks = {
            "task_start": [],
            "task_complete": [],
            "task_error": [],
            "task_cancel": [],
        }
    
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """
        注册事件回调
        
        Args:
            event_type: 事件类型，可选值: task_start, task_complete, task_error, task_cancel
            callback: 回调函数，接受任务ID和相关数据作为参数
        """
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def _trigger_callback(self, event_type: str, task_id: str, **kwargs) -> None:
        """触发事件回调"""
        for callback in self._callbacks[event_type]:
            callback(task_id, **kwargs)
    
    async def run_once(self, func: Callable, delay: float = 0, *args, **kwargs) -> str:
        """注册一次性任务"""
        task_id = f"once-{int(time.time()*1000)}-{len(self.tasks)}"
        
        async def _wrapper():
            await asyncio.sleep(delay)
            if not self._stop_event.is_set():
                self._trigger_callback("task_start", task_id, task_type="once")
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    self._trigger_callback("task_complete", task_id, result=result)
                except Exception as e:
                    self._trigger_callback("task_error", task_id, error=e)
                finally:
                    self.tasks.pop(task_id, None)
        
        self.tasks[task_id] = asyncio.create_task(_wrapper())
        return task_id
    
    async def run_periodically(self, func: Callable, interval: float, initial_delay: float = 0, *args, **kwargs) -> str:
        """注册周期性任务"""
        task_id = f"periodic-{int(time.time()*1000)}-{len(self.tasks)}"
        
        async def _wrapper():
            if initial_delay > 0:
                await asyncio.sleep(initial_delay)
                
            while not self._stop_event.is_set():
                start_time = time.time()
                self._trigger_callback("task_start", task_id, task_type="periodic")
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    self._trigger_callback("task_complete", task_id, result=result, duration=time.time()-start_time)
                except Exception as e:
                    self._trigger_callback("task_error", task_id, error=e, duration=time.time()-start_time)
                
                # 计算执行耗时并调整下一次执行时间
                elapsed = time.time() - start_time
                wait_time = max(0, interval - elapsed)
                await asyncio.sleep(wait_time)
        
        self.tasks[task_id] = asyncio.create_task(_wrapper())
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """取消指定任务"""
        task = self.tasks.pop(task_id, None)
        if task:
            task.cancel()
            self._trigger_callback("task_cancel", task_id)
            return True
        return False
    
    def cancel_all_tasks(self) -> None:
        """取消所有任务"""
        for task_id in list(self.tasks.keys()):
            self.cancel_task(task_id)

    async def stop(self) -> None:
        """停止调度器并清理资源"""
        self._stop_event.set()
        self.cancel_all_tasks()
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)
