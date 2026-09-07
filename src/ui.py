"""
SE Design System CSS injection for Streamlit.
Call inject_css() once at the top of every page (after set_page_config).
"""
import streamlit as st
from html import escape
from src.i18n import lang_switcher, t, is_rtl


_FONT    = "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
_FONT_AR = "https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;700&display=swap"

# Fonts loaded via a single async <link> with preconnect. NOT @import inside a
# <style> — that is render-blocking and stalls every page on Google Fonts.
_FONT_LINKS = (
    "<link rel='preconnect' href='https://fonts.googleapis.com'>"
    "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
    "<link rel='stylesheet' "
    "href='https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700"
    "&family=Cairo:wght@400;600;700&display=swap'>"
)

_CSS = """
/* ── Design tokens ── */
:root {
  --se-navy:   #1a2b38;
  --se-blue:   #354f61;
  --se-blue-d: #243949;
  --se-gold:   #f6ba3b;
  --se-ink:    #1a2b38;
  --se-muted:  #6b757d;
  --se-line:   #e5e8eb;
  --se-card:   #ffffff;
  --se-radius: 14px;
  --se-shadow: 0 1px 2px rgba(26,43,56,0.04), 0 4px 16px rgba(26,43,56,0.06);
  --se-shadow-hover: 0 6px 24px rgba(26,43,56,0.12);
}

/* ── Base font + smoothing ── */
html, body, [class*="css"], .stApp {
  font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* ── App background — soft vertical wash ── */
.stApp {
  background: linear-gradient(180deg, #f5f7f9 0%, #eef1f4 100%) !important;
  background-attachment: fixed !important;
}
:is(.main, [data-testid="stMain"]) > .block-container {
  padding-top: 2.2rem !important;
  padding-bottom: 3rem !important;
  max-width: 1240px !important;
}

/* ── Sidebar — SE dark blue gradient ── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child {
  background: linear-gradient(180deg, #1f3342 0%, #16242f 100%) !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.72) !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong { color: #fff !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.10) !important; }
[data-testid="stSidebar"] .stButton button {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  color: rgba(255,255,255,0.82) !important;
  border-radius: 9px !important;
  transition: all 0.18s ease !important;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: rgba(246,186,59,0.14) !important;
  border-color: var(--se-gold) !important;
  color: var(--se-gold) !important;
}
/* Custom nav (page_link) */
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
  color: rgba(255,255,255,0.66) !important;
  border-radius: 9px !important;
  padding: 8px 12px !important;
  margin-bottom: 3px !important;
  font-weight: 500 !important;
  transition: all 0.16s ease !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
  background: rgba(255,255,255,0.07) !important;
  color: #fff !important;
  transform: translateX(2px);
}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] input {
  background: rgba(255,255,255,0.08) !important;
  border-color: rgba(255,255,255,0.15) !important;
  color: rgba(255,255,255,0.9) !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[data-testid="baseButton-primary"] {
  background: var(--se-gold) !important;
  border-color: var(--se-gold) !important;
  color: var(--se-navy) !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  box-shadow: 0 2px 10px rgba(246,186,59,0.32) !important;
}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
  font-family: 'IBM Plex Sans', system-ui, sans-serif !important;
  color: var(--se-ink) !important;
  letter-spacing: -0.018em;
}

/* ── Metric cards — elevated with gold top accent ── */
[data-testid="stMetric"],
[data-testid="metric-container"] {
  background: var(--se-card) !important;
  border: 1px solid var(--se-line) !important;
  border-radius: var(--se-radius) !important;
  padding: 1.05rem 1.15rem !important;
  box-shadow: var(--se-shadow) !important;
  position: relative !important;
  overflow: hidden !important;
  transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="stMetric"]::before,
[data-testid="metric-container"]::before {
  content: "";
  position: absolute; top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--se-gold), #ffd67a);
  opacity: 0.9;
}
[data-testid="stMetric"]:hover,
[data-testid="metric-container"]:hover {
  transform: translateY(-2px);
  box-shadow: var(--se-shadow-hover) !important;
}
[data-testid="stMetricLabel"] {
  font-size: 11.5px !important;
  color: var(--se-muted) !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
[data-testid="stMetricValue"] {
  /* Auto-shrink to fit the card and never truncate the number */
  font-size: clamp(15px, 1.5vw, 22px) !important;
  font-weight: 700 !important;
  color: var(--se-ink) !important;
  letter-spacing: -0.02em;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  line-height: 1.15 !important;
}
[data-testid="stMetricValue"] > div { overflow: visible !important; text-overflow: clip !important; }
[data-testid="stMetricDelta"] { font-size: 12px !important; }

/* ── Buttons ── */
.stButton > button {
  font-family: 'IBM Plex Sans', sans-serif !important;
  border-radius: 9px !important;
  font-weight: 600 !important;
  min-height: 40px !important;
  transition: all 0.16s ease !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
  background: var(--se-blue) !important;
  border-color: var(--se-blue) !important;
  color: #fff !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--se-blue-d) !important;
  border-color: var(--se-blue-d) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(36,57,73,0.22) !important;
}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
  border-color: #d2d7dc !important;
  color: #364046 !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: var(--se-blue) !important;
  color: var(--se-blue) !important;
  background: #eef2f4 !important;
}
[data-testid="stDownloadButton"] > button { min-height: 40px !important; border-radius: 9px !important; }

/* ── Tabs — scrollable on small screens ── */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--se-line) !important;
  gap: 0 !important;
  overflow-x: auto !important;
  overflow-y: hidden !important;
  scrollbar-width: thin;
  -webkit-overflow-scrolling: touch;
}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { height: 3px; }
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb { background: #cdd4da; border-radius: 3px; }
.stTabs [data-baseweb="tab"] {
  font-family: 'IBM Plex Sans', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: var(--se-muted) !important;
  padding: 10px 16px !important;
  border-radius: 0 !important;
  border-bottom: 2px solid transparent !important;
  white-space: nowrap !important;
}
.stTabs [aria-selected="true"] {
  color: var(--se-blue) !important;
  font-weight: 600 !important;
  border-bottom: 2px solid var(--se-blue) !important;
  background: transparent !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem !important; }

/* ── Plotly charts wrapped as cards ── */
[data-testid="stPlotlyChart"] {
  background: var(--se-card) !important;
  border: 1px solid var(--se-line) !important;
  border-radius: var(--se-radius) !important;
  padding: 10px 12px !important;
  box-shadow: var(--se-shadow) !important;
  overflow: hidden !important;
}

/* ── Dataframe / data editor ── */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
  border-radius: var(--se-radius) !important;
  overflow: hidden !important;
  border: 1px solid var(--se-line) !important;
  box-shadow: var(--se-shadow) !important;
}

/* ── Responsive HTML data table (render_df) — full data, scrolls on mobile ── */
.se-table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border: 1px solid var(--se-line);
  border-radius: var(--se-radius);
  box-shadow: var(--se-shadow);
  margin: 4px 0 16px;
}
.se-table { border-collapse: collapse; width: 100%; font-size: 13px; background: #fff; }
.se-table th {
  background: var(--se-blue); color: #fff !important; font-weight: 600;
  padding: 10px 12px; text-align: start; white-space: nowrap;
}
.se-table td {
  padding: 8px 12px; border-top: 1px solid var(--se-line);
  text-align: start; white-space: nowrap; color: #243949;
}
.se-table tbody tr:nth-child(even) td { background: #f7f9fb; }
@media (max-width: 640px) {
  .se-table { font-size: 12px; }
  .se-table th, .se-table td { padding: 7px 9px; }
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  border: 1px solid var(--se-line) !important;
  border-radius: var(--se-radius) !important;
  overflow: hidden !important;
  background: var(--se-card) !important;
  margin-bottom: 10px !important;
  box-shadow: var(--se-shadow) !important;
}
[data-testid="stExpander"] summary {
  padding: 13px 16px !important;
  background: var(--se-card) !important;
  font-weight: 600 !important;
  color: var(--se-ink) !important;
}
[data-testid="stExpander"] summary:hover { background: #f7f9fb !important; }
[data-testid="stExpander"] > div:last-child { padding: 0 16px 16px !important; }

/* ── Forms ── */
.stForm {
  background: var(--se-card) !important;
  border: 1px solid var(--se-line) !important;
  border-radius: var(--se-radius) !important;
  padding: 1.15rem 1.3rem !important;
  box-shadow: var(--se-shadow) !important;
}

/* ── Inputs — comfortable touch targets ── */
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"] div[data-value] {
  font-family: 'IBM Plex Sans', sans-serif !important;
  border-radius: 8px !important;
}
[data-baseweb="input"], [data-baseweb="select"] > div {
  border-radius: 8px !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within {
  border-color: var(--se-blue) !important;
  box-shadow: 0 0 0 3px rgba(53,79,97,0.10) !important;
}

/* ── Alerts / info boxes ── */
[data-testid="stAlert"] { border-radius: 10px !important; }

/* ── Divider ── */
hr { border-color: var(--se-line) !important; margin: 1.1rem 0 !important; }

/* ── Toast ── */
[data-testid="toastContainer"] * {
  font-family: 'IBM Plex Sans', sans-serif !important;
  border-radius: 10px !important;
}

/* ── Running/status widget → brand colours ── */
[data-testid="stStatusWidget"] {
  background: var(--se-navy) !important;
  color: #fff !important;
  border-radius: 10px !important;
  box-shadow: 0 4px 14px rgba(0,0,0,0.2) !important;
}
[data-testid="stStatusWidget"] * { color: #fff !important; }
[data-testid="stStatusWidget"] svg { fill: var(--se-gold) !important; color: var(--se-gold) !important; }

/* Spinner accent */
.stSpinner > div { border-top-color: var(--se-gold) !important; }

/* ── Custom scrollbar (desktop) ── */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: #cbd3da; border-radius: 8px; border: 2px solid transparent; background-clip: content-box; }
::-webkit-scrollbar-thumb:hover { background: #aeb8c0; background-clip: content-box; }

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Sidebar collapse/expand toggle — styled, but visibility left to Streamlit
   so it does not leave a stray chip when the sidebar is open ── */
[data-testid="collapsedControl"] {
  background: var(--se-navy) !important;
  border-radius: 0 8px 8px 0 !important;
  box-shadow: 2px 2px 8px rgba(0,0,0,0.18) !important;
  z-index: 1000 !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] button svg {
  fill: rgba(255,255,255,0.92) !important;
  color: rgba(255,255,255,0.92) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   RESPONSIVE — TABLET (≤ 1024px)
   ═══════════════════════════════════════════════════════════════════════════ */
@media (max-width: 1024px) {
  :is(.main, [data-testid="stMain"]) > .block-container {
    padding-left: 1.4rem !important;
    padding-right: 1.4rem !important;
    padding-top: 1.6rem !important;
  }
  [data-testid="stMetricValue"] { font-size: 21px !important; }
}

/* ═══════════════════════════════════════════════════════════════════════════
   RESPONSIVE — MOBILE (≤ 640px)
   ═══════════════════════════════════════════════════════════════════════════ */
@media (max-width: 640px) {
  :is(.main, [data-testid="stMain"]) > .block-container {
    padding-left: 0.85rem !important;
    padding-right: 0.85rem !important;
    padding-top: 1.1rem !important;
    padding-bottom: 2rem !important;
  }

  /* Page header scales down */
  :is(.main, [data-testid="stMain"]) h1 { font-size: 20px !important; line-height: 1.25 !important; }
  :is(.main, [data-testid="stMain"]) h2 { font-size: 17px !important; }
  :is(.main, [data-testid="stMain"]) h3 { font-size: 15px !important; }

  /* Metric cards: tighter, prevent value clipping */
  [data-testid="stMetric"],
  [data-testid="metric-container"] { padding: 0.8rem 0.9rem !important; }
  [data-testid="stMetricValue"] { font-size: 19px !important; }
  [data-testid="stMetricLabel"] { font-size: 10.5px !important; }

  /* Stack multi-column rows in the main area so inputs are usable on a phone
     (scoped to :is(.main, [data-testid="stMain"]) so the sidebar's own columns are left intact) */
  :is(.main, [data-testid="stMain"]) [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.5rem !important;
  }
  :is(.main, [data-testid="stMain"]) [data-testid="stHorizontalBlock"] > [data-testid="column"],
  :is(.main, [data-testid="stMain"]) [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    flex: 1 1 100% !important;
    min-width: 100% !important;
    width: 100% !important;
  }

  /* Buttons full width for easy tapping */
  .stButton > button,
  [data-testid="stDownloadButton"] > button,
  [data-testid="stFormSubmitButton"] > button {
    width: 100% !important;
    min-height: 44px !important;
  }

  /* Tabs: smaller, keep horizontal scroll */
  .stTabs [data-baseweb="tab"] { padding: 9px 12px !important; font-size: 12.5px !important; }

  /* Tables scroll horizontally instead of overflowing the viewport */
  [data-testid="stDataFrame"], [data-testid="stDataEditor"],
  [data-testid="stTable"] { overflow-x: auto !important; }

  /* Forms & expanders: reduce inner padding */
  .stForm { padding: 0.9rem 0.95rem !important; }
  [data-testid="stExpander"] > div:last-child { padding: 0 12px 12px !important; }

  /* Plotly charts: less padding, avoid horizontal overflow */
  [data-testid="stPlotlyChart"] { padding: 6px 4px !important; }
  [data-testid="stPlotlyChart"] > div { width: 100% !important; }

  /* Keep the sidebar toggle comfortably tappable */
  [data-testid="collapsedControl"] { padding: 6px !important; }

  /* When collapsed on a phone, the sidebar must close COMPLETELY — no sliver.
     Streamlit sets aria-expanded="false"; force zero width + off-screen. */
  section[data-testid="stSidebar"][aria-expanded="false"] {
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    margin: 0 !important;
    transform: translateX(-110%) !important;
    overflow: hidden !important;
    box-shadow: none !important;
  }
  section[data-testid="stSidebar"][aria-expanded="false"] * { visibility: hidden !important; }
  /* Hide the drag-to-resize handle that can leave a vertical line on mobile */
  [data-testid="stSidebarResizeHandle"] { display: none !important; }
}

/* Very small phones */
@media (max-width: 380px) {
  [data-testid="stMetricValue"] { font-size: 17px !important; }
  :is(.main, [data-testid="stMain"]) h1 { font-size: 18px !important; }
}
"""


