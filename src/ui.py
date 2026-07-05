"""
SE Design System CSS injection for Streamlit.
Call inject_css() once at the top of every page (after set_page_config).
"""
import streamlit as st
from src.i18n import lang_switcher, t, is_rtl


_FONT    = "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
_FONT_AR = "https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;700&display=swap"

# SE logo SVG — white+gold version for dark backgrounds (sidebar, login card)
# Matches the letterhead: navy circle, gold arcs top-right + bottom-left,
# white total station on tripod at center, inner crosshair ring marks.
_LOGO_SVG_DARK = (
    "<svg width='56' height='56' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg' "
    "style='display:block;margin:0 auto 8px'>"
    # Navy filled circle (the logo background disc)
    "<circle cx='50' cy='50' r='44' fill='#1a2b38'/>"
    # Outer white ring outline
    "<circle cx='50' cy='50' r='44' fill='none' stroke='rgba(255,255,255,0.25)' stroke-width='2'/>"
    # Inner ring (target reticle detail)
    "<circle cx='50' cy='50' r='28' fill='none' stroke='rgba(255,255,255,0.18)' stroke-width='1'/>"
    # Gold arcs — top-right quadrant
    "<path d='M 50,6 A 44,44 0 0,1 94,50' fill='none' stroke='#f6ba3b' stroke-width='6' stroke-linecap='round'/>"
    # Gold arcs — bottom-left quadrant
    "<path d='M 50,94 A 44,44 0 0,1 6,50' fill='none' stroke='#f6ba3b' stroke-width='6' stroke-linecap='round'/>"
    # Crosshair tick marks (white lines from inner ring to outer ring)
    "<line x1='50' y1='6'  x2='50' y2='22' stroke='white' stroke-width='2'/>"
    "<line x1='50' y1='78' x2='50' y2='94' stroke='white' stroke-width='2'/>"
    "<line x1='6'  y1='50' x2='22' y2='50' stroke='white' stroke-width='2'/>"
    "<line x1='78' y1='50' x2='94' y2='50' stroke='white' stroke-width='2'/>"
    # Total station instrument body
    "<rect x='42' y='30' width='16' height='13' rx='3' fill='white'/>"
    # Lens aperture circle
    "<circle cx='50' cy='36' r='4' fill='none' stroke='#1a2b38' stroke-width='2'/>"
    "<circle cx='50' cy='36' r='1.5' fill='#1a2b38'/>"
    # Tripod stem
    "<line x1='50' y1='43' x2='50' y2='60' stroke='white' stroke-width='2.5'/>"
    # Cross bar on tripod
    "<line x1='42' y1='53' x2='58' y2='53' stroke='white' stroke-width='1.5'/>"
    # Tripod legs (spread from crossbar)
    "<line x1='50' y1='58' x2='39' y2='70' stroke='white' stroke-width='2'/>"
    "<line x1='50' y1='58' x2='61' y2='70' stroke='white' stroke-width='2'/>"
    "</svg>"
)

# SE logo SVG — navy+gold version for light/white backgrounds
_LOGO_SVG_LIGHT = (
    "<svg width='64' height='64' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg' "
    "style='display:block;margin:0 auto 12px'>"
    "<circle cx='50' cy='50' r='44' fill='#1a2b38'/>"
    "<circle cx='50' cy='50' r='44' fill='none' stroke='rgba(255,255,255,0.25)' stroke-width='2'/>"
    "<circle cx='50' cy='50' r='28' fill='none' stroke='rgba(255,255,255,0.18)' stroke-width='1'/>"
    "<path d='M 50,6 A 44,44 0 0,1 94,50' fill='none' stroke='#f6ba3b' stroke-width='6' stroke-linecap='round'/>"
    "<path d='M 50,94 A 44,44 0 0,1 6,50' fill='none' stroke='#f6ba3b' stroke-width='6' stroke-linecap='round'/>"
    "<line x1='50' y1='6'  x2='50' y2='22' stroke='white' stroke-width='2'/>"
    "<line x1='50' y1='78' x2='50' y2='94' stroke='white' stroke-width='2'/>"
    "<line x1='6'  y1='50' x2='22' y2='50' stroke='white' stroke-width='2'/>"
    "<line x1='78' y1='50' x2='94' y2='50' stroke='white' stroke-width='2'/>"
    "<rect x='42' y='30' width='16' height='13' rx='3' fill='white'/>"
    "<circle cx='50' cy='36' r='4' fill='none' stroke='#1a2b38' stroke-width='2'/>"
    "<circle cx='50' cy='36' r='1.5' fill='#1a2b38'/>"
    "<line x1='50' y1='43' x2='50' y2='60' stroke='white' stroke-width='2.5'/>"
    "<line x1='42' y1='53' x2='58' y2='53' stroke='white' stroke-width='1.5'/>"
    "<line x1='50' y1='58' x2='39' y2='70' stroke='white' stroke-width='2'/>"
    "<line x1='50' y1='58' x2='61' y2='70' stroke='white' stroke-width='2'/>"
    "</svg>"
)

