from __future__ import annotations
"""Authentication helpers — login wall, session management, cookie persistence."""
import hashlib
import os
import uuid
import datetime
import streamlit as st
from src.db import fetchone, fetchall, execute


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
_SESSION_DAYS = 30


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

    st.markdown(f"""
    <style>
      .login-wrap {{
        max-width:420px; margin:60px auto 0;
      }}
      .login-header {{
        background:{primary}; color:#fff; padding:28px 36px 22px;
        border-radius:12px 12px 0 0; text-align:center;
      }}
      .login-body {{
        background:#fff; padding:28px 36px 32px;
        border-radius:0 0 12px 12px;
        box-shadow:0 6px 28px rgba(0,0,0,0.10);
      }}
    </style>
    <div class="login-wrap">
      <div class="login-header">
        <p style="font-size:22px;font-weight:700;margin:0;">{company}</p>
        <p style="font-size:13px;opacity:0.75;margin:6px 0 0;">Commission Manager &mdash; Sign In</p>
      </div>
      <div class="login-body"></div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button(
                "Sign In", type="primary", use_container_width=True
            )

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
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
                st.error("Invalid username or password.")


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
    name = st.session_state.get('full_name', 'User')
    container.markdown(f"**{name}**")
    if container.button("Sign Out", key="_logout_btn"):
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
        st.error("⛔ Access denied. Settings are only available to administrators.")
        st.stop()
