import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'silentsurge'))

from dotenv import load_dotenv
load_dotenv()

from silentsurge.agent import (
    calculate_sepsis_risk,
    generate_physician_briefing,
    analyze_all_patients,
    monitor_patient_realtime,
    reset_patient_monitor,
)
from silentsurge.data.stream import reset_stream

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SilentSurge ICU Monitor",
    page_icon="🏥",
    layout="wide"
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🏥 SilentSurge")
st.markdown("### AI-Powered ICU Sepsis Detection System")
st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Controls")
mode = st.sidebar.radio("Select Mode", [
    "📊 Patient Overview",
    "🔍 Single Patient Analysis",
    "📡 Real-Time Monitor",
])

# ── Mode 1: All Patients Overview ─────────────────────────────────────────────
if mode == "📊 Patient Overview":
    st.markdown("## 📊 ICU Patient Overview")
    if st.button("🔄 Run Full Analysis", use_container_width=True):
        with st.spinner("Analyzing all patients..."):
            result = analyze_all_patients()
            patients = sorted(result["patients"], key=lambda x: x["final_risk_score"], reverse=True)

        for p in patients:
            score = p["final_risk_score"]
            name  = p["patient_name"]
            pid   = p["patient_id"]

            if score >= 60:
                color = "🚨"
                badge = "ESCALATE"
                tile_color = "#ff4b4b"
            elif score >= 30:
                color = "🟡"
                badge = "MONITOR"
                tile_color = "#ffa500"
            else:
                color = "🟢"
                badge = "STABLE"
                tile_color = "#21c354"

            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{color} {name}** ({pid})")
                with col2:
                    st.markdown(f"Risk: **{score}/100**")
                with col3:
                    st.markdown(f"`{badge}`")

                if score >= 60:
                    with st.expander(f"🚨 View Flags & Briefing — {name}"):
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.markdown("**Vitals Flags**")
                            for f in p["vitals_flags"]:
                                st.markdown(f"- {f}")
                        with col_b:
                            st.markdown("**Labs Flags**")
                            for f in p["labs_flags"]:
                                st.markdown(f"- {f}")
                        with col_c:
                            st.markdown("**Medication Flags**")
                            for f in p["meds_flags"]:
                                st.markdown(f"- {f}")

                        if p.get("self_correction_applied"):
                            st.warning("🔄 Self-correction applied: Beta-blocker masking detected. Risk score adjusted upward.")

                        with st.spinner("Generating physician briefing..."):
                            briefing = generate_physician_briefing(pid)
                        st.info(f"📋 **Physician Briefing:**\n\n{briefing['briefing']}")

            st.markdown("---")

# ── Mode 2: Single Patient ────────────────────────────────────────────────────
elif mode == "🔍 Single Patient Analysis":
    st.markdown("## 🔍 Single Patient Analysis")

    patient_id = st.text_input("Enter Patient ID (e.g. PT004)", placeholder="PT004").upper()

    if st.button("Analyze Patient", use_container_width=True) and patient_id:
        with st.spinner(f"Analyzing {patient_id}..."):
            result = calculate_sepsis_risk(patient_id)

        if "error" in result:
            st.error(result["error"])
        else:
            score = result["final_risk_score"]

            # Risk meter
            st.markdown(f"### Patient: {result['patient_name']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Risk Score", f"{score}/100")
            col2.metric("Escalation Required", "YES 🚨" if result["requires_escalation"] else "NO ✅")
            col3.metric("Self-Correction", "Applied 🔄" if result["self_correction_applied"] else "Not needed")

            st.progress(score / 100)

            # Flags
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown("**🫀 Vitals Flags**")
                for f in result["vitals_flags"]:
                    st.markdown(f"- {f}")
            with col_b:
                st.markdown("**🧪 Labs Flags**")
                for f in result["labs_flags"]:
                    st.markdown(f"- {f}")
            with col_c:
                st.markdown("**💊 Medication Flags**")
                for f in result["meds_flags"]:
                    st.markdown(f"- {f}")

            if result["self_correction_applied"]:
                st.warning("🔄 **Self-Correction Applied:** Beta-blocker masking detected. True sepsis severity was underestimated. Risk score adjusted upward by +25 points.")

            if result["requires_escalation"]:
                st.error("🚨 ESCALATION REQUIRED — Generating physician briefing...")
                with st.spinner("Contacting LLaMA 3.3 70B..."):
                    briefing = generate_physician_briefing(patient_id)
                st.info(f"📋 **Physician Briefing (via LLaMA 3.3 70B):**\n\n{briefing['briefing']}")

# ── Mode 3: Real-Time Monitor ─────────────────────────────────────────────────
elif mode == "📡 Real-Time Monitor":
    st.markdown("## 📡 Real-Time Patient Monitoring")

    patient_id = st.text_input("Enter Patient ID to Monitor", placeholder="PT009").upper()

    col1, col2 = st.columns(2)
    with col1:
        ticks = st.slider("Number of readings", min_value=3, max_value=12, value=6)
    with col2:
        if st.button("🔁 Reset Stream", use_container_width=True) and patient_id:
            reset_stream(patient_id)
            st.success(f"Stream reset for {patient_id}")

    if st.button("▶️ Start Monitoring", use_container_width=True) and patient_id:
        with st.spinner(f"Monitoring {patient_id}..."):
            result = monitor_patient_realtime(patient_id, ticks=ticks)

        st.markdown("### 📈 Vitals Timeline")

        for reading in result["readings"]:
            tick = reading["tick"]
            status = reading["status"]
            is_critical = reading["sepsis_suspected"]

            with st.container():
                cols = st.columns([1, 2, 2, 2, 2, 2])
                cols[0].markdown(f"**Tick {tick}**")
                cols[1].markdown(f"HR: `{reading['heart_rate']} bpm`")
                cols[2].markdown(f"Temp: `{reading['temp']}°C`")
                cols[3].markdown(f"BP: `{reading['bp_systolic']}`")
                cols[4].markdown(f"Lactate: `{reading['lactate']}`")
                cols[5].markdown(status)

            if is_critical:
                st.error(f"🚨 **Tick {tick} — SEPSIS SUSPECTED** | Alerts: {', '.join(reading['alerts'])}")

        if result["escalation_triggered"]:
            st.error(f"⚠️ Sepsis detected at Tick {result['escalation_at_tick']}. Generating physician briefing...")
            with st.spinner("Contacting LLaMA 3.3 70B via Groq..."):
                briefing = generate_physician_briefing(
                    patient_id,
                    risk_score=result["stream_risk_score"],
                    flags=result["final_alerts"]
                )
            st.info(f"📋 **Physician Briefing:**\n\n{briefing['briefing']}")
        else:
            st.success("✅ Patient stable across all readings. No escalation required.")
