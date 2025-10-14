# app.py — MM 369 tracker with Supabase Auth + DB persistence + URL-state fallback

from __future__ import annotations
import json, base64, zlib
from datetime import date, datetime, timedelta
from typing import Dict, Any, Tuple, Optional
import random
import streamlit as st

# ---------- Third-party auth/db ----------
from supabase import create_client, Client
from extra_streamlit_components import CookieManager

FINISH_WARN_THRESHOLD = 0.80  # confirm only if progress is below 80%

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="MM 369 Cleanse Tracker", page_icon="🥗", layout="wide")

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
            ]},
            "4-6": {"sections": [
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
            ]},
            "7-8": {"sections": [
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
                ]},
                {"name": "Dinnertime", "items": ["Blended melon, fresh watermelon juice, blended papaya, or blended ripe pear, or fresh-squeezed orange juice (as many servings and as often as desired)"]},
                {"name": "Evening", "items": ["16 ounces lemon or lime water", "Hibiscus, lemon balm, or chaga tea"]},
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
                {"name": "Mid-Afternoon", "items": ["Wait at least 60 mins", "32 ounces celery juice", "Wait at least 15–30 minutes then", "Apples if hungry"]},
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
# Helpers (dates/state)
# -----------------------------
def to_iso(d: date) -> str: return d.isoformat()
def iso_to_date(s: str) -> date: return datetime.strptime(s, "%Y-%m-%d").date()
def fmt_date(d: date) -> str: return d.strftime("%a, %b %d")
def cycle_id(program_key: str, start_iso: str) -> str: return f"{program_key}|{start_iso}"

def day_index(active: Dict[str, Any]) -> int:
    start = iso_to_date(active["start_iso"]) if isinstance(active["start_iso"], str) else active["start_iso"]
    idx = (date.today() - start).days + 1
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

# ---------- Supabase: client, auth, persistence ----------
def _sb_client() -> Optional[Client]:
    url = st.secrets.get("SUPABASE_URL"); key = st.secrets.get("SUPABASE_ANON_KEY")
    if not url or not key: return None
    return create_client(url, key)

# Mount once with a stable key; force it to render early
cookies = CookieManager(key="mm_cookies")
_ = cookies.get_all()

sb = _sb_client()

def sb_current_user():
    if not sb: return None
    try:
        res = sb.auth.get_user()
        return res.user
    except Exception:
        return None

def sb_restore_session_from_cookies():
    if not sb:
        return
    raw = cookies.get("sb-session")
    if not raw:
        return
    try:
        data = json.loads(raw)
        at, rt = data.get("at"), data.get("rt")
        if at and rt:
            sb.auth.set_session(at, rt)
    except Exception:
        cookies.delete("sb-session")

def sb_sign_in(email: str, password: str) -> bool:
    if not sb:
        st.error("Supabase not configured (missing SUPABASE_URL / SUPABASE_ANON_KEY).")
        return False
    try:
        res = sb.auth.sign_in_with_password({"email": email, "password": password})

        # Pull tokens (AuthResponse.session is an object in supabase-py v2)
        sess = getattr(res, "session", None)
        at = getattr(sess, "access_token", None) if sess else None
        rt = getattr(sess, "refresh_token", None) if sess else None
        if not at or not rt:
            st.error("Sign-in returned no session tokens.")
            # Helpful for debugging what came back:
            st.code(str(res))
            return False

        # Make the session active NOW (for this run)
        sb.auth.set_session(access_token=at, refresh_token=rt)

        # ✅ Persist for reruns (doesn't depend on the browser cookie)
        st.session_state["_sb_tokens"] = {"at": at, "rt": rt}

        # ✅ Try to persist to a browser cookie too (useful across tabs/devices)
        # CookieManager accepts a datetime for expires_at
        cookies.set("sb-session", json.dumps({"at": at, "rt": rt}),
                    expires_at=datetime.utcnow() + timedelta(days=30))

        # One-time toast + optional redirect
        st.session_state["_auth_toast"] = "Signed in successfully ✅"
        if st.session_state.get("active"):
            st.session_state.page = "home"

        st.rerun()
        return True

    except Exception as e:
        st.error("Sign-in failed.")
        st.code(repr(e))
        return False

