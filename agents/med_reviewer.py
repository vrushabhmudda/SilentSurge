import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.patients import get_patients

BETA_BLOCKERS = ["metoprolol", "atenolol", "carvedilol", "propranolol", "bisoprolol"]

def analyze_medications(patient: dict) -> dict:
    flags = []
    risk_adjustment = 0
    meds = [m.lower() for m in patient["medications"]]

    beta_blocker_found = any(med in BETA_BLOCKERS for med in meds)

    if beta_blocker_found:
        flags.append(f"⚠️  BETA-BLOCKER detected: {[m for m in meds if m in BETA_BLOCKERS]}")
        flags.append("   True heart rate may be MASKED — patient sicker than vitals suggest")
        risk_adjustment += 30

    if "warfarin" in meds:
        flags.append("ANTICOAGULANT (warfarin) active — bleeding risk during intervention")
        risk_adjustment += 10

    if "immunosuppressant" in meds or "prednisone" in meds:
        flags.append("IMMUNOSUPPRESSANT active — infection signs may be blunted")
        risk_adjustment += 20

    return {
        "patient_id": patient["id"],
        "patient_name": patient["name"],
        "flags": flags,
        "risk_adjustment": risk_adjustment,
        "beta_blocker_masking": beta_blocker_found,
        "triggered": risk_adjustment > 0
    }

def run_med_reviewer():
    patients = get_patients()
    results = []
    for patient in patients:
        result = analyze_medications(patient)
        results.append(result)
        if result["triggered"]:
            print(f"💊  MED ALERT — {result['patient_name']} ({result['patient_id']})")
            for flag in result["flags"]:
                print(f"   {flag}")
            print(f"   Risk adjustment: +{result['risk_adjustment']}")
            print()
    return results

if __name__ == "__main__":
    run_med_reviewer()
