"""Generate favicons, extension icons, and the circular InfoShield badge from the
master logo (assets/infoshield-logo.png).

Outputs:
  extension/icons/icon{16,32,48,128}.png   -> rounded-square app icons
  frontend/public/infoshield-logo.png       -> copy of master logo
  frontend/public/badge.png                 -> circular shield badge (flagged-post marker)
  frontend/public/favicon.ico               -> multi-size favicon
  frontend/public/favicon-32.png            -> 32px favicon fallback

Run:  python tools/make_icons.py
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, "assets", "infoshield-logo.png")

EXT_ICONS = os.path.join(ROOT, "extension", "icons")
PUBLIC = os.path.join(ROOT, "frontend", "public")

VIOLET_TOP = (124, 58, 237)     # #7C3AED
VIOLET_BOTTOM = (147, 51, 234)  # #9333EA


def ensure_dirs() -> None:
    os.makedirs(EXT_ICONS, exist_ok=True)
    os.makedirs(PUBLIC, exist_ok=True)


def rounded_square(img: Image.Image, size: int, radius_ratio: float = 0.22) -> Image.Image:
    """Resize the master logo to a rounded square at `size`px."""
    resized = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    radius = int(size * radius_ratio)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(resized, (0, 0), mask)
    return out


def violet_circle(size: int) -> Image.Image:
    """A soft top-to-bottom violet gradient clipped to a circle."""
    grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = grad.load()
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(VIOLET_TOP[0] + (VIOLET_BOTTOM[0] - VIOLET_TOP[0]) * t)
        g = int(VIOLET_TOP[1] + (VIOLET_BOTTOM[1] - VIOLET_TOP[1]) * t)
        b = int(VIOLET_TOP[2] + (VIOLET_BOTTOM[2] - VIOLET_TOP[2]) * t)
        for x in range(size):
            px[x, y] = (r, g, b, 255)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    grad.putalpha(mask)
    return grad


def make_badge(logo: Image.Image, size: int = 256) -> Image.Image:
    """Circular violet badge with the central shield mark.

    The master logo is a violet square whose center holds a white shield. We
    center-crop to zoom past the boxy corners, then composite the shield region
    onto a clean violet circle so the result reads as a round brand badge.
    """
    w, h = logo.size
    crop = 0.60  # keep central 60% -> drops dark corners, zooms the shield
    box = (int(w * (1 - crop) / 2), int(h * (1 - crop) / 2),
           int(w * (1 + crop) / 2), int(h * (1 + crop) / 2))
    shield = logo.crop(box).resize((size, size), Image.LANCZOS).convert("RGBA")

    base = violet_circle(size)
    # Clip the cropped shield to the circle and lay it over the clean violet base.
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    base.paste(shield, (0, 0), mask)

    # Subtle inner ring for a premium edge.
    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse(
        [2, 2, size - 3, size - 3], outline=(255, 255, 255, 90), width=max(2, size // 64)
    )
    base = Image.alpha_composite(base, ring)
    return base


def main() -> None:
    ensure_dirs()
    logo = Image.open(LOGO).convert("RGBA")

    for s in (16, 32, 48, 128):
        rounded_square(logo, s).save(os.path.join(EXT_ICONS, f"icon{s}.png"))

    logo.save(os.path.join(PUBLIC, "infoshield-logo.png"))

    badge = make_badge(logo, 256)
    badge.save(os.path.join(PUBLIC, "badge.png"))
    # Mirror the badge into the extension so the popup/overlay can use it offline.
    badge.save(os.path.join(EXT_ICONS, "badge.png"))

    fav = rounded_square(logo, 64)
    fav.resize((32, 32), Image.LANCZOS).save(os.path.join(PUBLIC, "favicon-32.png"))
    fav.save(os.path.join(PUBLIC, "favicon.ico"),
             sizes=[(16, 16), (32, 32), (48, 48)])

    print("Icons written:")
    print("  extension/icons/icon{16,32,48,128}.png + badge.png")
    print("  frontend/public/{infoshield-logo.png, badge.png, favicon.ico, favicon-32.png}")


if __name__ == "__main__":
    main()
