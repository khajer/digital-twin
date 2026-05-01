from __future__ import annotations
import time
import random

from .models import SensorReading
from .digital_twin import DigitalTwin


class SensorSimulator:
    """Simulates a physical device pushing readings to the twin."""

    def __init__(self, twin: DigitalTwin):
        self.twin     = twin
        self._running = False

    def _generate(self):
        return [
            SensorReading("temperature", 70 + 5 * random.gauss(0, 1), "°C"),
            SensorReading("pressure",    1.0 + 0.1 * random.gauss(0, 1), "bar"),
            SensorReading("rpm",         1500 + 200 * random.gauss(0, 1), "rpm"),
        ]

    def run(self, ticks: int = 20, interval: float = 0.3):
        for i in range(ticks):
            for reading in self._generate():
                self.twin.ingest(reading)
            time.sleep(interval)