_CSS += """
/* UI refresh: keep the shell stable in both reading directions. */
[data-testid="stAppViewContainer"] { direction: ltr !important; }
[data-testid="stMainBlockContainer"] { max-width: 1440px; padding: 2rem 2rem 3rem; }
.se-page-header {
  margin-bottom: 1.25rem; padding: 1.2rem 1.4rem;
  background: linear-gradient(115deg, #fff 65%, #fff8e9);
  border: 1px solid var(--se-line); border-inline-start: 4px solid var(--se-gold);
  border-radius: 14px;
}
.se-page-header h1 { line-height: 1.4 !important; }
.se-period-row { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin: 0.3rem 0 1rem; }
.se-period-pill { display:inline-flex; align-items:center; gap:6px; padding:5px 12px;
  border-radius:999px; font-size:12px; font-weight:600; border:1px solid #d9e2e8;
  background:#edf3f6; color:#243949; }
.se-period-pill.open { background:#edf8f1; border-color:#bcdcc9; color:#246341; }
.se-period-pill.locked { background:#fff6df; border-color:#ead299; color:#745310; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a { min-height:44px; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
  background:rgba(246,186,59,0.16) !important; border-inline-start:3px solid #f6ba3b;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] * { color:#ffe1a0 !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { margin-top:10px; font-weight:600; }
[data-testid="stSidebar"] .stButton button[kind="primary"] * { color:#1a2b38 !important; }
[data-testid="stMetric"] { box-shadow:0 2px 8px rgba(26,43,56,0.04) !important; }
[data-testid="stMetricLabel"] { font-size:12px !important; text-transform:none; letter-spacing:0; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] > div {
  font-variant-numeric:tabular-nums; direction:ltr !important; unicode-bidi:isolate;
  white-space:normal !important; overflow-wrap:anywhere; line-height:1.35 !important;
}
.se-table-wrap { max-height:540px; scrollbar-gutter:stable; }
.se-table thead th { position:sticky; top:0; z-index:1; }
.se-table td { padding:11px 14px; font-variant-numeric:tabular-nums; }
.se-table tbody tr:hover td { background:#eef4f8; }
.stTabs [data-baseweb="tab"] { min-height:44px; }
.stTabs [aria-selected="true"] { background:#eaf0f4 !important; border-radius:8px 8px 0 0 !important; }
button:focus-visible, a:focus-visible, .se-table-wrap:focus-visible {
  outline:3px solid #e2a52c !important; outline-offset:3px !important;
}
.stButton button:disabled { opacity:0.5; box-shadow:none !important; transform:none !important; cursor:not-allowed; }
@media (max-width: 900px) {
  [data-testid="stMainBlockContainer"] { padding:1.25rem 1rem 2rem; }
  [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stMetric"]) { flex-wrap:wrap !important; }
  [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stMetric"]) > [data-testid="stColumn"] {
    flex:1 1 calc(50% - 1rem) !important; min-width:calc(50% - 1rem) !important; width:auto !important;
  }
}
@media (max-width: 640px) {
  .se-page-header { padding:1rem; margin-bottom:1rem; }
  .se-page-header h1 { font-size:22px !important; }
  .se-page-header p { font-size:13px !important; }
  [data-testid="stSidebar"][aria-expanded="false"] { transform:translateX(-110%) !important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition:none !important; scroll-behavior:auto !important; }
  [data-testid="stMetric"]:hover, .stButton button:hover { transform:none !important; }
}
"""


