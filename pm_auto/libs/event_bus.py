import logging

class EventBus:
    def __init__(self, log=None):
        self.log = log or logging.Logger(__name__)
        self.subscribers = {}  # 事件名 -> 回调函数列表

    def subscribe(self, event_name, callback):
        """订阅事件"""
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        """取消订阅事件"""
        if event_name in self.subscribers:
            self.subscribers[event_name].remove(callback)

    def publish(self, event_name, *args, **kwargs):
        """发布事件"""
        # self.log.debug(f"Event bus publish event {event_name}, ({args}, {kwargs})")
        if event_name in self.subscribers:
            # self.log.debug(f"Event bus fire event: {event_name}")
            for callback in self.subscribers[event_name]:
                callback(*args, **kwargs)
        else:
            self.log.warning(f"Event bus publish a none subscribed event: {event_name}")

    def connect(self, pub_event_name, sub_event_name):
        """连接事件"""
        def bridge(*args, **kwargs):
            self.publish(sub_event_name, *args, **kwargs)
        self.subscribe(pub_event_name, bridge)

    def disconnect(self, pub_event_name, sub_event_name):
        """断开事件连接"""
        if pub_event_name in self.subscribers:
            self.unsubscribe(pub_event_name, bridge)
