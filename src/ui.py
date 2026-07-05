"""
SE Design System CSS injection for Streamlit.
Call inject_css() once at the top of every page (after set_page_config).
"""
import streamlit as st
from src.i18n import lang_switcher, t, is_rtl


_FONT    = "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
_FONT_AR = "https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;700&display=swap"

# SE logo SVG — white+gold version for dark backgrounds (sidebar, login card)
_LOGO_SVG_DARK = (
    "<svg width='48' height='48' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg' "
    "style='display:block;margin:0 auto 8px'>"
    # Compass points — white
    "<polygon points='50,1 44,20 56,20' fill='white'/>"
    "<polygon points='50,99 44,80 56,80' fill='white'/>"
    "<polygon points='1,50 20,44 20,56' fill='white'/>"
    "<polygon points='99,50 80,44 80,56' fill='white'/>"
    # Ring — white stroke, dark fill so instrument reads on top
    "<circle cx='50' cy='50' r='26' fill='#1a2b38' stroke='white' stroke-width='4'/>"
    # Gold arcs — top-right and bottom-left quadrants
    "<path d='M 50,24 A 26,26 0 0,1 76,50' fill='none' stroke='#f6ba3b' stroke-width='8'/>"
    "<path d='M 50,76 A 26,26 0 0,1 24,50' fill='none' stroke='#f6ba3b' stroke-width='8'/>"
    # Surveying instrument — body
    "<rect x='43' y='34' width='14' height='12' rx='3' fill='white'/>"
    # Lens aperture
    "<circle cx='50' cy='40' r='3.5' fill='none' stroke='#1a2b38' stroke-width='1.5'/>"
    # Tripod stem
    "<line x1='50' y1='46' x2='50' y2='57' stroke='white' stroke-width='2.5'/>"
    # Tripod legs
    "<line x1='50' y1='55' x2='42' y2='64' stroke='white' stroke-width='2'/>"
    "<line x1='50' y1='55' x2='58' y2='64' stroke='white' stroke-width='2'/>"
    # Cross bar
    "<line x1='43' y1='52' x2='57' y2='52' stroke='white' stroke-width='1.5'/>"
    "</svg>"
)

# SE logo SVG — navy+gold version for light/white backgrounds
_LOGO_SVG_LIGHT = (
    "<svg width='56' height='56' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg' "
    "style='display:block;margin:0 auto 12px'>"
    "<polygon points='50,1 44,20 56,20' fill='#1a2b38'/>"
    "<polygon points='50,99 44,80 56,80' fill='#1a2b38'/>"
    "<polygon points='1,50 20,44 20,56' fill='#1a2b38'/>"
    "<polygon points='99,50 80,44 80,56' fill='#1a2b38'/>"
    "<circle cx='50' cy='50' r='26' fill='#1a2b38' stroke='#1a2b38' stroke-width='4'/>"
    "<path d='M 50,24 A 26,26 0 0,1 76,50' fill='none' stroke='#f6ba3b' stroke-width='8'/>"
    "<path d='M 50,76 A 26,26 0 0,1 24,50' fill='none' stroke='#f6ba3b' stroke-width='8'/>"
    "<rect x='43' y='34' width='14' height='12' rx='3' fill='white'/>"
    "<circle cx='50' cy='40' r='3.5' fill='none' stroke='#1a2b38' stroke-width='1.5'/>"
    "<line x1='50' y1='46' x2='50' y2='57' stroke='white' stroke-width='2.5'/>"
    "<line x1='50' y1='55' x2='42' y2='64' stroke='white' stroke-width='2'/>"
    "<line x1='50' y1='55' x2='58' y2='64' stroke='white' stroke-width='2'/>"
    "<line x1='43' y1='52' x2='57' y2='52' stroke='white' stroke-width='1.5'/>"
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
    st.sidebar.markdown(
        f"<div style='padding:14px 0 14px;text-align:center;border-bottom:"
        f"1px solid rgba(255,255,255,0.1);margin-bottom:8px'>"
        f"{_LOGO_SVG_DARK}"
        f"<div style='font-size:14px;font-weight:700;color:#fff;line-height:1.2'>{company}</div>"
        f"<div style='font-size:10px;color:rgba(255,255,255,0.45);margin-top:2px'>"
        f"{t('Commission Manager')}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
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