_CSS = """
@import url('{font}');
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;700&display=swap');

/* ── Base font ── */
html, body, [class*="css"], .stApp {{
  font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
}}

/* ── App background ── */
.stApp, .main > .block-container {{
  background: #f8f9fa !important;
}}
.main > .block-container {{
  padding-top: 2rem !important;
  padding-bottom: 2rem !important;
  max-width: 1200px !important;
}}

/* ── Sidebar — SE dark blue ── */
[data-testid="stSidebar"] {{
  background: #1a2b38 !important;
}}
[data-testid="stSidebar"] > div:first-child {{
  background: #1a2b38 !important;
}}
[data-testid="stSidebar"] * {{
  color: rgba(255,255,255,0.7) !important;
}}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong {{
  color: #fff !important;
}}
[data-testid="stSidebar"] hr {{
  border-color: rgba(255,255,255,0.12) !important;
}}
[data-testid="stSidebar"] .stButton button {{
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  color: rgba(255,255,255,0.8) !important;
  border-radius: 7px !important;
}}
[data-testid="stSidebar"] .stButton button:hover {{
  background: rgba(246,186,59,0.12) !important;
  border-color: #f6ba3b !important;
  color: #f6ba3b !important;
}}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
  color: rgba(255,255,255,0.6) !important;
  border-radius: 7px !important;
  padding: 6px 10px !important;
  margin-bottom: 2px !important;
}}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{
  background: rgba(255,255,255,0.06) !important;
  color: #fff !important;
}}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[data-active="true"],
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current] {{
  background: rgba(246,186,59,0.10) !important;
  color: #f6ba3b !important;
  border-left: 2px solid #f6ba3b !important;
}}
/* selectbox / number input inside sidebar */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] input {{
  background: rgba(255,255,255,0.08) !important;
  border-color: rgba(255,255,255,0.15) !important;
  color: rgba(255,255,255,0.85) !important;
}}
/* Language switcher — active = SE gold, inactive = glass */
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[data-testid="baseButton-primary"] {{
  background: #f6ba3b !important;
  border-color: #f6ba3b !important;
  color: #1a2b38 !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  box-shadow: 0 2px 8px rgba(246,186,59,0.3) !important;
}}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {{
  font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
  color: #1a2b38 !important;
  letter-spacing: -0.015em;
}}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
  background: #ffffff !important;
  border: 1px solid #e5e8eb !important;
  border-radius: 10px !important;
  padding: 1rem 1.1rem !important;
  box-shadow: 0 1px 3px rgba(36,57,73,0.06) !important;
}}
[data-testid="stMetricLabel"] {{
  font-size: 12px !important;
  color: #6b757d !important;
  font-weight: 500 !important;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
[data-testid="stMetricValue"] {{
  font-size: 22px !important;
  font-weight: 700 !important;
  color: #1a2b38 !important;
}}
[data-testid="stMetricDelta"] {{
  font-size: 12px !important;
}}

/* ── Buttons ── */
.stButton > button {{
  font-family: 'IBM Plex Sans', sans-serif !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all 0.15s ease !important;
}}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {{
  background: #354f61 !important;
  border-color: #354f61 !important;
  color: #fff !important;
}}
.stButton > button[kind="primary"]:hover {{
  background: #243949 !important;
  border-color: #243949 !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(36,57,73,0.2) !important;
}}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {{
  border-color: #d2d7dc !important;
  color: #364046 !important;
}}
.stButton > button[kind="secondary"]:hover {{
  border-color: #354f61 !important;
  color: #354f61 !important;
  background: #eef2f4 !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
  background: transparent !important;
  border-bottom: 1px solid #e5e8eb !important;
  gap: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  color: #6b757d !important;
  padding: 10px 16px !important;
  border-radius: 0 !important;
  border-bottom: 2px solid transparent !important;
}}
.stTabs [aria-selected="true"] {{
  color: #354f61 !important;
  font-weight: 500 !important;
  border-bottom: 2px solid #354f61 !important;
  background: transparent !important;
}}
.stTabs [data-baseweb="tab-border"] {{
  display: none !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
  padding-top: 1.2rem !important;
}}

/* ── Dataframe / data editor ── */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {{
  border-radius: 10px !important;
  overflow: hidden !important;
  border: 1px solid #e5e8eb !important;
}}

/* ── Expanders ── */
[data-testid="stExpander"] {{
  border: 1px solid #e5e8eb !important;
  border-radius: 10px !important;
  overflow: hidden !important;
  background: #fff !important;
  margin-bottom: 8px !important;
}}
[data-testid="stExpander"] summary {{
  padding: 12px 16px !important;
  background: #fff !important;
  font-weight: 500 !important;
  color: #1a2b38 !important;
}}
[data-testid="stExpander"] > div:last-child {{
  padding: 0 16px 16px !important;
}}

/* ── Forms ── */
.stForm {{
  background: #fff !important;
  border: 1px solid #e5e8eb !important;
  border-radius: 10px !important;
  padding: 1rem 1.25rem !important;
}}

/* ── Inputs ── */
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] div[data-value] {{
  font-family: 'IBM Plex Sans', sans-serif !important;
  border-radius: 8px !important;
}}

/* ── Alerts / info boxes ── */
[data-testid="stAlert"] {{
  border-radius: 8px !important;
}}

/* ── Divider ── */
hr {{
  border-color: #e5e8eb !important;
  margin: 1rem 0 !important;
}}

/* ── Toast / success ── */
[data-testid="toastContainer"] * {{
  font-family: 'IBM Plex Sans', sans-serif !important;
  border-radius: 8px !important;
}}

/* ── Hide Streamlit footer + menu ── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* ── Hide auto-generated sidebar nav (replaced by translated custom nav) ── */
[data-testid="stSidebarNav"] {{ display: none !important; }}
/* DO NOT hide stToolbar — it contains the sidebar toggle in some Streamlit builds */

/* ── Sidebar collapse/expand toggle — always visible and clickable ── */
[data-testid="collapsedControl"] {{
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: all !important;
  background: #1a2b38 !important;
  border-radius: 0 8px 8px 0 !important;
  box-shadow: 2px 2px 8px rgba(0,0,0,0.18) !important;
  z-index: 999999 !important;
}}
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] button svg {{
  fill: rgba(255,255,255,0.9) !important;
  color: rgba(255,255,255,0.9) !important;
}}
"""


