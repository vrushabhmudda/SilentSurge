from silentsurge.data.mimic_loader import get_patient, get_available_patient_ids

def get_patients() -> list:
    return [get_patient(pid) for pid in get_available_patient_ids()]
