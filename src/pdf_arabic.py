"""Arabic text shaping and font registration for ReportLab PDFs.

On Streamlit Cloud the system package `fonts-hosny-amiri` is installed via
packages.txt, placing Amiri-Regular.ttf at a known path.  Locally the font
is searched in common locations or downloaded once to /tmp as a fallback.
"""
from __future__ import annotations
import os

_FONT_NAME = "Amiri"
_FONT_REGISTERED = False

_SYSTEM_PATHS = [
    "/usr/share/fonts/truetype/fonts-hosny-amiri/Amiri-Regular.ttf",
    "/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf",
    "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf",
]
_FALLBACK_URL = (
    "https://github.com/aliftype/amiri/releases/download/1.000/Amiri-Regular.ttf"
)


def _find_font() -> str | None:
    for p in _SYSTEM_PATHS:
        if os.path.exists(p):
            return p
    try:
        import urllib.request, tempfile
        dest = os.path.join(tempfile.gettempdir(), "Amiri-Regular.ttf")
        if not os.path.exists(dest):
            urllib.request.urlretrieve(_FALLBACK_URL, dest)
        return dest
    except Exception:
        return None


def register_arabic_font() -> bool:
    """Register Amiri with ReportLab. Returns True if successful."""
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return True
    path = _find_font()
    if not path:
        return False
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont(_FONT_NAME, path))
        _FONT_REGISTERED = True
        return True
    except Exception:
        return False


def ar(text: str) -> str:
    """Reshape and apply bidi algorithm to Arabic text for ReportLab rendering."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except ImportError:
        return str(text)


def pdf_font(lang: str) -> str:
    """Return the font name to use for the given language."""
    if lang == 'ar' and register_arabic_font():
        return _FONT_NAME
    return 'Helvetica'


def pdf_font_bold(lang: str) -> str:
    if lang == 'ar' and register_arabic_font():
        return _FONT_NAME
    return 'Helvetica-Bold'


def cell(text: str, lang: str) -> str:
    """Prepare a table cell value: reshape if Arabic, leave as-is otherwise."""
    if lang == 'ar':
        return ar(str(text))
    return str(text)
