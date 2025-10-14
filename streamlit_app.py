# app.py
# Streamlit implementation of a simple, elegant MM 369 tracker
# - Menu: choose program (Original / Simplified / Advanced) — text-only, no images
# - Pick a start date (calendar) or quick chips (yesterday/today/tomorrow)
# - Home: shows current day, phase, progress, medals, and a motivational quote
# - Tracker: Days 1–3, 4–6, 7–8, 9 grouped; interactive checkboxes
# - Progress bar; Start Over; Finish Cycle awards a medal
# - Optional export/import JSON for persistence without a database (future: Supabase)

from __future__ import annotations
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any, Tuple
import random
import base64, zlib
import streamlit as st

# -----------------------------
# Page config
# -----------------------------
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
:root{
  --st-bg: var(--background-color);
  --st-bg2: var(--secondary-background-color);
  --st-text: var(--text-color);
  --st-primary: var(--primary-color);
}
html, body { color: var(--st-text); }

.card{ border:1px solid rgba(0,0,0,.10); border-radius:16px; padding:1rem; background:var(--st-bg2); }
.card.selected{ outline:3px solid var(--st-primary); }

.select-card{
  border:1px solid rgba(0,0,0,.12);
  border-radius:14px; padding:1rem; text-align:center; background:var(--st-bg2);
  cursor: default; user-select:none; transition:outline-color .2s ease;
}
.select-card.selected{ outline:3px solid var(--st-primary); }

.stButton>button{
  border-radius:14px; padding:0.6rem 1rem; border:1px solid rgba(0,0,0,.12);
  background:transparent; color:var(--st-text);
}
.stButton>button:hover{ border-color: rgba(0,0,0,.35); }

.pill{display:inline-flex;gap:6px;align-items:center;padding:.35rem .6rem;border-radius:9999px;border:1px solid rgba(0,0,0,.12);background:var(--st-bg2); color:var(--st-text)}
.divider{height:1px; background:rgba(0,0,0,.12); margin:.75rem 0}

[data-theme="dark"] .card, @media (prefers-color-scheme: dark){
  .card{ border-color: rgba(255,255,255,.14) }
  .stButton>button{ border-color: rgba(255,255,255,.14) }
  .pill{ border-color: rgba(255,255,255,.14) }
  .divider{ background: rgba(255,255,255,.14) }
  .select-card{ border-color: rgba(255,255,255,.14) }
}

.big-title {font-size:2.1rem; font-weight:800; letter-spacing:.3px}
.subtle {font-size:0.9rem; opacity:.85}
.date-sub {opacity:.75; font-size:.85rem}
.section-label {font-weight:700; margin:.25rem 0 .35rem 0}
.medal {font-size:1.8rem; letter-spacing:2px}
.kicker {font-size:.85rem; text-transform:uppercase; letter-spacing:.1em; opacity:.7}

/***** Modern program option cards *****/
.option-card{
  position:relative;
  border:1.5px solid rgba(0,0,0,.12);
  border-radius:16px;
  padding:1.1rem;
  text-align:center;
  background:var(--st-bg2);
  transition:box-shadow .20s ease, border-color .20s ease, transform .12s ease;
}
.option-card:hover{ transform:translateY(-1px); box-shadow:0 6px 18px rgba(0,0,0,.08); }
.option-card.selected{ outline:3px solid var(--st-primary); }
.option-card-title{ font-weight:700; }

