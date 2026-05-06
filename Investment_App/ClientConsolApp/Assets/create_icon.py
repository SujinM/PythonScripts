"""
create_icon.py
==============
Generates Assets/app.ico for SujinsInvestment.
Icon design: dark-navy rounded square + gold upward-chart line.

Run from the ClientConsolApp root or Assets folder:
    python Assets/create_icon.py
"""
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw


# ── Palette ────────────────────────────────────────────────────────────────────
BG_DARK     = (15,  35,  80, 255)   # deep navy
BG_LIGHT    = (30,  60, 130, 255)   # mid-blue (gradient top)
GOLD        = (255, 200,  50, 255)  # chart line / accent
GOLD_LIGHT  = (255, 230, 120, 255)  # highlight dot
WHITE       = (255, 255, 255, 220)  # axis / bar

# ── Sizes to embed in the ICO ──────────────────────────────────────────────────
SIZES = [256, 128, 64, 48, 32, 16]


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))


def _draw_frame(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # --- vertical gradient background ---
    radius = max(4, size // 7)
    for y in range(size):
        t = y / size
        color = _lerp_color(BG_LIGHT, BG_DARK, t)
        draw.line([(0, y), (size, y)], fill=color)

    # Clip to rounded rectangle by masking corners
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    img.putalpha(mask)

    # --- chart bars (background) ---
    if size >= 32:
        bar_count  = 4
        pad        = size // 6
        bar_w      = max(1, (size - 2 * pad) // (bar_count * 2))
        bar_heights = [0.35, 0.55, 0.45, 0.75]
        for i, h in enumerate(bar_heights):
            x0 = pad + i * (bar_w * 2)
            x1 = x0 + bar_w
            y1 = size - pad
            y0 = int(size - pad - h * (size - 2 * pad) * 0.7)
            alpha = 60
            color = (255, 255, 255, alpha)
            draw.rectangle([x0, y0, x1, y1], fill=color)

    # --- upward chart line ---
    pad = size // 6
    available = size - 2 * pad
    if size >= 32:
        # 5 chart points trending upward
        rel_x = [0.0, 0.25, 0.45, 0.65, 1.0]
        rel_y = [0.85, 0.55, 0.68, 0.35, 0.12]
        pts = [
            (int(pad + rx * available), int(pad + ry * available))
            for rx, ry in zip(rel_x, rel_y)
        ]
        lw = max(1, size // 18)
        # Shadow pass (slightly offset)
        shadow_pts = [(x + 1, y + 1) for x, y in pts]
        draw.line(shadow_pts, fill=(0, 0, 0, 100), width=lw)
        # Main gold line
        draw.line(pts, fill=GOLD, width=lw)
        # Highlight dot at the peak (last point)
        r = max(1, size // 14)
        ex, ey = pts[-1]
        draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=GOLD_LIGHT)
    elif size == 16:
        # Simplified: just a diagonal arrow
        draw.line([(4, 12), (12, 4)], fill=GOLD, width=2)
        draw.polygon([(10, 3), (13, 3), (13, 6)], fill=GOLD)

    # --- "S" monogram (bottom-right corner for larger sizes) ---
    if size >= 64:
        font_size = size // 5
        corner_x = size - pad - font_size // 2
        corner_y = size - pad - font_size // 2
        r2 = font_size // 2
        draw.ellipse(
            [corner_x - r2, corner_y - r2, corner_x + r2, corner_y + r2],
            fill=(*BG_DARK[:3], 200)
        )
        # Draw a tiny "S" using lines (no font file needed)
        s = font_size // 2 - 2
        cx, cy = corner_x, corner_y
        draw.arc([cx - s, cy - s, cx + s, cy], start=180, end=0, fill=GOLD_LIGHT, width=max(1, size // 40))
        draw.arc([cx - s, cy, cx + s, cy + s], start=0, end=180, fill=GOLD_LIGHT, width=max(1, size // 40))

    return img


def main() -> None:
    out = Path(__file__).resolve().parent / "app.ico"
    frames = [_draw_frame(s) for s in SIZES]
    # Save as multi-size ICO
    frames[0].save(
        out,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
    )
    print(f"Icon saved → {out}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
