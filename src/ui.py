"""
SE Design System CSS injection for Streamlit.
Call inject_css() once at the top of every page (after set_page_config).
"""
import streamlit as st


_FONT = "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap"

_CSS = """
@import url('{font}');

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

/* ── Hide Streamlit footer + hamburger ── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
/* Use visibility (not display:none) so sidebar toggle stays in DOM */
[data-testid="stToolbar"] {{ visibility: hidden; }}

/* ── Sidebar collapse/expand toggle — always usable ── */
[data-testid="collapsedControl"] {{
  display: flex !important;
  visibility: visible !important;
  background: #1a2b38 !important;
  border-radius: 0 8px 8px 0 !important;
  padding: 6px 3px !important;
}}
[data-testid="collapsedControl"] svg {{
  color: rgba(255,255,255,0.85) !important;
  fill: rgba(255,255,255,0.85) !important;
}}
"""


def inject_css(primary: str = "#354f61") -> None:
    """Inject SE design system CSS. Call once per page after set_page_config."""
    st.markdown(
        f"<style>{_CSS.format(font=_FONT)}</style>",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", primary: str = "#354f61") -> None:
    """Render a consistent SE-branded page header."""
    sub_html = f"<p style='color:#6b757d;margin:2px 0 0;font-size:14px'>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"<div style='margin-bottom:1.5rem'>"
        f"<h1 style='color:{primary};margin:0;font-size:26px;font-weight:700;"
        f"letter-spacing:-0.02em'>{title}</h1>"
        f"{sub_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def sidebar_logo(company: str = "Surveying Experts", primary: str = "#354f61") -> None:
    """Render SE logo block in the sidebar."""
    st.sidebar.markdown(
        f"<div style='padding:18px 0 14px;text-align:center;border-bottom:"
        f"1px solid rgba(255,255,255,0.1);margin-bottom:8px'>"
        f"<div style='display:inline-flex;align-items:center;justify-content:center;"
        f"width:36px;height:36px;background:#f6ba3b;border-radius:8px;margin-bottom:8px'>"
        f"<span style='font-size:18px;color:#1a2b38'>+</span></div>"
        f"<div style='font-size:14px;font-weight:700;color:#fff;line-height:1.2'>{company}</div>"
        f"<div style='font-size:10px;color:rgba(255,255,255,0.45);margin-top:2px'>"
        f"Commission Manager</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


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
