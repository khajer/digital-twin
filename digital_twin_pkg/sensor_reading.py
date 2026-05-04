from __future__ import annotations
import time
from dataclasses import dataclass, field


@dataclass
class SensorReading:
    sensor_id: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
