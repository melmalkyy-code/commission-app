from __future__ import annotations
"""Authentication helpers — login wall, session management, cookie persistence."""
import hashlib
import os
import uuid
import datetime
import streamlit as st
from src.db import fetchone, fetchall, execute
from src.i18n import t, lang_switcher, get_lang, _LANG_KEY


# ── Password hashing (PBKDF2-SHA256) ─────────────────────────────────────────
def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200_000).hex()
    return f"{salt}:{h}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, h = stored_hash.split(':', 1)
        check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200_000).hex()
        return check == h
    except Exception:
        return False


# ── User DB helpers ───────────────────────────────────────────────────────────
def get_user(username: str) -> dict | None:
    return fetchone(
        "SELECT id, username, password_hash, full_name, role, is_active "
        "FROM app_users WHERE username=%s",
        (username,),
    )


def list_users() -> list[dict]:
    return fetchall(
        "SELECT id, username, full_name, role, is_active FROM app_users ORDER BY username"
    )


def create_user(username: str, password: str, full_name: str = "", role: str = "viewer") -> None:
    execute(
        "INSERT INTO app_users (username, password_hash, full_name, role) VALUES (%s,%s,%s,%s)",
        (username.strip().lower(), hash_password(password), full_name, role),
    )


def update_user_password(user_id: int, new_password: str) -> None:
    execute(
        "UPDATE app_users SET password_hash=%s WHERE id=%s",
        (hash_password(new_password), user_id),
    )


def delete_user(user_id: int) -> None:
    execute("DELETE FROM app_users WHERE id=%s", (user_id,))


def ensure_default_admin() -> None:
    row = fetchone("SELECT COUNT(*) as cnt FROM app_users", ())
    if row and row['cnt'] == 0:
        create_user("admin", "admin123", "Administrator", "admin")


# ── Session / cookie helpers ──────────────────────────────────────────────────
_COOKIE_NAME = "commission_auth"
_SESSION_DAYS = 365  # 1 year; rolling — extended on every access


def _create_session(user_id: int, username: str) -> str:
    token = str(uuid.uuid4())
    expires = (datetime.datetime.now() + datetime.timedelta(days=_SESSION_DAYS)).isoformat()
    execute(
        "INSERT INTO sessions (token, user_id, username, expires_at) VALUES (%s,%s,%s,%s)",
        (token, user_id, username, expires),
    )
    return token


def _validate_session(token: str) -> dict | None:
    if not token or len(token) < 10:
        return None
    row = fetchone(
        "SELECT s.user_id, s.username, s.expires_at, u.full_name, u.role, u.is_active "
        "FROM sessions s JOIN app_users u ON s.user_id=u.id "
        "WHERE s.token=%s AND s.is_active=1 AND u.is_active=1",
        (token,),
    )
    if not row:
        return None
    try:
        exp = datetime.datetime.fromisoformat(str(row['expires_at'])[:19])
        if exp < datetime.datetime.now():
            _revoke_session(token)
            return None
    except Exception:
        pass
    # Rolling expiry — extend the session every time it is used
    new_expires = (datetime.datetime.now() + datetime.timedelta(days=_SESSION_DAYS)).isoformat()
    execute("UPDATE sessions SET expires_at=%s WHERE token=%s", (new_expires, token))
    return row


def _revoke_session(token: str):
    if token:
        execute("UPDATE sessions SET is_active=0 WHERE token=%s", (token,))


def _set_auth_cookie(token: str):
    """Inject JS to set the auth cookie in the browser."""
    import streamlit.components.v1 as components
    max_age = _SESSION_DAYS * 86400
    components.html(
        f"""<script>
        document.cookie = "{_COOKIE_NAME}={token}; max-age={max_age}; path=/; SameSite=Strict";
        </script>""",
        height=0,
    )


