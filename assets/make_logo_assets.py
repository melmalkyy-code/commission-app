"""Generate the app logo assets from the official vector logo PDF.
Run:  python assets/make_logo_assets.py   (needs pymupdf + Pillow)

Produces (all transparent PNG unless noted):
  logo_full.png  — full lockup (compass mark + "SURVEYING Experts")  → light bg
  logo_icon.png  — compass / GNSS device mark only (square)          → chips
  favicon.png    — icon on a white rounded square                    → page_icon

Source is the company's own artwork, so these are the exact uploaded logo —
no recreation.
"""
import os
import numpy as np
from PIL import Image, ImageDraw

HERE   = os.path.dirname(__file__)
SRC    = r"D:/WORK/Assets/Logo Surveyingexperts.pdf"   # official vector logo


def _render_pdf(path, zoom=6):
    import fitz
    pix = fitz.open(path)[0].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
    return Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)


def _trim(im):
    a = np.array(im)[:, :, 3]
    ys, xs = np.where(a > 12)
    return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def main():
    full = _trim(_render_pdf(SRC))
    full.save(os.path.join(HERE, "logo_full.png"))

    # Icon = compass mark. It is horizontally symmetric about the north-arrow
    # tip; the west tip sits at x=0 after trimming, so the east tip mirrors it.
    a = np.array(full)[:, :, 3]
    h, w = a.shape
    top_cols = np.where((a[:int(h * 0.06), :] > 12).any(axis=0))[0]
    center = int((top_cols.min() + top_cols.max()) / 2)
    icon = _trim(full.crop((0, 0, 2 * center - 40, h)))   # -40 drops the 'S' sliver

    iw, ih = icon.size
    pad = int(0.06 * max(iw, ih))
    s = max(iw, ih) + 2 * pad
    sq = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sq.paste(icon, ((s - iw) // 2, (s - ih) // 2), icon)

    # Favicon = icon on a white rounded square (readable on any browser tab)
    F = 256
    fav = Image.new("RGBA", (F, F), (0, 0, 0, 0))
    mask = Image.new("L", (F, F), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, F - 1, F - 1], radius=48, fill=255)
    white = Image.new("RGBA", (F, F), (255, 255, 255, 255))
    fav.paste(white, (0, 0), mask)
    inner = int(F * 0.74)
    ic = sq.resize((inner, inner), Image.LANCZOS)
    fav.paste(ic, ((F - inner) // 2, (F - inner) // 2), ic)
    fav.save(os.path.join(HERE, "favicon.png"), optimize=True)

    # Downscale the display assets — they were multi-megapixel but render tiny.
    # Keeping them small removes ~100 KB of base64 from every page render.
    sq.resize((128, 128), Image.LANCZOS).save(
        os.path.join(HERE, "logo_icon.png"), optimize=True)
    fw, fh = full.size
    tw = 440
    full.resize((tw, round(fh * tw / fw)), Image.LANCZOS).save(
        os.path.join(HERE, "logo_full.png"), optimize=True)
    print("wrote logo_full.png, logo_icon.png, favicon.png")


if __name__ == "__main__":
    main()
