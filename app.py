"""
SkillBridge AI — Bridging Marginalized Talent to Enterprise Roles via SAP SuccessFactors
SAP Hackathon | Theme: Inclusive Workforce

A single-file Streamlit prototype demonstrating a 3-agent pipeline:
    1. Talent Inference Agent      — extracts real skills from GitHub/portfolio, ignoring degree gaps
    2. Reskilling Pathway Agent    — finds skill gaps vs. a target SAP role and builds a learning path
    3. SAP SuccessFactors Matching Agent — simulates Talent Intelligence Hub matching to open reqs

A Human-in-the-Loop HR Approval Dashboard lets an HR Manager review the AI's
recommendation and approve/reject the candidate for interview.

Run:
    pip install streamlit pandas
    streamlit run app.py
"""

import random
from datetime import datetime

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="SkillBridge AI",
    page_icon="🌉",
    layout="wide",
)

# ---------------------------------------------------------------------------
# MOCK REFERENCE DATA
# ---------------------------------------------------------------------------

TIER_CITIES = [
    "Warangal, Telangana (Tier-3)",
    "Coimbatore, Tamil Nadu (Tier-2)",
    "Bhubaneswar, Odisha (Tier-2)",
    "Guwahati, Assam (Tier-2)",
    "Madurai, Tamil Nadu (Tier-2)",
    "Jhansi, Uttar Pradesh (Tier-3)",
    "Other Tier-2/3 City",
]

# Universe of skills the Talent Inference Agent can "detect" from a
# GitHub/portfolio scan. In production this would come from an actual
# repo/README/commit-history analysis pipeline.
SKILL_UNIVERSE = [
    "Python", "JavaScript", "SQL", "HTML/CSS", "Java", "React", "Node.js",
    "REST APIs", "Git/GitHub", "Data Analysis", "Excel/Reporting",
    "Linux/Unix", "Statistics", "Machine Learning", "OOP Concepts",
    "Debugging", "Cloud Basics (AWS/Azure)", "Problem Solving",
    "Self-Learning/MOOCs", "Database Management", "JSON/OData",
]

# Target SAP enterprise roles this candidate could be matched against,
# each with the required skill set the Reskilling Pathway Agent checks for.
ROLE_REQUIREMENTS = {
    "SAP ABAP Developer": [
        "Python", "OOP Concepts", "SQL", "Debugging",
        "Database Management", "Problem Solving",
    ],
    "SAP Fiori/UI5 Developer": [
        "JavaScript", "HTML/CSS", "REST APIs", "JSON/OData",
        "React", "Git/GitHub",
    ],
    "SAP Business Analyst": [
        "Data Analysis", "Excel/Reporting", "SQL", "Statistics",
        "Problem Solving", "Self-Learning/MOOCs",
    ],
    "SAP Basis Administrator": [
        "Linux/Unix", "Database Management", "Cloud Basics (AWS/Azure)",
        "Debugging", "Problem Solving",
    ],
    "SAP Data Analyst": [
        "SQL", "Python", "Statistics", "Data Analysis", "Excel/Reporting",
    ],
}

# Mock open requisitions inside a simulated SAP SuccessFactors Talent
# Intelligence Hub. The Matching Agent picks the best-fit open role.
OPEN_REQUISITIONS = {
    "SAP ABAP Developer": {"req_id": "REQ-4471", "team": "Enterprise Core Dev", "location": "Hybrid — Chennai"},
    "SAP Fiori/UI5 Developer": {"req_id": "REQ-4502", "team": "UX Platform Engineering", "location": "Remote (India)"},
    "SAP Business Analyst": {"req_id": "REQ-4488", "team": "Retail Solutions BA Pod", "location": "Hybrid — Bengaluru"},
    "SAP Basis Administrator": {"req_id": "REQ-4390", "team": "Cloud Infrastructure Ops", "location": "Remote (India)"},
    "SAP Data Analyst": {"req_id": "REQ-4515", "team": "Supply Chain Analytics", "location": "Hybrid — Pune"},
}

