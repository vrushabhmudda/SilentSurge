import pandas as pd
import os

MIMIC_PATH = os.path.join(os.path.dirname(__file__), "mimic_samples")

# MIMIC-III item IDs for vitals
VITALS_ITEMS = {
    "heart_rate":    [211, 220045],
    "sbp":           [51, 220179],
    "temperature":   [678, 223761],  # °F
    "spo2":          [646, 220277],
}

# MIMIC-III item IDs for labs
LAB_ITEMS = {
    "lactate":    [50813],
    "wbc":        [51301],
    "creatinine": [50912],
}

BETA_BLOCKERS = ["metoprolol", "atenolol", "propranolol", "carvedilol", "labetalol"]

# Load once at module level
_chart = pd.read_csv(f"{MIMIC_PATH}/CHARTEVENTS.csv", low_memory=False)
_labs  = pd.read_csv(f"{MIMIC_PATH}/LABEVENTS.csv",   low_memory=False)
_meds  = pd.read_csv(f"{MIMIC_PATH}/PRESCRIPTIONS.csv", low_memory=False)

def get_available_patient_ids() -> list:
    """Return list of subject_ids present in all 3 data sources."""
    ids = set(_chart["subject_id"]) & set(_labs["subject_id"]) & set(_meds["subject_id"])
    return sorted([str(i) for i in ids])

def get_patient_vitals(patient_id: str) -> dict:
    pt = _chart[_chart["subject_id"] == int(patient_id)]
    
    def latest(item_ids):
        rows = pt[pt["itemid"].isin(item_ids)]["valuenum"].dropna()
        return round(float(rows.iloc[-1]), 1) if not rows.empty else None

    hr   = latest(VITALS_ITEMS["heart_rate"])
    sbp  = latest(VITALS_ITEMS["sbp"])
    temp_f = latest(VITALS_ITEMS["temperature"])
    temp_c = round((temp_f - 32) * 5/9, 1) if temp_f else None
    spo2 = latest(VITALS_ITEMS["spo2"])

    return {
        "heart_rate": hr,
        "sbp": sbp,
        "temperature": temp_c,
        "spo2": spo2,
        "source": "MIMIC-III ChartEvents"
    }

def get_patient_labs(patient_id: str) -> dict:
    pt = _labs[_labs["subject_id"] == int(patient_id)]
    
    def latest(item_ids):
        rows = pt[pt["itemid"].isin(item_ids)]["valuenum"].dropna()
        return round(float(rows.iloc[-1]), 2) if not rows.empty else None

    return {
        "lactate":    latest(LAB_ITEMS["lactate"]),
        "wbc":        latest(LAB_ITEMS["wbc"]),
        "creatinine": latest(LAB_ITEMS["creatinine"]),
        "source": "MIMIC-III LabEvents"
    }

def get_patient_meds(patient_id: str) -> dict:
    pt = _meds[_meds["subject_id"] == int(patient_id)]
    drugs = pt["drug"].dropna().str.lower().tolist()
    masking = [d for d in drugs if any(b in d for b in BETA_BLOCKERS)]
    
    return {
        "medications": list(set(drugs)),
        "beta_blocker_masking": len(masking) > 0,
        "masking_drugs": list(set(masking)),
        "source": "MIMIC-III Prescriptions"
    }

def get_patient(patient_id: str) -> dict:
    """Drop-in replacement for your existing get_patient()."""
    try:
        vitals = get_patient_vitals(patient_id)
        labs   = get_patient_labs(patient_id)
        meds   = get_patient_meds(patient_id)
        return {
            "id": patient_id,
            "name": f"ICU Patient {patient_id}",
            "age": 65,
            "vitals": vitals,
            "labs": labs,
            "medications": meds["medications"],
            "beta_blocker": meds["beta_blocker_masking"],
            "source": "MIMIC-III Demo Dataset"
        }
    except Exception as e:
        return {"error": str(e)}
