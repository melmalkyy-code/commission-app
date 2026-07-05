"""Lightweight branding constants — safe to import before any Streamlit call
(no streamlit import), so it can be used inside st.set_page_config()."""
import os

_ASSETS   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
FAVICON   = os.path.join(_ASSETS, "favicon.png")


def page_icon():
    """GNSS-device favicon path for st.set_page_config, with an emoji fallback."""
    return FAVICON if os.path.exists(FAVICON) else "🛰️"
