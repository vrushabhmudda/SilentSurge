import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from google.adk.agents import LlmAgent, ParallelAgent, LoopAgent
from google.adk.tools import FunctionTool

from silentsurge.agents.vitals_watcher import analyze_vitals
from silentsurge.agents.lab_interpreter import analyze_labs
from silentsurge.agents.med_reviewer import analyze_medications
from silentsurge.data.patients import get_patient
from silentsurge.data.stream import get_stream, reset_stream


def monitor_patient_realtime(patient_id: str, ticks: int = 6) -> dict:
    stream = get_stream(patient_id, scenario="deteriorating")
    timeline = []
    escalation_tick = None

    for _ in range(ticks):
        reading = next(stream)
        timeline.append(reading)
        if reading["sepsis_suspected"] and escalation_tick is None:
            escalation_tick = reading["tick"]

    final = timeline[-1]
    
    # Build stream-based risk score from alert count
    alert_count = final["alert_count"]
    stream_risk = min(alert_count * 35, 100)  # 1 alert=35, 2=70, 3+=100

    summary = {
        "patient_id": patient_id,
        "readings": timeline,
        "total_ticks": ticks,
        "escalation_triggered": escalation_tick is not None,
        "escalation_at_tick": escalation_tick,
        "final_status": final["status"],
        "final_alerts": final["alerts"],
        "stream_risk_score": stream_risk,  # ← pass this to briefing
    }

    if escalation_tick:
        summary["message"] = f"⚠️ Sepsis suspected at tick {escalation_tick}. Immediate review required."
    else:
        summary["message"] = "Patient stable across all readings."

    return summary



def reset_patient_monitor(patient_id: str) -> dict:
    """Reset a patient's monitoring stream back to baseline."""
    reset_stream(patient_id)
    return {"message": f"Stream for {patient_id} reset to baseline."}

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_physician_briefing(patient_id: str,
                                 risk_score: int = None,
                                 flags: list = None) -> dict:
    """Generate physician briefing using static or streamed patient data."""
    patient = get_patient(patient_id)
    name = patient["name"] if patient else f"Patient {patient_id}"
    age  = patient["age"]  if patient else "Unknown"

    # Use passed-in stream data if available, otherwise calculate from static
    if risk_score is None or flags is None:
        if not patient:
            return {"error": "No patient data available"}
        vitals = analyze_vitals(patient)
        labs   = analyze_labs(patient)
        meds   = analyze_medications(patient)
        risk_score = min(vitals["risk_score"] + labs["risk_score"] + meds["risk_adjustment"], 100)
        flags  = vitals["flags"] + labs["flags"] + meds["flags"]

    flags_text = "\n".join(flags) if flags else "Deteriorating vitals detected via real-time stream"

    prompt = f"""You are a clinical AI assistant. Write a concise physician briefing (3-4 sentences max).

Patient: {name}, {age} years old
Sepsis Risk Score: {risk_score}/100
Clinical Flags:
{flags_text}

Write a direct, clinical briefing. Start with the patient name. End with a specific recommended action."""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"briefing": response.choices[0].message.content, "risk_score": risk_score}


def analyze_all_patients() -> dict:
    """Analyze all ICU patients and return a summary of their sepsis risk."""
    from silentsurge.data.patients import get_patients
    results = []
    for patient in get_patients():
        result = calculate_sepsis_risk(patient["id"])
        results.append(result)
    return {"patients": results}
# ── Tools (your existing logic wrapped as ADK tools) ──────────────────────────

def check_vitals(patient_id: str) -> dict:
    """Check vital signs for a patient and flag sepsis indicators."""
    patient = get_patient(patient_id)
    if not patient:
        return {"error": f"Patient {patient_id} not found"}
    return analyze_vitals(patient)

def check_labs(patient_id: str) -> dict:
    """Analyze lab results for a patient and flag critical values."""
    patient = get_patient(patient_id)
    if not patient:
        return {"error": f"Patient {patient_id} not found"}
    return analyze_labs(patient)

def check_medications(patient_id: str) -> dict:
    """Review medications for a patient and detect masking drugs like beta-blockers."""
    patient = get_patient(patient_id)
    if not patient:
        return {"error": f"Patient {patient_id} not found"}
    return analyze_medications(patient)