def sb_sign_up(email: str, password: str) -> bool:
    if not sb: return False
    try:
        sb.auth.sign_up({"email": email, "password": password})
        st.success("Check your email to confirm your account. You may sign in now.")
        return True
    except Exception as e:
        st.error(f"Sign-up failed: {e}")
        return False

def sb_sign_out():
    # Try to invalidate the server session, but don't surface errors to the UI
    if sb:
        try:
            sb.auth.sign_out()
        except Exception:
            pass  # ignore; we'll still clear local state

    # Clear browser cookie (if set) and in-memory tokens
    try:
        cookies.delete("sb-session")
    except Exception:
        pass
    st.session_state.pop("_sb_tokens", None)

    # Clear any active program *and* the URL fallback so anon mode won't restore it
    st.session_state.active = None
    try:
        _clear_qp()  # removes ?s=... so _rehydrate_from_url() can't bring it back
    except Exception:
        pass

    # Send the user to Menu and show a toast on the next run
    st.session_state.page = "menu"
    st.session_state["_auth_toast"] = "Signed out ✅"

    # Hard rerun now so the router renders Menu immediately
    st.rerun()

    if not sb:
        return
    try:
        sb.auth.sign_out()
    finally:
        cookies.delete("sb-session")
        st.session_state.pop("_sb_tokens", None)  # NEW: clear in-memory tokens


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
        "updated_at": datetime.utcnow().isoformat(),
    }
    try:
        # Idempotent upsert based on unique index (user_id, cycle_id)
        sb.table("progress").upsert(payload, on_conflict="user_id,cycle_id").execute()
    except Exception as e:
        st.error("Saving progress failed.")
        st.code(repr(e))

def sb_mark_completed(user_id: str, cycle_id: str):
    if not sb: return
    sb.table("progress").update({"is_completed": True, "updated_at": datetime.utcnow().isoformat()}) \
      .eq("user_id", user_id).eq("cycle_id", cycle_id).execute()

def sb_completed_count(user_id: str) -> int:
    if not sb: return 0
    res = sb.table("progress").select("id", count="exact").eq("user_id", user_id).eq("is_completed", True).execute()
    return getattr(res, "count", None) or (len(res.data) if isinstance(res.data, list) else 0)

# -----------------------------
# Session state init
# -----------------------------
if "page" not in st.session_state: st.session_state.page = "home"
if "active" not in st.session_state: st.session_state.active = None
if "checks" not in st.session_state: st.session_state.checks = {}
if "completed_cycles" not in st.session_state: st.session_state.completed_cycles = 0  # used only for anon mode

# Try restore (order: Supabase auth → server state → URL fallback)
# NEW: try restoring a session from st.session_state tokens first (survives reruns)
if sb:
    t = st.session_state.get("_sb_tokens")
    if t and t.get("at") and t.get("rt"):
        try:
            sb.auth.set_session(access_token=t["at"], refresh_token=t["rt"])
        except Exception:
            # ignore and fall back to cookie
            pass
    sb_restore_session_from_cookies()
user = sb_current_user()
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
# --- Minimal debug, enable with ?debug=1 in the URL ---
_qp = {k: (v[0] if isinstance(v, list) else v) for k, v in _get_qp_dict().items()}
if _qp.get("debug") == "1":
    st.sidebar.header("Auth Debug")
    st.sidebar.write("session_state tokens present:", bool(st.session_state.get("_sb_tokens")))

    st.sidebar.write("sb client:", "OK" if sb else "None")
    st.sidebar.write("user present:", bool(user))
    if user:
        st.sidebar.write("user id:", getattr(user, "id", None))
        st.sidebar.write("email:", getattr(user, "email", None))
    st.sidebar.write("cookie sb-session present:", bool(cookies.get("sb-session")))
    st.sidebar.write("page:", st.session_state.page)
    st.sidebar.write("active set:", bool(st.session_state.get("active")))

