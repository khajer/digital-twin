from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque

from .sensor_reading import SensorReading


@dataclass
class TwinState:
    readings: dict[str, SensorReading] = field(default_factory=dict)
    desired:  dict[str, float]         = field(default_factory=dict)
    history:  dict[str, deque]         = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=100)))
    alerts:   list[str]                = field(default_factory=list)
