#!/usr/bin/env python3
"""LUMINARA — a travel poster for a place that does not exist.

Draws a vintage travel poster (768 x 1024) with PIL and writes it to
/output/entry.png (or argv[1] when given). No network, no copied image:
every pixel is generated here by code.

The place: LUMINARA, a cliff city above a glowing lagoon where the sea
keeps the light long after sunset. Its landmark is the Crystal Spire,
a lighthouse of living glass on the eastern cliff.
"""

import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 768, 1024
MAX_BYTES = 1_048_576

# --- palette -------------------------------------------------------------
INK = (24, 24, 34)            # near-black for silhouettes
CREAM = (250, 240, 214)       # poster paper / title type
GOLD = (246, 196, 94)         # moonlight, spire glow
AMBER = (232, 138, 58)        # horizon fire
TEAL_DEEP = (13, 48, 66)
TEAL = (23, 94, 104)
SKY_TOP = (16, 20, 58)
SKY_MID = (44, 48, 104)
SKY_LOW = (96, 84, 138)

random.seed(20261121)


def find_font(names, size):
    """First usable TTF from the candidate list, else PIL's default."""
    for path in names:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


SERIF_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
]
SANS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
]
SANS_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(draw, x0, y0, x1, y1, stops):
    """Vertical gradient across (x0,y0)-(x1,y1) through colour stops."""
    n = y1 - y0
    for y in range(n):
        t = y / max(n - 1, 1)
        for i in range(len(stops) - 1):
            lo, hi = i / (len(stops) - 1), (i + 1) / (len(stops) - 1)
            if lo <= t <= hi:
                c = lerp(stops[i], stops[i + 1], (t - lo) / (hi - lo or 1))
                break
        else:
            c = stops[-1]
        draw.line([(x0, y0 + y), (x1, y0 + y)], fill=c)


def glow_layer(size, cx, cy, radius, colour, peak=170):
    """Soft radial glow on a transparent overlay, to be composited."""
    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    steps = 24
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(peak * (1 - i / steps) ** 2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour + (a,))
    return ov.filter(ImageFilter.GaussianBlur(6))


