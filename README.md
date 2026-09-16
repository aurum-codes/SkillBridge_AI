# SkillBridge AI

SkillBridge AI is a Streamlit prototype for SAP Hackfest 2026, built around the
Inclusive Workforce theme. It helps surface demonstrated ability from
non-traditional candidates and connect that evidence to SAP enterprise roles,
while keeping the final hiring decision with a human HR manager.

## What It Demonstrates

The app runs a deterministic, three-agent workflow for each candidate:

1. **Talent Inference Agent** extracts a mock set of skills from GitHub and
   portfolio evidence without requiring or penalizing a formal degree.
2. **Reskilling Pathway Agent** compares those skills with the selected SAP
   role, identifies gaps, and estimates learning time and cost.
3. **SAP SuccessFactors Matching Agent** calculates skill coverage and a match
   score against a simulated open requisition.

An **HR Approval Dashboard** provides the human-in-the-loop checkpoint. HR can
review the recommendation, reskilling investment, and learning path before
approving a candidate for interview or rejecting the recommendation.

## Features

- Candidate intake for name, GitHub profile, portfolio, location, and target role
- Five simulated SAP roles: ABAP Developer, Fiori/UI5 Developer, Business Analyst,
  Basis Administrator, and Data Analyst
- Skill confidence scores, role-specific gap analysis, and learning paths
- Simulated SuccessFactors Talent Intelligence Hub requisition matching
- HR decision notes and an in-session decision log
- Two seeded candidates with completed analysis for an immediate demo

## Tech Stack

- Python 3.10+
- [Streamlit](https://streamlit.io/) for the interactive dashboard
- [pandas](https://pandas.pydata.org/) for tabular results

## Run Locally

```bash
git clone https://github.com/aurum-codes/SkillBridge_AI.git
cd SkillBridge_AI
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies and start the app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Demo Flow

1. Open **Candidate Upload** to inspect the seeded candidates or add a new one.
2. Open **AI Agent Analysis** and run the pipeline for a candidate.
3. Review inferred skills, role gaps, learning cost, and requisition match.
4. Open **HR Approval Dashboard** and record the human decision and notes.

## Project Structure

```text
SkillBridge_AI/
├── app.py              # Streamlit UI, mock agent logic, and session state
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## Prototype Scope

The agent logic and SAP SuccessFactors integration are simulated locally for
the hackathon demo. No external GitHub scanning, SAP connection, LLM API, or
candidate data storage is configured. Candidate data and HR decisions live in
Streamlit session state and reset when the app restarts.