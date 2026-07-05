"""Generate the app favicon / loading icon — the Surveying Experts GNSS device
mark (navy disc, gold survey arcs, white total-station on a tripod, compass
crosshair ticks). Run:  python assets/make_favicon.py

Draws at 4x super-sampling then downscales with LANCZOS for crisp edges at
small sizes (browser tab / mobile home-screen).
"""
import os
from PIL import Image, ImageDraw

OUT   = os.path.join(os.path.dirname(__file__), "favicon.png")
SIZE  = 512
SS    = 4                      # super-sampling factor
S     = SIZE * SS
K     = S / 100.0             # SVG (100x100) → pixel scale

NAVY  = (26, 43, 56, 255)     # #1a2b38
GOLD  = (246, 186, 59, 255)   # #f6ba3b
WHITE = (255, 255, 255, 255)


def x(v):  # scale helper
    return v * K


img  = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d    = ImageDraw.Draw(img)

# ── Navy disc ────────────────────────────────────────────────────────────────
d.ellipse([x(6), x(6), x(94), x(94)], fill=NAVY)

# Subtle inner reticle ring
d.ellipse([x(22), x(22), x(78), x(78)], outline=(255, 255, 255, 46), width=int(x(0.6)))

# ── Gold survey arcs (top-right + bottom-left quadrants) ────────────────────
bbox = [x(6), x(6), x(94), x(94)]
aw   = int(x(6))
# Pillow angles: 0°=east, growing clockwise (y down). N=270, E=0/360, S=90, W=180
d.arc(bbox, start=270, end=360, fill=GOLD, width=aw)   # top-right
d.arc(bbox, start=90,  end=180, fill=GOLD, width=aw)   # bottom-left

# ── Compass crosshair ticks ──────────────────────────────────────────────────
tw = int(x(2))
d.line([x(50), x(6),  x(50), x(22)], fill=WHITE, width=tw)   # N
d.line([x(50), x(78), x(50), x(94)], fill=WHITE, width=tw)   # S
d.line([x(6),  x(50), x(22), x(50)], fill=WHITE, width=tw)   # W
d.line([x(78), x(50), x(94), x(50)], fill=WHITE, width=tw)   # E

# ── Total-station instrument ────────────────────────────────────────────────
# Body
d.rounded_rectangle([x(42), x(30), x(58), x(43)], radius=x(3), fill=WHITE)
# Lens
d.ellipse([x(46), x(32), x(54), x(40)], outline=NAVY, width=int(x(2)))
d.ellipse([x(48.5), x(34.5), x(51.5), x(37.5)], fill=NAVY)
# Tripod stem
d.line([x(50), x(43), x(50), x(60)], fill=WHITE, width=int(x(2.5)))
# Crossbar
d.line([x(42), x(53), x(58), x(53)], fill=WHITE, width=int(x(1.6)))
# Legs
d.line([x(50), x(58), x(39), x(70)], fill=WHITE, width=int(x(2)))
d.line([x(50), x(58), x(61), x(70)], fill=WHITE, width=int(x(2)))

# ── Downscale ────────────────────────────────────────────────────────────────
img = img.resize((SIZE, SIZE), Image.LANCZOS)
img.save(OUT)
print("wrote", OUT, img.size)
