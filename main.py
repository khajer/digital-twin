from digital_twin_pkg.digital_twin import DigitalTwin
from digital_twin_pkg.sensor_simulator import SensorSimulator


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