def calculate_sepsis_risk(patient_id: str) -> dict:
    """Calculate final sepsis risk score by combining vitals, labs, and medication analysis."""
    patient = get_patient(patient_id)
    if not patient:
        return {"error": f"Patient {patient_id} not found"}
    
    vitals = analyze_vitals(patient)
    labs = analyze_labs(patient)
    meds = analyze_medications(patient)
    
    base_score = vitals["risk_score"] + labs["risk_score"] + meds["risk_adjustment"]
    
    correction_applied = False
    if meds["beta_blocker_masking"] and vitals["risk_score"] > 0:
        base_score += 25
        correction_applied = True
    
    final_score = min(base_score, 100)
    
    return {
        "patient_id": patient_id,
        "patient_name": patient["name"],
        "final_risk_score": final_score,
        "self_correction_applied": correction_applied,
        "vitals_flags": vitals["flags"],
        "labs_flags": labs["flags"],
        "meds_flags": meds["flags"],
        "requires_escalation": final_score >= 60
    }

# ── Specialist Agents ─────────────────────────────────────────────────────────

vitals_agent = LlmAgent(
    name="VitalsWatcher",
    model="gemini-2.5-flash",
    description="Specialist agent that monitors patient vital signs for sepsis indicators including heart rate trends, fever, and blood pressure drops.",
    instruction="""You are VitalsWatcher, a specialist ICU monitoring agent.
When given a patient_id, call check_vitals to analyze their vital signs.
Report any flags clearly. Focus on TRENDS not just current values.
If heart rate is rising rapidly, flag it as high priority.""",
    tools=[FunctionTool(check_vitals)],
)

lab_agent = LlmAgent(
    name="LabInterpreter",
    model="gemini-2.5-flash",
    description="Specialist agent that interprets lab results including lactate, WBC, and creatinine for sepsis indicators.",
    instruction="""You are LabInterpreter, a specialist ICU lab analysis agent.
When given a patient_id, call check_labs to analyze their lab results.
Lactate above 2.0 is a critical sepsis indicator. Report findings clearly.""",
    tools=[FunctionTool(check_labs)],
)

med_agent = LlmAgent(
    name="MedReviewer",
    model="gemini-2.5-flash",
    description="Specialist agent that reviews medications to detect drugs that mask sepsis symptoms like beta-blockers.",
    instruction="""You are MedReviewer, a specialist ICU medication review agent.
When given a patient_id, call check_medications to detect masking drugs.
Beta-blockers suppress heart rate and hide the true severity of sepsis.""",
    tools=[FunctionTool(check_medications)],
)

# ── Parallel Agent (all 3 specialists run simultaneously) ────────────────────

parallel_monitor = ParallelAgent(
    name="ParallelICUMonitor",
    description="Runs VitalsWatcher, LabInterpreter, and MedReviewer simultaneously across all data streams.",
    sub_agents=[vitals_agent, lab_agent, med_agent],
)

# ── Orchestrator Agent ────────────────────────────────────────────────────────

orchestrator = LlmAgent(
    name="SepsisOrchestrator",
    model="gemini-2.5-flash",
    instruction="""You are SilentSurge, an ICU sepsis detection orchestrator.

You can:
1. Analyze a single patient snapshot → call calculate_sepsis_risk(patient_id)
2. Analyze ALL patients → call analyze_all_patients()
3. Generate physician briefing for high-risk patients → call generate_physician_briefing(patient_id)
4. Continuously monitor a patient in real-time → call monitor_patient_realtime(patient_id, ticks=6)
5. Reset a patient's monitor stream → call reset_patient_monitor(patient_id)

For real-time monitoring requests like "monitor PT009", "watch PT009", or "continuously monitor":
- Call monitor_patient_realtime with that patient_id
- Present the timeline tick by tick showing vitals progression
- Highlight the exact tick where sepsis was first suspected
- If escalation_triggered is True in the result, call generate_physician_briefing with:
    patient_id = the patient_id
    risk_score = stream_risk_score from the monitoring result
    flags = final_alerts from the monitoring result

For single patient analysis requests like "analyze PT004" or "check PT004":
- Call calculate_sepsis_risk(patient_id)
- If requires_escalation is True, also call generate_physician_briefing(patient_id)
- Report risk score, all flags, and whether escalation is required

For overview requests like "all patients", "overview", "general runthrough":
- Call analyze_all_patients()
- Present results ranked from highest to lowest risk
- Auto-generate physician briefing for any patient with risk >= 60

Always be direct and clinical. Never ask for confirmation before running tools.""",
    tools=[
        FunctionTool(calculate_sepsis_risk),
        FunctionTool(generate_physician_briefing),
        FunctionTool(analyze_all_patients),
        FunctionTool(monitor_patient_realtime),
        FunctionTool(reset_patient_monitor),
    ],
)

# ── Root Agent ────────────────────────────────────────────────────────────────

root_agent = LoopAgent(
    name="SilentSurge",
    description="Root orchestrator for ICU sepsis monitoring.",
    sub_agents=[orchestrator],
    max_iterations=1,
)

