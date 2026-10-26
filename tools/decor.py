"""Décors du Studio @reyzinhoia — style « Archive lumineuse » (voir tools/PHILOSOPHIE-DECOR.md).
Méthode « canvas-design » demandée par l'utilisateur le 26 oct. 2026. Écrans PNG 1080x1920 pour tools/assembler.py.

    import sys; sys.path.insert(0, "tools"); from decor import ecran
    ecran("question", "Un {commerçant} peut-il refuser tes pièces ?", "q.png", icone="piece", compteur="1/5")

Types : "question", "decompte" ("3"/"2"/"1"), "vrai", "faux", "explication", "chiffre" ("GROS|phrase"), "fin".
{accolades} = MOT-CLÉ surligné en jaune. Icônes : piece, carte, cheque, billet, cerveau, os, globe, horloge, ampoule, livre.
Polices libres (OFL) dans fonts/. INTERDIT : logo, marque, badge IA, « Voix de synthèse », écran Sources, « n°X » en haut.
"""
import os, math, random, re
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
W, H = 1080, 1920
FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
BIG = os.path.join(FD, "Boldonse-Regular.ttf"); TXT = os.path.join(FD, "BricolageGrotesque-Bold.ttf")
MONO = os.path.join(FD, "GeistMono-Regular.ttf")
INK = (18, 21, 52); CREAM = (244, 239, 227); SIGNAL = (255, 206, 46)
FIELD = {"question": ((22, 26, 74), (108, 72, 220)), "decompte": ((12, 14, 40), (70, 52, 160)),
         "vrai": ((6, 92, 66), (40, 200, 140)), "faux": ((150, 32, 34), (255, 110, 70)),
         "explication": ((52, 24, 78), (200, 70, 140)), "chiffre": ((14, 52, 140), (60, 160, 255)),
         "fin": ((236, 150, 18), (255, 214, 90))}
LABEL = {"question": "VRAI OU FAUX ?", "decompte": "RÉFLÉCHIS", "vrai": "VERDICT", "faux": "VERDICT",
         "explication": "OBSERVATION", "chiffre": "MESURE", "fin": "À TOI"}
F = lambda p, s: ImageFont.truetype(p, s)

def _propre(t): return "".join(ch for ch in t if ord(ch) < 0x2190 or ch == "€").replace("  ", " ").strip()

