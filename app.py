import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from agent import (
    calculate_sepsis_risk,
    generate_physician_briefing,
    analyze_all_patients,
    monitor_patient_realtime,
    reset_patient_monitor,
)
from data.stream import reset_stream
from data.patients import get_patients

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SilentSurge ICU Monitor",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .badge-critical { background:#c0392b; color:white; padding:3px 10px; border-radius:4px; font-weight:600; font-size:13px; }
    .badge-monitor  { background:#d35400; color:white; padding:3px 10px; border-radius:4px; font-weight:600; font-size:13px; }
    .badge-stable   { background:#1e8449; color:white; padding:3px 10px; border-radius:4px; font-weight:600; font-size:13px; }
    .section-divider { border-top: 1px solid #e0e0e0; margin: 12px 0; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "escalation_decisions" not in st.session_state:
    st.session_state.escalation_decisions = {}

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# SilentSurge")
st.markdown("**Autonomous ICU Sepsis Detection** · Powered by Google ADK + Gemini 2.5 Flash + LLaMA 3.3 70B")
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("Controls")
mode = st.sidebar.radio("Select Mode", [
    "Patient Overview",
    "Single Patient Analysis",
    "Real-Time Monitor",
])

# Load patient IDs for dropdown
all_patient_ids = [p["id"] for p in get_patients()]

st.sidebar.markdown("---")
st.sidebar.markdown("**System Info**")
st.sidebar.markdown(f"- Data: MIMIC-III ({len(all_patient_ids)} ICU patients)")
st.sidebar.markdown("- Agents: VitalsWatcher, LabInterpreter, MedReviewer")
st.sidebar.markdown("- Architecture: ParallelAgent + LoopAgent")
st.sidebar.markdown("- Self-Correction: Beta-blocker masking detection")

# ── Helpers ───────────────────────────────────────────────────────────────────
def risk_badge(score):
    if score >= 60:
        return '<span class="badge-critical">ESCALATE</span>'
    elif score >= 30:
        return '<span class="badge-monitor">MONITOR</span>'
    return '<span class="badge-stable">STABLE</span>'

def render_flags(vitals, labs, meds):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**Vitals Flags**")
        st.markdown("\n".join([f"- {f}" for f in vitals]) if vitals else "- No flags")
    with col_b:
        st.markdown("**Labs Flags**")
        st.markdown("\n".join([f"- {f}" for f in labs]) if labs else "- No flags")
    with col_c:
        st.markdown("**Medication Flags**")
        st.markdown("\n".join([f"- {f}" for f in meds]) if meds else "- No flags")

def render_hitl(patient_id, briefing_text, risk_score):
    decision_key = f"decision_{patient_id}"
    st.markdown("---")
    st.markdown("**Physician Review Required**")
    st.info(f"Physician Briefing (LLaMA 3.3 70B):\n\n{briefing_text}")

    if decision_key not in st.session_state.escalation_decisions:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approve Escalation", key=f"approve_{patient_id}", use_container_width=True, type="primary"):
                st.session_state.escalation_decisions[decision_key] = "approved"
                st.rerun()
        with col2:
            if st.button("Dismiss Alert", key=f"dismiss_{patient_id}", use_container_width=True):
                st.session_state.escalation_decisions[decision_key] = "dismissed"
                st.rerun()
    else:
        decision = st.session_state.escalation_decisions[decision_key]
        if decision == "approved":
            st.success(f"Escalation approved — care team notified for patient {patient_id}.")
        else:
            st.warning(f"Alert dismissed — patient {patient_id} returned to monitoring queue.")

# ── Mode 1: Patient Overview ──────────────────────────────────────────────────
if mode == "Patient Overview":
    st.markdown("## ICU Patient Overview")
    if st.button("Run Full Analysis", use_container_width=True, type="primary"):
        with st.spinner("Running parallel analysis across all patients..."):
            result = analyze_all_patients()
            patients = sorted(result["patients"], key=lambda x: x["final_risk_score"], reverse=True)
        st.session_state["overview_patients"] = patients

    if "overview_patients" in st.session_state:
        patients = st.session_state["overview_patients"]
        critical = [p for p in patients if p["final_risk_score"] >= 60]
        monitor  = [p for p in patients if 30 <= p["final_risk_score"] < 60]
        stable   = [p for p in patients if p["final_risk_score"] < 30]

        c1, c2, c3 = st.columns(3)
        c1.metric("Critical", len(critical))
        c2.metric("Monitor", len(monitor))
        c3.metric("Stable", len(stable))

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        for p in patients:
            score = p["final_risk_score"]
            pid   = p["patient_id"]
            name  = p["patient_name"]

            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{name}** ({pid})")
                with col2:
                    st.markdown(f"Risk: **{score}/100**")
                with col3:
                    st.markdown(risk_badge(score), unsafe_allow_html=True)

                if score >= 60:
                    with st.expander(f"View Details — {name}"):
                        render_flags(p["vitals_flags"], p["labs_flags"], p["meds_flags"])

                        if p.get("self_correction_applied"):
                            st.warning("Self-correction applied: Beta-blocker masking detected. Risk score adjusted upward by +25 points.")

                        with st.spinner("Generating physician briefing..."):
                            briefing = generate_physician_briefing(pid)

                        render_hitl(pid, briefing["briefing"], score)

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Mode 2: Single Patient ────────────────────────────────────────────────────
elif mode == "Single Patient Analysis":
    st.markdown("## Single Patient Analysis")

    patient_id = st.selectbox("Select Patient ID", options=all_patient_ids)

    if st.button("Analyze Patient", use_container_width=True, type="primary") and patient_id:
        with st.spinner(f"Running parallel agent analysis for {patient_id}..."):
            result = calculate_sepsis_risk(patient_id)
        st.session_state["single_result"] = result
        st.session_state["single_pid"] = patient_id

    if "single_result" in st.session_state:
        result = st.session_state["single_result"]
        pid    = st.session_state["single_pid"]

        if "error" in result:
            st.error(result["error"])
        else:
            score = result["final_risk_score"]

            st.markdown(f"### {result['patient_name']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Risk Score", f"{score}/100")
            col2.metric("Escalation Required", "YES" if result["requires_escalation"] else "NO")
            col3.metric("Self-Correction", "Applied" if result["self_correction_applied"] else "Not Needed")

            st.progress(score / 100)
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            render_flags(result["vitals_flags"], result["labs_flags"], result["meds_flags"])

            if result["self_correction_applied"]:
                st.warning("Self-Correction Applied: Beta-blocker masking detected. True sepsis severity was underestimated. Risk score adjusted upward by +25 points.")

            if result["requires_escalation"]:
                st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                with st.spinner("Generating physician briefing via LLaMA 3.3 70B..."):
                    briefing = generate_physician_briefing(pid)
                render_hitl(pid, briefing["briefing"], score)

# ── Mode 3: Real-Time Monitor ─────────────────────────────────────────────────
elif mode == "Real-Time Monitor":
    st.markdown("## Real-Time Patient Monitoring")

    patient_id = st.selectbox("Select Patient ID to Monitor", options=all_patient_ids)

    col1, col2 = st.columns(2)
    with col1:
        ticks = st.slider("Number of readings", min_value=3, max_value=12, value=6)
    with col2:
        if st.button("Reset Stream", use_container_width=True) and patient_id:
            reset_stream(patient_id)
            st.success(f"Stream reset for {patient_id}")

    if st.button("Start Monitoring", use_container_width=True, type="primary") and patient_id:
        with st.spinner(f"Monitoring {patient_id}..."):
            result = monitor_patient_realtime(patient_id, ticks=ticks)
        st.session_state["monitor_result"] = result
        st.session_state["monitor_pid"] = patient_id

    if "monitor_result" in st.session_state:
        result = st.session_state["monitor_result"]
        pid    = st.session_state["monitor_pid"]

        st.markdown("### Vitals Timeline")

        header = st.columns([1, 2, 2, 2, 2, 3])
        for col, label in zip(header, ["Tick", "Heart Rate", "Temperature", "BP Systolic", "Lactate", "Status"]):
            col.markdown(f"**{label}**")
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        for reading in result["readings"]:
            cols = st.columns([1, 2, 2, 2, 2, 3])
            cols[0].markdown(f"Tick {reading['tick']}")
            cols[1].markdown(f"{reading['heart_rate']} bpm")
            cols[2].markdown(f"{reading['temp']} C")
            cols[3].markdown(f"{reading['bp_systolic']} mmHg")
            cols[4].markdown(f"{reading['lactate']} mmol/L")
            cols[5].markdown(reading["status"])

            if reading["sepsis_suspected"]:
                st.error(f"Tick {reading['tick']} — SEPSIS SUSPECTED | {', '.join(reading['alerts'])}")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        if result["escalation_triggered"]:
            st.error(f"Sepsis detected at Tick {result['escalation_at_tick']}. Generating physician briefing...")
            with st.spinner("Contacting LLaMA 3.3 70B via Groq..."):
                briefing = generate_physician_briefing(
                    pid,
                    risk_score=result["stream_risk_score"],
                    flags=result["final_alerts"]
                )
            render_hitl(pid, briefing["briefing"], result["stream_risk_score"])
        else:
            st.success("Patient stable across all readings. No escalation required.")