.option-card .badge{
  position:absolute; top:10px; right:12px;
  font-size:1rem; opacity:0; transition:opacity .2s ease;
}
.option-card.selected .badge{ opacity:1; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Program templates
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
                        "Breakfast & mid-morning snack (within guidelines) — Day 2–3 include 1–2 apples/applesauce",
                    ]},
                    {"name": "Lunchtime", "items": [
                        "Meal of your choice (within guidelines) + steamed zucchini/summer squash",
                    ]},
                    {"name": "Mid-Afternoon", "items": ["1–2 apples (or applesauce) with 1–2 dates"]},
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
                        "Wait another 15–30 minutes",
                        "Liver Rescue Smoothie",
                    ]},
                    {"name": "Lunchtime", "items": ["Steamed asparagus with Liver Rescue Salad"]},
                    {"name": "Mid-Afternoon", "items": ["At least 1–2 apples/applesauce + 1–3 dates + celery sticks"]},
                    {"name": "Dinnertime", "items": ["Steamed asparagus with Liver Rescue Salad. Day 5: brussels sprouts instead of asparagus. Day 6: both + liver rescue salad"]},
                    {"name": "Evening", "items": ["Apple/applesauce (if desired)", "16 ounces lemon/lime water", "Hibiscus, lemon balm, or chaga tea"]},
                ]
            },
            "7-8": {
                "sections": [
                    {"name": "Upon Waking", "items": ["16 ounces lemon or lime water"]},
                    {"name": "Morning", "items": [
                        "Wait 15–30 minutes",
                        "16 ounces celery juice",
                        "Wait another 15–30 minutes",
                        "Liver Rescue Smoothie",
                    ]},
                    {"name": "Lunchtime", "items": ["Spinach Soup over cucumber noodles"]},
                    {"name": "Mid-Afternoon", "items": [
                        "Wait at least 60 mins",
                        "16 ounces celery juice",
                        "Wait at least 15–30 minutes then",
                        "1–2 apples/applesauce + cucumber slices + celery sticks",
                    ]},
                    {"name": "Dinnertime", "items": ["Steamed squash, sweet potatoes, yams, or potatoes with steamed asparagus and/or brussels sprouts + optional liver rescue salad"]},
                    {"name": "Evening", "items": ["Optional apple/applesauce", "16 ounces lemon/lime water", "Hibiscus, lemon balm, or chaga tea"]},
                ]
            },
            "9": {
                "sections": [
                    {"name": "Upon Waking", "items": ["16 ounces lemon or lime water"]},
                    {"name": "Morning", "items": [
                        "Wait 15–30 minutes",
                        "16 ounces celery juice",
                        "Wait another 15–30 minutes",
                        "16–20 ounces cucumber-apple juice",
                        "16–20 ounces cucumber-apple juice",
                    ]},
                    {"name": "Lunchtime", "items": ["Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)"]},
                    {"name": "Mid-Afternoon", "items": [
                        "Wait at least 15 mins",
                        "Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)",
                        "Wait at least 15–30 minutes then",
                        "Water",
                        "Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)",
                    ]},
                    {"name": "Dinnertime", "items": ["Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)"]},
                    {"name": "Evening", "items": ["16 ounces lemon or lime water", "Hibiscus, lemon balm, or chaga tea"]},
                ]
            },
        },
    },
    "simplified": {
        "label": "Simplified 369",
        "groups": {
            "1-3": {"sections": [
                {"name": "Upon Waking", "items": ["16 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "16 ounces celery juice", "Wait another 15–30 mins", "Breakfast of your choice (within guidelines) and apples if desired"]},
                {"name": "Lunchtime", "items": ["Meal of your choice (within guidelines)"]},
                {"name": "Mid-Afternoon", "items": ["Optional apple + 1–4 dates + cucumber slices + celery sticks"]},
                {"name": "Dinnertime", "items": ["Meal of your choice (within guidelines)"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
            ]},
            "4-6": {"sections": [
                {"name": "Upon Waking", "items": ["16 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "24 ounces celery juice", "Wait another 15–30 mins", "Fruit-based breakfast of your choice (within guidelines) and apples if desired"]},
                {"name": "Lunchtime", "items": ["Meal of your choice (within guidelines)"]},
                {"name": "Mid-Afternoon", "items": ["Optional apple + 1–4 dates + cucumber slices + celery sticks"]},
                {"name": "Dinnertime", "items": ["Meal of your choice (within guidelines)"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
            ]},
            "7-8": {"sections": [
                {"name": "Upon Waking", "items": ["16 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "32 ounces celery juice", "Wait another 15–30 mins", "Fruit-based breakfast of your choice (within guidelines) and apples if desired"]},
                {"name": "Lunchtime", "items": ["Meal of your choice (within guidelines)"]},
                {"name": "Mid-Afternoon", "items": ["Optional apple + 1–4 dates + cucumber slices + celery sticks"]},
                {"name": "Dinnertime", "items": ["Meal of your choice (within guidelines) that incorporates steamed asparagus and/or brussels sprouts"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
            ]},
            "9": {"sections": [
                {"name": "Upon Waking", "items": ["16 ounces lemon or lime water"]},
                {"name": "Morning", "items": [
                    "Wait 15–30 minutes",
                    "16 ounces celery juice",
                    "Wait another 15–30 minutes",
                    "Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)",
                ]},
                {"name": "Lunchtime", "items": ["Spinach soup"]},
                {"name": "Mid-Afternoon", "items": [
                    "Wait at least 60 mins",
                    "16 ounces celery juice",
                    "Wait at least 15–30 minutes then",
                    "Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)",
                ]},
                {"name": "Dinnertime", "items": ["Asparagus Soup or Zucchini Basil Soup"]},
                {"name": "Evening", "items": ["16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
            ]},
        },
    },
    "advanced": {
        "label": "Advanced 369",
        "groups": {
            "1-3": {"sections": [
                {"name": "Upon Waking", "items": ["32 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "24 or 32 ounces celery juice", "Wait another 15–30 mins", "Heavy Metal Detox Smoothie", "Apples if desired"]},
                {"name": "Lunchtime", "items": ["Liver Rescue Smoothie or Spinach soup (with optional cucumber noodles)"]},
                {"name": "Mid-Afternoon", "items": ["Apples"]},
                {"name": "Dinnertime", "items": ["Kale Salad/Cauliflower and Greens Bowl/Tomato, Cucumber, and Herb Salad/Leafy Green Nori Rolls/Spinach Soup with optional cucumber noodles"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
            ]},
            "4-6": {"sections": [
                {"name": "Upon Waking", "items": ["32 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "32 ounces celery juice", "Wait another 15–30 mins", "Heavy Metal Detox Smoothie", "Apples if desired"]},
                {"name": "Lunchtime", "items": ["Liver Rescue Smoothie or Spinach soup (with optional cucumber noodles)"]},
                {"name": "Mid-Afternoon", "items": ["Apples if hungry"]},
                {"name": "Dinnertime", "items": ["Kale Salad/Cauliflower and Greens Bowl/Tomato, Cucumber, and Herb Salad/Leafy Green Nori Rolls/Spinach Soup with optional cucumber noodles"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
            ]},
            "7-8": {"sections": [
                {"name": "Upon Waking", "items": ["32 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "32 ounces celery juice", "Wait another 15–30 mins", "Heavy Metal Detox Smoothie", "Apples if desired"]},
                {"name": "Lunchtime", "items": ["Liver Rescue Smoothie or Spinach soup (with optional cucumber noodles)"]},
                {"name": "Mid-Afternoon", "items": ["Wait at least 60 mins","32 ounces celery juice","Wait at least 15–30 minutes then","Apples if hungry"]},
                {"name": "Dinnertime", "items": ["Kale Salad/Cauliflower and Greens Bowl/Tomato, Cucumber, and Herb Salad/Leafy Green Nori Rolls/Spinach Soup with optional cucumber noodles"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
            ]},
            "9": {"sections": [
                {"name": "Upon Waking", "items": ["32 ounces lemon or lime water"]},
                {"name": "Morning", "items": [
                    "32 ounces celery juice",
                    "Wait another 15–30 minutes",
                    "20-ounce cucumber-apple juice",
                    "20-ounce cucumber-apple juice",
                ]},
                {"name": "Lunchtime", "items": ["Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)"]},
                {"name": "Mid-Afternoon", "items": [
                    "Wait at least 15 mins",
                    "Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)",
                    "Wait at least 15–30 minutes then",
                    "Water",
                    "Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)",
                ]},
                {"name": "Dinnertime", "items": ["32 ounces celery juice", "Wait 15–30 mins", "Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)"]},
                {"name": "Evening", "items": ["16 ounces lemon or lime water",  "Hibiscus, lemon balm, or chaga tea"]},
            ]},
        },
    },
}

QUOTES = [
    "Artichoke contain phytochemicals that stop the growth of tumors and cysts",
    "Eat foods that love you back",
    "You deserve to heal. You deserve to be happy. You deserve to feel whole",
    "At times when you doubt yourself and things are difficult, think of nature",
    "Your heart serves as the compass for your actions, guiding you to do the right thing when your soul becomes lost",
    "Food is meant to be a joyful part of your life. Healthful eating isn’t meant to be an exercise in deprivation.",
    "Your body loves you",
    "Your body is fighting for you",
    "Rising out of the ashes",
]

# -----------------------------
# Helpers
# -----------------------------
def to_iso(d: date) -> str:
    return d.isoformat()

def iso_to_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def fmt_date(d: date) -> str:
    return d.strftime("%a, %b %d")

def cycle_id(program_key: str, start_iso: str) -> str:
    return f"{program_key}|{start_iso}"

def day_index(active: Dict[str, Any]) -> int:
    start = iso_to_date(active["start_iso"]) if isinstance(active["start_iso"], str) else active["start_iso"]
    idx = (date.today() - start).days + 1
    return max(1, min(9, idx))

def group_for_day(n: int) -> str:
    if n <= 3:
        return "1–3"
    if n <= 6:
        return "4–6"
    return "7–9"

def days_for(group_key: str) -> list[int]:
    if "-" in group_key:
        a, b = group_key.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(group_key)]

def group_keys_for_program(program: Dict[str, Any]) -> list[str]:
    return list(program["groups"].keys())

def group_label_for_day(active: Dict[str, Any], day_num: int) -> str:
    program = PROGRAMS[active["program_key"]]
    for gkey in group_keys_for_program(program):
        if day_num in days_for(gkey):
            return gkey.replace("-", "–")
    keys = group_keys_for_program(program)
    return keys[-1].replace("-", "–")

def required_keys_ok(state: Dict[str, Any]) -> bool:
    needed = {"program_key", "start_iso", "id", "checks"}
    return isinstance(state, dict) and needed.issubset(state.keys())

# ---------- URL persistence helpers ----------
def _get_qp_dict() -> Dict[str, Any]:
    try:
        return dict(st.query_params)
    except Exception:
        return st.experimental_get_query_params()

def _set_qp_dict(d: Dict[str, Any]):
    try:
        st.query_params.clear()
        for k, v in d.items():
            st.query_params[k] = v
    except Exception:
        st.experimental_set_query_params(**d)

def _clear_qp():
    _set_qp_dict({})

def _slim_state(state: Dict[str, Any]) -> Dict[str, Any]:
    # Keep only True checkmarks to shorten the URL token
    slim = dict(state)
    slim["checks"] = {k: True for k, v in state.get("checks", {}).items() if v}
    return slim

def _encode_state(state: Dict[str, Any]) -> str:
    j = json.dumps(state, separators=(",", ":"), ensure_ascii=False)
    c = zlib.compress(j.encode("utf-8"))
    return base64.urlsafe_b64encode(c).decode("ascii")

def _decode_state(token: str) -> Dict[str, Any] | None:
    try:
        j = zlib.decompress(base64.urlsafe_b64decode(token.encode("ascii"))).decode("utf-8")
        return json.loads(j)
    except Exception:
        return None

def _persist_active_to_url():
    if st.session_state.active:
        _set_qp_dict({"s": _encode_state(_slim_state(st.session_state.active))})
    else:
        _clear_qp()

def _rehydrate_from_url() -> bool:
    qp = _get_qp_dict()
    token = qp.get("s")
    if token:
        if isinstance(token, list):
            token = token[0]
        state = _decode_state(token)
        if state and required_keys_ok(state):
            st.session_state.active = state
            # Mirror to a separate key if you like; not required
            st.session_state.checks = dict(state.get("checks", {}))
            _persist_active_to_url()
            return True
    return False

# -----------------------------
# Session state init
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "active" not in st.session_state:
    st.session_state.active = None
if "completed_cycles" not in st.session_state:
    st.session_state.completed_cycles = 0
if "checks" not in st.session_state:
    st.session_state.checks = {}

# Rehydrate from URL AFTER defaults, BEFORE routing
_rehydrate_from_url()

# -----------------------------
# UI Components
# -----------------------------
def header_bar():
    with st.container():
        cols = st.columns([1, 2, 2])
        with cols[0]:
            st.markdown("<div class='big-title'>Cleanse to heal 369 tracker</div>", unsafe_allow_html=True)
            st.markdown("<div class='subtle'>YOU CAN HEAL. Keep up the good work</div>", unsafe_allow_html=True)
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
                _clear_qp()
                st.session_state.page = "menu"
                st.rerun()
            if st.session_state.active and is_cycle_complete(st.session_state.active):
                if c3.button("🥇 Finish this program"):
                    st.session_state.completed_cycles += 1
                    st.session_state.active = None
                    _clear_qp()
                    st.session_state.page = "history"
                    st.balloons()
                    st.rerun()

# -----------------------------
# Views
# -----------------------------
def view_menu():
    header_bar()
    st.write("")
    st.markdown("### Choose your program")

    keys = ["original", "simplified", "advanced"]
    selected_key = st.session_state.get("_home_selection", "original")

    cols = st.columns(3, gap="large")
    for col, key in zip(cols, keys):
        label = PROGRAMS[key]["label"]
        is_selected = key == selected_key
        with col:
            st.markdown(
                f"""
                <div class="option-card {'selected' if is_selected else ''}">
                  <div class="option-card-title">{label}</div>
                  <div class="badge">✓</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            btn_label = "✅ Selected" if is_selected else "Select"
            btn_type = "primary" if is_selected else "secondary"
            if st.button(btn_label, key=f"pick_{key}", use_container_width=True, type=btn_type):
                st.session_state._home_selection = key
                st.session_state._home_label = PROGRAMS[key]["label"]
                st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    prog_key = st.session_state.get("_home_selection", "original")
    st.markdown(f"##### Selected: **{PROGRAMS[prog_key]['label']}**")

    today = date.today()
    start_mode = st.radio("Quick start", ["Yesterday", "Today", "Tomorrow", "Pick a date"], index=1, horizontal=True)
    if start_mode == "Yesterday":
        start_date = today - timedelta(days=1)
    elif start_mode == "Tomorrow":
        start_date = today + timedelta(days=1)
    elif start_mode == "Today":
        start_date = today
    else:
        start_date = st.date_input("Start on", value=today)

    if st.button("Start", type="primary"):
        begin_cycle(prog_key, start_date)
        st.session_state.page = "home"
        st.rerun()

    # Resume block
    if st.session_state.active:
        st.info("You have an in-progress cycle. Go to Home or click Log now to resume.")
        if st.button("Log now"):
            st.session_state.page = "tracker"
            st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # Export / Import
    with st.expander("Export / Import"):
        if st.session_state.active:
            data = json.dumps(st.session_state.active, indent=2)
            st.download_button("⬇️ Export current progress", data, file_name="mm369_progress.json")
        uploaded = st.file_uploader("Your data belong to you. Restore from exported JSON", type=["json"])
        if uploaded is not None:
            try:
                state = json.loads(uploaded.read().decode("utf-8"))
                if required_keys_ok(state):
                    st.session_state.active = state
                    st.session_state.checks = dict(state.get("checks", {}))
                    _persist_active_to_url()
                    st.success("Progress restored.")
                else:
                    st.error("This JSON does not look like a saved MM 369 state.")
            except Exception as e:
                st.error(f"Could not parse file: {e}")

def view_home():
    if not st.session_state.active:
        st.session_state.page = "menu"
        st.rerun()

    header_bar()
    active = st.session_state.active
    program = PROGRAMS[active["program_key"]]

    colA, colB = st.columns([2, 1])
    with colA:
        st.markdown(f"### {program['label']}")
        st.caption(f"Start: {active['start_iso']}")

        total, done = count_tasks(active)
        pct = int(round((done / total) * 100)) if total else 0
        st.progress(pct / 100.0, text=f"Overall progress: {pct}% ({done}/{total})")

        d_idx = day_index(active)
        group_label = group_label_for_day(active, d_idx)
        today_date = fmt_date(iso_to_date(active["start_iso"]) + timedelta(days=d_idx - 1))
        st.write(f"**Today:** Day {d_idx} · Phase {group_label} · {today_date}")

        if st.button("📊 Log now", type="primary"):
            st.session_state.page = "tracker"
            st.rerun()

    with colB:
        st.markdown("**Medals**")
        count = st.session_state.completed_cycles
        if count == 0:
            st.info("No completed 9-day cycles yet. You got this!")
        else:
            st.markdown(f"<div class='medal'>{'🥇' * min(count, 12)} {'+' if count>12 else ''}</div>", unsafe_allow_html=True)
            st.caption(f"Completed cycles: {count}")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        seed = int(datetime.now().strftime('%Y%j'))
        random.seed(seed)
        quote = random.choice(QUOTES)
        st.markdown("<div class='kicker'>MM quote</div>", unsafe_allow_html=True)
        st.write(f"“{quote}”")

    with st.expander("Export / Import"):
        if st.session_state.active:
            data = json.dumps(st.session_state.active, indent=2)
            st.download_button("⬇️ Export current progress", data, file_name="mm369_progress.json")
        uploaded = st.file_uploader("Your data belong to you. Restore from exported JSON", type=["json"], key="restore_home")
        if uploaded is not None:
            try:
                state = json.loads(uploaded.read().decode("utf-8"))
                if required_keys_ok(state):
                    st.session_state.active = state
                    st.session_state.checks = dict(state.get("checks", {}))
                    _persist_active_to_url()
                    st.success("Progress restored.")
                else:
                    st.error("This JSON does not look like a saved MM 369 state.")
            except Exception as e:
                st.error(f"Could not parse file: {e}")

def view_tracker():
    if not st.session_state.active:
        st.session_state.page = "menu"
        st.rerun()

    header_bar()
    active = st.session_state.active
    program = PROGRAMS[active["program_key"]]
    st.subheader(program["label"])
    st.caption(f"Start: {active['start_iso']}")

    total, done = count_tasks(active)
    pct = int(round((done / total) * 100)) if total else 0
    st.progress(pct / 100.0, text=f"Overall progress: {pct}%")

    group_keys = group_keys_for_program(program)
    tab_labels = [f"Days {g.replace('-', '–')}" if "-" in g else f"Day {g}" for g in group_keys]
    tabs = st.tabs(tab_labels)
    for tab, gkey in zip(tabs, group_keys):
        with tab:
            render_group(active, gkey)

def render_group(active: Dict[str, Any], group_key: str):
    program = PROGRAMS[active["program_key"]]
    group = program["groups"][group_key]
    days = days_for(group_key)

    cols = st.columns(len(days))
    for idx, day_num in enumerate(days):
        with cols[idx]:
            d = iso_to_date(active["start_iso"]) + timedelta(days=day_num - 1)
            st.markdown(f"**Day {day_num}**")
            st.markdown(f"<div class='date-sub'>{fmt_date(d)}</div>", unsafe_allow_html=True)
            for s_idx, section in enumerate(group["sections"]):
                st.markdown(f"<div class='section-label'>{section['name']}</div>", unsafe_allow_html=True)
                for i_idx, txt in enumerate(section["items"]):
                    cid = f"{active['id']}|d{day_num}|s{s_idx}|i{i_idx}"
                    val = active["checks"].get(cid, False)
                    new_val = st.checkbox(txt, key=cid, value=val)
                    # Store only True, drop False to keep the URL short
                    if new_val:
                        active["checks"][cid] = True
                    else:
                        if cid in active["checks"]:
                            del active["checks"][cid]

    # Persist after rendering/updating
    st.session_state.active = active
    _persist_active_to_url()

# -----------------------------
# History / medals
# -----------------------------
def view_history():
    header_bar()
    st.subheader("Your medals")
    count = st.session_state.completed_cycles
    if count == 0:
        st.info("No completed 9-day cycles yet. You got this!")
    else:
        st.markdown(f"<div class='medal'>{'🥇' * min(count, 12)} {'+' if count>12 else ''}</div>", unsafe_allow_html=True)
        st.caption(f"Completed cycles: {count}")

# -----------------------------
# Utilities for counting
# -----------------------------
def count_tasks(state: Dict[str, Any]) -> Tuple[int, int]:
    program = PROGRAMS[state["program_key"]]
    total, done = 0, 0
    for group_key in group_keys_for_program(program):
        group = program["groups"].get(group_key)
        if not group:
            continue
        for s_idx, section in enumerate(group["sections"]):
            for i_idx, _ in enumerate(section["items"]):
                for day_num in days_for(group_key):
                    cid = f"{state['id']}|d{day_num}|s{s_idx}|i{i_idx}"
                    total += 1
                    if state["checks"].get(cid):
                        done += 1
    return total, done

def is_cycle_complete(state: Dict[str, Any]) -> bool:
    total, done = count_tasks(state)
    return total > 0 and total == done

# -----------------------------
# Actions
# -----------------------------
def begin_cycle(program_key: str, start_dt: date):
    start_iso = to_iso(start_dt)
    st.session_state.active = {
        "program_key": program_key,
        "start_iso": start_iso,
        "id": cycle_id(program_key, start_iso),
        "checks": {},
    }
    _persist_active_to_url()

# -----------------------------
# Router
# -----------------------------
if st.session_state.page == "home":
    if st.session_state.active is None:
        st.session_state.page = "menu"
        view_menu()
    else:
        view_home()
elif st.session_state.page == "menu":
    view_menu()
elif st.session_state.page == "tracker":
    view_tracker()
else:
    view_history()