COST_PER_WEEK_INR = 3500  # mock reskilling cost rate used by the Pathway Agent


# ---------------------------------------------------------------------------
# MOCK AGENT LOGIC
# ---------------------------------------------------------------------------

def run_talent_inference_agent(candidate: dict) -> dict:
    """
    Mock 'Talent Inference Agent'.
    Simulates parsing a candidate's GitHub repos / portfolio to extract
    demonstrated skills — deliberately ignoring absence of a formal degree,
    since the whole point is surfacing real, evidenced ability.
    """
    seed_key = candidate["name"] + candidate["github"]
    rng = random.Random(seed_key)  # deterministic per-candidate "analysis"

    num_skills = rng.randint(6, 10)
    extracted = rng.sample(SKILL_UNIVERSE, num_skills)
    skills_with_confidence = {
        skill: round(rng.uniform(0.68, 0.97), 2) for skill in extracted
    }
    return {
        "skills": skills_with_confidence,
        "note": (
            f"Inference based on {rng.randint(8, 34)} public repositories and portfolio artifacts. "
            "No formal degree required or penalized — signal is drawn purely from demonstrated work."
        ),
    }


def run_reskilling_pathway_agent(candidate: dict, inferred_skills: dict) -> dict:
    """
    Mock 'Reskilling Pathway Agent'.
    Compares inferred skills against the target role's requirements,
    identifies gaps, and builds a mock learning path with duration/cost.
    """
    target_role = candidate["target_role"]
    required = ROLE_REQUIREMENTS[target_role]
    have = set(inferred_skills.keys())

    matched = [s for s in required if s in have]
    gaps = [s for s in required if s not in have]

    rng = random.Random(candidate["name"] + target_role)
    learning_path = []
    total_cost, total_weeks = 0, 0
    for skill in gaps:
        weeks = rng.randint(2, 6)
        cost = weeks * COST_PER_WEEK_INR
        learning_path.append({
            "Skill Gap": skill,
            "Recommended Course": f"{skill} Foundations — SAP Learning Hub",
            "Duration (weeks)": weeks,
            "Cost (INR)": cost,
        })
        total_cost += cost
        total_weeks += weeks

    return {
        "matched_skills": matched,
        "gap_skills": gaps,
        "learning_path": learning_path,
        "total_cost_inr": total_cost,
        "total_weeks": total_weeks,
    }


def run_sf_matching_agent(candidate: dict, inferred_skills: dict, pathway_result: dict) -> dict:
    """
    Mock 'SAP SuccessFactors Matching Agent'.
    Simulates SAP SuccessFactors Talent Intelligence Hub logic: scores the
    candidate against the target role's open requisition using matched
    skill coverage weighted by extraction confidence.
    """
    target_role = candidate["target_role"]
    required = ROLE_REQUIREMENTS[target_role]
    matched = pathway_result["matched_skills"]

    coverage_pct = (len(matched) / len(required)) * 100 if required else 0
    avg_confidence = (
        sum(inferred_skills[s] for s in matched) / len(matched) if matched else 0
    )
    match_score = round((coverage_pct * 0.7) + (avg_confidence * 100 * 0.3), 1)
    match_score = min(match_score, 99.0)

    req = OPEN_REQUISITIONS[target_role]

    return {
        "match_score": match_score,
        "coverage_pct": round(coverage_pct, 1),
        "confidence_avg": round(avg_confidence * 100, 1),
        "req_id": req["req_id"],
        "team": req["team"],
        "location": req["location"],
    }


def run_full_pipeline(candidate: dict) -> dict:
    """Chains all three agents together and returns the full analysis bundle."""
    inference = run_talent_inference_agent(candidate)
    pathway = run_reskilling_pathway_agent(candidate, inference["skills"])
    matching = run_sf_matching_agent(candidate, inference["skills"], pathway)
    return {"inference": inference, "pathway": pathway, "matching": matching}


