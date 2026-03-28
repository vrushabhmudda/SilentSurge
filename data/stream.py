import random
from datetime import datetime

_streams = {}

def generate_vitals_stream(patient_id: str, scenario: str = "deteriorating"):
    profiles = {
        "deteriorating": {
            "heart_rate": 78, "hr_drift": 2.5,
            "temp": 37.2,     "temp_drift": 0.15,
            "resp_rate": 16,  "rr_drift": 0.8,
            "bp_sys": 118,    "bp_drift": -3.0,
            "lactate": 1.2,   "lac_drift": 0.2,
        },
        "stable": {
            "heart_rate": 72, "hr_drift": 0.0,
            "temp": 37.0,     "temp_drift": 0.0,
            "resp_rate": 15,  "rr_drift": 0.0,
            "bp_sys": 122,    "bp_drift": 0.0,
            "lactate": 1.0,   "lac_drift": 0.01,
        },
        "recovering": {
            "heart_rate": 95, "hr_drift": -1.5,
            "temp": 38.8,     "temp_drift": -0.2,
            "resp_rate": 23,  "rr_drift": -0.5,
            "bp_sys": 96,     "bp_drift": +2.0,
            "lactate": 2.6,   "lac_drift": -0.15,
        }
    }

    state = {k: v for k, v in profiles[scenario].items()}
    tick = 0

    while True:
        tick += 1
        n = lambda scale=1.0: random.uniform(-0.3, 0.3) * scale

        reading = {
            "patient_id": patient_id,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "tick": tick,
            "heart_rate": round(max(40, state["heart_rate"] + n(2)), 1),
            "temp": round(state["temp"] + n(0.1), 1),
            "resp_rate": round(max(8, state["resp_rate"] + n(0.5)), 1),
            "bp_systolic": round(max(60, state["bp_sys"] + n(2)), 1),
            "lactate": round(max(0.3, state["lactate"] + n(0.05)), 2),
        }

        # Drift forward
        state["heart_rate"] += state["hr_drift"]
        state["temp"]       += state["temp_drift"]
        state["resp_rate"]  += state["rr_drift"]
        state["bp_sys"]     += state["bp_drift"]
        state["lactate"]    += state["lac_drift"]

        # Cap drift so it doesn't go infinite
        state["heart_rate"] = min(state["heart_rate"], 140)
        state["temp"]       = min(state["temp"], 40.5)
        state["resp_rate"]  = min(state["resp_rate"], 35)
        state["lactate"]    = min(state["lactate"], 8.0)

        # Evaluate alerts
        alerts = []
        if reading["heart_rate"] > 90:    alerts.append(f"HIGH HR: {reading['heart_rate']} bpm")
        if reading["temp"] > 38.0:        alerts.append(f"FEVER: {reading['temp']}°C")
        if reading["resp_rate"] > 20:     alerts.append(f"HIGH RR: {reading['resp_rate']} breaths/min")
        if reading["bp_systolic"] < 100:  alerts.append(f"LOW BP: {reading['bp_systolic']} mmHg")
        if reading["lactate"] > 2.0:      alerts.append(f"CRITICAL LACTATE: {reading['lactate']} mmol/L")

        alert_count = len(alerts)
        if alert_count == 0:
            status = "🟢 STABLE"
        elif alert_count == 1:
            status = "🟡 MONITOR"
        else:
            status = "🚨 SEPSIS SUSPECTED"

        reading["alerts"] = alerts
        reading["alert_count"] = alert_count
        reading["status"] = status
        reading["sepsis_suspected"] = alert_count >= 2

        yield reading


def get_stream(patient_id: str, scenario: str = "deteriorating"):
    """Get or create a persistent stream for a patient."""
    key = f"{patient_id}_{scenario}"
    if key not in _streams:
        _streams[key] = generate_vitals_stream(patient_id, scenario)
    return _streams[key]


def reset_stream(patient_id: str):
    """Reset a patient's stream back to baseline."""
    keys_to_delete = [k for k in _streams if k.startswith(patient_id)]
    for k in keys_to_delete:
        del _streams[k]
