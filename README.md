# SkillBridge AI — SAP Hackathon (Theme: Inclusive Workforce)

Single-file Streamlit prototype demonstrating a 3-agent pipeline that
bridges marginalized talent (Tier-2/3 cities, non-traditional credentials)
to enterprise roles via a simulated SAP SuccessFactors integration, with a
Human-in-the-Loop HR approval step.

## How to open in VS Code
1. Unzip this folder and open it in VS Code (**File > Open Folder**).
2. Install the Python extension if you don't already have it.

## How to run
```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) and
should open it in your browser automatically. If not, open it manually.

## What's pre-loaded
Two mock candidates (Ananya Reddy, Farhan Sheikh) are seeded on startup
with analysis already run, so the **AI Agent Analysis** and **HR Approval
Dashboard** pages have data immediately — no setup steps needed for a demo.

## Pages
- **Candidate Upload** — add a new candidate (name, GitHub, portfolio, Tier-2/3 location, target SAP role)
- **AI Agent Analysis** — runs the Talent Inference, Reskilling Pathway, and SAP SuccessFactors Matching agents
- **HR Approval Dashboard (Human-in-the-Loop)** — HR reviews the AI's match score and reskilling budget, then approves or rejects

## Notes
- All agent logic is simulated in pure Python (deterministic per-candidate, via seeded `random`) — no external APIs or real SAP connection required.
- To stop the app, press `Ctrl+C` in the terminal running `streamlit run app.py`.