# ---------------------------------------------------------------------------
# SESSION STATE INITIALIZATION (with mock candidates so the app works
# immediately on first run, per hackathon demo requirements)
# ---------------------------------------------------------------------------

def seed_mock_candidates():
    seed_candidates = [
        {
            "name": "Ananya Reddy",
            "github": "github.com/ananya-codes",
            "portfolio": "ananyareddy.dev",
            "location": TIER_CITIES[0],
            "target_role": "SAP Data Analyst",
        },
        {
            "name": "Farhan Sheikh",
            "github": "github.com/farhansheikh21",
            "portfolio": "farhansheikh.vercel.app",
            "location": TIER_CITIES[2],
            "target_role": "SAP Fiori/UI5 Developer",
        },
    ]
    candidates = []
    for c in seed_candidates:
        c["analysis"] = run_full_pipeline(c)
        c["decision"] = None
        candidates.append(c)
    return candidates


if "candidates" not in st.session_state:
    st.session_state.candidates = seed_mock_candidates()

if "decision_log" not in st.session_state:
    st.session_state.decision_log = []

if "active_candidate_idx" not in st.session_state:
    st.session_state.active_candidate_idx = 0


# ---------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------------------------

st.sidebar.title("🌉 SkillBridge AI")
st.sidebar.caption("SAP Hackathon — Theme: Inclusive Workforce")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["Candidate Upload", "AI Agent Analysis", "HR Approval Dashboard (Human-in-the-Loop)"],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Pipeline:**\n"
    "1. Talent Inference Agent\n"
    "2. Reskilling Pathway Agent\n"
    "3. SAP SuccessFactors Matching Agent\n"
    "4. HR Human-in-the-Loop Approval"
)
st.sidebar.caption(f"{len(st.session_state.candidates)} candidate(s) in pipeline")


# ---------------------------------------------------------------------------
# PAGE 1 — CANDIDATE UPLOAD
# ---------------------------------------------------------------------------

if page == "Candidate Upload":
    st.title("📋 Candidate Upload")
    st.write(
        "Submit a candidate's public work evidence instead of a traditional resume. "
        "SkillBridge AI evaluates **demonstrated skill**, not pedigree."
    )

    with st.form("candidate_upload_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Candidate Name", placeholder="e.g., Priya Kumar")
            github = st.text_input("GitHub Profile URL", placeholder="github.com/username")
            portfolio = st.text_input("Portfolio / Personal Site URL", placeholder="username.dev")
        with col2:
            location = st.selectbox("Location", TIER_CITIES)
            target_role = st.selectbox("Target SAP Role", list(ROLE_REQUIREMENTS.keys()))

        submitted = st.form_submit_button("Submit Candidate ▶")

    if submitted:
        if not name or not github:
            st.error("Please provide at least a candidate name and GitHub URL.")
        else:
            new_candidate = {
                "name": name,
                "github": github,
                "portfolio": portfolio or "Not provided",
                "location": location,
                "target_role": target_role,
                "analysis": None,
                "decision": None,
            }
            st.session_state.candidates.append(new_candidate)
            st.session_state.active_candidate_idx = len(st.session_state.candidates) - 1
            st.success(
                f"✅ Candidate **{name}** submitted successfully. "
                "Head to **AI Agent Analysis** to run the pipeline."
            )

    st.markdown("---")
    st.subheader("Candidates in Pipeline")
    table_rows = [
        {
            "Name": c["name"],
            "Location": c["location"],
            "Target Role": c["target_role"],
            "GitHub": c["github"],
            "Analyzed": "✅" if c["analysis"] else "⏳ Pending",
            "HR Decision": c["decision"] or "—",
        }
        for c in st.session_state.candidates
    ]
    st.dataframe(pd.DataFrame(table_rows), width='stretch', hide_index=True)


# ---------------------------------------------------------------------------
# PAGE 2 — AI AGENT ANALYSIS
# ---------------------------------------------------------------------------

