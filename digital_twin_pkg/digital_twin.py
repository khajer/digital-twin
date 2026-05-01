from __future__ import annotations
import statistics

from .models import SensorReading, TwinState
from .event_bus import EventBus


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
