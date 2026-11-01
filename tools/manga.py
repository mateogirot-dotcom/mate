"""Mika — version « style manga » pour comparer (1er nov. 2026). Personnage ORIGINAL du Studio.

Même moteur d'animation que tools/perso.py (Filou) : seul le dessin change.
Usage : python3 tools/manga.py plan.json sortie.mp4   (même plan.json que tools/prof.py)
"""
import math, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perso
from perso import S, CW, CH, P, ik, limb, blob

INK = (40, 26, 34)
SKIN = (255, 226, 206); SKIN_S = (246, 196, 176)
HAIR = (112, 60, 46); HAIR_D = (80, 40, 34); HAIR_L = (168, 98, 72)
IRIS_T = (60, 70, 170); IRIS_B = (120, 150, 235); WHITE = (255, 255, 255)
HOOD = (120, 200, 180); HOOD_D = (86, 160, 144); STAR = (255, 205, 60)
MOUTH = (150, 40, 60); TONGUE = (240, 120, 130)

def shape(d, pts, col, ow=8):
    d.polygon([P(*q) for q in pts], fill=col, outline=INK, width=ow * S)

def head(st, t):
    img = Image.new("RGBA", (perso.HW * S, perso.HH * S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    sway = 6 * math.sin(t * 2.1)                       # les cheveux suivent un peu le mouvement
    # cheveux arrière (carré)
    d.rounded_rectangle((*P(176, 250), *P(624, 560 + sway * 0.3)), 90 * S, fill=INK)
    d.rounded_rectangle((*P(186, 258), *P(614, 550 + sway * 0.3)), 84 * S, fill=HAIR_D)
    blob(d, (400, 300), 232, 210, HAIR_D)
    # visage
    face = [(226, 330), (228, 420), (262, 492), (330, 548), (400, 568), (470, 548), (538, 492), (572, 420), (574, 330)]
    blob(d, (400, 330), 176, 170, SKIN)
    shape(d, face, SKIN)
    d.ellipse((*P(230, 170), *P(570, 470)), fill=SKIN)
    # yeux manga
    lx, ly = st["look"]; es = st["eyes"]; cl = st["blink"]
    for side in (-1, 1):
        cx, cy = 400 + side * 82, 410
        rx, ry = 46 * es, 58 * es
        d.ellipse((*P(cx - rx, cy - ry), *P(cx + rx, cy + ry)), fill=WHITE)
        ix, iy = cx + lx * 0.8, cy + ly * 0.7 + 4
        d.ellipse((*P(ix - rx * 0.78, iy - ry * 0.86), *P(ix + rx * 0.78, iy + ry * 0.9)), fill=IRIS_T)
        d.ellipse((*P(ix - rx * 0.62, iy - ry * 0.1), *P(ix + rx * 0.62, iy + ry * 0.82)), fill=IRIS_B)
        d.ellipse((*P(ix - rx * 0.3, iy - ry * 0.3), *P(ix + rx * 0.3, iy + ry * 0.36)), fill=(26, 24, 60))
        d.ellipse((*P(ix - rx * 0.62, iy - ry * 0.7), *P(ix - rx * 0.62 + 30, iy - ry * 0.7 + 38)), fill=WHITE)
        d.ellipse((*P(ix + rx * 0.22, iy + ry * 0.3), *P(ix + rx * 0.22 + 13, iy + ry * 0.3 + 13)), fill=WHITE)
        d.ellipse((*P(ix - rx * 0.1, iy + ry * 0.55), *P(ix + rx * 0.3, iy + ry * 0.72)), fill=(200, 220, 255))
        if cl > 0.02:
            top = cy - ry - 6; bot = top + (2 * ry + 10) * cl
            d.rectangle((*P(cx - rx - 8, top - 12), *P(cx + rx + 8, bot)), fill=SKIN)
        lid = cy - ry + (2 * ry) * cl
        d.arc((*P(cx - rx - 6, lid - 16), *P(cx + rx + 6, lid + 30)), 195, 345, fill=INK, width=11 * S)   # cils du haut
        ox = cx + side * (rx + 2); d.line([P(ox, lid + 2), P(ox + side * 18, lid - 12)], fill=INK, width=8 * S)
        if cl < 0.9: d.arc((*P(cx - rx * 0.7, cy + ry - 14), *P(cx + rx * 0.7, cy + ry + 8)), 30, 150, fill=INK, width=4 * S)
        b = st["brow"]; up = max(0, -b) + (b * 1.4 if (b > 0 and side == 1) else 0)
        by_ = cy - ry - 30 - up
        d.arc((*P(cx - 34, by_ - 4), *P(cx + 34, by_ + 20)), 205, 335, fill=HAIR_D, width=6 * S)
    # joues (traits roses façon manga)
    for side in (-1, 1):
        bl = Image.new("RGBA", img.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(bl)
        bd.ellipse((*P(400 + side * 140 - 40, 476), *P(400 + side * 140 + 40, 506)), fill=(255, 150, 160, 110))
        for k in range(3):
            x = 400 + side * 140 - 22 + k * 16; bd.line([P(x + 8, 480), P(x - 2, 502)], fill=(235, 110, 130, 200), width=4 * S)
        img.alpha_composite(bl); d = ImageDraw.Draw(img)
    d.line([P(404, 470), P(398, 480)], fill=SKIN_S, width=5 * S)                    # petit nez
    o = st["mouth"]
    if o < 0.08:
        d.arc((*P(378, 498), *P(422, 520)), 20, 160, fill=INK, width=5 * S)
    else:
        w = 16 + 14 * o; h = 8 + 34 * o; y = 506
        d.polygon([P(400 - w - 4, y - 4), P(400 + w + 4, y - 4), P(400 + w * 0.5, y + h + 4), P(400 - w * 0.5, y + h + 4)], fill=INK)
        d.polygon([P(400 - w, y), P(400 + w, y), P(400 + w * 0.48, y + h), P(400 - w * 0.48, y + h)], fill=MOUTH)
        if o > 0.35: d.ellipse((*P(400 - w * 0.45, y + h * 0.45), *P(400 + w * 0.45, y + h * 1.05)), fill=TONGUE)
    # frange (mèches) + mèches sur les côtés
    bangs = [(206, 330), (218, 210), (300, 132), (400, 112), (500, 132), (582, 210), (594, 330),
             (560, 300), (540, 250), (520, 318), (486, 236), (456, 330), (430, 226), (396, 318), (370, 230), (338, 312), (318, 240), (290, 318), (262, 250), (238, 320)]
    shape(d, bangs, HAIR)
    for side in (-1, 1):
        lock = [(400 + side * 160, 260), (400 + side * 196, 300), (400 + side * 206, 470 + sway), (400 + side * 186, 560 + sway), (400 + side * 168, 470)]
        shape(d, lock, HAIR)
    d.arc((*P(270, 140), *P(530, 260)), 200, 290, fill=HAIR_L, width=12 * S)        # reflet des cheveux
    # barrette étoile
    cx, cy = 548, 236; pts = []
    for k in range(10):
        r = 30 if k % 2 == 0 else 13; a = -math.pi / 2 + k * math.pi / 5
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    shape(d, pts, STAR, 6)
    return img

def draw(st, t):
    img = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    jy = -st["jump"]; br = math.sin(t * 2 * math.pi / 2.6)
    sq = st["squash"]
    # sweat à capuche
    body = [(236, 660 + jy), (564, 660 + jy), (640 + 10 * sq, 1010), (160 - 10 * sq, 1010)]
    d.polygon([P(*q) for q in body], fill=HOOD, outline=INK, width=10 * S)
    d.rounded_rectangle((*P(300, 840 + jy), *P(500, 940 + jy)), 30 * S, fill=HOOD_D, outline=INK, width=6 * S)   # poche
    d.chord((*P(286, 600 + jy), *P(514, 720 + jy)), 0, 180, fill=INK)            # capuche autour du cou
    d.chord((*P(296, 606 + jy), *P(504, 710 + jy)), 0, 180, fill=HOOD_D)
    for x in (372, 428): d.line([P(x, 690 + jy), P(x + (x - 400) * 0.1, 790 + jy + 4 * br)], fill=WHITE, width=6 * S)
    limb(d, [(400, 560 + jy), (400, 640 + jy)], 64, SKIN)                             # cou
    hd = head(st, t).rotate(-st["tilt"], resample=Image.BICUBIC, center=(400 * S, 600 * S))
    img.alpha_composite(hd, (0, int((jy + 50 + 3 * br - 3 * st["mouth"]) * S)))
    d = ImageDraw.Draw(img)
    for side, key, sh in ((-1, "L", (262, 690 + jy)), (1, "R", (538, 690 + jy))):
        tg = st[key]; tg = (tg[0], tg[1] + jy)
        el, hand = ik(sh, tg, side=(1 if side < 0 else -1))
        limb(d, [sh, el, hand], 56, HOOD)
        blob(d, hand, 28, 28, SKIN, 8)
    return img.reduce(S)

if __name__ == "__main__":
    perso.draw = draw
    perso.main(sys.argv[1], sys.argv[2])