_RTL_CSS = """
@import url('{font_ar}');
/* ── Arabic RTL overrides ── */
html, body, .main, .main .block-container,
.main [data-testid="stVerticalBlock"],
.main [data-testid="stHorizontalBlock"] > div,
.stForm, .stExpander, .stAlert,
[data-testid="stMarkdownContainer"],
[data-testid="stText"],
[data-baseweb="tab-panel"] {{
  direction: rtl !important;
  text-align: right !important;
}}
html, body, [class*="css"], .stApp {{
  font-family: 'Cairo', system-ui, sans-serif !important;
}}
h1, h2, h3, h4, h5, h6 {{
  font-family: 'Cairo', system-ui, sans-serif !important;
  text-align: right !important;
}}
/* Input labels and captions */
label, .stTextInput label, .stSelectbox label,
.stNumberInput label, .stCheckbox label,
.stRadio label, [data-testid="stWidgetLabel"] {{
  direction: rtl !important;
  text-align: right !important;
  width: 100% !important;
}}
/* Metrics */
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {{
  text-align: right !important;
}}
/* Tabs — RTL order */
[data-baseweb="tab-list"] {{
  direction: rtl !important;
}}
/* Keep sidebar LTR so navigation stays readable */
[data-testid="stSidebar"],
[data-testid="stSidebar"] * {{
  direction: ltr !important;
  text-align: left !important;
}}
"""


