"""Render a PNG preview of the watch face (mirrors source/GMTView.mc geometry)."""
import math, sys
from PIL import Image, ImageDraw, ImageFont
from brand_assets import make_blocks

S = 4  # supersampling

def render(size=260, style=0, h=10, m=10, s=32, gmt_h=15.5, day=9):
    W = size * S
    R = W / 2; cx = cy = R
    img = Image.new("RGB", (W, W), "black"); d = ImageDraw.Draw(img)
    cols = {0: ("#0055AA", "#AA0000", "#AA0000"), 1: ("#AA0000", "#0055AA", "#AA0000"),
            2: ("#000000", "#0055AA", "#0055AA"), 3: ("#000000", "#AA0000", "#AA0000"),
            4: ("#00AA00", "#000000", "#00AA00")}[style]
    def polar(a, f): return (cx + R*f*math.sin(a), cy - R*f*math.cos(a))
    def xf(pts, a):
        sn, cs = math.sin(a), math.cos(a)
        return [(cx + y*R*sn + x*R*cs, cy - y*R*cs + x*R*sn) for x, y in pts]
    def circ(c, r, fill): d.ellipse([c[0]-r, c[1]-r, c[0]+r, c[1]+r], fill=fill)
    def poly(p, fill, edge=None): d.polygon(p, fill=fill, outline=edge, width=S if edge else 0)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", int(R*0.115))
        sfont = ImageFont.truetype("DejaVuSans.ttf", int(R*0.075))
    except OSError:
        font = sfont = ImageFont.load_default()
    # bezel
    d.pieslice([0, 0, W, W], 180, 360, fill=cols[0]); d.pieslice([0, 0, W, W], 0, 180, fill=cols[1])
    d.ellipse([S, S, W-S, W-S], outline="#AAAAAA", width=2*S)
    for i in range(24):
        a = i/24*2*math.pi
        if i == 0: poly([polar(a, .835), polar(a-.075, .975), polar(a+.075, .975)], "white")
        elif i % 2 == 0: d.text(polar(a, .90), str(i), font=font, fill="white", anchor="mm")
        else: poly(xf([(-.012, .86), (-.012, .95), (.012, .95), (.012, .86)], a), "white")
    circ((cx, cy), R*.80, "black"); d.ellipse([cx-R*.8, cy-R*.8, cx+R*.8, cy+R*.8], outline="#AAAAAA", width=2*S)
    for k in range(60):
        a = k/60*2*math.pi; inner = .735 if k % 5 == 0 else .755
        d.line([polar(a, inner), polar(a, .785)], fill="white", width=(2 if k % 5 == 0 else 1)*S)
    for hh in range(12):
        a = hh/12*2*math.pi
        if hh == 0: poly(xf([(0, .55), (-.085, .715), (.085, .715)], a), "white", "#AAAAAA")
        elif hh == 3:
            x, y, bw, bh = cx+R*.63, cy, R*.25, R*.17
            d.rectangle([x-bw/2-2*S, y-bh/2-2*S, x+bw/2+2*S, y+bh/2+2*S], fill="#AAAAAA")
            d.rectangle([x-bw/2, y-bh/2, x+bw/2, y+bh/2], fill="white")
            d.text((x, y), str(day), font=font, fill="black", anchor="mm")
        elif hh in (6, 9): poly(xf([(-.04, .54), (-.04, .715), (.04, .715), (.04, .54)], a), "white", "#AAAAAA")
        else:
            p = polar(a, .645); circ(p, R*.068, "#AAAAAA"); circ(p, R*.055, "white")
    t, b = make_blocks(size)
    t = t.resize((t.width*S, t.height*S), Image.LANCZOS); b = b.resize((b.width*S, b.height*S), Image.LANCZOS)
    img.paste(t, (int(cx - t.width/2), int(cy - R*.53)), t); img.paste(b, (int(cx - b.width/2), int(cy + R*.165)), b)
    # hands
    aH = ((h % 12) + m/60)/12*2*math.pi; aM = (m + s/60)/60*2*math.pi; aG = gmt_h/24*2*math.pi; aS = s/60*2*math.pi
    poly(xf([(-.035, -.10), (-.035, .36), (.035, .36), (.035, -.10)], aH), "white", "#555555")
    poly(xf([(-.05, .48), (0, .585), (.05, .48)], aH), "white", "#555555")
    c = polar(aH, .42); circ(c, R*.088, "#AAAAAA"); circ(c, R*.076, "white"); circ(c, R*.056, "black")
    for k in range(3):
        t = k*2*math.pi/3; dx, dy = math.sin(t), math.cos(t); px, py = dy, -dx; L, w = .058, .012
        poly(xf([(px*w, .42+py*w), (dx*L+px*w, .42+dy*L+py*w), (dx*L-px*w, .42+dy*L-py*w), (-px*w, .42-py*w)], aH), "white")
    circ(c, R*.016, "white")
    poly(xf([(-.013, -.12), (-.013, .66), (.013, .66), (.013, -.12)], aG), cols[2])
    poly(xf([(-.075, .645), (0, .80), (.075, .645)], aG), cols[2], "#AAAAAA")
    poly(xf([(-.04, .67), (0, .75), (.04, .67)], aG), "white")
    poly(xf([(-.032, -.12), (-.032, .66), (0, .76), (.032, .66), (.032, -.12)], aM), "white", "#555555")
    poly(xf([(-.009, -.20), (-.009, .76), (.009, .76), (.009, -.20)], aS), "white", "#555555")
    p = polar(aS, .56); circ(p, R*.045, "#AAAAAA"); circ(p, R*.035, "white")
    circ((cx, cy), R*.045, "#AAAAAA"); circ((cx, cy), R*.025, "white")
    # round mask
    mask = Image.new("L", (W, W), 0); ImageDraw.Draw(mask).ellipse([0, 0, W, W], fill=255)
    bg = Image.new("RGB", (W, W), "#1b1b1b"); bg.paste(img, (0, 0), mask)
    return bg.resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "preview.png"
    names = ["Pepsi", "Pepsi omvendt", "Batman", "Coke", "Sprite"]
    tiles = [render(520, st) for st in range(5)]
    sheet = Image.new("RGB", (520*3 + 80, 520*2 + 60), "#1b1b1b")
    for i, t in enumerate(tiles[:3]): sheet.paste(t, (20 + i*540, 20))
    for i, t in enumerate(tiles[3:]): sheet.paste(t, (290 + i*540, 560))
    tiles[0].save(out)
    sheet.save(out.replace(".png", "_varianter.png"))
    render(40, 0, s=0).save(sys.argv[2] if len(sys.argv) > 2 else "launcher_icon.png")
