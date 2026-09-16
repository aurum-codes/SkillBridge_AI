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
import re
from html import unescape
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="SkillBridge AI",
    page_icon="🌉",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #132238;
        --muted: #617086;
        --paper: #f4f7fb;
        --line: #dce5ef;
        --blue: #1464a5;
        --teal: #008c95;
        --coral: #e56b52;
    }
    .stApp { background: var(--paper); }
    [data-testid="stSidebar"] { background: var(--ink); }
    [data-testid="stSidebar"] * { color: #eef5fb; }
    [data-testid="stSidebar"] hr { border-color: #34445a; }
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 4px 18px rgba(19, 34, 56, 0.05);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--ink); }
    .hero {
        background: linear-gradient(115deg, #132238 0%, #174d76 62%, #008c95 100%);
        border-radius: 18px;
        padding: 28px 32px;
        color: white;
        margin-bottom: 22px;
    }
    .hero h1 { color: white; margin: 0 0 6px 0; letter-spacing: 0; }
    .hero p { color: #d9eef5; margin: 0; font-size: 1.05rem; }
    .eyebrow { color: #8fe1d4; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
    .source-pill { color: var(--teal); font-weight: 700; font-size: 0.85rem; }
    .stButton > button[kind="primary"] { background: var(--coral); border-color: var(--coral); }
    .stButton > button[kind="primary"]:hover { background: #c8533e; border-color: #c8533e; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# MOCK REFERENCE DATA
# ---------------------------------------------------------------------------

FALLBACK_LOCATIONS = [
    "Warangal, Telangana (Tier-3)",
    "Coimbatore, Tamil Nadu (Tier-2)",
    "Bhubaneswar, Odisha (Tier-2)",
    "Guwahati, Assam (Tier-2)",
    "Madurai, Tamil Nadu (Tier-2)",
    "Jhansi, Uttar Pradesh (Tier-3)",
    "Other Tier-2/3 City",
]

COUNTRIES_API = "https://countriesnow.space/api/v0.1/countries"
JOBS_API = "https://www.arbeitnow.com/api/job-board-api"

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

FALLBACK_JOB_POSITIONS = [
    {
        "title": role,
        "company_name": "SkillBridge Enterprise Network",
        "location": details["location"],
        "url": "",
        "description": "",
        "source": "SkillBridge catalog",
        "req_id": details["req_id"],
        "skills": requirements,
    }
    for role, requirements in ROLE_REQUIREMENTS.items()
    for details in [OPEN_REQUISITIONS[role]]
]

SKILL_ALIASES = {
    "Python": ["python"],
    "JavaScript": ["javascript", "typescript"],
    "SQL": ["sql", "postgresql", "mysql"],
    "HTML/CSS": ["html", "css"],
    "Java": ["java", "spring boot"],
    "React": ["react", "react.js"],
    "Node.js": ["node.js", "nodejs"],
    "REST APIs": ["rest api", "restful", "web api"],
    "Git/GitHub": ["git", "github", "version control"],
    "Data Analysis": ["data analysis", "analytics", "tableau", "power bi"],
    "Excel/Reporting": ["excel", "reporting", "dashboard"],
    "Linux/Unix": ["linux", "unix"],
    "Statistics": ["statistics", "statistical"],
    "Machine Learning": ["machine learning", "ml", "artificial intelligence"],
    "OOP Concepts": ["object-oriented", "oop"],
    "Debugging": ["debugging", "troubleshooting"],
    "Cloud Basics (AWS/Azure)": ["aws", "azure", "cloud"],
    "Problem Solving": ["problem solving", "analytical"],
    "Self-Learning/MOOCs": ["learning", "certification", "course"],
    "Database Management": ["database", "data warehouse", "etl"],
    "JSON/OData": ["json", "odata"],
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_worldwide_locations() -> tuple[list[str], dict[str, list[str]], str]:
    """Load countries and cities, returning a small fallback when offline."""
    try:
        response = requests.get(COUNTRIES_API, timeout=12)
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise ValueError(payload.get("msg", "Location API returned an error"))
        locations = {
            item["country"]: sorted(item.get("cities", []))
            for item in payload.get("data", [])
            if item.get("country")
        }
        if not locations:
            raise ValueError("Location API returned no countries")
        return sorted(locations), locations, "Live · CountriesNow"
    except (requests.RequestException, ValueError, KeyError, TypeError):
        countries = sorted({location.rsplit(", ", 1)[-1].split(" (")[0] for location in FALLBACK_LOCATIONS})
        return countries, {country: [] for country in countries}, "Fallback · local catalog"


def clean_job_description(description: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", description or ""))).strip()


def extract_job_skills(text: str) -> list[str]:
    normalized = text.lower()
    matches = [skill for skill, aliases in SKILL_ALIASES.items() if any(alias in normalized for alias in aliases)]
    return matches or ["Problem Solving", "Self-Learning/MOOCs"]


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_live_jobs() -> tuple[list[dict], str]:
    """Load public job postings and convert them to SkillBridge requisitions."""
    try:
        response = requests.get(JOBS_API, timeout=15)
        response.raise_for_status()
        records = response.json().get("data", [])
        jobs = []
        for record in records:
            title = (record.get("title") or "").strip()
            if not title:
                continue
            description = clean_job_description(record.get("description", ""))
            jobs.append({
                "title": title,
                "company_name": record.get("company_name") or "Undisclosed company",
                "location": record.get("location") or ("Remote" if record.get("remote") else "Worldwide"),
                "url": record.get("url", ""),
                "description": description,
                "source": "Live · Arbeitnow",
                "req_id": record.get("slug", "LIVE")[:18].upper(),
                "skills": extract_job_skills(f"{title} {description}"),
            })
        if not jobs:
            raise ValueError("Jobs API returned no positions")
        return jobs, "Live · Arbeitnow"
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return FALLBACK_JOB_POSITIONS, "Fallback · role catalog"


def job_catalog() -> list[dict]:
    live_jobs, _ = fetch_live_jobs()
    return FALLBACK_JOB_POSITIONS + live_jobs


def get_job_position(role_title: str) -> dict:
    return next((job for job in job_catalog() if job["title"] == role_title), FALLBACK_JOB_POSITIONS[0])


def get_role_requirements(role_title: str) -> list[str]:
    return get_job_position(role_title).get("skills") or ["Problem Solving"]

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
    required = get_role_requirements(target_role)
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
    required = get_role_requirements(target_role)
    matched = pathway_result["matched_skills"]

    coverage_pct = (len(matched) / len(required)) * 100 if required else 0
    avg_confidence = (
        sum(inferred_skills[s] for s in matched) / len(matched) if matched else 0
    )
    match_score = round((coverage_pct * 0.7) + (avg_confidence * 100 * 0.3), 1)
    match_score = min(match_score, 99.0)

    req = get_job_position(target_role)

    return {
        "match_score": match_score,
        "coverage_pct": round(coverage_pct, 1),
        "confidence_avg": round(avg_confidence * 100, 1),
        "req_id": req["req_id"],
        "team": req["company_name"],
        "location": req["location"],
        "source": req["source"],
        "job_url": req["url"],
        "job_description": req["description"],
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
            "location": "Warangal, India",
            "target_role": "SAP Data Analyst",
        },
        {
            "name": "Farhan Sheikh",
            "github": "github.com/farhansheikh21",
            "portfolio": "farhansheikh.vercel.app",
            "location": "Bhubaneswar, India",
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


COUNTRY_NAMES, CITIES_BY_COUNTRY, LOCATION_SOURCE = fetch_worldwide_locations()
LIVE_JOBS, JOBS_SOURCE = fetch_live_jobs()
JOB_OPTIONS = list(dict.fromkeys([job["title"] for job in FALLBACK_JOB_POSITIONS + LIVE_JOBS]))


# ---------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------------------------

st.sidebar.markdown("## 🌉 SkillBridge AI")
st.sidebar.caption("Inclusive talent intelligence for the global workforce")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["Candidate Upload", "AI Agent Analysis", "Talent Market Explorer", "HR Approval Dashboard (Human-in-the-Loop)"],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Pipeline:**\n"
    "1. Talent Inference Agent\n"
    "2. Reskilling Pathway Agent\n"
    "3. SAP SuccessFactors Matching Agent\n"
    "4. HR Human-in-the-Loop Approval"
)
st.sidebar.markdown("---")
st.sidebar.caption(f"{len(st.session_state.candidates)} candidate(s) in pipeline")
st.sidebar.caption(f"🌍 {LOCATION_SOURCE}")
st.sidebar.caption(f"💼 {JOBS_SOURCE} · {len(LIVE_JOBS)} postings")


# ---------------------------------------------------------------------------
# PAGE 1 — CANDIDATE UPLOAD
# ---------------------------------------------------------------------------

if page == "Candidate Upload":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Talent intake · evidence over pedigree</div>'
        '<h1>Build a stronger talent signal.</h1>'
        '<p>Capture public work evidence, choose any country, and match a candidate to live global roles.</p></div>',
        unsafe_allow_html=True,
    )

    metrics = st.columns(4)
    metrics[0].metric("Candidates", len(st.session_state.candidates))
    metrics[1].metric("Countries available", len(COUNTRY_NAMES))
    metrics[2].metric("Live positions", len(LIVE_JOBS))
    metrics[3].metric("HR decisions", len(st.session_state.decision_log))

    with st.form("candidate_upload_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Candidate Name", placeholder="e.g., Priya Kumar")
            github = st.text_input("GitHub Profile URL", placeholder="github.com/username")
            portfolio = st.text_input("Portfolio / Personal Site URL", placeholder="username.dev")
        with col2:
            country = st.selectbox("Country", COUNTRY_NAMES, index=COUNTRY_NAMES.index("India") if "India" in COUNTRY_NAMES else 0)
            city = st.text_input("City or region", placeholder="e.g., Bengaluru, Ontario, or Remote")
            target_role = st.selectbox("Target position", JOB_OPTIONS)

        st.caption(f"🌍 Location directory: {LOCATION_SOURCE} · {len(COUNTRY_NAMES)} countries")
        st.caption(f"💼 Position feed: {JOBS_SOURCE} · live titles are analyzed from their descriptions")

        submitted = st.form_submit_button("Submit Candidate ▶")

    if submitted:
        if not name or not github:
            st.error("Please provide at least a candidate name and GitHub URL.")
        else:
            new_candidate = {
                "name": name,
                "github": github,
                "portfolio": portfolio or "Not provided",
                "location": f"{city.strip()}, {country}" if city.strip() else country,
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

    st.markdown("### Candidates in Pipeline")
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
    st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# PAGE 2 — AI AGENT ANALYSIS
# ---------------------------------------------------------------------------

elif page == "AI Agent Analysis":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Three-agent decision support</div>'
        '<h1>Evidence to opportunity.</h1>'
        '<p>Trace how demonstrated skills become a transparent, reviewable role recommendation.</p></div>',
        unsafe_allow_html=True,
    )

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
            f"**Best-fit position:** `{matching['req_id']}` — {candidate['target_role']}\n\n"
            f"**Company:** {matching['team']}  |  **Location:** {matching['location']}\n\n"
            f"**Data source:** {matching['source']}"
        )
        if matching.get("job_url"):
            st.link_button("Open live job posting", matching["job_url"])

    st.markdown("---")
    st.write("➡️ Proceed to **HR Approval Dashboard (Human-in-the-Loop)** to review and decide.")


# ---------------------------------------------------------------------------
# PAGE 3 — TALENT MARKET EXPLORER
# ---------------------------------------------------------------------------

elif page == "Talent Market Explorer":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Global opportunity intelligence</div>'
        '<h1>Explore the talent market.</h1>'
        '<p>Browse live positions, inspect skill signals, and bring a role directly into candidate analysis.</p></div>',
        unsafe_allow_html=True,
    )

    top_left, top_right = st.columns([3, 1])
    with top_left:
        search = st.text_input("Search positions", placeholder="Try data, engineer, analyst, remote...")
    with top_right:
        if st.button("↻ Refresh live data"):
            fetch_live_jobs.clear()
            fetch_worldwide_locations.clear()
            st.rerun()

    visible_jobs = LIVE_JOBS
    if search.strip():
        query = search.lower().strip()
        visible_jobs = [
            job for job in LIVE_JOBS
            if query in f"{job['title']} {job['company_name']} {job['location']} {job['description']}".lower()
        ]

    summary = st.columns(3)
    summary[0].metric("Positions shown", len(visible_jobs))
    summary[1].metric("Countries in directory", len(COUNTRY_NAMES))
    summary[2].metric("Feed status", "Live" if JOBS_SOURCE.startswith("Live") else "Fallback")

    if visible_jobs:
        job_rows = [
            {
                "Position": job["title"],
                "Company": job["company_name"],
                "Location": job["location"],
                "Signals": ", ".join(job["skills"][:5]),
                "Source": job["source"],
            }
            for job in visible_jobs
        ]
        st.dataframe(pd.DataFrame(job_rows), width="stretch", hide_index=True)

        selected_job = st.selectbox("Inspect a position", range(len(visible_jobs)), format_func=lambda i: visible_jobs[i]["title"])
        job = visible_jobs[selected_job]
        with st.container(border=True):
            st.subheader(job["title"])
            st.caption(f"{job['company_name']} · {job['location']} · {job['source']}")
            st.write(f"**Skill signals:** {', '.join(job['skills'])}")
            if job["description"]:
                st.write(job["description"][:1200] + ("..." if len(job["description"]) > 1200 else ""))
            if job["url"]:
                st.link_button("View original posting", job["url"])
    else:
        st.info("No positions match this search. Try a broader keyword or refresh the live feed.")


# ---------------------------------------------------------------------------
# PAGE 3 — HR APPROVAL DASHBOARD (HUMAN-IN-THE-LOOP)
# ---------------------------------------------------------------------------

elif page == "HR Approval Dashboard (Human-in-the-Loop)":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Human-in-the-loop governance</div>'
        '<h1>Make the final call with context.</h1>'
        '<p>Review evidence, investment, and model confidence before a candidate moves forward.</p></div>',
        unsafe_allow_html=True,
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
