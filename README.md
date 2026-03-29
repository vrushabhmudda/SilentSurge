# SilentSurge

Multi-agent AI system for real-time sepsis detection in ICU patients. Built with Google ADK, Gemini 2.5 Flash, and LLaMA 3.3 70B.

# Overview
SilentSurge monitors ICU patients using real MIMIC-III clinical data and a parallel multi-agent workforce to detect sepsis before it becomes fatal. Sepsis kills 11 million people per year — 80% preventable with early detection.

# Architecture 
```bash
ParallelAgent
├── VitalsWatcher      → heart rate, temp, BP, lactate
├── LabInterpreter     → lab panels, biomarkers
└── MedReviewer        → beta-blocker masking detection

LoopAgent              → iterative self-correction
EscalationAgent        → physician briefing via LLaMA 3.3 70B
Human-in-the-Loop      → physician approval before escalation
```
# Tech Stack

| Layer      | Technology                                        |
| ---------- | ------------------------------------------------- |
| Agents     | Google ADK, ParallelAgent, LoopAgent              |
| LLMs       | Gemini 2.5 Flash, LLaMA 3.3 70B                   |
| Inference  | Groq API                                          |
| Data       | MIMIC-III (ChartEvents, LabEvents, Prescriptions) |
| Frontend   | Streamlit                                         |
| Deployment | Google Cloud Run, Docker                          |
| Language   | Python                                            |

# Run Locally
```bash
git clone https://github.com/vrushabhmudda/silentsurge
cd silentsurge
pip install -r requirements.txt
streamlit run app.py
```

# SDG Alignment

UN SDG 3 — Good Health and Well-Being

