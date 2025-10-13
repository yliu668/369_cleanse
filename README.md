
from __future__ import annotations
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Tuple
import streamlit as st

st.set_page_config(
    page_title="MM 369 Cleanse Tracker",
    page_icon="🥗",
    layout="wide",
)

# -----------------------------
# Styles (clean + minimal)
# -----------------------------
st.markdown(
    """
    <style>
    .main {background: linear-gradient(180deg,#0b0c10,#0d1117 30%,#0b0c10);} 
    h1,h2,h3,h4,h5,h6, p, span, div {color:#eef2ff !important}
    .stButton>button {border-radius:14px; padding:0.6rem 1rem; border:1px solid #263042; background:#101826}
    .stButton>button:hover {border-color:#2f3b52}
    .chip > div {display:inline-flex; gap:.5rem; padding:.35rem .75rem; border:1px solid #263042; border-radius:999px; background:#0f1320; color:#aab1c5;}
    .muted {color:#9aa3b2 !important}
    .card {border:1px solid #263042; border-radius:16px; padding:1rem; background:#0f1320}
    .pill {display:inline-flex;gap:6px;align-items:center;padding:.35rem .6rem;border-radius:9999px;border:1px solid #2a344a;background:#0e1422}
    .good {background: linear-gradient(180deg,#135,#024);}
    .big-title {font-size:2.1rem; font-weight:800; letter-spacing:.3px}
    .subtle {font-size:0.9rem; color:#9aa3b2}
    .date-sub {color:#9aa3b2; font-size:.85rem}
    .section-label {font-weight:700; margin:.25rem 0 .35rem 0}
    .stProgress > div > div {background: linear-gradient(90deg,#7dd3fc,#a78bfa)}
    .medal {font-size:1.8rem; letter-spacing:2px}
    .divider {height:1px; background:#263042; margin:.75rem 0}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Program templates (edit later with your exact content)
# -----------------------------
PROGRAMS: Dict[str, Dict[str, Any]] = {
    "original": {
        "label": "Original 369",
        "groups": {
            "1-3": {
                "sections": [
                    {"name": "Upon Waking", "items": ["16 ounces lemon or lime water"]},
                    {"name": "Morning", "items": [
                        "Wait 15–30 minutes",
                        "16 ounces celery juice",
                        "Wait another 15–30 minutes",
                        "Breakfast & mid‑morning snack (within guidelines) — Day 2–3 include 1–2 apples/applesauce",
                    ]},
                    {"name": "Lunchtime", "items": [
                        "Meal of your choice (within guidelines) + steamed zucchini/summer squash",
                    ]},
                    {"name": "Mid‑Afternoon", "items": ["1–2 apples (or applesauce) with 1–2 dates"]},
                    {"name": "Dinnertime", "items": ["Meal of your choice (within guidelines)"]},
                    {"name": "Evening", "items": [
                        "Apple or applesauce (optional)",
                        "16 ounces lemon or lime water",
                        "Herbal tea: hibiscus, lemon balm, or chaga",
                    ]},
                ]
            },
            "4-6": {
                "sections": [
                    {"name": "Upon Waking", "items": ["16 ounces lemon or lime water"]},
                    {"name": "Morning", "items": [
                        "Wait 15–30 minutes",
                        "16 ounces celery juice",
                        "Breakfast & mid‑morning snack per plan",
                    ]},
                    {"name": "Lunchtime", "items": ["Guideline meal (more steamed veg)"]},
                    {"name": "Mid‑Afternoon", "items": ["1–2 apples/applesauce + dates"]},
                    {"name": "Dinnertime", "items": ["Guideline meal"]},
                    {"name": "Evening", "items": ["Optional apple", "Lemon/lime water", "Herbal tea"]},
                ]
            },
            "7-9": {
                "sections": [
                    {"name": "Upon Waking", "items": ["16 ounces lemon or lime water"]},
                    {"name": "Morning", "items": [
                        "Wait 15–30 minutes",
                        "16 ounces celery juice",
                        "Breakfast & mid‑morning snack per plan",
                    ]},
                    {"name": "Lunchtime", "items": ["Guideline meal"]},
                    {"name": "Mid‑Afternoon", "items": ["1–2 apples/applesauce + dates"]},
                    {"name": "Dinnertime", "items": ["Guideline meal"]},
                    {"name": "Evening", "items": ["Optional apple", "Lemon/lime water", "Herbal tea"]},
                ]
            },
        },
    },
    "simplified": {
        "label": "Simplified 369",
        "groups": {
            "1-3": {"sections": [
                {"name": "Upon Waking", "items": ["Lemon/lime water"]},
                {"name": "Morning", "items": ["Celery juice", "Breakfast"]},
                {"name": "Lunchtime", "items": ["Simple meal"]},
                {"name": "Mid‑Afternoon", "items": ["Apple + dates"]},
                {"name": "Dinnertime", "items": ["Simple meal"]},
                {"name": "Evening", "items": ["Tea"]},
            ]},
            "4-6": {"sections": [
                {"name": "Upon Waking", "items": ["Lemon/lime water"]},
                {"name": "Morning", "items": ["Celery juice", "Snack"]},
                {"name": "Lunchtime", "items": ["Meal"]},
                {"name": "Mid‑Afternoon", "items": ["Apple"]},
                {"name": "Dinnertime", "items": ["Meal"]},
                {"name": "Evening", "items": ["Tea"]},
            ]},
            "7-9": {"sections": [
                {"name": "Upon Waking", "items": ["Lemon/lime water"]},
                {"name": "Morning", "items": ["Celery juice"]},
                {"name": "Lunchtime", "items": ["Meal"]},
                {"name": "Mid‑Afternoon", "items": ["Apple"]},
                {"name": "Dinnertime", "items": ["Meal"]},
                {"name": "Evening", "items": ["Tea"]},
            ]},
        },
    },
    "advanced": {
        "label": "Advanced 369",
        "groups": {
            "1-3": {"sections": [
                {"name": "Upon Waking", "items": ["Lemon/lime water (advanced)"]},
                {"name": "Morning", "items": ["Celery juice", "Additional step"]},
                {"name": "Lunchtime", "items": ["Meal (advanced)"]},
                {"name": "Mid‑Afternoon", "items": ["Apple + dates"]},
                {"name": "Dinnertime", "items": ["Meal (advanced)"]},
                {"name": "Evening", "items": ["Tea"]},
            ]},
            "4-6": {"sections": [
                {"name": "Upon Waking", "items": ["Lemon/lime water"]},
                {"name": "Morning", "items": ["Celery juice"]},
                {"name": "Lunchtime", "items": ["Meal"]},
                {"name": "Mid‑Afternoon", "items": ["Snack"]},
                {"name": "Dinnertime", "items": ["Meal"]},
                {"name": "Evening", "items": ["Tea"]},
            ]},
            "7-9": {"sections": [
                {"name": "Upon Waking", "items": ["Lemon/lime water"]},
                {"name": "Morning", "items": ["Celery juice"]},
                {"name": "Lunchtime", "items": ["Meal"]},
                {"name": "Mid‑Afternoon", "items": ["Snack"]},
                {"name": "Dinnertime", "items": ["Meal"]},
                {"name": "Evening", "items": ["Tea"]},
            ]},
        },
    },
}
GROUP_ORDER = ["1-3", "4-6", "7-9"]

# -----------------------------
# Helpers
# -----------------------------

def add_days(d: date, n: int) -> date:
    return d + timedelta(days=n)


def to_iso(d: date) -> str:
    return d.isoformat()


def fmt_date(d: date) -> str:
    return d.strftime("%a, %b %d")


def cycle_id(program_key: str, start_iso: str) -> str:
    return f"{program_key}|{start_iso}"


# -----------------------------
# Session state init
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "active" not in st.session_state:
    st.session_state.active = None  # dict with program_key, start_iso, id, checks
if "completed_cycles" not in st.session_state:
    st.session_state.completed_cycles = 0


# -----------------------------
# UI Components
# -----------------------------

def header_bar():
    with st.container():
        cols = st.columns([1, 2, 2])
        with cols[0]:
            st.markdown("<div class='big-title'>MM 369 Cleanse</div>", unsafe_allow_html=True)
            st.markdown("<div class='subtle'>simple · flexible · elegant</div>", unsafe_allow_html=True)
        with cols[1]:
            if st.session_state.active:
                st.markdown(
                    f"<div class='pill'>📆 Start: <b>{st.session_state.active['start_iso']}</b></div>",
                    unsafe_allow_html=True,
                )
        with cols[2]:
            c1, c2, c3 = st.columns([1, 1, 1])
            if c1.button("🏠 Home"):
                st.session_state.page = "home"
                st.rerun()
            if c2.button("🔄 Start Over"):
                st.session_state.active = None
                st.session_state.page = "home"
                st.rerun()
            if st.session_state.active and is_cycle_complete(st.session_state.active):
                if c3.button("🥇 Finish Cycle"):
                    st.session_state.completed_cycles += 1
                    st.session_state.active = None
                    st.session_state.page = "history"
                    st.balloons()
                    st.rerun()


def view_home():
    header_bar()
    st.write("")
    st.markdown("### Choose your program")

    # Three option cards
    col1, col2, col3 = st.columns(3)
    selected = st.session_state.get("_home_selection", "original")

    def draw_card(col, key, title, desc):
        with col:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"#### {title}")
            st.markdown(f"<span class='muted'>{desc}</span>", unsafe_allow_html=True)
            picked = st.button("Select", key=f"pick_{key}")
            if picked:
                st.session_state._home_selection = key
                st.session_state._home_label = PROGRAMS[key]["label"]
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    draw_card(col1, "original", PROGRAMS["original"]["label"], "Classic protocol")
    draw_card(col2, "simplified", PROGRAMS["simplified"]["label"], "Lighter variant")
    draw_card(col3, "advanced", PROGRAMS["advanced"]["label"], "Power users")

    prog_key = st.session_state.get("_home_selection", "original")
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown(f"##### Selected: **{PROGRAMS[prog_key]['label']}**")

    # Quick chips + calendar
    today = date.today()
    start_mode = st.radio(
        "Quick start",
        options=["Yesterday", "Today", "Tomorrow", "Pick a date"],
        index=1,
        horizontal=True,
    )
    if start_mode == "Yesterday":
        start_date = today - timedelta(days=1)
    elif start_mode == "Tomorrow":
        start_date = today + timedelta(days=1)
    elif start_mode == "Today":
        start_date = today
    else:
        start_date = st.date_input("Start on", value=today)

    cta = st.button("Start")
    if cta:
        begin_cycle(prog_key, start_date)
        st.session_state.page = "tracker"
        st.rerun()

    # Resume block
    if st.session_state.active:
        st.info("You have an in‑progress cycle. Click Tracker to resume.")
        if st.button("Go to Tracker"):
            st.session_state.page = "tracker"
            st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    # Export / Import (optional persistence)
    st.subheader("Export / Import")
    if st.session_state.active:
        data = json.dumps(st.session_state.active, indent=2)
        st.download_button("⬇️ Export current progress", data, file_name="mm369_progress.json")
    uploaded = st.file_uploader("Restore from exported JSON", type=["json"])
    if uploaded is not None:
        try:
            state = json.loads(uploaded.read().decode("utf-8"))
            if required_keys_ok(state):
                st.session_state.active = state
                st.success("Progress restored.")
            else:
                st.error("This JSON does not look like a saved MM 369 state.")
        except Exception as e:
            st.error(f"Could not parse file: {e}")


def begin_cycle(program_key: str, start_dt: date):
    start_iso = to_iso(start_dt)
    st.session_state.active = {
        "program_key": program_key,
        "start_iso": start_iso,
        "id": cycle_id(program_key, start_iso),
        "checks": {},  # id -> bool
    }


def view_tracker():
    if not st.session_state.active:
        st.session_state.page = "home"
        st.rerun()
    header_bar()

    active = st.session_state.active
    program = PROGRAMS[active["program_key"]]
    st.subheader(program["label"])
    st.caption(f"Start: {active['start_iso']}")

    # Progress
    total, done = count_tasks(active)
    pct = int(round((done / total) * 100)) if total else 0
    st.progress(pct / 100.0, text=f"Overall progress: {pct}%")

    tabs = st.tabs(["Days 1–3", "Days 4–6", "Days 7–9"])
    for tab, group_key in zip(tabs, GROUP_ORDER):
        with tab:
            render_group(active, group_key)


def render_group(active: Dict[str, Any], group_key: str):
    program = PROGRAMS[active["program_key"]]
    group = program["groups"][group_key]
    start_day, end_day = [int(x) for x in group_key.split("-")]
    days = list(range(start_day, end_day + 1))

    # Three columns for three days in the group
    cols = st.columns(3)
    for idx, day_num in enumerate(days):
        with cols[idx]:
            d = iso_to_date(active["start_iso"]) + timedelta(days=day_num - 1)
            st.markdown(f"**Day {day_num}**")
            st.markdown(f"<div class='date-sub'>{fmt_date(d)}</div>", unsafe_allow_html=True)
            for s_idx, section in enumerate(group["sections"]):
                st.markdown(f"<div class='section-label'>{section['name']}</div>", unsafe_allow_html=True)
                for i_idx, txt in enumerate(section["items"]):
                    cid = f"{active['id']}|d{day_num}|s{s_idx}|i{i_idx}"
                    # initialize default on first render
                    if cid not in st.session_state.get("checks", {}):
                        st.session_state.setdefault("checks", {})
                        st.session_state["checks"].setdefault(cid, False)
                    # sync with active state storage
                    if cid not in active["checks"]:
                        active["checks"][cid] = False
                    # draw checkbox bound to session state
                    new_val = st.checkbox(txt, key=cid, value=active["checks"][cid])
                    if new_val != active["checks"][cid]:
                        active["checks"][cid] = new_val
    # persist
    st.session_state.active = active


# -----------------------------
# History / medals
# -----------------------------

def view_history():
    header_bar()
    st.subheader("Your medals")
    count = st.session_state.completed_cycles
    if count == 0:
        st.info("No completed 9‑day cycles yet. You got this!")
    else:
        st.markdown(f"<div class='medal'>{'🥇' * min(count, 12)} {'+' if count>12 else ''}</div>", unsafe_allow_html=True)
        st.caption(f"Completed cycles: {count}")


# -----------------------------
# Utilities for validation & counting
# -----------------------------

def required_keys_ok(state: Dict[str, Any]) -> bool:
    needed = {"program_key", "start_iso", "id", "checks"}
    return isinstance(state, dict) and needed.issubset(state.keys())


def iso_to_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def count_tasks(state: Dict[str, Any]) -> Tuple[int, int]:
    program = PROGRAMS[state["program_key"]]
    total = 0
    done = 0
    for group_key in GROUP_ORDER:
        group = program["groups"].get(group_key)
        if not group:
            continue
        start_day, end_day = [int(x) for x in group_key.split("-")]
        days = list(range(start_day, end_day + 1))
        for s_idx, section in enumerate(group["sections"]):
            for i_idx, _ in enumerate(section["items"]):
                for day_num in days:
                    cid = f"{state['id']}|d{day_num}|s{s_idx}|i{i_idx}"
                    total += 1
                    if state["checks"].get(cid):
                        done += 1
    return total, done


def is_cycle_complete(state: Dict[str, Any]) -> bool:
    total, done = count_tasks(state)
    return total > 0 and total == done


# -----------------------------
# Router
# -----------------------------
if st.session_state.page == "home":
    view_home()
elif st.session_state.page == "tracker":
    view_tracker()
else:
    view_history()
