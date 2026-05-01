from __future__ import annotations
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        self._subs: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable):
        self._subs[event].append(handler)

    def publish(self, event: str, payload: Any):
        for handler in self._subs[event]:
            handler(payload)