_RTL_CSS = """
/* ── Arabic RTL overrides ── */
:is(.main, [data-testid="stMain"]), :is(.main, [data-testid="stMain"]) .block-container,
:is(.main, [data-testid="stMain"]) [data-testid="stVerticalBlock"],
:is(.main, [data-testid="stMain"]) [data-testid="stHorizontalBlock"] > div,
.stForm, .stExpander, .stAlert,
[data-testid="stMarkdownContainer"],
[data-testid="stText"],
[data-baseweb="tab-panel"] {
  direction: rtl !important;
  text-align: right !important;
}
html, body, [class*="css"], .stApp {
  font-family: 'Cairo', system-ui, sans-serif !important;
}
h1, h2, h3, h4, h5, h6 {
  font-family: 'Cairo', system-ui, sans-serif !important;
  text-align: right !important;
}
/* Input labels and captions */
label, .stTextInput label, .stSelectbox label,
.stNumberInput label, .stCheckbox label,
.stRadio label, [data-testid="stWidgetLabel"] {
  direction: rtl !important;
  text-align: right !important;
  width: 100% !important;
}
/* Metrics */
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
  text-align: right !important;
}
/* Tabs — RTL order */
[data-baseweb="tab-list"] {
  direction: rtl !important;
}
/* Arabic navigation follows reading order; the app shell stays LTR. */
[data-testid="stSidebar"],
[data-testid="stSidebar"] * {
  direction: rtl !important;
  text-align: right !important;
}
"""