# One-time auth toast (shown after a successful rerun from sb_sign_in)
_msg = st.session_state.pop("_auth_toast", None)
if _msg:
    st.toast(_msg)

# -----------------------------
# UI Components
# -----------------------------
def header_bar():
    with st.container():
        left, mid, right = st.columns([2, 2, 3])

        # --- Left: title/strapline ---
        with left:
            st.markdown("<div class='big-title'>Cleanse to heal 369 tracker</div>", unsafe_allow_html=True)
            st.markdown("<div class='subtle'>YOU CAN HEAL. Keep up the good work</div>", unsafe_allow_html=True)

        # --- Mid: start date pill ---
        with mid:
            if st.session_state.active:
                st.markdown(
                    f"<div class='pill'>📆 Start: <b>{st.session_state.active['start_iso']}</b></div>",
                    unsafe_allow_html=True,
                )

        # --- Right: auth + nav + actions ---
        with right:
            # Signed-in indicator
            if user:
                usr_email = getattr(user, "email", None) or "account"
                st.markdown(f"<div class='pill'>🔐 Signed in as <b>{usr_email}</b></div>", unsafe_allow_html=True)
                st.write("")  # spacer

            c1, c2, c3, c4 = st.columns(4)

            # Auth
            if user:
                if c1.button("🔒 Sign out"):
                    sb_sign_out()

            # Nav
            if c2.button("🏠 Home"):
                st.session_state.page = "home"
                st.rerun()

            if c3.button("🔄 Start Over"):
                if user and st.session_state.active:
                    pass  # (keep your future logic hook here if needed)
                st.session_state.active = None
                _clear_qp()
                st.session_state.page = "menu"
                st.rerun()

            # --- Finish button (always shown if a cycle is active) ---
            if st.session_state.active:
                total, done = count_tasks(st.session_state.active)
                frac = (done / total) if total else 0.0

                if c4.button("🥇 Finish program"):
                    if is_cycle_complete(st.session_state.active) or (frac >= FINISH_WARN_THRESHOLD):
                        # Finish immediately when complete or ≥ threshold
                        if user:
                            sb_mark_completed(user.id, st.session_state.active["id"])
                        else:
                            st.session_state.completed_cycles += 1
                        st.session_state.active = None
                        _clear_qp()
                        st.session_state.page = "history"
                        st.balloons()
                        st.rerun()
                    else:
                        # ask for confirmation if < threshold
                        st.session_state["_confirm_finish"] = {"pct": frac}
                        st.rerun()

    # --- Confirmation UI for early finish (<80%) ---
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
                    if user:
                        sb_mark_completed(user.id, st.session_state.active["id"])
                    else:
                        st.session_state.completed_cycles += 1
                    st.session_state.active = None
                    _clear_qp()
                    st.session_state.page = "history"
                    st.balloons()
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
    with st.form("auth"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        c1, c2 = st.columns(2)
        do_login  = c1.form_submit_button("Sign in", type="primary")
        do_signup = c2.form_submit_button("Sign up")

    if do_login:
        if not email or not pw:
            st.warning("Please enter email and password.")
        elif sb_sign_in(email, pw):      # sets session, cookie, and reruns
            st.session_state.page = "home"
            st.rerun()

    if do_signup:
        if not email or not pw:
            st.warning("Please enter email and password.")
        else:
            sb_sign_up(email, pw)

def view_menu():
    # If signed in and there is an active cycle, land on Home
    if user and st.session_state.get("active"):
        st.session_state.page = "home"
        st.rerun()

    header_bar()
    st.markdown("<div style='height: 18px'></div>", unsafe_allow_html=True)
    # Auth gate (hidden automatically when signed in)
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

    today = date.today()
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
        seed = int(datetime.now().strftime('%Y%j')); random.seed(seed)
        st.markdown("<div class='kicker'>MM quote</div>", unsafe_allow_html=True)
        st.write(f"“{random.choice(QUOTES)}”")

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

# -----------------------------
# History / medals
# -----------------------------
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
