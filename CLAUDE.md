# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the project

```bash
python main.py
```

No build step, no external dependencies — pure Python stdlib.

## Architecture

This is a proof-of-concept digital twin for a physical machine (`machine-001`), using an event-driven architecture.

**Data flow:**
1. `SensorSimulator` generates Gaussian-noise readings (temperature, pressure, rpm)
2. Readings are ingested by `DigitalTwin.ingest()`, which updates state and checks for anomalies
3. Anomaly detection uses two strategies: absolute threshold violations and z-score (>3σ) over rolling history
4. Events (`"reading"`, `"alert"`, `"desired_changed"`) are published via `EventBus` (pub-sub)
5. `DigitalTwin` also tracks a *desired* (shadow) state; `sync_delta()` returns the gap between desired and actual

**Key modules in `digital_twin_pkg/`:**

- `digital_twin.py` — core state machine: ingests readings, manages thresholds, computes analytics
- `event_bus.py` — minimal pub-sub; no ordering guarantees, no persistence
- `models.py` — `SensorReading` and `TwinState` dataclasses; history is a `deque(maxlen=100)` per sensor
- `sensor_simulator.py` — drives the twin by calling `ingest()` in a loop

**State stored on `TwinState`:** latest readings per sensor, desired values, per-sensor history deque, alert list.
