from __future__ import annotations
"""Authentication helpers — login wall, session management, password hashing."""
import hashlib
import os
import streamlit as st
from src.db import fetchone, execute


# ── Password hashing (PBKDF2-SHA256, no extra packages) ──────────────────────
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


# ── DB helpers ────────────────────────────────────────────────────────────────
def get_user(username: str) -> dict | None:
    return fetchone("SELECT id, username, password_hash, full_name, role, is_active FROM app_users WHERE username=%s", (username,))


def get_all_users() -> list[dict]:
    return fetchone("SELECT id, username, full_name, role, is_active FROM app_users", ()) or []


def list_users() -> list[dict]:
    from src.db import fetchall
    return fetchall("SELECT id, username, full_name, role, is_active FROM app_users ORDER BY username")


def create_user(username: str, password: str, full_name: str = "", role: str = "viewer") -> None:
    execute("INSERT INTO app_users (username, password_hash, full_name, role) VALUES (%s,%s,%s,%s)",
            (username.strip().lower(), hash_password(password), full_name, role))


def update_user_password(user_id: int, new_password: str) -> None:
    execute("UPDATE app_users SET password_hash=%s WHERE id=%s", (hash_password(new_password), user_id))


def delete_user(user_id: int) -> None:
    execute("DELETE FROM app_users WHERE id=%s", (user_id,))


def ensure_default_admin() -> None:
    """Create admin account on first run if no users exist."""
    row = fetchone("SELECT COUNT(*) as cnt FROM app_users", ())
    if row and row['cnt'] == 0:
        create_user("admin", "admin123", "Administrator", "admin")


# ── Login UI ──────────────────────────────────────────────────────────────────
def _show_login():
    # Try to get branding — fall back to defaults if DB not ready
    try:
        from src.models import get_setting
        primary = get_setting('primary_color', '#354f61')
        company = get_setting('company_name', 'Surveying Experts')
    except Exception:
        primary, company = '#354f61', 'Surveying Experts'

    st.markdown(f"""
    <style>
      .login-card {{
        max-width:420px; margin:80px auto 0; padding:40px 36px 32px;
        border-radius:12px; box-shadow:0 4px 24px rgba(0,0,0,0.10);
        background:#fff;
      }}
      .login-header {{
        background:{primary}; color:#fff; padding:24px 36px 20px;
        border-radius:12px 12px 0 0; text-align:center; margin:-40px -36px 28px;
      }}
    </style>
    <div class="login-card">
      <div class="login-header">
        <p style="font-size:22px;font-weight:700;margin:0;">{company}</p>
        <p style="font-size:13px;opacity:0.75;margin:4px 0 0;">Commission Manager — Sign In</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
                return
            user = get_user(username.strip().lower())
            if user and user['is_active'] and verify_password(password, user['password_hash']):
                st.session_state['authenticated'] = True
                st.session_state['username']      = user['username']
                st.session_state['full_name']     = user['full_name'] or user['username']
                st.session_state['role']          = user['role']
                st.rerun()
            else:
                st.error("Invalid username or password.")


def require_login() -> None:
    """Call near the top of every page. Stops page if not logged in."""
    if not st.session_state.get('authenticated'):
        # Ensure page config is set before rendering the login form
        try:
            st.set_page_config(
                page_title="Sign In",
                page_icon="🔐",
                layout="centered",
            )
        except Exception:
            pass  # already set by this page
        _show_login()
        st.stop()


def logout_button(sidebar: bool = True) -> None:
    """Render a logout button. Pass sidebar=False to place it inline."""
    container = st.sidebar if sidebar else st
    name = st.session_state.get('full_name', 'User')
    container.markdown(f"👤 **{name}**")
    if container.button("🚪 Sign Out", key="_logout_btn"):
        for key in ['authenticated', 'username', 'full_name', 'role']:
            st.session_state.pop(key, None)
        st.rerun()


def is_admin() -> bool:
    return st.session_state.get('role') == 'admin'