def tracked_text(draw, cx, y, text, font, fill, tracking=6):
    """Draw centred text with extra letter spacing."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking
    return total


def draw_poster():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # --- paper frame ------------------------------------------------------
    d.rectangle([0, 0, W - 1, H - 1], fill=CREAM)
    # inner picture area
    mx, my = 34, 34
    px0, py0, px1, py1 = mx, my, W - mx, H - 118
    horizon = py0 + int((py1 - py0) * 0.56)

    # --- sky ---------------------------------------------------------------
    vgrad(d, px0, py0, px1, horizon, [SKY_TOP, SKY_MID, SKY_LOW, AMBER])
    # --- sea ----------------------------------------------------------------
    vgrad(d, px0, horizon, px1, py1, [AMBER, TEAL, TEAL_DEEP, (8, 30, 44)])

    # moon glow + moon, upper right of the sky
    moon_cx, moon_cy, moon_r = 556, 190, 56
    glow = glow_layer((W, H), moon_cx, moon_cy, 190, (250, 214, 130), peak=150)
    img.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(img)
    d.ellipse([moon_cx - moon_r, moon_cy - moon_r,
               moon_cx + moon_r, moon_cy + moon_r], fill=(252, 236, 180))
    # moon craters, faint
    for cx, cy, r in [(536, 200, 9), (572, 232, 12), (548, 244, 6), (580, 198, 5)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(238, 214, 150))

    # stars: denser and brighter near the top
    for _ in range(240):
        x = random.randint(px0 + 4, px1 - 4)
        y = random.randint(py0 + 4, horizon - 60)
        r = random.choice([1, 1, 1, 2, 2, 3])
        a = random.randint(120, 255)
        fade = 1.0 - (y - py0) / max(horizon - py0, 1)
        if random.random() < 0.35 + 0.6 * fade:
            d.ellipse([x - r, y - r, x + r, y + r],
                      fill=(255, 244, 214) if a > 200 else (200, 205, 235))
    # a few bright four-point stars
    for cx, cy, s in [(180, 130, 9), (420, 96, 7), (300, 210, 6), (640, 330, 7)]:
        d.line([(cx - s, cy), (cx + s, cy)], fill=(255, 246, 220), width=2)
        d.line([(cx, cy - s), (cx, cy + s)], fill=(255, 246, 220), width=2)

    # --- moonlight path on the water ----------------------------------------
    for i in range(70):
        t = i / 69
        y = horizon + 14 + t * (py1 - horizon - 26)
        half = 6 + t * 42
        cx = moon_cx + random.randint(-10, 10)
        x0 = cx - half + random.randint(-6, 6)
        x1 = cx + half + random.randint(-6, 6)
        d.line([(max(px0, x0), y), (min(px1, x1), y)],
               fill=(250, 214, 130), width=2)

    # --- distant headland, left ----------------------------------------------
    d.polygon([(px0, horizon - 8), (150, horizon - 66), (268, horizon - 30),
               (330, horizon - 52), (392, horizon - 6), (px0, horizon - 2)],
              fill=(52, 52, 96))
    # tiny windows on the distant town
    for x in range(180, 320, 16):
        for y in (horizon - 46, horizon - 34):
            if random.random() < 0.55:
                d.rectangle([x, y, x + 3, y + 4], fill=(246, 196, 94))

    # --- cliffs ---------------------------------------------------------------
    # left cliff, dark silhouette
    d.polygon([(px0, py1), (px0, horizon + 96), (118, horizon + 30),
               (196, horizon + 96), (238, horizon + 190), (196, py1)],
              fill=INK)
    # right cliff, holding the Crystal Spire
    d.polygon([(px1, py1), (px1, horizon + 70), (640, horizon + 18),
               (578, horizon + 120), (606, horizon + 240), (560, py1)],
              fill=INK)

    # --- the Crystal Spire (landmark lighthouse) ------------------------------
    sx, base = 622, horizon + 66          # spire foot on the right cliff
    spire_top = horizon - 118
    # faceted glass tower, tapering upward
    d.polygon([(sx - 26, base), (sx - 15, spire_top + 26), (sx - 7, spire_top),
               (sx + 7, spire_top), (sx + 15, spire_top + 26), (sx + 26, base)],
              fill=(214, 226, 240))
    d.polygon([(sx - 15, spire_top + 26), (sx - 7, spire_top), (sx, spire_top + 30),
               (sx, base), (sx - 26, base)], fill=(168, 190, 214))
    d.polygon([(sx + 15, spire_top + 26), (sx + 7, spire_top), (sx, spire_top + 30),
               (sx, base), (sx + 26, base)], fill=(238, 242, 248))
    # glowing lantern room
    d.rectangle([sx - 12, spire_top - 26, sx + 12, spire_top], fill=GOLD)
    d.polygon([(sx - 16, spire_top - 26), (sx, spire_top - 42),
               (sx + 16, spire_top - 26)], fill=(250, 222, 140))
    # light beams sweeping left across the bay and up into the sky
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(sx, spire_top - 12), (px0 + 6, spire_top + 96),
                (px0 + 6, spire_top + 150), (sx, spire_top + 4)],
               fill=(250, 222, 140, 60))
    bd.polygon([(sx, spire_top - 12), (px1 - 4, spire_top - 128),
                (px1 - 4, spire_top - 84), (sx, spire_top + 2)],
               fill=(250, 222, 140, 42))
    beam = beam.filter(ImageFilter.GaussianBlur(4))
    img.paste(beam, (0, 0), beam)
    d = ImageDraw.Draw(img)
    # spire glow
    glow2 = glow_layer((W, H), sx, spire_top - 12, 110, (246, 196, 94), peak=130)
    img.paste(glow2, (0, 0), glow2)
    d = ImageDraw.Draw(img)
    # lit windows up the tower
    for i, y in enumerate(range(base - 26, spire_top + 40, 26)):
        w = 5 if i % 2 == 0 else 4
        d.rectangle([sx - w, y, sx + w, y + 9], fill=(255, 224, 150))

    # --- sailboats in the bay -------------------------------------------------
    def sailboat(cx, cy, s, colour):
        d.polygon([(cx, cy), (cx, cy - 34 * s), (cx + 26 * s, cy)],
                  fill=colour)
        d.polygon([(cx - 3, cy), (cx - 3, cy - 24 * s), (cx - 20 * s, cy)],
                  fill=colour)
        d.line([(cx, cy - 36 * s), (cx, cy + 2)], fill=colour, width=2)
        d.polygon([(cx - 16 * s, cy + 2), (cx + 18 * s, cy + 2),
                   (cx + 12 * s, cy + 9), (cx - 10 * s, cy + 9)], fill=INK)

    sailboat(300, horizon + 118, 1.0, (250, 240, 214))
    sailboat(430, horizon + 168, 0.72, (226, 214, 186))
    sailboat(196, horizon + 196, 0.55, (200, 190, 164))

    # --- birds ------------------------------------------------------------------
    for cx, cy, s in [(250, 300, 10), (290, 282, 8), (330, 306, 9), (470, 250, 8)]:
        d.arc([cx - s, cy - s // 2, cx, cy + s // 2], 200, 340, fill=INK, width=2)
        d.arc([cx, cy - s // 2, cx + s, cy + s // 2], 200, 340, fill=INK, width=2)

    # --- picture frame -----------------------------------------------------------
    d.rectangle([px0, py0, px1, py1], outline=INK, width=4)
    d.rectangle([px0 + 8, py0 + 8, px1 - 8, py1 - 8], outline=GOLD, width=2)

    # --- type ---------------------------------------------------------------------
    # fit the title inside the picture frame, shrinking the font as needed
    title = "LUMINARA"
    title_size = 118
    while title_size > 40:
        title_font = find_font(SERIF_BOLD, title_size)
        if d.textlength(title, font=title_font) <= (px1 - px0) - 48:
            break
        title_size -= 4
    tagline = "WHERE THE SEA KEEPS THE LIGHT"
    tag_size, tag_tracking = 30, 7
    while tag_size > 14:
        tag_font = find_font(SANS_BOLD, tag_size)
        w = sum(d.textlength(ch, font=tag_font) for ch in tagline) \
            + tag_tracking * (len(tagline) - 1)
        if w <= (px1 - px0) - 40:
            break
        tag_size -= 2
        tag_tracking = max(2, tag_tracking - 1)
    foot_font = find_font(SANS, 22)

    # title shadow + title, set across the sky above the horizon
    cx = W // 2
    ty = py0 + 84
    tw = d.textlength(title, font=title_font)
    d.text((cx - tw / 2 + 4, ty + 5), title, font=title_font, fill=(20, 16, 40))
    d.text((cx - tw / 2, ty), title, font=title_font, fill=CREAM)
    # thin gold rule under the title
    d.line([(cx - tw / 2, ty + title_size + 22), (cx + tw / 2, ty + title_size + 22)],
           fill=GOLD, width=3)

    tracked_text(d, cx, ty + title_size + 42, tagline,
                 tag_font, CREAM, tracking=tag_tracking)

    # footer strip: small line under the picture, on the paper
    foot = "BEYOND THE EDGE OF EVERY MAP"
    fw = d.textlength(foot, font=foot_font)
    d.text((cx - fw / 2, H - 78), foot, font=foot_font, fill=(90, 70, 60))
    # tiny diamonds flanking the footer
    for dx in (-fw / 2 - 26, fw / 2 + 18):
        x = cx + dx
        d.polygon([(x, H - 70), (x + 6, H - 64), (x, H - 58), (x - 6, H - 64)],
                  fill=GOLD)

    return img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/output/entry.png"
    img = draw_poster()
    # keep within the gate: 1024 x 1024 and at most 1 MiB
    img.save(out, format="PNG", optimize=True)
    size = os.path.getsize(out)
    if size > MAX_BYTES:  # safety net: shrink until it fits
        scale = 0.85
        while size > MAX_BYTES and scale > 0.4:
            small = img.resize((int(W * scale), int(H * scale)),
                               Image.LANCZOS)
            small.save(out, format="PNG", optimize=True)
            size = os.path.getsize(out)
            scale -= 0.1
    print(f"wrote {out} {img.size[0]}x{img.size[1]} {size} bytes")


if __name__ == "__main__":
    main()
