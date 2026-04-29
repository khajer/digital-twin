from __future__ import annotations
import time, random, threading, statistics
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Callable, Any

# ─── Data model ────────────────────────────────────────────────────────────────

@dataclass
class SensorReading:
    sensor_id: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class TwinState:
    readings: dict[str, SensorReading] = field(default_factory=dict)
    desired:  dict[str, float]         = field(default_factory=dict)
    history:  dict[str, deque]         = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=100)))
    alerts:   list[str]                = field(default_factory=list)

# ─── Event bus ─────────────────────────────────────────────────────────────────

class EventBus:
    def __init__(self):
        self._subs: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable):
        self._subs[event].append(handler)

    def publish(self, event: str, payload: Any):
        for handler in self._subs[event]:
            handler(payload)

# ─── Digital Twin core ─────────────────────────────────────────────────────────

class DigitalTwin:
    def __init__(self, twin_id: str):
        self.twin_id = twin_id
        self.state   = TwinState()
        self.bus     = EventBus()
        self._thresholds: dict[str, tuple[float, float]] = {}

    # Ingest a sensor reading
    def ingest(self, reading: SensorReading):
        self.state.readings[reading.sensor_id] = reading
        self.state.history[reading.sensor_id].append(reading.value)
        self.bus.publish("reading", reading)
        self._check_anomaly(reading)

    # Set acceptable range per sensor
    def set_threshold(self, sensor_id: str, lo: float, hi: float):
        self._thresholds[sensor_id] = (lo, hi)

    # Set a desired value (shadow / command)
    def set_desired(self, sensor_id: str, value: float):
        self.state.desired[sensor_id] = value
        self.bus.publish("desired_changed", {"sensor": sensor_id, "value": value})

    # Sync delta: what needs to change to reach desired state
    def sync_delta(self) -> dict[str, float]:
        delta = {}
        for sid, target in self.state.desired.items():
            current = self.state.readings.get(sid)
            if current:
                diff = target - current.value
                if abs(diff) > 0.01:
                    delta[sid] = diff
        return delta

    # Simple anomaly detection: threshold + z-score
    def _check_anomaly(self, reading: SensorReading):
        sid = reading.sensor_id
        alerts = []

        if sid in self._thresholds:
            lo, hi = self._thresholds[sid]
            if not (lo <= reading.value <= hi):
                alerts.append(f"[THRESHOLD] {sid}={reading.value:.2f} outside [{lo}, {hi}]")

        hist = list(self.state.history[sid])
        if len(hist) >= 10:
            mean = statistics.mean(hist)
            stdev = statistics.stdev(hist) or 1e-9
            z = abs((reading.value - mean) / stdev)
            if z > 3.0:
                alerts.append(f"[ANOMALY] {sid}={reading.value:.2f} z={z:.2f}")

        for alert in alerts:
            self.state.alerts.append(alert)
            self.bus.publish("alert", alert)

    # Analytics snapshot
    def analytics(self, sensor_id: str) -> dict:
        hist = list(self.state.history[sensor_id])
        if not hist:
            return {}
        return {
            "count":  len(hist),
            "mean":   round(statistics.mean(hist), 3),
            "stdev":  round(statistics.stdev(hist), 3) if len(hist) > 1 else 0,
            "min":    round(min(hist), 3),
            "max":    round(max(hist), 3),
            "latest": round(hist[-1], 3),
        }

    def summary(self):
        print(f"\n{'─'*50}")
        print(f"Twin: {self.twin_id}")
        for sid, r in self.state.readings.items():
            a = self.analytics(sid)
            delta = self.sync_delta().get(sid, 0)
            print(f"  {sid}: {r.value:.2f} {r.unit}  "
                  f"(mean={a['mean']}, stdev={a['stdev']}, Δdesired={delta:+.2f})")
        if self.state.alerts:
            print(f"  Alerts ({len(self.state.alerts)}):")
            for alert in self.state.alerts[-3:]:
                print(f"    ⚠ {alert}")

# ─── Physical sensor simulator ─────────────────────────────────────────────────

class SensorSimulator:
    """Simulates a physical device pushing readings to the twin."""

    def __init__(self, twin: DigitalTwin):
        self.twin    = twin
        self._running = False

    def _generate(self):
        t = time.time()
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

# ─── Demo ──────────────────────────────────────────────────────────────────────

def main():
    twin = DigitalTwin("machine-001")

    # Set normal operating ranges
    twin.set_threshold("temperature", 60, 80)
    twin.set_threshold("pressure",    0.8, 1.2)
    twin.set_threshold("rpm",         1200, 1800)

    # Set desired state (shadow)
    twin.set_desired("temperature", 72.0)

    # Subscribe to alerts
    twin.bus.subscribe("alert", lambda msg: print(f"  🔔 {msg}"))

    # Run simulator
    sim = SensorSimulator(twin)

    print("Starting digital twin simulation...")
    sim.run(ticks=30, interval=0.2)

    # Final analytics
    twin.summary()
    print("\nSync delta (desired vs actual):")
    for sid, diff in twin.sync_delta().items():
        print(f"  {sid}: needs {diff:+.2f} adjustment")

if __name__ == "__main__":
    main()