def _fond(kind, seed):
    base, glow = FIELD[kind]; rnd = random.Random(seed)
    img = Image.new("RGBA", (W, H), base + (255,))
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(halo)
    d.ellipse((W/2-760, 560-760, W/2+760, 560+760), fill=glow + (150,))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(220)))
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lines)
    for x in range(0, W+1, 90): d.line((x, 0, x, H), fill=(255, 255, 255, 14), width=1)        # grille d'observation
    for y in range(0, H+1, 90): d.line((0, y, W, y), fill=(255, 255, 255, 14), width=1)
    for r in range(260, 1300, 120): d.ellipse((W/2-r, 560-r, W/2+r, 560+r), outline=(255, 255, 255, 18), width=2)  # anneaux
    img.alpha_composite(lines)
    m = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(m); c = (255, 255, 255, 120)
    for (x, y) in ((70, 70), (W-70, 70), (70, H-70), (W-70, H-70)):                                  # repères de calage
        d.line((x-22, y, x+22, y), fill=c, width=3); d.line((x, y-22, x, y+22), fill=c, width=3); d.ellipse((x-9, y-9, x+9, y+9), outline=c, width=2)
    # (aucun texte en haut de l'écran : demande de l'utilisateur)
    img.alpha_composite(m)
    noise = Image.effect_noise((W//2, H//2), 40).resize((W, H)).convert("L")                         # grain papier
    gr = Image.new("RGBA", (W, H), (255, 255, 255, 0)); gr.putalpha(noise.point(lambda v: max(0, v-128)//10))
    img.alpha_composite(gr)
    vg = Image.new("L", (W, H), 0); ImageDraw.Draw(vg).ellipse((-260, -160, W+260, H+160), fill=255)
    img = Image.composite(img, Image.alpha_composite(img, Image.new("RGBA", (W, H), (0, 0, 0, 110))), vg.filter(ImageFilter.GaussianBlur(170)))
    return img

def _wrap(d, txt, font, maxw):
    words, lines, cur = [w for w in txt.split(" ") if w], [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t.replace("{", "").replace("}", ""), font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def _cartel(img, txt, y0, size, maxw=840):
    """Étiquette crème au double filet (cartel de musée), mot-clé surligné."""
    txt = re.sub(r"\{[^}]*\}", lambda m: m.group(0).replace(" ", " "), _propre(txt)); d = ImageDraw.Draw(img)
    for s in range(size, 40, -4):
        f = F(TXT, s); lines = _wrap(d, txt, f, maxw)
        if len(lines) <= 5: break
    lh = int(s*1.18); th = lh*len(lines); pad = 58
    x0, x1, y1 = (W-maxw)//2-pad, (W+maxw)//2+pad, y0+th+pad
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((x0+14, y0-pad+18, x1+14, y1+18), fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18))); d = ImageDraw.Draw(img)
    d.rectangle((x0, y0-pad, x1, y1), fill=CREAM)
    d.rectangle((x0+14, y0-pad+14, x1-14, y1-14), outline=INK, width=3); d.rectangle((x0+22, y0-pad+22, x1-22, y1-22), outline=INK, width=1)
    for i, line in enumerate(lines):
        plain = line.replace("{", "").replace("}", ""); x = (W - d.textlength(plain, font=f))/2; y = y0 + i*lh
        for p in re.split(r"(\{[^}]*\})", line):
            if not p: continue
            hl = p.startswith("{"); p = p.strip("{}"); w = d.textlength(p, font=f)
            if hl: d.rectangle((x-6, y+s*0.55, x+w+6, y+s*1.02), fill=SIGNAL)
            d.text((x, y), p, font=f, fill=INK); x += w
    return y1

def _monument(img, txt, cy, size, fill=CREAM, shadow=SIGNAL, angle=0, maxw=940):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    while True:
        f = F(BIG, size); bb = d.textbbox((0, 0), txt, font=f); w, h = bb[2]-bb[0], bb[3]-bb[1]
        if w <= maxw or size < 50: break
        size -= 8
    x, y = (W-w)/2-bb[0], cy-h/2-bb[1]
    d.text((x+12, y+12), txt, font=f, fill=shadow)          # second passage mal calé (risographie)
    d.text((x, y), txt, font=f, fill=fill)
    if angle: lay = lay.rotate(angle, center=(W/2, cy), resample=Image.BICUBIC)
    img.alpha_composite(lay)

def _cadran(img, cy, r):
    d = ImageDraw.Draw(img)
    for k in range(60):                                        # graduations d'instrument
        a = k/60*2*math.pi - math.pi/2; l = 34 if k % 5 == 0 else 16; w = 5 if k % 5 == 0 else 2
        d.line((W/2+math.cos(a)*(r-l), cy+math.sin(a)*(r-l), W/2+math.cos(a)*r, cy+math.sin(a)*r), fill=CREAM, width=w)
    d.ellipse((W/2-r-18, cy-r-18, W/2+r+18, cy+r+18), outline=SIGNAL, width=6)

ICONES = ("piece", "carte", "cheque", "billet", "cerveau", "os", "globe", "horloge", "ampoule", "livre")
def _specimen(img, nom, cx, cy, r=170):
    d = ImageDraw.Draw(img)
    d.ellipse((cx-r-40, cy-r-40, cx+r+40, cy+r+40), outline=(255, 255, 255, 90), width=2)
    for k in range(36):
        a = k/36*2*math.pi; d.line((cx+math.cos(a)*(r+40), cy+math.sin(a)*(r+40), cx+math.cos(a)*(r+54), cy+math.sin(a)*(r+54)), fill=(255, 255, 255, 120), width=2)
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=CREAM, outline=INK, width=6)
    s = r*0.62; lw = 9; gold = SIGNAL
    if nom == "piece":
        for dx, dy in ((-s*0.45, s*0.18), (s*0.45, s*0.18), (0, -s*0.25)):
            d.ellipse((cx+dx-s*0.55, cy+dy-s*0.55, cx+dx+s*0.55, cy+dy+s*0.55), fill=gold, outline=INK, width=lw)
            d.ellipse((cx+dx-s*0.33, cy+dy-s*0.33, cx+dx+s*0.33, cy+dy+s*0.33), outline=INK, width=4)
    elif nom == "carte":
        d.rounded_rectangle((cx-s*1.1, cy-s*0.68, cx+s*1.1, cy+s*0.68), 18, fill=(60, 80, 170), outline=INK, width=lw)
        d.rounded_rectangle((cx-s*0.8, cy-s*0.32, cx-s*0.35, cy+s*0.05), 8, fill=gold, outline=INK, width=5)
    elif nom in ("cheque", "billet"):
        d.rectangle((cx-s*1.15, cy-s*0.6, cx+s*1.15, cy+s*0.6), fill=CREAM if nom == "cheque" else (120, 200, 140), outline=INK, width=lw)
        for i in range(3): d.line((cx-s*0.9, cy-s*0.2+i*s*0.22, cx+s*0.3, cy-s*0.2+i*s*0.22), fill=INK, width=6)
    elif nom == "horloge":
        d.ellipse((cx-s, cy-s, cx+s, cy+s), outline=INK, width=lw); d.line((cx, cy, cx, cy-s*0.7), fill=INK, width=10); d.line((cx, cy, cx+s*0.5, cy+s*0.2), fill=INK, width=10)
    elif nom == "ampoule":
        d.ellipse((cx-s*0.7, cy-s*0.95, cx+s*0.7, cy+s*0.4), fill=gold, outline=INK, width=lw); d.rectangle((cx-s*0.3, cy+s*0.4, cx+s*0.3, cy+s*0.8), fill=(190, 190, 200), outline=INK, width=6)
    elif nom == "globe":
        d.ellipse((cx-s, cy-s, cx+s, cy+s), fill=(70, 140, 230), outline=INK, width=lw); d.ellipse((cx-s*0.6, cy-s*0.6, cx+s*0.1, cy-s*0.05), fill=(90, 190, 120)); d.ellipse((cx+s*0.1, cy+s*0.1, cx+s*0.65, cy+s*0.6), fill=(90, 190, 120))
    elif nom == "livre":
        d.polygon([(cx, cy-s*0.5), (cx-s*1.1, cy-s*0.7), (cx-s*1.1, cy+s*0.6), (cx, cy+s*0.8)], fill=(255, 255, 255), outline=INK); d.polygon([(cx, cy-s*0.5), (cx+s*1.1, cy-s*0.7), (cx+s*1.1, cy+s*0.6), (cx, cy+s*0.8)], fill=(255, 255, 255), outline=INK)
    else:
        d.ellipse((cx-s*0.95, cy-s*0.7, cx+s*0.95, cy+s*0.7), fill=(255, 170, 195) if nom == "cerveau" else (255, 255, 255), outline=INK, width=lw)

def ecran(kind, texte, out, compteur=None, icone=None, seed=None):
    img = _fond(kind, seed if seed is not None else hash((kind, texte)) & 0xffff)
    if compteur:
        d = ImageDraw.Draw(img); f = F(MONO, 40); w = d.textlength(compteur, font=f)
        d.rectangle(((W-w)/2-28, 1430, (W+w)/2+28, 1500), fill=INK, outline=SIGNAL, width=3); d.text(((W-w)/2, 1442), compteur, font=f, fill=SIGNAL)
    if kind == "decompte":
        _cadran(img, 900, 330); _monument(img, texte, 900, 400, fill=CREAM, shadow=SIGNAL)
    elif kind in ("vrai", "faux"):
        _monument(img, "VRAI" if kind == "vrai" else "FAUX", 520, 230, angle=-4)
        if texte: _cartel(img, texte, 860, 76)
    elif kind == "chiffre":
        if icone: _specimen(img, icone, W//2, 470, 150)
        big, _, small = texte.partition("|"); _monument(img, big, 820, 160, fill=CREAM, shadow=SIGNAL)
        if small: _cartel(img, small, 1030, 70)
    elif kind == "fin":
        _monument(img, "ET TOI ?", 540, 200, fill=INK, shadow=CREAM, angle=-3)
        _cartel(img, texte, 860, 80)
    else:
        if icone: _specimen(img, icone, W//2, 520)
        _cartel(img, texte, 860 if icone else 720, 92 if kind == "question" else 76)
    img.convert("RGB").save(out); return out