def inject_css(primary: str = "#354f61") -> None:
    """Inject SE design system CSS. Call once per page after set_page_config."""
    html = _FONT_LINKS
    html += "<style>" + _CSS.replace("{font}", _FONT) + "</style>"
    if is_rtl():
        html += "<style>" + _RTL_CSS.replace("{font_ar}", _FONT_AR) + "</style>"
    st.html(html)


def render_df(df) -> None:
    """Render a DataFrame as a fully-visible, mobile-friendly HTML table.

    st.dataframe uses a canvas grid that squeezes columns and truncates cell
    text on small screens (data appears hidden). This renders a plain HTML
    table instead: every value is shown and the table scrolls horizontally on
    narrow screens, so nothing is hidden.
    """
    try:
        html = df.to_html(index=False, escape=True, border=0, classes="se-table")
        st.markdown(f"<div class='se-table-wrap' tabindex='0' role='region' aria-label='{escape(t("Results table"))}'>{html}</div>",
                    unsafe_allow_html=True)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True)


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
        f"<div class='se-page-header' style='direction:{dir_s};text-align:{align}'>"
        f"<h1 style='color:{primary};margin:0;font-size:26px;font-weight:700;"
        f"letter-spacing:-0.02em;font-family:{font};text-align:{align}'>{escape(title)}</h1>"
        f"{sub_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def sidebar_nav() -> None:
    """Render translated page navigation links in the sidebar.

    Read-only viewers see only the pages they may use: the Dashboard, the
    Commission Report (read-only) and the Reports Center (downloads). The
    input/settings/audit pages are hidden and also gated server-side.
    """
    from src.auth import is_viewer
    _all_pages = [
        ("Home.py",               "Dashboard"),
        ("pages/2_Sales.py",      "Sales Input"),
        ("pages/3_KPI.py",        "KPI Calculation"),
        ("pages/4_Commission.py", "Commission Report"),
        ("pages/5_Reports.py",    "Reports Center"),
        ("pages/6_Settings.py",   "Settings"),
        ("pages/7_Audit.py",      "Audit Log"),
    ]
    _viewer_pages = {"Home.py", "pages/4_Commission.py", "pages/5_Reports.py"}
    viewer = is_viewer()
    icons = ["dashboard", "edit_note", "fact_check", "payments", "download", "settings", "history"]
    st.sidebar.caption(t("Workspace"))
    for (_path, _label), icon in zip(_all_pages, icons):
        if viewer and _path not in _viewer_pages:
            continue
        if _label == "Settings":
            st.sidebar.caption(t("Administration"))
        st.sidebar.page_link(_path, label=t(_label), icon=f":material/{icon}:")
    st.sidebar.markdown("---")