def inject_css(primary: str = "#354f61") -> None:
    """Inject SE design system CSS. Call once per page after set_page_config."""
    css = f"<style>{_CSS.format(font=_FONT)}</style>"
    if is_rtl():
        css += f"<style>{_RTL_CSS.format(font_ar=_FONT_AR)}</style>"
    st.html(css)


def page_header(title: str, subtitle: str = "", primary: str = "#354f61") -> None:
    """Render a consistent SE-branded page header."""
    rtl   = is_rtl()
    align = "right" if rtl else "left"
    dir_s = "rtl"   if rtl else "ltr"
    font  = "'Cairo',system-ui,sans-serif" if rtl else "'IBM Plex Sans',system-ui,sans-serif"
    sub_html = (
        f"<p style='color:#6b757d;margin:2px 0 0;font-size:14px;"
        f"text-align:{align};direction:{dir_s};font-family:{font}'>{subtitle}</p>"
    ) if subtitle else ""
    # Use st.markdown (not st.html) — avoids duplicate resize-event reruns
    st.markdown(
        f"<div style='margin-bottom:1.5rem;direction:{dir_s};text-align:{align}'>"
        f"<h1 style='color:{primary};margin:0;font-size:26px;font-weight:700;"
        f"letter-spacing:-0.02em;font-family:{font};text-align:{align}'>{title}</h1>"
        f"{sub_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def sidebar_nav() -> None:
    """Render translated page navigation links in the sidebar."""
    _pages = [
        ("Home.py",               "Dashboard"),
        ("pages/2_Sales.py",      "Sales Input"),
        ("pages/3_KPI.py",        "KPI Calculation"),
        ("pages/4_Commission.py", "Commission Report"),
        ("pages/5_Reports.py",    "Reports Center"),
        ("pages/6_Settings.py",   "Settings"),
        ("pages/7_Audit.py",      "Audit Log"),
    ]
    for _path, _label in _pages:
        st.sidebar.page_link(_path, label=t(_label))
    st.sidebar.markdown("---")


def sidebar_logo(company: str = "Surveying Experts", primary: str = "#354f61") -> None:
    """Render SE logo block + language switcher + navigation in the sidebar."""
    from src.db import db_status
    status = db_status()
    if status['ok'] and status['backend'] == 'postgresql':
        dot, badge_color, badge_text = "●", "#4caf7d", t("Cloud database")
    elif status['ok']:
        dot, badge_color, badge_text = "●", "#f6ba3b", t("Local database (dev only)")
    else:
        dot, badge_color, badge_text = "●", "#e05d5d", t("Database unreachable")
    st.sidebar.markdown(
        f"<div style='padding:14px 0 14px;text-align:center;border-bottom:"
        f"1px solid rgba(255,255,255,0.1);margin-bottom:8px'>"
        f"{_LOGO_SVG_DARK}"
        f"<div style='font-size:14px;font-weight:700;color:#fff;line-height:1.2'>{company}</div>"
        f"<div style='font-size:10px;color:rgba(255,255,255,0.45);margin-top:2px'>"
        f"{t('Commission Manager')}</div>"
        f"<div style='font-size:9px;margin-top:6px;color:{badge_color}'>"
        f"{dot} {badge_text}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if not status['ok']:
        st.sidebar.error(t("Changes will NOT be saved — database connection failed."))
    lang_switcher()
    sidebar_nav()
    # Logout always rendered here so it appears on every page without per-page calls
    from src.auth import logout_button
    logout_button()


def period_selector(suffix: str = "") -> tuple[int, int, dict]:
    """Standard year/quarter selector. Returns (year, quarter, period_dict)."""
    from src.models import get_or_create_period
    c1, c2, _ = st.columns([1, 1, 4])
    year    = c1.selectbox("Year",    [2024, 2025, 2026, 2027], index=2, key=f"yr{suffix}")
    quarter = c2.selectbox("Quarter", [1, 2, 3, 4],             index=1, key=f"q{suffix}",
                            format_func=lambda q: f"Q{q}")
    period  = get_or_create_period(year, quarter)
    return year, quarter, period


def sar(v: float) -> str:
    return f"SAR {v:,.0f}"


def pct(v: float) -> str:
    return f"{v:.1f}%"
