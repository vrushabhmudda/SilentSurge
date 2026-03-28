import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent, ParallelAgent, LoopAgent
from google.adk.tools import FunctionTool

from silentsurge.agents.vitals_watcher import analyze_vitals
from silentsurge.agents.lab_interpreter import analyze_labs
from silentsurge.agents.med_reviewer import analyze_medications
from silentsurge.data.patients import get_patient

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
    description="Orchestrates sepsis analysis by extracting patient ID and coordinating all specialist agents.",
    instruction="""You are SilentSurge, an ICU sepsis detection orchestrator.

When the user provides a patient ID (e.g. 'Analyze patient PT004' or just 'PT004'):
1. Extract the patient_id from their message
2. Call calculate_sepsis_risk with that patient_id
3. Report the final risk score, flags, and whether escalation is required
4. Be direct and clinical in your response

Always extract and use the patient_id from the user's input. Never ask sub-agents to request it.""",
    tools=[FunctionTool(calculate_sepsis_risk)],
)

# ── Root Agent ────────────────────────────────────────────────────────────────

root_agent = LoopAgent(
    name="SilentSurge",
    description="Root orchestrator for ICU sepsis monitoring.",
    sub_agents=[orchestrator],
    max_iterations=3,
)

