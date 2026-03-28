import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from groq import Groq
from data.patients import get_patients
from agents.vitals_watcher import analyze_vitals
from agents.lab_interpreter import analyze_labs
from agents.med_reviewer import analyze_medications

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def calculate_final_risk(vitals_result, labs_result, meds_result):
    base_score = vitals_result["risk_score"] + labs_result["risk_score"] + meds_result["risk_adjustment"]
    
    # LoopAgent self-correction: if beta-blocker masking, vitals are underestimated
    if meds_result["beta_blocker_masking"] and vitals_result["risk_score"] > 0:
        correction = 25
        print(f"   🔄 SELF-CORRECTION: Beta-blocker masking detected.")
        print(f"   Previous estimate was too conservative. Adding +{correction} correction.")
        base_score += correction

    return min(base_score, 100)

def generate_briefing(patient, final_risk, vitals_flags, labs_flags, meds_flags):
    all_flags = vitals_flags + labs_flags + meds_flags
    flags_text = "\n".join(all_flags)

    prompt = f"""You are a clinical AI assistant. Write a concise physician briefing (3-4 sentences max) for the following patient showing sepsis indicators.

Patient: {patient['name']}, {patient['age']} years old
Sepsis Risk Score: {final_risk}/100
Clinical Flags:
{flags_text}

Write a direct, clinical briefing. Start with the patient name. End with a specific recommended action."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def run_escalation_agent():
    patients = get_patients()
    alerts = []

    print("🏥 SilentSurge — ICU Sepsis Monitoring System")
    print("=" * 55)

    for patient in patients:
        vitals = analyze_vitals(patient)
        labs = analyze_labs(patient)
        meds = analyze_medications(patient)

        final_risk = calculate_final_risk(vitals, labs, meds)

        if final_risk >= 60:
            print(f"\n🚨 ESCALATION ALERT — {patient['name']} ({patient['id']})")
            print(f"   Initial Risk Score: {vitals['risk_score'] + labs['risk_score'] + meds['risk_adjustment'] - (25 if meds['beta_blocker_masking'] else 0)}%")
            print(f"   Final Risk Score:   {final_risk}%")
            print(f"\n   Generating physician briefing...")
            briefing = generate_briefing(patient, final_risk, vitals["flags"], labs["flags"], meds["flags"])
            print(f"\n📋 PHYSICIAN BRIEFING:")
            print(f"   {briefing}")
            print("=" * 55)
            alerts.append({"patient": patient["name"], "risk": final_risk, "briefing": briefing})

        else:
            status = "🟡 MONITOR" if final_risk >= 30 else "🟢 STABLE"
            print(f"{status} — {patient['name']:20} Risk: {final_risk}%")

    return alerts

if __name__ == "__main__":
    run_escalation_agent()
