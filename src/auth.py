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


def _cookie_controller():
    """Construct + mount a fresh CookieController for THIS run, or None if the
    component isn't installed.

    A real bidirectional component (served same-origin) is required to write a
    cookie that survives a full page refresh. `components.html` runs in a
    sandboxed srcDoc iframe with an opaque origin, so cookies set there never
    reach the app domain and are lost on refresh — that was the logout bug.

    Must be constructed fresh each run (so the component actually mounts in the
    current widget tree) and at most once per run (a second construction with
    the same key raises a duplicate-id error). The login page mounts it once at
    the top and threads the instance into _set_auth_cookie on submit.
    """
    try:
        from streamlit_cookies_controller import CookieController
        return CookieController(key='se_auth_cookie_ctrl')
    except Exception:
        return None


def _set_auth_cookie(token: str, ctrl=None):
    """Persist the auth cookie on the real app domain so it survives refresh.

    SameSite=Lax + Secure: Lax still sends the cookie on top-level navigations
    (a refresh) and is more compatible across mobile / embedded contexts than
    Strict; Secure is required by browsers for SameSite on HTTPS (Streamlit
    Cloud is always HTTPS). `ctrl` is the already-mounted controller from the
    login run so the write reaches a live component.
    """
    if ctrl is None:
        ctrl = _cookie_controller()
    if ctrl is None:
        return
    expires = datetime.datetime.now() + datetime.timedelta(days=_SESSION_DAYS)
    try:
        ctrl.set(_COOKIE_NAME, token, expires=expires, path='/',
                 same_site='lax', secure=True)
    except Exception:
        try:
            ctrl.set(_COOKIE_NAME, token)
        except Exception:
            pass


def _clear_auth_cookie():
    """Delete the auth cookie from the browser."""
    ctrl = _cookie_controller()
    if ctrl is None:
        return
    try:
        ctrl.remove(_COOKIE_NAME)
    except Exception:
        pass


def _read_auth_cookie() -> str:
    """Read the auth cookie sent by the browser on the current request.

    On a full refresh the browser includes the cookie in the HTTP request, so
    the server-side st.context.cookies reads it reliably with no async round
    trip and no extra component in the widget tree.
    """
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

    # Mount the cookie component once for this run so that, on submit, the
    # write below reaches an already-live component and flushes before rerun.
    _login_ctrl = _cookie_controller()

    from src.ui import _FONT_LINKS
    from src.branding import logo_data_uri
    _logo = logo_data_uri("full")
    _logo_html = (
        f"<img src='{_logo}' style='max-width:230px;width:70%;height:auto;"
        f"margin:0 auto 18px;display:block'/>"
    ) if _logo else ""

    # Clean LIGHT card — dark, legible input text on a white field (no more
    # white-on-white), real company logo, custom fonts loaded via <link>.
    st.html(f"""
    {_FONT_LINKS}
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    #MainMenu, footer, [data-testid="stToolbar"] {{ visibility:hidden !important; }}
    [data-testid="stSidebar"], [data-testid="stSidebarNav"],
    [data-testid="collapsedControl"] {{ display:none !important; }}

    html, body, .stApp {{
        font-family: {font} !important;
        background: linear-gradient(160deg, #eef2f5 0%, #e3e9ee 55%, #dbe2e8 100%) !important;
        min-height: 100vh !important;
    }}

    /* White card */
    .main .block-container {{
        max-width: 430px !important;
        margin: 7vh auto 0 !important;
        padding: 2.4rem 2.4rem 2rem !important;
        background: #ffffff !important;
        border: 1px solid #e5e8eb !important;
        border-radius: 20px !important;
        box-shadow: 0 20px 60px rgba(26,43,56,0.16) !important;
    }}

    /* Labels — dark */
    [data-testid="stTextInput"] label,
    [data-testid="stWidgetLabel"] {{
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #354f61 !important;
        font-family: {font} !important;
        direction: {dir_s} !important;
        text-align: {align} !important;
    }}

    /* Input fields — white with DARK text (fixes the invisible white text) */
    [data-baseweb="input"] {{
        background: #ffffff !important;
        border: 1px solid #cfd6dc !important;
        border-radius: 10px !important;
    }}
    [data-baseweb="input"] input {{
        color: #1a2b38 !important;
        -webkit-text-fill-color: #1a2b38 !important;
        font-size: 15px !important;
        font-family: {font} !important;
        direction: {dir_s} !important;
        background: transparent !important;
    }}
    [data-baseweb="input"] input::placeholder {{ color: #9aa6b0 !important; }}
    [data-baseweb="input"]:focus-within {{
        border-color: #354f61 !important;
        box-shadow: 0 0 0 3px rgba(53,79,97,0.12) !important;
    }}
    /* Neutralise browser autofill turning the field white-on-white */
    input:-webkit-autofill, input:-webkit-autofill:focus {{
        -webkit-text-fill-color: #1a2b38 !important;
        -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
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
        background: #f2f5f7 !important;
        border-color: #d2d7dc !important;
        color: #5a7080 !important;
    }}
    .stButton > button[kind="primary"] {{
        background: #354f61 !important;
        border-color: #354f61 !important;
        color: #ffffff !important;
    }}

    /* Form — no extra border */
    .stForm {{
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
    }}

    /* Sign In button — brand gold */
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
        box-shadow: 0 4px 14px rgba(246,186,59,0.35) !important;
    }}
    [data-testid="stFormSubmitButton"] > button:hover {{
        background: #eaa91f !important; border-color: #eaa91f !important;
    }}

    /* Alert */
    [data-testid="stAlert"] {{
        border-radius: 10px !important;
        font-family: {font} !important;
        direction: {dir_s} !important;
    }}

    /* ── Mobile: tighten the login card ── */
    @media (max-width: 640px) {{
        .main .block-container {{
            max-width: 94vw !important;
            margin: 4vh auto 0 !important;
            padding: 1.6rem 1.4rem 1.4rem !important;
            border-radius: 16px !important;
        }}
        [data-testid="stFormSubmitButton"] > button {{ height: 46px !important; }}
    }}
    </style>
    <div style="text-align:center;padding:6px 0 20px;direction:{dir_s}">
      {_logo_html}
      <div style="font-size:24px;font-weight:700;color:#1a2b38;
          font-family:{font};letter-spacing:-0.02em;line-height:1.2;margin-bottom:4px">{company}</div>
      <div style="font-size:13px;color:#6b757d;font-family:{font}">
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
            _set_auth_cookie(token, _login_ctrl)
            # Give the cookie component a moment to flush the write to the
            # browser before the rerun tears down this run — otherwise the
            # cookie is lost and the next refresh logs the user out again.
            import time
            time.sleep(0.6)
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
        from src.branding import page_icon
        st.set_page_config(
            page_title="Sign In — Surveying Experts",
            page_icon=page_icon(),
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


def is_viewer() -> bool:
    """Read-only role: may view dashboards and download reports only."""
    return st.session_state.get('role') == 'viewer'


def require_admin() -> None:
    """Stop execution with an access-denied message if the user is not an admin."""
    if not is_admin():
        st.error(t("Access denied. Settings are only available to administrators."))
        st.stop()


def require_editor() -> None:
    """Block read-only viewers from data-entry and management pages.

    Viewers may only view dashboards and download reports; any page that
    accepts input or exposes settings/audit calls this right after
    require_login() to deny them.
    """
    if is_viewer():
        st.error(t("View-only access: you can view dashboards and download "
                   "reports, but cannot edit data or open this page."))
        st.stop()
