import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.patients import get_patients

def analyze_vitals(patient: dict) -> dict:
    flags = []
    risk_score = 0
    v = patient["vitals"]

    if v["heart_rate"] > 90:
        flags.append(f"HIGH heart rate: {v['heart_rate']} bpm")
        risk_score += 20

    if v["hr_trend"] >= 5:
        flags.append(f"RISING heart rate trend: +{v['hr_trend']} bpm/hr")
        risk_score += 25

    if v["temp"] >= 38.3:
        flags.append(f"FEVER: {v['temp']}°C")
        risk_score += 20

    if v["resp_rate"] >= 20:
        flags.append(f"HIGH respiratory rate: {v['resp_rate']} breaths/min")
        risk_score += 15

    systolic = int(v["bp"].split("/")[0])
    if systolic < 100:
        flags.append(f"LOW blood pressure: {v['bp']}")
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
