import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.patients import get_patients

def analyze_labs(patient: dict) -> dict:
    flags = []
    risk_score = 0
    labs = patient["labs"]

    if labs["lactate"] >= 2.0:
        flags.append(f"CRITICAL lactate: {labs['lactate']} mmol/L (normal < 2.0)")
        risk_score += 40

    elif labs["lactate"] >= 1.5:
        flags.append(f"ELEVATED lactate: {labs['lactate']} mmol/L")
        risk_score += 20

    if labs["wbc"] > 12.0:
        flags.append(f"HIGH white blood cells: {labs['wbc']} K/uL (infection indicator)")
        risk_score += 25

    elif labs["wbc"] < 4.0:
        flags.append(f"CRITICALLY LOW white blood cells: {labs['wbc']} K/uL")
        risk_score += 25

    if labs["creatinine"] >= 1.5:
        flags.append(f"ELEVATED creatinine: {labs['creatinine']} mg/dL (kidney stress)")
        risk_score += 20

    return {
        "patient_id": patient["id"],
        "patient_name": patient["name"],
        "flags": flags,
        "risk_score": risk_score,
        "triggered": len(flags) >= 1
    }

def run_lab_interpreter():
    patients = get_patients()
    results = []
    for patient in patients:
        result = analyze_labs(patient)
        results.append(result)
        if result["triggered"]:
            print(f"🧪  LAB ALERT — {result['patient_name']} ({result['patient_id']})")
            for flag in result["flags"]:
                print(f"   → {flag}")
            print(f"   Risk contribution: {result['risk_score']}")
            print()
    return results

if __name__ == "__main__":
    run_lab_interpreter()