elif page == "AI Agent Analysis":
    st.title("🤖 AI Agent Analysis")
    st.write("Run the three-agent pipeline against a candidate's submitted evidence.")

    if not st.session_state.candidates:
        st.warning("No candidates yet. Go to **Candidate Upload** first.")
        st.stop()

    names = [c["name"] for c in st.session_state.candidates]
    selected_idx = st.selectbox(
        "Select Candidate",
        range(len(names)),
        format_func=lambda i: names[i],
        index=min(st.session_state.active_candidate_idx, len(names) - 1),
    )
    st.session_state.active_candidate_idx = selected_idx
    candidate = st.session_state.candidates[selected_idx]

    # Candidate summary card
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Candidate", candidate["name"])
        c2.metric("Location", candidate["location"].split(",")[0])
        c3.metric("Target Role", candidate["target_role"])
        c4.metric("GitHub", candidate["github"])

    run_col, status_col = st.columns([1, 3])
    with run_col:
        run_clicked = st.button("▶ Run AI Agent Pipeline", type="primary")

    if run_clicked:
        with st.spinner("Agents processing candidate evidence..."):
            candidate["analysis"] = run_full_pipeline(candidate)
        st.success("Analysis complete — results below.")

    analysis = candidate["analysis"]
    if not analysis:
        st.info("No analysis yet for this candidate. Click **Run AI Agent Pipeline** above.")
        st.stop()

    inference = analysis["inference"]
    pathway = analysis["pathway"]
    matching = analysis["matching"]

    # --- Agent 1: Talent Inference Agent -----------------------------------
    with st.expander("🧠 Agent 1 — Talent Inference Agent", expanded=True):
        st.caption(inference["note"])
        skills_df = pd.DataFrame(
            [{"Skill": k, "Confidence": v} for k, v in inference["skills"].items()]
        ).sort_values("Confidence", ascending=False)
        st.bar_chart(skills_df.set_index("Skill"))
        st.dataframe(
            skills_df.assign(Confidence=lambda d: (d["Confidence"] * 100).round(1).astype(str) + "%"),
            width='stretch', hide_index=True,
        )

    # --- Agent 2: Reskilling Pathway Agent ----------------------------------
    with st.expander("📈 Agent 2 — Reskilling Pathway Agent", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Skills Already Matched", len(pathway["matched_skills"]))
        col2.metric("Skill Gaps Identified", len(pathway["gap_skills"]))
        col3.metric("Est. Time to Job-Ready", f"{pathway['total_weeks']} wks")

        if pathway["matched_skills"]:
            st.write("**Already demonstrated for this role:**")
            st.success(", ".join(pathway["matched_skills"]))

        if pathway["gap_skills"]:
            st.write("**Recommended Learning Path:**")
            st.table(pd.DataFrame(pathway["learning_path"]))
            st.metric("Total Reskilling Investment", f"₹{pathway['total_cost_inr']:,}")
        else:
            st.success("No skill gaps — candidate is fully role-ready today.")

    # --- Agent 3: SAP SuccessFactors Matching Agent -------------------------
    with st.expander("🔗 Agent 3 — SAP SuccessFactors Matching Agent", expanded=True):
        st.caption("Simulated SAP SuccessFactors Talent Intelligence Hub matching logic.")
        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Match Score", f"{matching['match_score']}%")
        col2.metric("Skill Coverage", f"{matching['coverage_pct']}%")
        col3.metric("Avg. Extraction Confidence", f"{matching['confidence_avg']}%")

        st.info(
            f"**Best-fit open requisition:** `{matching['req_id']}` — {candidate['target_role']}\n\n"
            f"**Team:** {matching['team']}  |  **Location:** {matching['location']}"
        )

    st.markdown("---")
    st.write("➡️ Proceed to **HR Approval Dashboard (Human-in-the-Loop)** to review and decide.")


# ---------------------------------------------------------------------------
# PAGE 3 — HR APPROVAL DASHBOARD (HUMAN-IN-THE-LOOP)
# ---------------------------------------------------------------------------

elif page == "HR Approval Dashboard (Human-in-the-Loop)":
    st.title("✅ HR Approval Dashboard")
    st.write(
        "Human-in-the-Loop checkpoint: an HR Manager reviews the AI's recommendation "
        "before any candidate is moved forward — the AI advises, a human decides."
    )

    analyzed_candidates = [c for c in st.session_state.candidates if c["analysis"]]
    if not analyzed_candidates:
        st.warning("No analyzed candidates yet. Run the pipeline on **AI Agent Analysis** first.")
        st.stop()

    names = [c["name"] for c in analyzed_candidates]
    selected_name = st.selectbox("Select Candidate to Review", names)
    candidate = next(c for c in analyzed_candidates if c["name"] == selected_name)
    analysis = candidate["analysis"]
    matching = analysis["matching"]
    pathway = analysis["pathway"]

    # --- Candidate profile card ---------------------------------------------
    with st.container(border=True):
        st.subheader(f"👤 {candidate['name']}")
        col1, col2, col3 = st.columns(3)
        col1.write(f"**Location:** {candidate['location']}")
        col1.write(f"**GitHub:** {candidate['github']}")
        col2.write(f"**Portfolio:** {candidate['portfolio']}")
        col2.write(f"**Target Role:** {candidate['target_role']}")
        col3.write(f"**Open Req:** {matching['req_id']}")
        col3.write(f"**Team:** {matching['team']}")

    st.markdown("### AI Recommendation Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("AI Match Score", f"{matching['match_score']}%")
    m2.metric("Skill Coverage", f"{matching['coverage_pct']}%")
    m3.metric("Recommended Reskilling Budget", f"₹{pathway['total_cost_inr']:,}")
    m4.metric("Time to Job-Ready", f"{pathway['total_weeks']} wks")

    if matching["match_score"] >= 75:
        st.success("🟢 Strong AI recommendation: high match score, low reskilling burden.")
    elif matching["match_score"] >= 55:
        st.warning("🟡 Moderate AI recommendation: viable with a structured reskilling plan.")
    else:
        st.error("🔴 Low AI match score: significant upskilling required before this role.")

    with st.expander("View full skill gap & learning path detail"):
        if pathway["gap_skills"]:
            st.table(pd.DataFrame(pathway["learning_path"]))
        else:
            st.success("No skill gaps identified for this role.")

    st.markdown("---")
    st.markdown("### Human Decision")
    hr_notes = st.text_area(
        "HR Manager Notes (optional)",
        placeholder="e.g., Strong problem-solving signal from repo history; recommend fast-track interview.",
        key=f"notes_{candidate['name']}",
    )

    col_a, col_b, _ = st.columns([1, 1, 3])
    approve_clicked = col_a.button("✅ Approve for Interview", type="primary", key=f"approve_{candidate['name']}")
    reject_clicked = col_b.button("❌ Reject", key=f"reject_{candidate['name']}")

    if approve_clicked or reject_clicked:
        decision = "Approved for Interview" if approve_clicked else "Rejected"
        candidate["decision"] = decision
        st.session_state.decision_log.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Candidate": candidate["name"],
            "Target Role": candidate["target_role"],
            "AI Match Score": f"{matching['match_score']}%",
            "HR Decision": decision,
            "HR Notes": hr_notes or "—",
        })
        if approve_clicked:
            st.success(f"✅ {candidate['name']} approved for interview and routed to {matching['team']}.")
        else:
            st.error(f"❌ {candidate['name']} marked as rejected for this requisition.")

    # --- Decision log ---------------------------------------------------
    if st.session_state.decision_log:
        st.markdown("---")
        st.subheader("📜 HR Decision Log")
        st.dataframe(
            pd.DataFrame(st.session_state.decision_log),
            width='stretch', hide_index=True,
        )
