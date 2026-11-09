"""Render the static dial (bezel, dial print, markers) as full-screen bitmaps per variant and
screen size, date digits, launcher icon and previews.

Usage:  python3 tools/render_face.py            (run from repo root)

Hand geometry here mirrors source/GMTView.mc so the previews match the watch.
All lengths are in units of the screen radius R.
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
F = lambda n: os.path.join(HERE, "fonts", n)
SYS = "/usr/share/fonts/truetype/liberation/"
FONT_BEZEL = F("Barlow-SemiBold.ttf")
FONT_SMALL = F("BarlowSemiCondensed-Medium.ttf")
FONT_MODEL = F("BarlowSemiCondensed-SemiBold.ttf")
FONT_LOGO = SYS + "LiberationSerif-Bold.ttf"
FONT_DATE = SYS + "LiberationSans-Bold.ttf"

SS = 6                         # supersampling factor
SIZES = (240, 260, 280)        # fenix 7S / 7 / 7X (+ Pro)

# MIP-friendly colours (fenix 7 has a 64-colour palette: channels 00/55/AA/FF)
BLACK, WHITE, SILVER, STEEL = (0, 0, 0), (255, 255, 255), (170, 170, 170), (85, 85, 85)
VARIANTS = {
    #          top (18-06, night)   bottom (06-18, day)  GMT hand        model text   date at
    "pepsi":  dict(top=(0, 0, 170), bot=(170, 0, 0),    gmt=(170, 0, 0),   model=WHITE, date=3),
    "batman": dict(top=(0, 0, 0),    bot=(0, 85, 170),   gmt=(0, 85, 170),  model=WHITE, date=3),
    "sprite": dict(top=(0, 170, 85), bot=(0, 0, 0),      gmt=(0, 170, 85),  model=(0, 170, 85), date=9),
}

# Date window (centre radius, width, height)
DATE_R, DATE_W, DATE_H = 0.625, 0.27, 0.21


class Canvas:
    def __init__(self, size):
        self.size = size
        self.W = size * SS
        self.R = self.W / 2
        self.c = self.R
        self.img = Image.new("RGB", (self.W, self.W), BLACK)
        self.d = ImageDraw.Draw(self.img)

    def polar(self, a, f):
        return (self.c + self.R * f * math.sin(a), self.c - self.R * f * math.cos(a))

    def xf(self, pts, a):
        s, c = math.sin(a), math.cos(a)
        return [(self.c + y * self.R * s + x * self.R * c, self.c - y * self.R * c + x * self.R * s) for x, y in pts]

    def circle(self, p, r, fill):
        r *= self.R
        self.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)

    def ring(self, f, width_px, fill):
        r = self.R * f
        self.d.ellipse([self.c - r, self.c - r, self.c + r, self.c + r], outline=fill, width=int(width_px * SS))

    def font(self, path, cap_h):
        """Font whose capital height is cap_h (in R units)."""
        target = cap_h * self.R
        size = max(4, int(target / 0.7))
        for _ in range(3):
            f = ImageFont.truetype(path, size)
            b = f.getbbox("H")
            size = max(4, int(size * target / max(1, b[3] - b[1])))
        return ImageFont.truetype(path, size)

    def text(self, cx, cy, txt, path, cap_h, fill, track=0.0, stretch=1.0, rot=0.0):
        """Draw text centred (on cap height) at cx, cy; track = letter spacing in cap heights."""
        f = self.font(path, cap_h)
        cap = f.getbbox("H")
        ch = cap[3] - cap[1]
        widths = [f.getlength(ch_) for ch_ in txt]
        tw = sum(widths) + track * ch * (len(txt) - 1)
        pad = int(ch)
        tile = Image.new("L", (int(tw) + 2 * pad, int(ch) + 2 * pad), 0)
        td = ImageDraw.Draw(tile)
        x = pad
        for c_, w_ in zip(txt, widths):
            td.text((x, pad - cap[1]), c_, font=f, fill=255)
            x += w_ + track * ch
        if stretch != 1.0:
            tile = tile.resize((int(tile.width * stretch), tile.height), Image.LANCZOS)
        if rot:
            tile = tile.rotate(-math.degrees(rot), resample=Image.BICUBIC, expand=True)
        col = Image.new("RGB", tile.size, fill)
        self.img.paste(col, (int(cx - tile.width / 2), int(cy - tile.height / 2)), tile)


def crown(cv, cx, top, w, fill):
    """Five-pointed coronet: tines tipped with pearls on an oval-pierced band."""
    d, h = cv.d, w * 0.80
    by0, by1 = top + h * 0.70, top + h * 0.98
    tips = [(-0.47, 0.34), (-0.25, 0.13), (0.0, 0.05), (0.25, 0.13), (0.47, 0.34)]
    for tx, ty in tips:
        bx = cx + tx * w * 0.50
        px, py = cx + tx * w, top + ty * h + w * 0.07
        t0, t1 = w * 0.055, w * 0.035
        d.polygon([(bx - t0, by0 + 1), (px - t1, py), (px + t1, py), (bx + t0, by0 + 1)], fill=fill)
        r = w * 0.068
        d.ellipse([px - r, py - r * 1.25, px + r, py + r * 0.75], fill=fill)
    # cup joining the tines to the band
    d.chord([cx - w * 0.36, by0 - h * 0.20, cx + w * 0.36, by0 + h * 0.20], 0, 180, fill=fill)
    d.rounded_rectangle([cx - w * 0.36, by0, cx + w * 0.36, by1], radius=h * 0.11, fill=fill)
    for k in (-2, -1, 0, 1, 2):
        ox = cx + k * w * 0.135
        d.ellipse([ox - w * 0.034, by0 + h * 0.07, ox + w * 0.034, by1 - h * 0.07], fill=BLACK)


def render_background(size, v):
    cv = Canvas(size)
    d, R, c = cv.d, cv.R, cv.c
    W = cv.W
    # --- Cerachrom insert: night half on top, day half below
    d.pieslice([0, 0, W, W], 180, 360, fill=v["top"])
    d.pieslice([0, 0, W, W], 0, 180, fill=v["bot"])
    cv.ring(1.0, 2, SILVER)
    # 24h graduations, radially oriented (base towards centre), platinum-coloured
    for i in range(24):
        a = i / 24 * 2 * math.pi
        if i == 0:
            d.polygon([cv.polar(a, 0.835), cv.polar(a - 0.078, 0.965), cv.polar(a + 0.078, 0.965)], fill=WHITE)
        elif i % 2 == 0:
            p = cv.polar(a, 0.898)
            cv.text(p[0], p[1], str(i), FONT_BEZEL, 0.098, WHITE, track=0.08, rot=a)
        else:
            d.polygon(cv.xf([(-0.013, 0.865), (-0.013, 0.935), (0.013, 0.935), (0.013, 0.865)], a), fill=WHITE)
    # --- rehaut / dial
    cv.circle((c, c), 0.80, BLACK)
    cv.ring(0.80, 2, SILVER)
    # minute track
    for m in range(60):
        a = m / 60 * 2 * math.pi
        inner = 0.742 if m % 5 == 0 else 0.758
        d.line([cv.polar(a, inner), cv.polar(a, 0.783)], fill=WHITE, width=int((2 if m % 5 == 0 else 1) * SS))
    # hour markers: white-gold surrounds, Chromalight lume
    date_h = v["date"]
    batons = {6, 9} if date_h == 3 else {3, 6}
    for hh in range(12):
        a = hh / 12 * 2 * math.pi
        if hh == 0:
            d.polygon(cv.xf([(0, 0.535), (-0.095, 0.715), (0.095, 0.715)], a), fill=SILVER)
            d.polygon(cv.xf([(0, 0.565), (-0.068, 0.698), (0.068, 0.698)], a), fill=WHITE)
        elif hh == date_h:
            p = cv.polar(a, DATE_R)
            bw, bh = DATE_W * R, DATE_H * R
            d.rectangle([p[0] - bw / 2 - 2 * SS, p[1] - bh / 2 - 2 * SS, p[0] + bw / 2 + 2 * SS, p[1] + bh / 2 + 2 * SS], fill=SILVER)
            d.rectangle([p[0] - bw / 2, p[1] - bh / 2, p[0] + bw / 2, p[1] + bh / 2], fill=WHITE)
        elif hh in batons:
            d.polygon(cv.xf([(-0.048, 0.53), (-0.048, 0.72), (0.048, 0.72), (0.048, 0.53)], a), fill=SILVER)
            d.polygon(cv.xf([(-0.032, 0.545), (-0.032, 0.705), (0.032, 0.705), (0.032, 0.545)], a), fill=WHITE)
        else:
            p = cv.polar(a, 0.645)
            cv.circle(p, 0.07, SILVER)
            cv.circle(p, 0.055, WHITE)
    # --- dial print (12 o'clock): coronet, wordmark, OYSTER PERPETUAL DATE
    crown(cv, c, c - 0.505 * R, 0.19 * R, WHITE)
    cv.text(c, c - 0.285 * R, "ROLEX", FONT_LOGO, 0.088, WHITE, track=0.10, stretch=1.18)
    cv.text(c, c - 0.185 * R, "OYSTER PERPETUAL DATE", FONT_SMALL, 0.048, WHITE, track=0.12)
    # --- dial print (6 o'clock)
    cv.text(c, c + 0.205 * R, "GMT-MASTER II", FONT_MODEL, 0.072, v["model"], track=0.10)
    cv.text(c, c + 0.300 * R, "SUPERLATIVE CHRONOMETER", FONT_SMALL, 0.044, WHITE, track=0.12)
    cv.text(c, c + 0.365 * R, "OFFICIALLY CERTIFIED", FONT_SMALL, 0.044, WHITE, track=0.12)
    # SWISS ♛ MADE at the very bottom of the dial
    y = c + 0.765 * R
    cv.text(c - 0.105 * R, y, "SWISS", FONT_SMALL, 0.034, WHITE, track=0.1)
    crown(cv, c, y - 0.022 * R, 0.05 * R, WHITE)
    cv.text(c + 0.100 * R, y, "MADE", FONT_SMALL, 0.034, WHITE, track=0.1)
    # round mask
    out = cv.img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * SS, size * SS), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size * SS - 1, size * SS - 1], fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    bg = Image.new("RGB", (size, size), BLACK)
    bg.paste(out, (0, 0), mask)
    return bg


def render_digits(size):
    """Black date numerals on white, sized for the (cyclops-magnified) date window."""
    R = size / 2
    h = int(DATE_H * R)
    S = 8
    f = ImageFont.truetype(FONT_DATE, 10)
    # size font so digit height = 78% of window height
    target = h * S * 0.78
    fs = 10
    for _ in range(4):
        f = ImageFont.truetype(FONT_DATE, fs)
        b = f.getbbox("0")
        fs = max(6, int(fs * target / (b[3] - b[1])))
    f = ImageFont.truetype(FONT_DATE, fs)
    digits = []
    for n in range(10):
        b = f.getbbox(str(n))
        wpx = int(f.getlength("0") * 0.98)
        im = Image.new("RGB", (wpx, h * S), WHITE)
        dd = ImageDraw.Draw(im)
        bb = f.getbbox("0")
        dd.text(((wpx - (b[2] - b[0])) / 2 - b[0], (h * S - (bb[3] - bb[1])) / 2 - bb[1]), str(n), font=f, fill=BLACK)
        digits.append(im.resize((max(1, wpx // S), h), Image.LANCZOS))
    return digits


# ------------------------------------------------------------------ hands (preview only)
def draw_hands(img, v, hh, mm, ss, gmt_h, day, show_seconds=True):
    size = img.width
    cv = Canvas(size)
    cv.img = img.resize((size * SS, size * SS), Image.LANCZOS)
    cv.d = ImageDraw.Draw(cv.img)
    d, R = cv.d, cv.R
    tau = 2 * math.pi
    # date digits
    a_date = v["date"] / 12 * tau
    p = cv.polar(a_date, DATE_R)
    digs = [x.resize((x.width * SS, x.height * SS), Image.NEAREST) for x in render_digits(size)]
    s = str(day)
    tw = sum(digs[int(ch)].width for ch in s)
    x = p[0] - tw / 2
    for ch in s:
        im = digs[int(ch)]
        cv.img.paste(im, (int(x), int(p[1] - im.height / 2)))
        x += im.width
    aH = ((hh % 12) + mm / 60) / 12 * tau
    aM = (mm + ss / 60) / 60 * tau
    aG = gmt_h / 24 * tau
    aS = ss / 60 * tau
    poly = lambda pts, a, col: d.polygon(cv.xf(pts, a), fill=col)
    # hour hand (Mercedes)
    poly([(-0.032, -0.10), (-0.032, 0.34), (0.032, 0.34), (0.032, -0.10)], aH, SILVER)
    poly([(-0.018, 0.03), (-0.018, 0.33), (0.018, 0.33), (0.018, 0.03)], aH, WHITE)
    poly([(-0.048, 0.455), (0, 0.575), (0.048, 0.455)], aH, SILVER)
    poly([(-0.030, 0.47), (0, 0.548), (0.030, 0.47)], aH, WHITE)
    cc = cv.polar(aH, 0.40)
    cv.circle(cc, 0.085, SILVER); cv.circle(cc, 0.068, WHITE)
    for k in range(3):
        t = k * tau / 3
        dx, dy = math.sin(t), math.cos(t)
        px, py = dy, -dx
        L, w = 0.072, 0.009
        poly([(px * w, 0.40 + py * w), (dx * L + px * w, 0.40 + dy * L + py * w),
              (dx * L - px * w, 0.40 + dy * L - py * w), (-px * w, 0.40 - py * w)], aH, SILVER)
    cv.circle(cc, 0.016, SILVER)
    # GMT hand
    poly([(-0.012, -0.15), (-0.012, 0.65), (0.012, 0.65), (0.012, -0.15)], aG, v["gmt"])
    poly([(-0.072, 0.635), (0, 0.79), (0.072, 0.635)], aG, v["gmt"])
    poly([(-0.044, 0.658), (0, 0.748), (0.044, 0.658)], aG, WHITE)
    # minute hand
    poly([(-0.030, -0.12), (-0.030, 0.66), (0, 0.765), (0.030, 0.66), (0.030, -0.12)], aM, SILVER)
    poly([(-0.016, 0.06), (-0.016, 0.655), (0, 0.735), (0.016, 0.655), (0.016, 0.06)], aM, WHITE)
    if show_seconds:
        poly([(-0.008, -0.22), (-0.008, 0.775), (0.008, 0.775), (0.008, -0.22)], aS, SILVER)
        q = cv.polar(aS, 0.60)
        cv.circle(q, 0.046, SILVER); cv.circle(q, 0.034, WHITE)
    cv.circle((cv.c, cv.c), 0.042, SILVER)
    cv.circle((cv.c, cv.c), 0.018, STEEL)
    return cv.img.resize((size, size), Image.LANCZOS)


def mip(img):
    """Approximate the fenix 7 64-colour MIP palette."""
    q = lambda x: min(255, int(round(x / 85.0)) * 85)
    return img.point(q)


def main():
    for size in SIZES:
        out = os.path.join(ROOT, f"resources-round-{size}x{size}", "drawables")
        os.makedirs(out, exist_ok=True)
        xml = ["<drawables>"]
        for name, v in VARIANTS.items():
            render_background(size, v).save(os.path.join(out, f"bg_{name}.png"))
            xml.append(f'    <bitmap id="Bg{name.capitalize()}" filename="bg_{name}.png" dithering="none"/>')
        for n, im in enumerate(render_digits(size)):
            im.save(os.path.join(out, f"d{n}.png"))
            xml.append(f'    <bitmap id="D{n}" filename="d{n}.png" dithering="none"/>')
        xml.append("</drawables>\n")
        with open(os.path.join(out, "face.xml"), "w") as f:
            f.write("\n".join(xml))
    # previews
    tiles = []
    for name, v in VARIANTS.items():
        big = draw_hands(render_background(520, v), v, 10, 9, 32, 16.3, 9)
        tiles.append(big)
        if name == "pepsi":
            big.save(os.path.join(ROOT, "preview.png"))
            draw_hands(render_background(40, v), v, 10, 9, 0, 16.3, 9, False).save(
                os.path.join(ROOT, "resources", "drawables", "launcher_icon.png"))
    sheet = Image.new("RGB", (520 * 3 + 80, 560), (27, 27, 27))
    for i, t in enumerate(tiles):
        sheet.paste(t, (20 + i * 540, 20))
    sheet.save(os.path.join(ROOT, "preview_varianter.png"))
    # what the watch will actually show (fenix 7, 260 px, 64 colours)
    natives = [mip(draw_hands(render_background(260, v), v, 10, 9, 32, 16.3, 9)) for v in VARIANTS.values()]
    ns = Image.new("RGB", (260 * 3 + 40, 280), (27, 27, 27))
    for i, t in enumerate(natives):
        ns.paste(t, (10 + i * 270, 10))
    ns.save(os.path.join(ROOT, "preview_fenix7_faktisk.png"))


if __name__ == "__main__":
    main()
