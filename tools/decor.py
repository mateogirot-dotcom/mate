"""Décors « attractifs » du Studio @reyzinhoia (demande de l'utilisateur du 26 oct. 2026).
Fabrique des écrans PNG 1080x1920 prêts pour tools/assembler.py.

from decor import ecran
ecran("question", "Un commerçant peut refuser tes {pièces} ?", "q.png", compteur="1/5", icone="🪙")
Types : "question", "decompte" (texte = "3"/"2"/"1"), "vrai", "faux", "explication", "fin", "chiffre".
Mettre un mot entre {accolades} le surligne en jaune (le MOT-CLÉ de recherche, à faire dès le 1er écran).
icone : un petit dessin simple facultatif parmi ICONES (dessiné en formes, aucune marque).
Polices libres (licence OFL) dans fonts/ : Anton (titres), Montserrat (texte).
INTERDIT dans le décor : logo, marque, badge IA, « Voix de synthèse », écran Sources, « n°X » en haut.
"""
import os, math, random, re
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H = 1080, 1920
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANTON = os.path.join(ROOT, "fonts", "Anton-Regular.ttf")
MONT = os.path.join(ROOT, "fonts", "Montserrat-VF.ttf")
PAL = {  # dégradé haut -> bas, couleur des bulles, accent
  "question":    ("#2b2d8f", "#7b2ff7", "#ffd23f"),
  "decompte":    ("#14163d", "#3a1c71", "#ffd23f"),
  "vrai":        ("#0f9d58", "#00c9a7", "#ffffff"),
  "faux":        ("#e5484d", "#ff8a3d", "#ffffff"),
  "explication": ("#5b2a86", "#d6457e", "#ffd23f"),
  "chiffre":     ("#0b4f9c", "#1fa2ff", "#ffd23f"),
  "fin":         ("#ff7a18", "#ffb300", "#14163d"),
}
def _hex(c): c = c.lstrip("#"); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
def _font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f
def _fond(kind, seed):
    a, b, acc = PAL[kind]; A, B = _hex(a), _hex(b)
    g = Image.new("RGB", (W, H))
    px = g.load()
    for y in range(H):
        t = y/(H-1); col = tuple(int(A[i]*(1-t)+B[i]*t) for i in range(3))
        for x in range(0, W): px[x, y] = col
    rnd = random.Random(seed)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(halo)
    for _ in range(9):                                   # grosses bulles lumineuses floues
        r = rnd.randint(140, 360); x = rnd.randint(-100, W+100); y = rnd.randint(-100, H+100)
        d.ellipse((x-r, y-r, x+r, y+r), fill=(255, 255, 255, rnd.randint(18, 40)))
    halo = halo.filter(ImageFilter.GaussianBlur(60))
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d2 = ImageDraw.Draw(rays)   # rayons doux depuis le haut
    for k in range(12):
        ang = -math.pi/2 + (k-5.5)*0.16
        d2.polygon([(W/2, -200), (W/2+2400*math.cos(ang-0.035), -200+2400*math.sin(ang+math.pi)*-1),
                    (W/2+2400*math.cos(ang+0.035), -200+2400*math.sin(ang+math.pi)*-1)], fill=(255, 255, 255, 10 if k % 2 else 0))
    rays = rays.filter(ImageFilter.GaussianBlur(8))
    sp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d3 = ImageDraw.Draw(sp)       # petites étincelles
    for _ in range(60):
        x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.choice([2, 2, 3, 4])
        d3.ellipse((x-r, y-r, x+r, y+r), fill=(255, 255, 255, rnd.randint(60, 160)))
    img = g.convert("RGBA"); img.alpha_composite(rays); img.alpha_composite(halo); img.alpha_composite(sp)
    vg = Image.new("L", (W, H), 0); dv = ImageDraw.Draw(vg); dv.ellipse((-300, -200, W+300, H+200), fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(160)); dark = Image.new("RGBA", (W, H), (0, 0, 0, 90))
    img = Image.composite(img, Image.alpha_composite(img, dark), vg)
    return img, _hex(acc)
def _propre(t):  # retire les émojis (non affichables avec ces polices)
    return "".join(ch for ch in t if ord(ch) < 0x2190 or ch in "€").replace("  ", " ").strip()
