patients = [
    {"id": "PT001", "name": "James Carter", "age": 72, "vitals": {"heart_rate": 88, "hr_trend": 2, "temp": 37.1, "resp_rate": 16, "bp": "118/76"}, "labs": {"wbc": 8.2, "lactate": 1.1, "creatinine": 1.0}, "medications": ["lisinopril"], "beta_blocker": False, "sepsis_risk": 12},
    {"id": "PT002", "name": "Maria Lopez", "age": 65, "vitals": {"heart_rate": 91, "hr_trend": 1, "temp": 37.4, "resp_rate": 17, "bp": "122/80"}, "labs": {"wbc": 9.1, "lactate": 1.3, "creatinine": 1.1}, "medications": ["metformin"], "beta_blocker": False, "sepsis_risk": 18},
    {"id": "PT003", "name": "Robert Kim", "age": 58, "vitals": {"heart_rate": 85, "hr_trend": 0, "temp": 36.9, "resp_rate": 15, "bp": "130/85"}, "labs": {"wbc": 7.8, "lactate": 1.0, "creatinine": 0.9}, "medications": ["atorvastatin"], "beta_blocker": False, "sepsis_risk": 8},
    {"id": "PT004", "name": "Susan Patel", "age": 67, "vitals": {"heart_rate": 93, "hr_trend": 8, "temp": 38.6, "resp_rate": 22, "bp": "98/62"}, "labs": {"wbc": 14.2, "lactate": 2.8, "creatinine": 1.8}, "medications": ["metoprolol", "warfarin"], "beta_blocker": True, "sepsis_risk": 35},
    {"id": "PT005", "name": "David Chen", "age": 45, "vitals": {"heart_rate": 80, "hr_trend": 0, "temp": 37.0, "resp_rate": 14, "bp": "125/82"}, "labs": {"wbc": 7.5, "lactate": 0.9, "creatinine": 0.8}, "medications": ["omeprazole"], "beta_blocker": False, "sepsis_risk": 5},
    {"id": "PT006", "name": "Linda Brown", "age": 79, "vitals": {"heart_rate": 95, "hr_trend": 3, "temp": 37.8, "resp_rate": 19, "bp": "110/70"}, "labs": {"wbc": 11.1, "lactate": 1.6, "creatinine": 1.3}, "medications": ["amlodipine"], "beta_blocker": False, "sepsis_risk": 28},
    {"id": "PT007", "name": "Thomas Wright", "age": 55, "vitals": {"heart_rate": 82, "hr_trend": 1, "temp": 37.2, "resp_rate": 16, "bp": "135/88"}, "labs": {"wbc": 8.9, "lactate": 1.2, "creatinine": 1.0}, "medications": ["lisinopril", "aspirin"], "beta_blocker": False, "sepsis_risk": 14},
    {"id": "PT008", "name": "Patricia Moore", "age": 83, "vitals": {"heart_rate": 89, "hr_trend": 2, "temp": 37.5, "resp_rate": 18, "bp": "115/72"}, "labs": {"wbc": 10.2, "lactate": 1.4, "creatinine": 1.2}, "medications": ["furosemide"], "beta_blocker": False, "sepsis_risk": 22},
    {"id": "PT009", "name": "Alex Turner", "age": 54, "vitals": {"heart_rate": 78, "hr_trend": 0, "temp": 37.2, "resp_rate": 16, "bp": "118/76"}, "labs": {"lactate": 1.2, "wbc": 8.1, "creatinine": 0.9}, "medications": [], "beta_blocker": False, "sepsis_risk": 5},
]


def get_patients():
    return patients


def get_patient(patient_id):
    return next((p for p in patients if p["id"] == patient_id), None)