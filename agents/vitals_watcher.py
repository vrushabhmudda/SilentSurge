import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.patients import get_patients

def analyze_vitals(patient: dict) -> dict:
    flags = []
    risk_score = 0
    v = patient["vitals"]

    hr = v.get("heart_rate")
    temp = v.get("temperature")
    sbp = v.get("sbp")
    spo2 = v.get("spo2")

    if hr and hr > 90:
        flags.append(f"HIGH heart rate: {hr} bpm")
        risk_score += 20

    if temp and temp >= 38.3:
        flags.append(f"FEVER: {temp}°C")
        risk_score += 20

    if sbp and sbp < 100:
        flags.append(f"LOW blood pressure: {sbp} mmHg")
        risk_score += 20

    if spo2 and spo2 < 95:
        flags.append(f"LOW SpO2: {spo2}%")
        risk_score += 20

    return {
        "patient_id": patient["id"],
        "patient_name": patient["name"],
        "flags": flags,
        "risk_score": risk_score,
        "triggered": len(flags) >= 2
    }

def run_vitals_watcher():
    patients = get_patients()
    results = []
    for patient in patients:
        result = analyze_vitals(patient)
        results.append(result)
        if result["triggered"]:
            print(f"⚠️  VITALS ALERT — {result['patient_name']} ({result['patient_id']})")
            for flag in result["flags"]:
                print(f"   → {flag}")
            print(f"   Risk contribution: {result['risk_score']}")
            print()
    return results

if __name__ == "__main__":
    run_vitals_watcher()