@st.cache_data(ttl=30, show_spinner=False)
def _cached_db_status():
    """Health badge state, cached so it is not a live query on every rerun."""
    from src.db import db_status
    return db_status()


def sidebar_logo(company: str = "Surveying Experts", primary: str = "#354f61") -> None:
    """Render SE logo block + language switcher + navigation in the sidebar."""
    from src.branding import logo_data_uri
    status = _cached_db_status()
    if status['ok'] and status['backend'] == 'postgresql':
        dot, badge_color, badge_text = "●", "#4caf7d", t("Cloud database")
    elif status['ok']:
        dot, badge_color, badge_text = "●", "#f6ba3b", t("Local database (dev only)")
    else:
        dot, badge_color, badge_text = "●", "#e05d5d", t("Database unreachable")

    # Real company logo (compass mark) on a light chip so the navy artwork
    # reads clearly against the dark sidebar. If the asset is missing, no icon.
    icon = logo_data_uri("icon")
    logo_html = (
        f"<div style='width:76px;height:76px;margin:0 auto 10px;border-radius:18px;"
        f"background:#ffffff;box-shadow:0 4px 14px rgba(0,0,0,0.25);"
        f"display:flex;align-items:center;justify-content:center'>"
        f"<img src='{icon}' style='width:60px;height:60px;object-fit:contain'/></div>"
    ) if icon else ""

    st.sidebar.markdown(
        f"<div style='padding:16px 0 14px;text-align:center;border-bottom:"
        f"1px solid rgba(255,255,255,0.1);margin-bottom:8px'>"
        f"{logo_html}"
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


def period_status(period: dict) -> None:
    """Show the selected quarter and its edit status without changing data."""
    from src.i18n import q_label
    state = "locked" if period.get("is_locked") else "open"
    label = t("Locked") if state == "locked" else t("Open for entry")
    quarter = escape(f"{q_label(period['quarter'])} · {period['year']}")
    st.markdown(f'<div class="se-period-row"><span class="se-period-pill">{quarter}</span>'
                f'<span class="se-period-pill {state}">{escape(label)}</span></div>', unsafe_allow_html=True)
