"""Generate dial-print bitmaps (crown + wordmarks) for each fenix 7 screen size.

Top block is drawn with its top edge at cy - 0.53R, bottom block with its top edge at cy + 0.165R,
both horizontally centred (see GMTView.mc)."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

SS = 6
FD = "/usr/share/fonts/truetype/"
SERIF_B = FD + "liberation/LiberationSerif-Bold.ttf"
SANS = FD + "liberation/LiberationSans-Regular.ttf"
SANS_B = FD + "liberation/LiberationSans-Bold.ttf"
WHITE = (255, 255, 255, 255)
GREEN = (0, 170, 85, 255)


def text_fit(d, cx, y, txt, font_path, h, max_w, fill, spacing=0.0):
    size = int(h)
    while True:
        f = ImageFont.truetype(font_path, size)
        w = sum(d.textlength(c, font=f) for c in txt) + spacing * size * (len(txt) - 1)
        if w <= max_w or size < 4:
            break
        size -= 1
    x = cx - w / 2
    for c in txt:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + spacing * size
    return y + size


def crown(d, cx, top, w, fill):
    h = w * 0.78
    base_y0, base_y1 = top + h * 0.72, top + h
    # base band with oval cut-outs
    d.rounded_rectangle([cx - w * 0.36, base_y0, cx + w * 0.36, base_y1], radius=h * 0.12, fill=fill)
    for k in (-2, -1, 0, 1, 2):
        ox = cx + k * w * 0.14
        d.ellipse([ox - w * 0.035, base_y0 + h * 0.07, ox + w * 0.035, base_y1 - h * 0.07], fill=(0, 0, 0, 255))
    # five tines fanning out, each tipped with a ball
    tips = [(-0.44, 0.30), (-0.24, 0.12), (0.0, 0.05), (0.24, 0.12), (0.44, 0.30)]
    for tx, ty in tips:
        bx = cx + tx * w * 0.55
        px, py = cx + tx * w, top + ty * h + h * 0.08
        tw = w * 0.055
        d.polygon([(bx - tw * 1.3, base_y0 + 1), (px - tw * 0.6, py), (px + tw * 0.6, py), (bx + tw * 1.3, base_y0 + 1)], fill=fill)
        r = w * 0.065
        d.ellipse([px - r, py - r * 1.4, px + r, py + r * 0.6], fill=fill)


def make_blocks(size):
    R = size / 2.0
    W = int(R * 1.0) * SS
    # --- top: crown, ROLEX, OYSTER PERPETUAL DATE (spans 0.53R .. 0.17R above centre)
    Ht = int(R * 0.36) * SS
    top = Image.new("RGBA", (W, Ht), (0, 0, 0, 0)); d = ImageDraw.Draw(top)
    u = R * SS
    crown(d, W / 2, 0, u * 0.20, WHITE)
    y = text_fit(d, W / 2, u * 0.17, "ROLEX", SERIF_B, u * 0.105, u * 0.40, WHITE, 0.06)
    text_fit(d, W / 2, u * 0.285, "OYSTER PERPETUAL DATE", SANS, u * 0.058, u * 0.86, WHITE, 0.04)
    # --- bottom: GMT-MASTER II, SUPERLATIVE CHRONOMETER, OFFICIALLY CERTIFIED
    Hb = int(R * 0.30) * SS
    bot = Image.new("RGBA", (W, Hb), (0, 0, 0, 0)); d = ImageDraw.Draw(bot)
    text_fit(d, W / 2, 0, "GMT-MASTER II", SANS_B, u * 0.085, u * 0.72, GREEN, 0.05)
    text_fit(d, W / 2, u * 0.125, "SUPERLATIVE CHRONOMETER", SANS, u * 0.055, u * 0.86, WHITE, 0.03)
    text_fit(d, W / 2, u * 0.195, "OFFICIALLY CERTIFIED", SANS, u * 0.055, u * 0.80, WHITE, 0.03)
    ds = lambda im: im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    return ds(top), ds(bot)


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    for s in (240, 260, 280):
        t, b = make_blocks(s)
        out = os.path.join(root, f"resources-round-{s}x{s}", "drawables")
        os.makedirs(out, exist_ok=True)
        t.save(os.path.join(out, "dial_top.png")); b.save(os.path.join(out, "dial_bottom.png"))
        with open(os.path.join(out, "dial.xml"), "w") as f:
            f.write('<drawables>\n    <bitmap id="DialTop" filename="dial_top.png" dithering="none"/>\n'
                    '    <bitmap id="DialBottom" filename="dial_bottom.png" dithering="none"/>\n</drawables>\n')
        print(s, t.size, b.size)