def _clear_auth_cookie():
    """Inject JS to delete the auth cookie from the browser."""
    import streamlit.components.v1 as components
    components.html(
        f"""<script>
        document.cookie = "{_COOKIE_NAME}=; max-age=0; path=/; SameSite=Strict";
        </script>""",
        height=0,
    )


def _read_auth_cookie() -> str:
    """Read the auth cookie from the browser request (requires Streamlit >= 1.37)."""
    try:
        return st.context.cookies.get(_COOKIE_NAME) or ""
    except Exception:
        return ""


# ── Login UI ──────────────────────────────────────────────────────────────────
def _show_login():
    try:
        from src.models import get_setting
        primary = get_setting('primary_color', '#354f61')
        company = get_setting('company_name', 'Surveying Experts')
    except Exception:
        primary, company = '#354f61', 'Surveying Experts'

    _lang = get_lang()
    rtl    = _lang == 'ar'
    dir_s  = 'rtl' if rtl else 'ltr'
    font   = "'Cairo',system-ui,sans-serif" if rtl else "'IBM Plex Sans',system-ui,sans-serif"
    align  = 'right' if rtl else 'left'

    from src.ui import _LOGO_SVG_DARK
    # Single st.html() call — CSS + header in one block to avoid rerun loops.
    # Design: dark gradient background + glass-morphism card + white text throughout.
    st.html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;700&display=swap');

    #MainMenu, footer, [data-testid="stToolbar"] {{ visibility:hidden !important; }}
    [data-testid="stSidebar"], [data-testid="stSidebarNav"],
    [data-testid="collapsedControl"] {{ display:none !important; }}

    html, body, .stApp {{
        font-family: {font} !important;
        background: linear-gradient(145deg, {primary} 0%, #1a2b38 55%, #0e1c27 100%) !important;
        min-height: 100vh !important;
    }}

    /* Glass-morphism card — works on all Streamlit versions */
    .main .block-container {{
        max-width: 440px !important;
        margin: 7vh auto 0 !important;
        padding: 2.5rem 2.5rem 2rem !important;
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        border-radius: 20px !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
        box-shadow: 0 24px 64px rgba(0,0,0,0.40) !important;
    }}

    /* Label text — white */
    [data-testid="stTextInput"] label,
    [data-testid="stWidgetLabel"] {{
        font-size: 13px !important;
        font-weight: 600 !important;
        color: rgba(255,255,255,0.85) !important;
        font-family: {font} !important;
        direction: {dir_s} !important;
        text-align: {align} !important;
    }}

    /* Input fields — glass style */
    [data-baseweb="input"] {{
        background: rgba(255,255,255,0.10) !important;
        border-color: rgba(255,255,255,0.22) !important;
        border-radius: 10px !important;
    }}
    [data-baseweb="input"] input {{
        color: #ffffff !important;
        font-size: 15px !important;
        font-family: {font} !important;
        direction: {dir_s} !important;
    }}
    [data-baseweb="input"] input::placeholder {{
        color: rgba(255,255,255,0.40) !important;
    }}

    /* Language pill buttons */
    .stButton > button {{
        border-radius: 20px !important;
        font-size: 12px !important;
        padding: 3px 16px !important;
        font-weight: 600 !important;
        font-family: {font} !important;
        min-height: 32px !important;
    }}
    .stButton > button[kind="secondary"] {{
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.25) !important;
        color: rgba(255,255,255,0.80) !important;
    }}
    .stButton > button[kind="primary"] {{
        background: #f6ba3b !important;
        border-color: #f6ba3b !important;
        color: #1a2b38 !important;
    }}

    /* Form — no extra border */
    .stForm {{
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }}

    /* Sign In button */
    [data-testid="stFormSubmitButton"] > button {{
        background: #f6ba3b !important;
        border-color: #f6ba3b !important;
        color: #1a2b38 !important;
        border-radius: 10px !important;
        height: 50px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        width: 100% !important;
        margin-top: 8px !important;
        font-family: {font} !important;
        letter-spacing: 0.02em !important;
    }}

    /* Alert */
    [data-testid="stAlert"] {{
        border-radius: 10px !important;
        font-family: {font} !important;
        direction: {dir_s} !important;
        background: rgba(214,69,69,0.15) !important;
        border-color: rgba(214,69,69,0.4) !important;
        color: #ffb3b3 !important;
    }}
    </style>
    <div style="text-align:center;padding:8px 0 24px;direction:{dir_s}">
      {_LOGO_SVG_DARK}
      <div style="font-size:26px;font-weight:700;color:#ffffff;
          font-family:{font};letter-spacing:-0.02em;line-height:1.2;margin-bottom:6px">{company}</div>
      <div style="font-size:13px;color:rgba(255,255,255,0.55);font-family:{font}">
        {t('Commission Manager — Sign In')}</div>
    </div>
    """)

    # ── Language switcher (right-aligned pill buttons) ────────────────────────
    _, lc1, lc2 = st.columns([4, 1, 1])
    with lc1:
        if st.button("EN", type="primary" if _lang == 'en' else "secondary",
                     key="_login_lang_en", use_container_width=True):
            st.session_state[_LANG_KEY] = 'en'
            st.rerun()
    with lc2:
        if st.button("عربي", type="primary" if _lang == 'ar' else "secondary",
                     key="_login_lang_ar", use_container_width=True):
            st.session_state[_LANG_KEY] = 'ar'
            st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Login form ────────────────────────────────────────────────────────────
    with st.form("login_form", clear_on_submit=False):
        username  = st.text_input(t("Username"), placeholder=t("Enter username"))
        password  = st.text_input(t("Password"), type="password",
                                  placeholder=t("Enter password"))
        submitted = st.form_submit_button(t("Sign In"), use_container_width=True)

    if submitted:
        if not username or not password:
            st.error(t("Please enter both username and password."))
            return
        user = get_user(username.strip().lower())
        if user and user['is_active'] and verify_password(password, user['password_hash']):
            token = _create_session(user['id'], user['username'])
            st.session_state.update({
                'authenticated': True,
                'username':      user['username'],
                'full_name':     user['full_name'] or user['username'],
                'role':          user['role'],
                'auth_token':    token,
            })
            _set_auth_cookie(token)
            st.rerun()
        else:
            st.error(t("Invalid username or password."))


# ── Core auth gate ────────────────────────────────────────────────────────────
def require_login() -> None:
    """Call at the top of every page. Stops execution if not logged in."""
    # Already authenticated in this session
    if st.session_state.get('authenticated'):
        return

    # Try to restore session from cookie (survives browser refresh & new tabs)
    token = _read_auth_cookie()
    if token:
        user = _validate_session(token)
        if user:
            st.session_state.update({
                'authenticated': True,
                'username':      user['username'],
                'full_name':     user.get('full_name') or user['username'],
                'role':          user['role'],
                'auth_token':    token,
            })
            return  # Silently restored — no rerun needed

    # Not authenticated — show login page
    try:
        st.set_page_config(
            page_title="Sign In",
            page_icon="lock",
            layout="centered",
        )
    except Exception:
        pass
    _show_login()
    st.stop()


# ── Logout ────────────────────────────────────────────────────────────────────
def logout_button(sidebar: bool = True) -> None:
    container = st.sidebar if sidebar else st
    name = st.session_state.get('full_name', t('User'))
    container.markdown(f"**{name}**")
    if container.button(t("Sign Out"), key="_logout_btn"):
        token = st.session_state.get('auth_token', '')
        if token:
            _revoke_session(token)
        _clear_auth_cookie()
        for key in ['authenticated', 'username', 'full_name', 'role', 'auth_token']:
            st.session_state.pop(key, None)
        st.rerun()


def is_admin() -> bool:
    return st.session_state.get('role') == 'admin'


def require_admin() -> None:
    """Stop execution with an access-denied message if the user is not an admin."""
    if not is_admin():
        st.error(t("Access denied. Settings are only available to administrators."))
        st.stop()