def _wrap(d, txt, font, maxw):
    words, lines, cur = [w for w in txt.split(" ") if w], [], ""
    for w in words:
        t = (cur+" "+w).strip()
        if d.textlength(t.replace("{", "").replace("}", ""), font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines
def _texte(img, txt, y0, size, maxw, color=(20, 22, 61), carte=True, centre=True):
    txt = re.sub(r"\{[^}]*\}", lambda m: m.group(0).replace(" ", "\u00a0"), _propre(txt)); d = ImageDraw.Draw(img)
    for s in range(size, 40, -4):
        f = _font(MONT, s, 800); lines = _wrap(d, txt, f, maxw)
        if len(lines) <= 6: break
    lh = int(s*1.22); th = lh*len(lines)
    if carte:
        pad = 54; x0, x1 = (W-maxw)//2-pad, (W+maxw)//2+pad
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
        ds.rounded_rectangle((x0+10, y0-pad+22, x1+10, y0+th+pad+22), 48, fill=(0, 0, 0, 110))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
        ImageDraw.Draw(img).rounded_rectangle((x0, y0-pad, x1, y0+th+pad), 48, fill=(255, 255, 255, 245))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        parts = re.split(r"(\{[^}]*\})", line); plain = line.replace("{", "").replace("}", "")
        x = (W-d.textlength(plain, font=f))/2 if centre else (W-maxw)/2; y = y0+i*lh
        for p in parts:
            if not p: continue
            hl = p.startswith("{"); p = p.strip("{}"); w = d.textlength(p, font=f)
            if hl: d.rounded_rectangle((x-8, y+s*0.12, x+w+8, y+s*1.12), 14, fill=(255, 210, 63))
            d.text((x, y), p, font=f, fill=color); x += w
    return y0+th
def _gros(img, txt, cy, size, fill, stroke=(20, 22, 61), angle=0):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    while True:
        f = _font(ANTON, size); w = d.textlength(txt, font=f)
        if w <= 960 or size < 60: break
        size -= 10
    d.text(((W-w)/2+8, cy-size*0.62+12), txt, font=f, fill=(0, 0, 0, 120))
    d.text(((W-w)/2, cy-size*0.62), txt, font=f, fill=fill, stroke_width=max(4, size//28), stroke_fill=stroke)
    if angle: lay = lay.rotate(angle, center=(W/2, cy), resample=Image.BICUBIC)
    img.alpha_composite(lay)
ICONES = ("piece", "carte", "cheque", "cerveau", "os", "globe", "horloge", "ampoule", "billet", "livre")
def _icone(img, nom, cx, cy, r=150):
    d = ImageDraw.Draw(img); ink = (20, 22, 61); gold = (255, 210, 63); wht = (255, 255, 255)
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(halo).ellipse((cx-r*1.5, cy-r*1.5, cx+r*1.5, cy+r*1.5), fill=(255, 255, 255, 70))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(40))); d = ImageDraw.Draw(img); lw = 10
    if nom == "piece":
        for k, dx in enumerate((-70, 70, 0)):
            d.ellipse((cx+dx-r*0.7, cy-r*0.7+(k == 2)*-30, cx+dx+r*0.7, cy+r*0.7+(k == 2)*-30), fill=gold, outline=ink, width=lw)
            d.ellipse((cx+dx-r*0.48, cy-r*0.48+(k == 2)*-30, cx+dx+r*0.48, cy+r*0.48+(k == 2)*-30), outline=(214, 160, 20), width=8)
    elif nom == "carte":
        d.rounded_rectangle((cx-r*1.3, cy-r*0.8, cx+r*1.3, cy+r*0.8), 30, fill=(80, 90, 150), outline=ink, width=lw)
        d.rounded_rectangle((cx-r*1.0, cy-r*0.45, cx-r*0.5, cy-r*0.05), 10, fill=gold, outline=ink, width=6)
        for i in range(4): d.rounded_rectangle((cx-r*1.0+i*r*0.55, cy+r*0.3, cx-r*0.6+i*r*0.55, cy+r*0.42), 6, fill=wht)
    elif nom in ("cheque", "billet"):
        d.rounded_rectangle((cx-r*1.4, cy-r*0.7, cx+r*1.4, cy+r*0.7), 22, fill=(250, 246, 230) if nom == "cheque" else (120, 200, 140), outline=ink, width=lw)
        for i in range(3): d.line((cx-r*1.1, cy-r*0.25+i*r*0.25, cx+r*0.4, cy-r*0.25+i*r*0.25), fill=ink, width=8)
        d.rounded_rectangle((cx+r*0.6, cy-r*0.45, cx+r*1.15, cy-r*0.1), 8, outline=ink, width=6)
    elif nom == "horloge":
        d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=wht, outline=ink, width=lw); d.line((cx, cy, cx, cy-r*0.65), fill=ink, width=12); d.line((cx, cy, cx+r*0.45, cy+r*0.2), fill=ink, width=12)
    elif nom == "ampoule":
        d.ellipse((cx-r*0.8, cy-r, cx+r*0.8, cy+r*0.5), fill=gold, outline=ink, width=lw); d.rectangle((cx-r*0.35, cy+r*0.45, cx+r*0.35, cy+r*0.9), fill=(200, 200, 210), outline=ink, width=8)
    elif nom == "globe":
        d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(70, 150, 240), outline=ink, width=lw)
        d.ellipse((cx-r*0.6, cy-r*0.7, cx+r*0.1, cy-r*0.1), fill=(90, 200, 120)); d.ellipse((cx+r*0.1, cy+r*0.1, cx+r*0.7, cy+r*0.6), fill=(90, 200, 120))
    elif nom == "livre":
        d.polygon([(cx, cy-r*0.6), (cx-r*1.3, cy-r*0.8), (cx-r*1.3, cy+r*0.7), (cx, cy+r*0.9)], fill=wht, outline=ink); d.polygon([(cx, cy-r*0.6), (cx+r*1.3, cy-r*0.8), (cx+r*1.3, cy+r*0.7), (cx, cy+r*0.9)], fill=wht, outline=ink)
    elif nom in ("cerveau", "os"):
        d.ellipse((cx-r*1.1, cy-r*0.8, cx+r*1.1, cy+r*0.8), fill=(255, 160, 190) if nom == "cerveau" else wht, outline=ink, width=lw)
