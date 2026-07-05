"""Lightweight branding constants + logo helpers.

Safe to import before any Streamlit call (no streamlit import), so page_icon()
can be used inside st.set_page_config(). Logos are the company's official
artwork extracted from the vendor logo PDF (see assets/make_logo_assets.py) —
the exact uploaded logo, not a recreation.
"""
import base64
import functools
import os

_ASSETS   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
FAVICON   = os.path.join(_ASSETS, "favicon.png")
LOGO_FULL = os.path.join(_ASSETS, "logo_full.png")   # mark + wordmark (for light bg)
LOGO_ICON = os.path.join(_ASSETS, "logo_icon.png")   # compass mark only (square)


def page_icon():
    """GNSS-device favicon path for st.set_page_config, with an emoji fallback."""
    return FAVICON if os.path.exists(FAVICON) else "🛰️"


@functools.lru_cache(maxsize=8)
def logo_data_uri(which: str = "icon") -> str:
    """Return a base64 data URI for a logo, or '' if the file is missing.
    which: 'icon' (compass mark) or 'full' (mark + wordmark)."""
    path = LOGO_FULL if which == "full" else LOGO_ICON
    try:
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except Exception:
        return ""
