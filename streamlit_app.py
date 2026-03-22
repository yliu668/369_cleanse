# app.py — MM 369 tracker with Supabase Auth + DB persistence + URL-state fallback

from __future__ import annotations
import json, base64, zlib
from typing import Dict, Any, Tuple, Optional
import random
import streamlit as st
from datetime import date, datetime, timedelta, timezone

# ---------- Third-party auth/db ----------
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

try:
    from extra_streamlit_components import CookieManager
    COOKIES_AVAILABLE = True
except ImportError:
    COOKIES_AVAILABLE = False
    CookieManager = None

FINISH_WARN_THRESHOLD = 0.80  # confirm only if progress is below 80%

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="MM 369 Cleanse Tracker", page_icon="🥗", layout="wide")
import streamlit.components.v1 as components


# -----------------------------
# Styles
# -----------------------------
st.markdown(
    """
    <style>
:root{ --st-bg: var(--background-color); --st-bg2: var(--secondary-background-color);
--st-text: var(--text-color); --st-primary: var(--primary-color) }
html, body { color: var(--st-text); }
.card{ border:1px solid rgba(0,0,0,.10); border-radius:16px; padding:1rem; background:var(--st-bg2) }
.select-card{ border:1px solid rgba(0,0,0,.12); border-radius:14px; padding:1rem; text-align:center; background:var(--st-bg2) }
.stButton>button{ border-radius:14px; padding:0.6rem 1rem; border:1px solid rgba(0,0,0,.12); background:transparent; color:var(--st-text) }
.stButton>button:hover{ border-color: rgba(0,0,0,.35) }
.pill{display:inline-flex;gap:6px;align-items:center;padding:.35rem .6rem;border-radius:9999px;border:1px solid rgba(0,0,0,.12);background:var(--st-bg2)}
.divider{height:1px; background:rgba(0,0,0,.12); margin:.75rem 0}
.big-title {font-size:2.1rem; font-weight:800; letter-spacing:.3px}
.subtle {font-size:0.9rem; opacity:.85}
.date-sub {opacity:.75; font-size:.85rem}
.section-label {font-weight:700; margin:.25rem 0 .35rem 0}
.medal {font-size:1.8rem; letter-spacing:2px}
.kicker {font-size:.85rem; text-transform:uppercase; letter-spacing:.1em; opacity:.7}
.option-card{ position:relative; border:1.5px solid rgba(0,0,0,.12); border-radius:16px; padding:1.1rem; text-align:center; background:var(--st-bg2); transition:box-shadow .20s ease, border-color .20s ease, transform .12s ease }
.option-card:hover{ transform:translateY(-1px); box-shadow:0 6px 18px rgba(0,0,0,.08) }
.option-card.selected{ outline:3px solid var(--st-primary) }
.option-card-title{ font-weight:700 }
.option-card .badge{ position:absolute; top:10px; right:12px; font-size:1rem; opacity:0; transition:opacity .2s ease }
.option-card.selected .badge{ opacity:1 }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Program templates (content preserved; minor typos fixed)
# -----------------------------
PROGRAMS: Dict[str, Dict[str, Any]] = {
    "original": {
        "label": "Original 369",
        "groups": {
            "1-3": {"sections": [
                {"name": "Upon Waking", "items": ["16 ounces lemon or lime water"]},
                {"name": "Morning", "items": [
                    "Wait 15–30 minutes",
                    "16 ounces celery juice",
                    "Wait another 15–30 minutes",
                    "Breakfast & mid-morning snack (within guidelines) — Day 2–3 include 1–2 apples/applesauce",
                ]},
                {"name": "Lunchtime", "items": ["Meal of your choice (within guidelines) + steamed zucchini/summer squash"]},
                {"name": "Mid-Afternoon", "items": ["1–2 apples (or applesauce) with 1–2 dates"]},
                {"name": "Dinnertime", "items": ["Meal of your choice (within guidelines)"]},
                {"name": "Evening", "items": ["Apple or applesauce (optional)", "16 ounces lemon or lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
                {"name": "Guidelines", "items": ["Reduce consumption of radical fats", "Avoid No foods (eggs, dairy, gluten, salt, pork, corn, oils, soy, lamb, tuna, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives)", "Avoid baked or roasted foods","1L water during the day"]}
            ]},
            "4-6": {"sections": [
                {"name": "Upon Waking", "items": ["16 ounces lemon or lime water"]},
                {"name": "Morning", "items": [
                    "Wait 15–30 minutes",
                    "16 ounces celery juice",
                    "Wait another 15–30 minutes",
                    "Liver Rescue Smoothie (wblueberries + bananas+red pitayas)",
                ]},
                {"name": "Lunchtime", "items": ["Steamed asparagus with Liver Rescue Salad"]},
                {"name": "Mid-Afternoon", "items": ["At least 1–2 apples/applesauce + 1–3 dates + celery sticks"]},
                {"name": "Dinnertime", "items": ["Steamed asparagus with Liver Rescue Salad. Day 5: brussels sprouts instead of asparagus. Day 6: both + liver rescue salad"]},
                {"name": "Evening", "items": ["Apple/applesauce (if desired)", "16 ounces lemon/lime water", "Hibiscus, lemon balm, or chaga tea"]},
                {"name": "Guidelines", "items": ["Avoid radical fats entirely. Skip beans too", "Avoid No foods (eggs, dairy, gluten, salt, pork, corn, oils, soy, lamb, tuna, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives)","Bring more fruits and leafy greens everyday", "Avoid baked or roasted foods","Devote yourself to fruits and veggies","1L water during the day"]},
            ]},
            "7-8": {"sections": [
                {"name": "Upon Waking", "items": ["16 ounces lemon or lime water"]},
                {"name": "Morning", "items": [
                    "Wait 15–30 minutes",
                    "16 ounces celery juice",
                    "Wait another 15–30 minutes",
                    "Liver Rescue Smoothie (wblueberries + bananas+red pitayas)",
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
                {"name": "Guidelines", "items": ["Avoid radical fats entirely. Skip beans too", "Avoid No foods (eggs, dairy, gluten, salt, corn, oils, meat, soy, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives", "Avoid baked or roasted foods","Devote yourself to fruits and veggies", "1L water during the day"]},
            ]},
            "9": {"sections": [
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
                    "Wait at least 15–30 minutes then",
                    "early evening: 16 ounces celery juice",
                ]},
                {"name": "Dinnertime", "items": ["Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)"]},
                {"name": "Evening", "items": ["16 ounces lemon or lime water", "Hibiscus, lemon balm, or chaga tea"]},
                {"name": "Guidelines", "items": ["Avoid radical fats entirely. Skip beans too", "Avoid No foods (eggs, dairy, gluten, salt, corn, oils, meat, soy, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives", "Avoid baked or roasted foods", "1L water during the day", "Stick with liquid and blended", "Give yourself rest", "Give yourself a thumbs up 👍"]},
            ]},
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
                {"name": "Guidelines", "items": ["Avoid radical fats (nuts, seeds, oils, coconut, avocado...)entirely", "Avoid No foods (eggs, dairy, gluten, salt, corn, oils, meat, soy, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives)","Stick to fruits and leafy greens, millet and oats (if desired)", "Avoid baked or roasted foods","1L water during the day"]}
            ]},
            "4-6": {"sections": [
                {"name": "Upon Waking", "items": ["16 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "24 ounces celery juice", "Wait another 15–30 mins", "Fruit-based breakfast of your choice (dried mangoes, figs, dates OK) and apples if desired"]},
                {"name": "Lunchtime", "items": ["Meal of your choice (within guidelines)"]},
                {"name": "Mid-Afternoon", "items": ["Optional apple + 1–4 dates + cucumber slices + celery sticks"]},
                {"name": "Dinnertime", "items": ["Meal of your choice (within guidelines)"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
                {"name": "Guidelines", "items": ["Avoid radical fats (nuts, seeds, oils, coconut, avocado...)entirely", "Avoid No foods (eggs, dairy, gluten, salt, corn, oils, meat, soy, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives)","Stick to fruits and leafy greens, millet and oats (if desired)", "Avoid baked or roasted foods","1L water during the day"]}
            ]},
            "7-8": {"sections": [
                {"name": "Upon Waking", "items": ["16 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "32 ounces celery juice", "Wait another 15–30 mins", "Fruit-based breakfast of your choice (fresh only, frozen OK) and apples if desired"]},
                {"name": "Lunchtime", "items": ["Meal of your choice (within guidelines)"]},
                {"name": "Mid-Afternoon", "items": ["Optional apple + 1–4 dates + cucumber slices + celery sticks"]},
                {"name": "Dinnertime", "items": ["Meal of your choice (within guidelines) that incorporates steamed asparagus and/or brussels sprouts"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
                {"name": "Guidelines", "items": ["Avoid radical fats (nuts, seeds, oils, coconut, avocado...)entirely", "Avoid No foods (eggs, dairy, gluten, salt, corn, oils, meat, soy, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives)","Stick to fruits and leafy greens, millet and oats (if desired)", "Avoid baked or roasted foods","1L water during the day"]}
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
                {"name": "Guidelines", "items": ["Avoid radical fats (nuts, seeds, oils, coconut, avocado...)entirely", "Avoid No foods (eggs, dairy, gluten, salt, corn, oils, meat, soy, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives)","Stick to fruits. Avoid millet and oats on Day 9)", "Avoid baked or roasted foods","1L water during the day", "Stick with liquid and blended", "Give yourself rest", "Give yourself a thumbs up 👍"]}
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
                {"name": "Guidelines", "items": ["Avoid radical fats (nuts, seeds, oils, coconut, avocado...)entirely", "Avoid No foods (eggs, dairy, gluten, salt, corn, oils, meat, soy, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives)","Devote yourself exclusively to raw fruits, vegetables, and leafy greens)", "Avoid baked or roasted foods","1L water during the day"]}
            ]},
            "4-6": {"sections": [
                {"name": "Upon Waking", "items": ["32 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "32 ounces celery juice", "Wait another 15–30 mins", "Heavy Metal Detox Smoothie", "Apples if desired"]},
                {"name": "Lunchtime", "items": ["Liver Rescue Smoothie or Spinach soup (with optional cucumber noodles)"]},
                {"name": "Mid-Afternoon", "items": ["Apples if hungry"]},
                {"name": "Dinnertime", "items": ["Kale Salad/Cauliflower and Greens Bowl/Tomato, Cucumber, and Herb Salad/Leafy Green Nori Rolls/Spinach Soup with optional cucumber noodles"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
                {"name": "Guidelines", "items": ["Avoid radical fats (nuts, seeds, oils, coconut, avocado...)entirely", "Avoid No foods (eggs, dairy, gluten, salt, corn, oils, meat, soy, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives)","Devote yourself exclusively to raw fruits, vegetables, and leafy greens)", "Avoid baked or roasted foods","1L water during the day"]}
            ]},
            "7-8": {"sections": [
                {"name": "Upon Waking", "items": ["32 ounces lemon/lime water"]},
                {"name": "Morning", "items": ["Wait 15–30 mins", "32 ounces celery juice", "Wait another 15–30 mins", "Heavy Metal Detox Smoothie", "Apples if desired"]},
                {"name": "Lunchtime", "items": ["Liver Rescue Smoothie or Spinach soup (with optional cucumber noodles)"]},
                {"name": "Mid-Afternoon", "items": ["Wait at least 60 mins", "32 ounces celery juice", "Wait at least 15–30 minutes then", "Apples if hungry"]},
                {"name": "Dinnertime", "items": ["Kale Salad/Cauliflower and Greens Bowl/Tomato, Cucumber, and Herb Salad/Leafy Green Nori Rolls/Spinach Soup with optional cucumber noodles"]},
                {"name": "Evening", "items": ["Apple/applesauce", "16 ounces of lemon/lime water", "Herbal tea: hibiscus, lemon balm, or chaga"]},
                {"name": "Guidelines", "items": ["Avoid radical fats (nuts, seeds, oils, coconut, avocado...)entirely", "Avoid No foods (eggs, dairy, gluten, salt, corn, oils, meat, soy, seafood...grains, vinegar, natural flavors, fermented foods, nutritional yeast...preservatives)","Devote yourself exclusively to raw fruits, vegetables, and leafy greens)", "Avoid baked or roasted foods","1L water during the day"]}
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
                {"name": "Guidelines", "items": ["Guidelines from previous days", "Stick with liquid and blended", "Give yourself rest", "Give yourself a thumbs up 👍"]}
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
    "Food is meant to be a joyful part of your life. Healthful eating isn't meant to be an exercise in deprivation.",
    "Your body loves you",
    "Your body is fighting for you",
    "Rising out of the ashes",
]

# -----------------------------
# Helpers (dates/state)
# -----------------------------
def to_iso(d: date) -> str: return d.isoformat()
def iso_to_date(s: str) -> date: return datetime.strptime(s, "%Y-%m-%d").date()
def fmt_date(d: date) -> str: return d.strftime("%a, %b %d")
def cycle_id(program_key: str, start_iso: str) -> str: return f"{program_key}|{start_iso}"

def day_index(active: Dict[str, Any]) -> int:
    start = iso_to_date(active["start_iso"]) if isinstance(active["start_iso"], str) else active["start_iso"]
    idx = (today_local() - start).days + 1
    return max(1, min(9, idx))

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

# ---------- URL-state (fallback for anonymous users; stores only True checks) ----------
def _slim_state(state: Dict[str, Any]) -> Dict[str, Any]:
    slim = dict(state)
    slim["checks"] = {k: True for k, v in state.get("checks", {}).items() if v}
    return slim

def _encode_state(state: Dict[str, Any]) -> str:
    j = json.dumps(state, separators=(",", ":"), ensure_ascii=False)
    c = zlib.compress(j.encode("utf-8"))
    return base64.urlsafe_b64encode(c).decode("ascii")

def _decode_state(token: str) -> Optional[Dict[str, Any]]:
    try:
        j = zlib.decompress(base64.urlsafe_b64decode(token.encode("ascii"))).decode("utf-8")
        return json.loads(j)
    except Exception:
        return None

def _get_qp_dict() -> Dict[str, Any]:
    try: return dict(st.query_params)
    except Exception: return st.experimental_get_query_params()

def _set_qp_dict(d: Dict[str, Any]):
    try:
        st.query_params.clear()
        for k, v in d.items(): st.query_params[k] = v
    except Exception:
        st.experimental_set_query_params(**d)

def _clear_qp(): _set_qp_dict({})

def _persist_active_to_url():
    if st.session_state.active: _set_qp_dict({"s": _encode_state(_slim_state(st.session_state.active))})
    else: _clear_qp()

def _rehydrate_from_url() -> bool:
    qp = _get_qp_dict(); token = qp.get("s")
    if token:
        if isinstance(token, list): token = token[0]
        state = _decode_state(token)
        if state and required_keys_ok(state):
            st.session_state.active = state
            st.session_state.checks = dict(state.get("checks", {}))
            _persist_active_to_url()
            return True
    return False

def finish_active_cycle():
    active = st.session_state.get("active")
    if not active:
        return
    if user:
        sb_mark_completed(user.id, active["id"])
    else:
        st.session_state.completed_cycles += 1
    st.session_state.active = None
    _clear_qp()
    st.session_state.page = "history"
    st.balloons()
    st.rerun()

def sb_delete_active(user_id: str, cycle_id: str):
    """Remove the unfinished cycle so it won't restore, and no medal is awarded."""
    if not sb:
        return
    try:
        sb.table("progress").delete().eq("user_id", user_id).eq("cycle_id", cycle_id).execute()
    except Exception as e:
        st.error("Couldn't end the program without awarding a medal.")
        st.code(repr(e))

def sb_finish_cycle(user_id: str, state: Dict[str, Any], medal_awarded: bool, pct_done: int):
    """
    Mark the active cycle as finished (persist checks), and record whether a medal was awarded.
    """
    if not sb or not state:
        return
    try:
        payload = {
            "is_completed": True,
            "medal_awarded": medal_awarded,
            "pct_done": pct_done,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            # persist whatever checks we have at finish time
            "checks": {k: True for k, v in state.get("checks", {}).items() if v},
        }
        (
            sb.table("progress")
              .update(payload)
              .eq("user_id", user_id)
              .eq("cycle_id", state["id"])
              .execute()
        )
    except Exception as e:
        st.error("Couldn't finish the program.")
        st.code(repr(e))

# ---------- Supabase: client, auth, persistence ----------
def _sb_client() -> Optional[Client]:
    """Create Supabase client. Returns None if connection fails or Supabase not available."""
    if not SUPABASE_AVAILABLE:
        return None
    
    # Try multiple ways to access secrets
    url = None
    key = None
    
    try:
        # Method 1: Direct access
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_ANON_KEY")
    except Exception:
        pass
    
    if not url or not key:
        try:
            # Method 2: Dictionary access
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_ANON_KEY"]
        except Exception:
            pass
    
    if not url or not key:
        try:
            # Method 3: Nested in supabase section
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["anon_key"]
        except Exception:
            pass
    
    if not url or not key:
        try:
            # Method 4: Alternate names
            url = st.secrets.get("supabase_url") or st.secrets.get("url")
            key = st.secrets.get("supabase_anon_key") or st.secrets.get("anon_key")
        except Exception:
            pass
    
    if not url or not key: 
        return None
        
    try:
        return create_client(url, key)
    except Exception:
        # SSL certificate errors or other connection issues - fall back to anonymous mode
        return None

# Mount once with a stable key; force it to render early
if COOKIES_AVAILABLE:
    cookies = CookieManager(key="mm_cookies")
    try:
        _ = cookies.get_all()
    except Exception:
        # Cookie manager failed, create a mock
        class MockCookies:
            def get(self, key): return None
            def get_all(self): return {}
            def set(self, *args, **kwargs): pass
            def delete(self, key): pass
        cookies = MockCookies()
else:
    # Create a mock cookie manager
    class MockCookies:
        def get(self, key): return None
        def get_all(self): return {}
        def set(self, *args, **kwargs): pass
        def delete(self, key): pass
    cookies = MockCookies()

# --- Capture browser timezone/offset into cookies (reload at most once) ---
components.html("""
<script>
(function(){
  try{
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
    const offset = -new Date().getTimezoneOffset(); // minutes east of UTC

    const get = (n)=> (document.cookie.match(new RegExp('(?:^|; )'+n+'=([^;]*)'))||[])[1];
    const set = (n,v)=> document.cookie = n+'='+encodeURIComponent(v)+'; path=/; max-age=31536000';

    const hadOff = !!get('mm-off');
    const prevOff = get('mm-off');
    const prevTz  = get('mm-tz');

    if (!prevTz || prevTz !== tz) set('mm-tz', tz);
    if (!prevOff || prevOff !== String(offset)) set('mm-off', String(offset));

    const FLAG = 'mm-tz-reload-attempted';
    const tried = sessionStorage.getItem(FLAG) === '1';

    if (!hadOff && !tried) {
      sessionStorage.setItem(FLAG, '1');
      location.reload();
    }
  } catch(e) {}
})();
</script>
""", height=0)

sb = _sb_client()

# ---- Session token helpers & robust restore/refresh ----
def _put_tokens(at: str, rt: str):
    """
    Persist Supabase tokens:
      - in memory (st.session_state)
      - server cookie "sb-session" (JSON: {"at","rt"}) for convenience
      - server cookie "sb-rt" (string refresh token) for reliable, small cold-restore
      - client localStorage "mm_sb_session" (JSON) + first-party cookies (sb-session, sb-rt) immediately via JS
    """
    st.session_state["_sb_tokens"] = {"at": at, "rt": rt}

    try:
        cookies.set(
            "sb-session",
            json.dumps({"at": at, "rt": rt}),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        cookies.set("sb-rt", rt, expires_at=datetime.now(timezone.utc) + timedelta(days=30))
    except Exception:
        pass

    try:
        js_payload = json.dumps({"at": at, "rt": rt})
        js_rt = json.dumps(rt)
        components.html(f"""
        <script>
        (function(){{
          try {{
            localStorage.setItem('mm_sb_session', {js_payload});
            var secure = (location.protocol === 'https:') ? '; Secure' : '';
            document.cookie = 'sb-session=' + encodeURIComponent({js_payload})
                              + '; path=/; max-age=2592000; SameSite=Lax' + secure;
            document.cookie = 'sb-rt=' + encodeURIComponent({js_rt})
                              + '; path=/; max-age=2592000; SameSite=Lax' + secure;
            setTimeout(function(){{ sessionStorage.setItem('sb-auth-ready', '1'); }}, 50);
          }} catch(e) {{ console.error('Token storage failed:', e); }}
        }})();
        </script>
        """, height=0)
    except Exception:
        pass


def _read_tokens_from_cookie() -> Tuple[Optional[str], Optional[str]]:
    raw = cookies.get("sb-session")
    if not raw:
        return None, None
    try:
        data = json.loads(raw)
        return data.get("at"), data.get("rt")
    except Exception:
        try:
            cookies.delete("sb-session")
        except Exception:
            pass
        return None, None
    
def _read_refresh_cookie() -> Optional[str]:
    """Small cookie that carries ONLY the refresh token (rt)."""
    try:
        return cookies.get("sb-rt")
    except Exception:
        return None

def _try_refresh_with_rt(rt: str):
    """
    Try to mint a fresh session *using only a refresh token*.
    Handles both newer and older gotrue/supabase-py call signatures.
    Returns the new session (or None on failure).
    """
    if not sb or not rt:
        return None

    try:
        res = sb.auth.refresh_session(rt)
        return getattr(res, "session", None)
    except TypeError:
        try:
            sb.auth.set_session(access_token="", refresh_token=rt)
        except Exception:
            pass
        try:
            res = sb.auth.refresh_session()
            return getattr(res, "session", None)
        except Exception:
            return None
    except Exception:
        return None


def _ensure_supabase_session():
    """
    Restore/refresh Supabase session in this order:
      1) In-memory tokens (current run)
      2) Full "sb-session" cookie ({"at","rt"})
      3) Small "sb-rt" cookie (refresh only) -> mint a fresh session
    Then apply tokens via set_session() and proactively refresh near expiry.
    Returns the current user or None.
    """
    if not sb:
        return None

    at = rt = None

    # 1) In-memory
    t = st.session_state.get("_sb_tokens")
    if t:
        at, rt = t.get("at"), t.get("rt")

    # 2) Full cookie {at, rt}
    if not (at and rt):
        cat, crt = _read_tokens_from_cookie()
        if cat and crt:
            at, rt = cat, crt

    # 3) Refresh-token-only cookie -> try minting a fresh session
    if not (at and rt):
        c_rt = _read_refresh_cookie()
        if c_rt:
            new_sess = _try_refresh_with_rt(c_rt)
            if new_sess:
                at = getattr(new_sess, "access_token", None)
                rt = getattr(new_sess, "refresh_token", None)
                if at and rt:
                    _put_tokens(at, rt)

    # Apply tokens if we have them
    if at and rt:
        try:
            sb.auth.set_session(access_token=at, refresh_token=rt)
        except Exception:
            pass

    # Proactive refresh if close to expiry (≈5 minutes)
    try:
        sess_obj = sb.auth.get_session()
        if sess_obj and getattr(sess_obj, "expires_at", None):
            exp = datetime.fromtimestamp(sess_obj.expires_at, tz=timezone.utc)
            if exp - datetime.now(timezone.utc) < timedelta(minutes=5):
                refreshed = _try_refresh_with_rt(rt)
                if refreshed:
                    _put_tokens(refreshed.access_token, refreshed.refresh_token)
                    try:
                        sb.auth.set_session(
                            access_token=refreshed.access_token,
                            refresh_token=refreshed.refresh_token,
                        )
                    except Exception:
                        pass

        res = sb.auth.get_user()
        return getattr(res, "user", None)
    except Exception:
        return None


def sb_current_user():
    if not sb: return None
    try:
        res = sb.auth.get_user()
        return res.user
    except Exception:
        return None


def sb_sign_in(email: str, password: str) -> bool:
    if not sb:
        st.error("⚠️ **Supabase not configured**")
        st.write("**Please check your Streamlit secrets configuration:**")
        st.write("1. Go to your app settings in Streamlit Cloud")
        st.write("2. Click on 'Secrets' in the left sidebar")
        st.write("3. Make sure you have these exact keys:")
        st.code("""SUPABASE_URL = "your-project-url"
SUPABASE_ANON_KEY = "your-anon-key" """)
        st.write("**OR** if using nested format:")
        st.code("""[supabase]
url = "your-project-url"
anon_key = "your-anon-key" """)
        
        with st.expander("🔍 Debug: Show what secrets are available"):
            try:
                available_keys = list(st.secrets.keys())
                st.write("Available secret keys:", available_keys)
                if "supabase" in available_keys:
                    st.write("Nested supabase keys:", list(st.secrets["supabase"].keys()))
            except Exception as e:
                st.write("Could not read secrets:", e)
        return False
    try:
        res = sb.auth.sign_in_with_password({"email": email, "password": password})

        sess = getattr(res, "session", None)
        at = getattr(sess, "access_token", None) if sess else None
        rt = getattr(sess, "refresh_token", None) if sess else None
        if not at or not rt:
            st.error("Sign-in returned no session tokens.")
            st.code(str(res))
            return False

        # Make the session active NOW
        sb.auth.set_session(access_token=at, refresh_token=rt)

        # Store in memory
        st.session_state["_sb_tokens"] = {"at": at, "rt": rt}

        # Store in server-side cookies
        try:
            cookies.set("sb-session", json.dumps({"at": at, "rt": rt}),
                       expires_at=datetime.now(timezone.utc) + timedelta(days=30))
            cookies.set("sb-rt", rt,
                       expires_at=datetime.now(timezone.utc) + timedelta(days=30))
        except Exception:
            pass

        # Write to localStorage + client cookies, then reload
        js_payload = json.dumps({"at": at, "rt": rt})
        js_rt = json.dumps(rt)
        
        st.session_state["_auth_toast"] = "Signed in ✅"
        st.session_state.page = "home"
        st.markdown("Signing you in...")
        
        components.html(f"""
        <script>
        (function(){{
          try {{
            if (sessionStorage.getItem('auth-reloading') === '1') return;
            sessionStorage.setItem('auth-reloading', '1');
            
            localStorage.setItem('mm_sb_session', {js_payload});
            
            var secure = (location.protocol === 'https:') ? '; Secure' : '';
            document.cookie = 'sb-session=' + encodeURIComponent({js_payload})
                              + '; path=/; max-age=2592000; SameSite=Lax' + secure;
            document.cookie = 'sb-rt=' + encodeURIComponent({js_rt})
                              + '; path=/; max-age=2592000; SameSite=Lax' + secure;
            
            setTimeout(function(){{ location.reload(); }}, 800);
          }} catch(e) {{
            console.error('Auth error:', e);
            sessionStorage.removeItem('auth-reloading');
          }}
        }})();
        </script>
        """, height=0)
        st.stop()

    except Exception as e:
        st.error("Sign-in failed.")
        st.code(repr(e))
        return False


def sb_sign_up(email: str, password: str) -> bool:
    if not sb: return False
    try:
        sb.auth.sign_up({"email": email, "password": password})
        st.success("Account created! You may sign in now.")
        return True
    except Exception as e:
        st.error(f"Sign-up failed: {e}")
        return False


def sb_sign_out():
    if sb:
        try:
            sb.auth.sign_out()
        except Exception:
            pass

    try:
        cookies.delete("sb-session")
    except Exception:
        pass
    try:
        cookies.delete("sb-rt")
    except Exception:
        pass

    st.session_state.pop("_sb_tokens", None)
    st.session_state.active = None
    try:
        _clear_qp()
    except Exception:
        pass

    st.session_state.page = "menu"
    st.session_state["_auth_toast"] = "Signed out ✅"
    
    components.html("""
    <script>
    try {
      localStorage.removeItem('mm_sb_session');
      sessionStorage.removeItem('sb-restored');
      sessionStorage.removeItem('auth-reloading');
      sessionStorage.removeItem('sb-restore-attempts');

      var attrs = '; path=/; max-age=0; SameSite=Lax' + (location.protocol==='https:'?'; Secure':'');
      document.cookie = 'sb-session=' + '' + attrs;
      document.cookie = 'sb-rt=' + '' + attrs;
    } catch(e) {}
    setTimeout(function(){ location.reload(); }, 50);
    </script>
    """, height=0)
    st.stop()


def sb_load_active_row(user_id: str) -> Optional[Dict[str, Any]]:
    if not sb: return None
    try:
        q = (
            sb.table("progress")
              .select("*")
              .eq("user_id", user_id)
              .eq("is_completed", False)
              .order("updated_at", desc=True)
              .limit(1)
              .execute()
        )
        rows = q.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def sb_cleanup_duplicate_active(user_id: str):
    """Clean up duplicate active cycles - keep only the most recent one."""
    if not sb:
        return
    try:
        q = (
            sb.table("progress")
              .select("*")
              .eq("user_id", user_id)
              .eq("is_completed", False)
              .order("updated_at", desc=True)
              .execute()
        )
        rows = q.data or []
        if len(rows) > 1:
            # Keep the first (most recent), delete the rest
            for row in rows[1:]:
                sb.table("progress").delete().eq("id", row["id"]).execute()
    except Exception:
        pass


def sb_upsert_active(user_id: str, state: Dict[str, Any]):
    if not sb or not state:
        return
    payload = {
        "user_id": user_id,
        "cycle_id": state["id"],
        "program_key": state["program_key"],
        "start_iso": state["start_iso"],
        "checks": {k: True for k, v in state.get("checks", {}).items() if v},
        "is_completed": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        sb.table("progress").upsert(payload, on_conflict="user_id,cycle_id").execute()
    except Exception as e:
        st.error("Saving progress failed.")
        st.code(repr(e))


def sb_mark_completed(user_id: str, cycle_id: str):
    if not sb: return
    sb.table("progress").update({"is_completed": True, "updated_at": datetime.now(timezone.utc).isoformat()}) \
      .eq("user_id", user_id).eq("cycle_id", cycle_id).execute()


def sb_completed_count(user_id: str) -> int:
    if not sb: return 0
    res = (sb.table("progress")
             .select("id", count="exact")
             .eq("user_id", user_id)
             .eq("is_completed", True)
             .eq("medal_awarded", True)
             .execute())
    return getattr(res, "count", None) or (len(res.data) if isinstance(res.data, list) else 0)


def _browser_offset_minutes() -> int:
    try:
        return int(cookies.get("mm-off") or "0")
    except Exception:
        return 0


def today_local() -> date:
    return (datetime.now(timezone.utc) + timedelta(minutes=_browser_offset_minutes())).date()


def now_local() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=_browser_offset_minutes())


# -----------------------------
# Session state init
# -----------------------------
if "page" not in st.session_state: st.session_state.page = "home"
if "active" not in st.session_state: st.session_state.active = None
if "checks" not in st.session_state: st.session_state.checks = {}
if "completed_cycles" not in st.session_state: st.session_state.completed_cycles = 0

# Cold-start restoration: restore cookies from localStorage
components.html("""
<script>
(function(){
  try{
    var hasCookie = document.cookie.indexOf('sb-session=') !== -1;
    var didReload = sessionStorage.getItem('sb-restored') === '1';

    if (!hasCookie && !didReload) {
      var raw = localStorage.getItem('mm_sb_session');
      if (raw) {
        var secure = (location.protocol === 'https:') ? '; Secure' : '';
        document.cookie = 'sb-session=' + encodeURIComponent(raw)
                          + '; path=/; max-age=2592000; SameSite=Lax' + secure;
        sessionStorage.setItem('sb-restored', '1');
        location.reload();
      }
    }
  }catch(e){}
})();
</script>
""", height=0)

# Restore session
try:
    user = _ensure_supabase_session()
except Exception as e:
    user = None
    # Silently fail - app will work in anonymous mode

# Clear auth guards after successful restoration
if user:
    components.html("""
    <script>
    sessionStorage.removeItem('auth-reloading');
    sessionStorage.removeItem('sb-restore-attempts');
    </script>
    """, height=0)
    
    # Clean up any duplicate active cycles
    sb_cleanup_duplicate_active(user.id)

# Load active cycle
if user and not st.session_state.active:
    row = sb_load_active_row(user.id)
    if row:
        st.session_state.active = {
            "program_key": row["program_key"],
            "start_iso": row["start_iso"],
            "id": row["cycle_id"],
            "checks": dict(row.get("checks", {})),
        }
        st.session_state.checks = dict(row.get("checks", {}))
else:
    _rehydrate_from_url()

# Debug panel
_qp = {k: (v[0] if isinstance(v, list) else v) for k, v in _get_qp_dict().items()}
if _qp.get("debug") == "1":
    st.sidebar.header("System Status")
    st.sidebar.write("Supabase available:", SUPABASE_AVAILABLE)
    st.sidebar.write("Cookies available:", COOKIES_AVAILABLE)
    
    # Check secrets
    st.sidebar.write("---")
    st.sidebar.header("Secrets Status")
    try:
        available_keys = list(st.secrets.keys())
        st.sidebar.write("Secret keys found:", len(available_keys))
        st.sidebar.write("Keys:", available_keys)
        
        has_url = any(k in available_keys for k in ["SUPABASE_URL", "supabase_url", "url", "supabase"])
        has_key = any(k in available_keys for k in ["SUPABASE_ANON_KEY", "supabase_anon_key", "anon_key"])
        st.sidebar.write("URL found:", has_url)
        st.sidebar.write("Key found:", has_key)
    except Exception as e:
        st.sidebar.write("Cannot read secrets:", str(e))
    
    st.sidebar.write("---")
    st.sidebar.header("Auth Debug")
    st.sidebar.write("session_state tokens:", bool(st.session_state.get("_sb_tokens")))
    st.sidebar.write("sb client:", "OK" if sb else "None")
    st.sidebar.write("user present:", bool(user))
    if user:
        st.sidebar.write("user id:", getattr(user, "id", None))
        st.sidebar.write("email:", getattr(user, "email", None))
    st.sidebar.write("cookie sb-session:", bool(cookies.get("sb-session")))
    st.sidebar.write("page:", st.session_state.page)
    st.sidebar.write("active:", bool(st.session_state.get("active")))

# Show toast if present
_msg = st.session_state.pop("_auth_toast", None)
if _msg:
    st.toast(_msg)


# -----------------------------
# Nuclear Reset (if needed)
# -----------------------------
if _qp.get("reset") == "nuclear":
    st.warning("⚠️ NUCLEAR RESET MODE")
    st.write("This will:")
    st.write("- Clear all browser storage (localStorage, sessionStorage, cookies)")
    st.write("- Sign you out completely")
    st.write("- Reset all app state")
    
    if st.button("🔴 EXECUTE NUCLEAR RESET", type="primary"):
        # Server-side cleanup
        if user:
            sb_sign_out()
        
        # Client-side nuclear option
        components.html("""
        <script>
        try {
            // Clear ALL storage
            localStorage.clear();
            sessionStorage.clear();
            
            // Clear ALL cookies
            document.cookie.split(";").forEach(function(c) {
                document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
            });
            
            alert('Nuclear reset complete. The page will now reload.');
            setTimeout(function(){ window.location.href = '/'; }, 500);
        } catch(e) {
            alert('Reset failed: ' + e);
        }
        </script>
        """, height=0)
        st.stop()
    
    st.info("👆 Click the button above to reset everything. Or remove ?reset=nuclear from URL to continue normally.")
    st.stop()


# -----------------------------
# UI Components
# -----------------------------
def header_bar():
    # Show anonymous mode warning if Supabase failed to connect
    if not sb and not user:
        st.info("ℹ️ Running in **anonymous mode** - Your progress is saved in the URL. Make sure to bookmark the page or export your progress regularly!")
    
    with st.container():
        left, mid, right = st.columns([2, 2, 3])

        with left:
            st.markdown("<div class='big-title'>Cleanse to heal 369 tracker</div>", unsafe_allow_html=True)
            st.markdown("<div class='subtle'>YOU CAN HEAL. Keep up the good work</div>", unsafe_allow_html=True)

        with mid:
            if st.session_state.active:
                st.markdown(
                    f"<div class='pill'>📆 Start: <b>{st.session_state.active['start_iso']}</b></div>",
                    unsafe_allow_html=True,
                )

        with right:
            if user:
                usr_email = getattr(user, "email", None) or "account"
                st.markdown(f"<div class='pill'>🔐 Signed in as <b>{usr_email}</b></div>", unsafe_allow_html=True)
                st.write("")

            c1, c2, c3, c4 = st.columns(4)

            if user:
                if c1.button("🔒 Sign out"):
                    sb_sign_out()

            if c2.button("🏠 Home"):
                st.session_state.page = "home"
                st.rerun()

            if c3.button("🔄 Start Over"):
                if user and st.session_state.active:
                    st.session_state["_show_start_over_hint"] = True
                    st.rerun()
                else:
                    st.session_state.active = None
                    _clear_qp()
                    st.session_state.page = "menu"
                    st.rerun()

            if st.session_state.active:
                if c4.button("🥇 Finish program"):
                    total, done = count_tasks(st.session_state.active)
                    frac = (done / total) if total else 0.0
                    pct = int(round(frac * 100))

                    if is_cycle_complete(st.session_state.active) or (frac >= FINISH_WARN_THRESHOLD):
                        if user:
                            sb_finish_cycle(user.id, st.session_state.active, medal_awarded=True, pct_done=pct)
                        else:
                            st.session_state.completed_cycles += 1

                        st.session_state.active = None
                        _clear_qp()
                        st.session_state.page = "history"
                        st.balloons()
                        st.rerun()
                    else:
                        st.session_state["_confirm_finish"] = {"pct": frac}
                        st.rerun()

        if st.session_state.pop("_show_start_over_hint", False):
            st.info("Change your mind? Click Finish program button to re-select a new program")

    cf = st.session_state.get("_confirm_finish")
    if cf:
        pct = int(round(cf.get("pct", 0.0) * 100))
        st.warning(
            f"You haven't fully finished the program ({pct}% complete). "
            "Are you sure you want to end it now? If you finish it when you're at least 80%, you will earn a medal"
        )
        cc1, cc2 = st.columns([1, 1])
        with cc1:
            if st.button("Yes – finish without medal", key="confirm_finish_yes", type="primary"):
                st.session_state.pop("_confirm_finish", None)
                if st.session_state.active:
                    total, done = count_tasks(st.session_state.active)
                    frac = (done / total) if total else 0.0
                    pct2 = int(round(frac * 100))

                    if user:
                        sb_finish_cycle(user.id, st.session_state.active, medal_awarded=False, pct_done=pct2)

                st.session_state.active = None
                _clear_qp()
                st.session_state.page = "history"
                st.rerun()

        with cc2:
            if st.button("Go back. I'll keep trying", key="confirm_finish_no"):
                st.session_state.pop("_confirm_finish", None)
                st.toast("Continuing current program")


# -----------------------------
# Views
# -----------------------------
def view_auth_gate():
    st.subheader("Sign up or sign in to save your progress")
    
    # Show nuclear reset option if stuck
    with st.expander("🆘 Stuck at login? Try nuclear reset"):
        st.warning("If you're stuck in a login loop, try the nuclear reset:")
        st.markdown("[🔴 Click here for NUCLEAR RESET](?reset=nuclear)")
        st.caption("This will clear all your browser data and sign you out. You'll need to sign in again.")
    
    with st.form("auth"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        c1, c2 = st.columns(2)
        do_login  = c1.form_submit_button("Sign in", type="primary")
        do_signup = c2.form_submit_button("Sign up")

    if do_login:
        if not email or not pw:
            st.warning("Please enter email and password.")
        elif sb_sign_in(email, pw):
            st.session_state.page = "home"
            st.rerun()

    if do_signup:
        if not email or not pw:
            st.warning("Please enter email and password.")
        else:
            sb_sign_up(email, pw)

    with st.expander("Forgot password? Get a one-time code"):
        otp_email = st.text_input("Email for sign-in code", key="otp_email", value=email or "")
        c_send, c_verify = st.columns([1, 1])

        if c_send.button("Send code"):
            if not sb:
                st.error("Supabase not configured.")
            elif not otp_email:
                st.warning("Enter your email.")
            else:
                try:
                    sb.auth.sign_in_with_otp({"email": otp_email})
                except Exception:
                    pass
                st.success("If an account exists, a 6-digit code was sent.")

        otp_code = st.text_input("Enter 6-digit code", key="otp_code")
        if c_verify.button("Verify & sign in"):
            if not otp_email or not otp_code:
                st.warning("Enter your email and the code.")
            else:
                try:
                    res = sb.auth.verify_otp({
                        "email": otp_email,
                        "token": otp_code,
                        "type": "email",
                    })
                    sess = getattr(res, "session", None)
                    at = getattr(sess, "access_token", None) if sess else None
                    rt = getattr(sess, "refresh_token", None) if sess else None
                    if at and rt:
                        sb.auth.set_session(access_token=at, refresh_token=rt)
                        _put_tokens(at, rt)
                        st.session_state["_auth_toast"] = "Signed in ✅"
                        st.session_state.page = "home"
                        st.rerun()
                    else:
                        st.error("That code is invalid or expired. Request a new one.")
                except Exception:
                    st.error("That code is invalid or expired. Request a new one.")


def view_menu():
    # Allow authenticated users to access menu to start new cycles
    # (previously this redirected to "home", causing an infinite loop
    #  when no active cycle existed)

    header_bar()
    st.markdown("<div style='height: 18px'></div>", unsafe_allow_html=True)
    
    if not user:
        with st.expander("Sign in (optional) to save progress across multiple devices", expanded=False):
            view_auth_gate()

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
            if st.button(
                "✅ Selected" if is_selected else "Select",
                key=f"pick_{key}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                st.session_state._home_selection = key
                st.session_state._home_label = PROGRAMS[key]["label"]
                st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    prog_key = st.session_state.get("_home_selection", "original")
    st.markdown(f"##### Selected: **{PROGRAMS[prog_key]['label']}**")

    today = today_local()
    start_mode = st.radio(
        "Quick start",
        ["Yesterday", "Today", "Tomorrow", "Pick a date"],
        index=1,
        horizontal=True,
    )
    start_date = (
        today
        if start_mode == "Today"
        else (
            today - timedelta(days=1)
            if start_mode == "Yesterday"
            else (
                today + timedelta(days=1)
                if start_mode == "Tomorrow"
                else st.date_input("Start on", value=today)
            )
        )
    )

    if st.button("Start", type="primary"):
        begin_cycle(prog_key, start_date)
        st.session_state.page = "home"
        st.rerun()

    if st.session_state.active:
        st.info("You have an in-progress cycle. Go to Home or click Log now to resume.")
        if st.button("Log now"):
            st.session_state.page = "tracker"
            st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    with st.expander("Export / Import"):
        if st.session_state.active:
            data = json.dumps(st.session_state.active, indent=2)
            st.download_button("⬇️ Export current progress", data, file_name="mm369_progress.json")

        uploaded = st.file_uploader(
            "Your data belong to you. Restore from exported JSON",
            type=["json"],
        )
        if uploaded is not None:
            try:
                state = json.loads(uploaded.read().decode("utf-8"))
                if required_keys_ok(state):
                    st.session_state.active = state
                    st.session_state.checks = dict(state.get("checks", {}))
                    if user:
                        sb_upsert_active(user.id, st.session_state.active)
                    else:
                        _persist_active_to_url()
                    st.success("Progress restored.")
                else:
                    st.error("This JSON does not look like a saved MM 369 state.")
            except Exception as e:
                st.error(f"Could not parse file: {e}")


def view_home():
    if not st.session_state.active:
        st.session_state.page = "menu"; st.rerun()

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
            st.session_state.page = "tracker"; st.rerun()

    with colB:
        st.markdown("**Medals**")
        if user:
            count = sb_completed_count(user.id)
        else:
            count = st.session_state.completed_cycles
        if count == 0:
            st.info("No completed 9-day cycles yet. You got this!")
        else:
            st.markdown(f"<div class='medal'>{'🥇' * min(count, 12)} {'+' if count>12 else ''}</div>", unsafe_allow_html=True)
            st.caption(f"Completed cycles: {count}")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        today_ord = now_local().date().toordinal()
        quote = QUOTES[today_ord % len(QUOTES)]
        st.markdown("<div class='kicker'>Daily MM quote</div>", unsafe_allow_html=True)
        st.write(f'"{quote}"')

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
                    if user: sb_upsert_active(user.id, st.session_state.active)
                    else: _persist_active_to_url()
                    st.success("Progress restored.")
                else:
                    st.error("This JSON does not look like a saved MM 369 state.")
            except Exception as e:
                st.error(f"Could not parse file: {e}")


def view_tracker():
    if not st.session_state.active:
        st.session_state.page = "menu"; st.rerun()

    header_bar()
    active = st.session_state.active
    program = PROGRAMS[active["program_key"]]
    st.subheader(program["label"]); st.caption(f"Start: {active['start_iso']}")

    total, done = count_tasks(active)
    pct = int(round((done / total) * 100)) if total else 0
    st.progress(pct / 100.0, text=f"Overall progress: {pct}%")

    group_keys = group_keys_for_program(program)
    tab_labels = [f"Days {g.replace('-', '–')}" if "-" in g else f"Day {g}" for g in group_keys]
    tabs = st.tabs(tab_labels)
    for tab, gkey in zip(tabs, group_keys):
        with tab: render_group(active, gkey)


def render_group(active: Dict[str, Any], group_key: str):
    program = PROGRAMS[active["program_key"]]
    group = program["groups"][group_key]; days = days_for(group_key)

    cols = st.columns(len(days))
    changed = False
    for col, day_num in zip(cols, days):
        with col:
            d = iso_to_date(active["start_iso"]) + timedelta(days=day_num - 1)
            st.markdown(f"**Day {day_num}**")
            st.markdown(f"<div class='date-sub'>{fmt_date(d)}</div>", unsafe_allow_html=True)
            for s_idx, section in enumerate(group["sections"]):
                st.markdown(f"<div class='section-label'>{section['name']}</div>", unsafe_allow_html=True)
                for i_idx, txt in enumerate(section["items"]):
                    cid = f"{active['id']}|d{day_num}|s{s_idx}|i{i_idx}"
                    val = active["checks"].get(cid, False)
                    new_val = st.checkbox(txt, key=cid, value=val)
                    if new_val and not val:
                        active["checks"][cid] = True; changed = True
                    elif not new_val and val:
                        del active["checks"][cid]; changed = True

    if changed:
        st.session_state.active = active
        if user:
            sb_upsert_active(user.id, active)
            st.toast("Saved to cloud ⛅")
        else:
            _persist_active_to_url()


def view_history():
    header_bar()
    st.subheader("Your medals")
    count = sb_completed_count(user.id) if user else st.session_state.completed_cycles
    if count == 0:
        st.info("No completed 9-day cycles yet. You got this!")
    else:
        st.markdown(f"<div class='medal'>{'🥇' * min(count, 12)} {'+' if count>12 else ''}</div>", unsafe_allow_html=True)
        st.caption(f"Completed cycles: {count}")


# -----------------------------
# Counting & completion
# -----------------------------
def count_tasks(state: Dict[str, Any]) -> Tuple[int, int]:
    program = PROGRAMS[state["program_key"]]
    total = done = 0
    for group_key in group_keys_for_program(program):
        group = program["groups"].get(group_key)
        if not group: continue
        for s_idx, section in enumerate(group["sections"]):
            for i_idx, _ in enumerate(section["items"]):
                for day_num in days_for(group_key):
                    cid = f"{state['id']}|d{day_num}|s{s_idx}|i{i_idx}"
                    total += 1
                    if state["checks"].get(cid): done += 1
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
    if user:
        sb_upsert_active(user.id, st.session_state.active)
        st.toast("Started + saved to cloud ⛅")
    else:
        _persist_active_to_url()


# -----------------------------
# Router
# -----------------------------
if st.session_state.page == "home":
    if st.session_state.active is None:
        st.session_state.page = "menu"; view_menu()
    else:
        view_home()
elif st.session_state.page == "menu":
    view_menu()
elif st.session_state.page == "tracker":
    view_tracker()
else:
    view_history()