def ecran(kind, texte, out, compteur=None, icone=None, seed=None):
    img, acc = _fond(kind, seed if seed is not None else hash(texte) & 0xffff)
    d = ImageDraw.Draw(img)
    if compteur:   # petit compteur discret en bas (pas de badge en haut)
        f = _font(MONT, 44, 800); w = d.textlength(compteur, font=f)
        d.rounded_rectangle(((W-w)/2-30, 1420, (W+w)/2+30, 1496), 38, fill=(20, 22, 61)); d.text(((W-w)/2, 1428), compteur, font=f, fill=(255, 210, 63))
    if kind == "decompte":
        cy = 960; R = 260
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((W/2-R-40, cy-R-40, W/2+R+40, cy+R+40), outline=(255, 210, 63, 200), width=40)
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30))); d = ImageDraw.Draw(img)
        d.ellipse((W/2-R, cy-R, W/2+R, cy+R), outline=(255, 210, 63), width=22)
        _gros(img, texte, cy+20, 380, (255, 255, 255))
    elif kind in ("vrai", "faux"):
        _gros(img, "VRAI !" if kind == "vrai" else "FAUX !", 520, 260, (255, 255, 255), angle=-6)
        if texte: _texte(img, texte, 860, 76, 860)
    elif kind == "chiffre":
        if icone: _icone(img, icone, W//2, 420)
        _gros(img, texte.split("|")[0], 860, 210, acc)
        if "|" in texte: _texte(img, texte.split("|")[1], 1120, 72, 860)
    elif kind == "fin":
        _gros(img, "ET TOI ?", 520, 230, (255, 255, 255), angle=-4)
        _texte(img, texte, 860, 80, 860)
    else:  # question, explication
        if icone: _icone(img, icone, W//2, 470)
        _texte(img, texte, 860 if icone else 720, 92 if kind == "question" else 76, 880)
    img.convert("RGB").save(out)
    return out
