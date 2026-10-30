"""Le Prof Marius — vidéos « on t'apprend un truc » du Studio @reyzinhoia (format validé le 30 oct. 2026).

Un prof dessiné (personnage ORIGINAL du Studio) explique face caméra : sa bouche suit la voix, il cligne des
yeux, fait des gestes, montre le tableau. En haut, le « tableau » montre l'idée de chaque scène (style
« Archive lumineuse » de tools/decor.py). Interactif : question au spectateur, choix A/B/C, décompte, réponse.

Usage : python3 tools/prof.py plan.json sortie.mp4

plan.json :
{
  "son_decompte": "sons/son-A-horloge-carillon.wav",
  "scenes": [
    {"voix": "voix/out/<id>/seg0.wav", "pose": "question",
     "tableau": {"type": "question", "texte": "Pourquoi le {ciel est bleu} ?", "icone": "soleil"}},
    {"voix": "voix/out/<id>/seg1.wav", "pose": "question", "decompte": 3,
     "tableau": {"type": "choix", "titre": "À ton avis ?", "options": ["Il reflète la mer", "...", "..."]}},
    {"voix": "voix/out/<id>/seg2.wav", "pose": "wow",
     "tableau": {"type": "choix", "titre": "Réponse B !", "options": [...], "bonne": "B"}},
    {"voix": "...", "pose": "montre", "tableau": {"type": "explication", "texte": "...", "icone": "arcenciel"}},
    {"voix": "...", "pose": "explique", "tableau": {"type": "chiffre", "texte": "GROS|petite phrase"}},
    {"voix": "...", "pose": "explique", "tableau": {"type": "fin", "texte": "Dis-le en {commentaire} !"}}
  ]
}
Poses : "explique" (mains qui bougent), "montre" (montre le tableau avec sa baguette), "question" (main au menton),
"wow" (mains en l'air), "neutre". Types de tableau : question, choix, explication, chiffre, fin.
Icônes : celles de decor.py (piece, carte, cheque, billet, cerveau, os, globe, horloge, ampoule, livre)
+ soleil, arcenciel, coucher, lune, coeur, eau, plante, eclair, terre.
{accolades} = mot-clé surligné. Décompte : n secondes, tic-tac sur les 2 dernières, carillon sur la scène suivante.
INTERDIT : logo, marque, personnage connu, badge IA, écran Sources, « Voix de synthèse ».
"""
import json, math, os, random, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decor
from decor import W, H, INK, CREAM, SIGNAL, F, TXT, BIG, MONO

FPS = 30
SKIN = (238, 190, 150); SKIN_D = (214, 156, 118); HAIR = (58, 38, 32); VEST = (32, 140, 132)
SHIRT = (250, 248, 240); MOUTH = (120, 30, 45); TONGUE = (235, 110, 120); CHEEK = (240, 140, 140)
S = 2                       # sur-échantillonnage du personnage (traits lisses)
CW, CH = 760, 1000          # taille du personnage (pixels finaux)
CX0, CY0 = 470 - 380, 930   # position du personnage dans l'image

# ---------------------------------------------------------------- personnage
ARMS = {  # (coude, main) pour le bras gauche (à l'écran) puis le droit, en pixels du personnage
    "neutre":     [((168, 690), (196, 860)), ((592, 690), (564, 860))],
    "explique_a": [((150, 700), (262, 600)), ((610, 700), (500, 612))],
    "explique_b": [((158, 690), (236, 630)), ((604, 712), (528, 570))],
    "montre":     [((112, 390), (96, 214)), ((592, 690), (564, 860))],
    "question":   [((214, 700), (412, 650)), ((566, 640), (452, 430))],
    "wow":        [((122, 530), (150, 330)), ((638, 530), (610, 330))],
}
BROWS = {"neutre": (0, 0), "explique_a": (0, -4), "explique_b": (0, -4), "montre": (-6, -8),
         "question": (10, -14), "wow": (-10, -22)}

def _p(x, y): return (x * S, y * S)

def _limb(d, pts, w, col):
    pts = [_p(*q) for q in pts]
    d.line(pts, fill=INK, width=(w + 14) * S, joint="curve")
    for q in (pts[0], pts[-1]):
        r = (w + 14) * S / 2; d.ellipse((q[0]-r, q[1]-r, q[0]+r, q[1]+r), fill=INK)
    d.line(pts, fill=col, width=w * S, joint="curve")
    for q in (pts[0], pts[-1]):
        r = w * S / 2; d.ellipse((q[0]-r, q[1]-r, q[0]+r, q[1]+r), fill=col)

def _circle(d, c, r, fill, ow=7):
    x, y = _p(*c); R = r * S; o = ow * S
    d.ellipse((x-R-o, y-R-o, x+R+o, y+R+o), fill=INK); d.ellipse((x-R, y-R, x+R, y+R), fill=fill)

def _arm(d, side, pose):
    sh = (214, 500) if side == 0 else (546, 500)
    (el, ha) = ARMS[pose][side]
    _limb(d, [sh, el, ha], 54, SHIRT)
    if pose == "montre" and side == 0:   # baguette de prof
        d.line([_p(*ha), _p(ha[0] - 40, ha[1] - 230)], fill=INK, width=16 * S)
        d.line([_p(*ha), _p(ha[0] - 40, ha[1] - 230)], fill=(196, 140, 80), width=9 * S)
        _circle(d, (ha[0] - 40, ha[1] - 230), 9, SIGNAL, 5)
    _circle(d, ha, 36, SKIN)

def _mouth(d, lvl, pose):
    cx, cy = 380, 338
    if pose == "wow": lvl = max(lvl, 1)
    if lvl == 0:
        d.arc((*_p(cx-42, cy-30), *_p(cx+42, cy+16)), 20, 160, fill=INK, width=8 * S); return
    w, h = {1: (34, 18), 2: (40, 32), 3: (46, 46)}[lvl]
    box = (*_p(cx-w, cy-h/2), *_p(cx+w, cy+h/2+6))
    o = 6 * S
    d.ellipse((box[0]-o, box[1]-o, box[2]+o, box[3]+o), fill=INK); d.ellipse(box, fill=MOUTH)
    if lvl >= 2: d.ellipse((*_p(cx-w*0.6, cy+h*0.05), *_p(cx+w*0.6, cy+h/2+4)), fill=TONGUE)
    if lvl == 3: d.rectangle((*_p(cx-w*0.55, cy-h/2+2), *_p(cx+w*0.55, cy-h/2+12)), fill=SHIRT)

def _sprite(pose, lvl, closed):
    img = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    # buste : gilet sur chemise, col et nœud papillon jaune
    body = [_p(120, 1010), _p(150, 560), _p(250, 470), _p(510, 470), _p(610, 560), _p(640, 1010)]
    d.polygon(body, fill=INK); inner = [_p(134, 1010), _p(162, 566), _p(256, 484), _p(504, 484), _p(598, 566), _p(626, 1010)]
    d.polygon(inner, fill=VEST)
    d.polygon([_p(318, 484), _p(442, 484), _p(380, 640)], fill=INK); d.polygon([_p(328, 488), _p(432, 488), _p(380, 620)], fill=SHIRT)
    for k in range(3): _circle(d, (380, 690 + k * 90), 9, SIGNAL, 4)
    _limb(d, [(380, 400), (380, 470)], 60, SKIN)   # cou
    d.polygon([_p(330, 470), _p(380, 500), _p(330, 530)], fill=INK); d.polygon([_p(430, 470), _p(380, 500), _p(430, 530)], fill=INK)
    d.polygon([_p(336, 480), _p(374, 500), _p(336, 520)], fill=SIGNAL); d.polygon([_p(424, 480), _p(386, 500), _p(424, 520)], fill=SIGNAL)
    _circle(d, (380, 500), 12, SIGNAL, 5)
    behind_face = pose != "question"
    if behind_face:
        for s in (0, 1): _arm(d, s, pose)
    # tête
    for ex in (205, 555): _circle(d, (ex, 270), 34, SKIN)          # oreilles
    (x0, y0), (x1, y1) = _p(212, 92), _p(548, 430)
    o = 8 * S; d.ellipse((x0-o, y0-o, x1+o, y1+o), fill=INK); d.ellipse((x0, y0, x1, y1), fill=SKIN)
    # cheveux : masse + mèche bouclée (personnage original)
    d.chord((*_p(200, 66), *_p(560, 330)), 180, 360, fill=INK)
    for k, cx in enumerate((262, 330, 400, 470)):
        _circle(d, (cx, 118 - (k % 2) * 14), 44, HAIR, 7)
    d.chord((*_p(212, 80), *_p(548, 316)), 180, 360, fill=HAIR)
    for k, cx in enumerate((262, 330, 400, 470)):
        _circle(d, (cx, 118 - (k % 2) * 14), 44, HAIR, 0)
    d.arc((*_p(356, 40), *_p(420, 104)), 200, 520, fill=HAIR, width=14 * S)
    # sourcils
    by, tilt = BROWS.get(pose, (0, 0))[1], BROWS.get(pose, (0, 0))[0]
    for s, ex in ((-1, 310), (1, 450)):
        a = (ex - 46, 196 + by - s * tilt / 2); b = (ex + 46, 196 + by + s * tilt / 2)
        d.line([_p(*a), _p(*b)], fill=HAIR, width=16 * S)
    # yeux + lunettes rondes
    for ex in (310, 450):
        if closed:
            d.arc((*_p(ex-28, 236), *_p(ex+28, 276)), 200, 340, fill=INK, width=7 * S)
        else:
            d.ellipse((*_p(ex-24, 228), *_p(ex+24, 282)), fill=(255, 255, 255))
            d.ellipse((*_p(ex-13, 240), *_p(ex+13, 272)), fill=INK)
            d.ellipse((*_p(ex-5, 244), *_p(ex+3, 252)), fill=(255, 255, 255))
        d.ellipse((*_p(ex-58, 196), *_p(ex+58, 312)), outline=INK, width=10 * S)
    d.line([_p(368, 250), _p(392, 250)], fill=INK, width=10 * S)
    d.arc((*_p(362, 262), *_p(398, 312)), 20, 160, fill=SKIN_D, width=8 * S)   # nez
    for ex in (262, 498):                                                      # joues
        d.ellipse((*_p(ex-26, 312), *_p(ex+26, 336)), fill=CHEEK)
    _mouth(d, lvl, pose)
    if not behind_face:
        for s in (0, 1): _arm(d, s, pose)
    return img.resize((CW, CH), Image.LANCZOS)

_SPR = {}
def sprite(pose, lvl, closed):
    k = (pose, lvl, closed)
    if k not in _SPR: _SPR[k] = _sprite(pose, lvl, closed)
    return _SPR[k]

# ---------------------------------------------------------------- tableau
def _icone(img, nom, cx, cy, r):
    if nom in decor.ICONES: decor._specimen(img, nom, cx, cy, r); return
    d = ImageDraw.Draw(img)
    d.ellipse((cx-r-34, cy-r-34, cx+r+34, cy+r+34), outline=(255, 255, 255, 90), width=2)
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=CREAM, outline=INK, width=6)
    s = r * 0.62
    if nom in ("soleil", "coucher"):
        if nom == "coucher":
            d.rectangle((cx-s*1.1, cy, cx+s*1.1, cy+s*0.9), fill=(70, 120, 210))
            d.pieslice((cx-s*0.6, cy-s*0.6, cx+s*0.6, cy+s*0.6), 180, 360, fill=(255, 130, 60), outline=INK, width=6)
            d.line((cx-s*1.1, cy, cx+s*1.1, cy), fill=INK, width=6)
        else:
            for k in range(12):
                a = k / 12 * 2 * math.pi
                d.line((cx+math.cos(a)*s*0.62, cy+math.sin(a)*s*0.62, cx+math.cos(a)*s*1.05, cy+math.sin(a)*s*1.05), fill=INK, width=9)
            d.ellipse((cx-s*0.55, cy-s*0.55, cx+s*0.55, cy+s*0.55), fill=SIGNAL, outline=INK, width=7)
    elif nom == "arcenciel":
        cols = [(230, 60, 60), (255, 150, 40), (255, 215, 50), (70, 190, 100), (60, 130, 230), (130, 80, 200)]
        for i, c in enumerate(cols):
            rr = s * 1.1 - i * s * 0.14
            d.arc((cx-rr, cy-rr+s*0.35, cx+rr, cy+rr+s*0.35), 180, 360, fill=c, width=int(s*0.14)+1)
    elif nom == "lune":
        d.ellipse((cx-s*0.8, cy-s*0.8, cx+s*0.8, cy+s*0.8), fill=SIGNAL, outline=INK, width=7)
        d.ellipse((cx-s*0.35, cy-s*0.95, cx+s*1.1, cy+s*0.55), fill=CREAM)
    elif nom == "coeur":
        d.polygon([(cx, cy+s*0.9), (cx-s*0.95, cy-s*0.05), (cx+s*0.95, cy-s*0.05)], fill=(220, 60, 80))
        for dx in (-0.45, 0.45): d.ellipse((cx+dx*s-s*0.52, cy-s*0.62, cx+dx*s+s*0.52, cy+s*0.3), fill=(220, 60, 80))
    elif nom == "eau":
        d.polygon([(cx, cy-s*1.0), (cx-s*0.62, cy+s*0.2), (cx+s*0.62, cy+s*0.2)], fill=(60, 150, 230))
        d.ellipse((cx-s*0.62, cy-s*0.3, cx+s*0.62, cy+s*0.9), fill=(60, 150, 230), outline=INK, width=6)
    elif nom == "plante":
        d.rectangle((cx-s*0.45, cy+s*0.2, cx+s*0.45, cy+s*0.9), fill=(200, 110, 60), outline=INK, width=6)
        d.line((cx, cy+s*0.2, cx, cy-s*0.7), fill=(40, 140, 70), width=10)
        for sg in (-1, 1): d.ellipse((cx+sg*s*0.6-s*0.35, cy-s*0.55, cx+sg*s*0.6+s*0.35, cy-s*0.15), fill=(70, 180, 90), outline=INK, width=5)
    elif nom == "eclair":
        d.polygon([(cx+s*0.2, cy-s), (cx-s*0.55, cy+s*0.1), (cx-s*0.05, cy+s*0.1), (cx-s*0.25, cy+s), (cx+s*0.55, cy-s*0.15), (cx+s*0.05, cy-s*0.15)], fill=SIGNAL, outline=INK)
    else:  # terre
        d.ellipse((cx-s, cy-s, cx+s, cy+s), fill=(70, 140, 230), outline=INK, width=8)
        d.ellipse((cx-s*0.7, cy-s*0.5, cx+s*0.05, cy+s*0.2), fill=(90, 190, 120)); d.ellipse((cx+s*0.15, cy+s*0.05, cx+s*0.7, cy+s*0.6), fill=(90, 190, 120))

FOND = {"question": "question", "choix": "decompte", "explication": "explication", "chiffre": "chiffre", "fin": "fin"}

def _options(img, t):
    d = ImageDraw.Draw(img); bonne = (t.get("bonne") or "").upper()
    decor._monument(img, decor._propre(t.get("titre", "À ton avis ?")).upper(), 205, 96, maxw=900)
    for i, txt in enumerate(t.get("options", [])[:3]):
        L = "ABC"[i]; y = 330 + i * 175; x0, x1 = 110, 970
        ok = bonne == L; dim = bool(bonne) and not ok
        fill = (120, 220, 160) if ok else (CREAM if not dim else (150, 150, 165))
        d.rounded_rectangle((x0+10, y+12, x1+10, y+150+12), 26, fill=(0, 0, 0, 90))
        d.rounded_rectangle((x0, y, x1, y+150), 26, fill=fill, outline=INK, width=6)
        d.ellipse((x0+24, y+27, x0+120, y+123), fill=SIGNAL if not dim else (200, 200, 205), outline=INK, width=5)
        f = F(BIG, 46); w = d.textlength(L, font=f); d.text((x0+72-w/2, y+44), L, font=f, fill=INK)
        txt = decor._propre(txt)
        for sz in range(54, 30, -2):
            fo = F(TXT, sz); lines = decor._wrap(d, txt, fo, x1-x0-190)
            if len(lines) <= 2: break
        lh = int(sz*1.15); ty = y + 75 - lh*len(lines)/2
        for k, line in enumerate(lines): d.text((x0+150, ty+k*lh), line, font=fo, fill=INK)
        if ok: d.line((x1-92, y+78, x1-66, y+104, x1-30, y+50), fill=INK, width=12, joint="curve")

def tableau(t, seed=0):
    """Renvoie (fond RGBA, calque du tableau RGBA)."""
    kind = t.get("type", "explication")
    fond = decor._fond("vrai" if (kind == "choix" and t.get("bonne")) else FOND.get(kind, "explication"), seed)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    txt = t.get("texte", "")
    if kind == "choix": _options(lay, t)
    elif kind == "chiffre":
        big, _, small = txt.partition("|"); decor._monument(lay, big, 300, 170)
        if small: decor._cartel(lay, small, 560, 66, maxw=820)
    elif kind == "fin":
        decor._monument(lay, "ET TOI ?", 290, 190, fill=INK, shadow=CREAM, angle=-3)
        decor._cartel(lay, txt, 560, 74, maxw=820)
    else:
        if t.get("icone"): _icone(lay, t["icone"], W // 2, 300, 140)
        decor._cartel(lay, txt, 590 if t.get("icone") else 330, 80 if kind == "question" else 70, maxw=820)
    return fond, lay

def _badge(img, n):
    d = ImageDraw.Draw(img); cx, cy, r = W // 2, 890, 74
    d.ellipse((cx-r-8, cy-r-8, cx+r+8, cy+r+8), fill=SIGNAL); d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=INK)
    f = F(BIG, 74); s = str(n); bb = d.textbbox((0, 0), s, font=f)
    d.text((cx-(bb[2]-bb[0])/2-bb[0], cy-(bb[3]-bb[1])/2-bb[1]), s, font=f, fill=CREAM)

# ---------------------------------------------------------------- son
def run(*a): subprocess.run(list(a), check=True, capture_output=True)

def _pcm(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

def _niveaux(x, n, delay):
    """Ouverture de la bouche (0-3) pour chaque image, d'après le volume de la voix."""
    sr = 44100; hop = sr // FPS; lv = np.zeros(n, dtype=int)
    rms = np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)) if i*hop < len(x) else 0 for i in range(n)])
    ref = np.percentile(rms[rms > 0], 90) if np.any(rms > 0) else 1
    off = int(round(delay * FPS)); prev = 0
    for i in range(n):
        j = i - off; v = rms[j] / ref if 0 <= j < n else 0
        l = 0 if v < 0.12 else 1 if v < 0.38 else 2 if v < 0.7 else 3
        if l == 0 and prev >= 2: l = 1          # fermeture douce
        lv[i] = prev = l
    return lv

# ---------------------------------------------------------------- montage
def main(plan_path, out):
    plan = json.load(open(plan_path)); son = plan.get("son_decompte"); tmp = tempfile.mkdtemp()
    rnd = random.Random(7); audio = []; frames_total = 0
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                           "-pix_fmt", "yuv420p", f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    t_glob = 0.0; next_blink = 2.0; carillon = False
    def emit(base, pose_seq, lvls, n, tab_in, fond, lay, badge=None):
        nonlocal t_glob, next_blink, frames_total
        static = None
        for i in range(n):
            t = t_glob + i / FPS
            if tab_in and i < 8:
                a = (i + 1) / 8; img = fond.copy()
                l2 = lay.copy(); l2.putalpha(l2.getchannel("A").point(lambda v: int(v * a)))
                img.alpha_composite(l2, (0, int((1 - a) * 40)))
            else:
                if static is None:
                    static = fond.copy(); static.alpha_composite(lay)
                img = static.copy() if badge is None else static.copy()
            if badge is not None: _badge(img, badge[i])
            closed = next_blink <= t < next_blink + 0.12
            if t >= next_blink + 0.12: next_blink = t + rnd.uniform(2.4, 4.6)
            pose = pose_seq(i); lvl = int(lvls[i])
            dy = 6 * math.sin(t * 2 * math.pi / 1.9) - 3 * lvl; dx = 4 * math.sin(t * 2 * math.pi / 3.7)
            img.alpha_composite(sprite(pose, lvl, closed), (int(CX0 + dx), int(CY0 + dy)))
            ff.stdin.write(img.convert("RGB").tobytes())
        t_glob += n / FPS; frames_total += n
    for k, sc in enumerate(plan["scenes"]):
        v = f"{tmp}/v{k}.wav"
        run("ffmpeg", "-y", "-loglevel", "error", "-i", sc["voix"], "-af",
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,aresample=44100",
            "-ac", "1", "-c:a", "pcm_s16le", v)
        x = _pcm(v); delay = 0.25 if carillon else 0.0
        n = int(round((len(x) / 44100 + delay + 0.35) * FPS)); d = n / FPS
        lv = _niveaux(x, n, delay)
        p = sc.get("pose", "explique")
        if p == "explique":
            seq = lambda i, lv=lv: ("explique_a" if (i // 11) % 2 == 0 else "explique_b") if lv[i] > 0 else "explique_a"
        else:
            seq = lambda i, p=p: p
        fond, lay = tableau(sc.get("tableau", {}), seed=k * 31 + 5)
        emit(None, seq, lv, n, True, fond, lay)
        a = f"{tmp}/a{k}.wav"
        if carillon and son:
            run("ffmpeg", "-y", "-loglevel", "error", "-i", v, "-i", son, "-filter_complex",
                f"[1:a]atrim=start=2.0,asetpts=PTS-STARTPTS,volume=0.8[c];[0:a]adelay=250|250[vv];[vv][c]amix=inputs=2:normalize=0,apad,atrim=0:{d:.4f}[a]",
                "-map", "[a]", "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", a)
        else:
            run("ffmpeg", "-y", "-loglevel", "error", "-i", v, "-af", f"apad,atrim=0:{d:.4f}", "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", a)
        audio.append(a); carillon = False
        if sc.get("decompte"):
            m = int(sc["decompte"]); nd = m * FPS
            badge = [m - i // FPS for i in range(nd)]
            emit(None, lambda i: "question", np.zeros(nd, dtype=int), nd, False, fond, lay, badge)
            da = f"{tmp}/d{k}.wav"; st = max(0, m - 2.0)
            if son:
                run("ffmpeg", "-y", "-loglevel", "error", "-i", son, "-af", f"atrim=0:2.0,adelay={int(st*1000)}|{int(st*1000)},apad,atrim=0:{m}",
                    "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", da)
            else:
                run("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", str(m), "-c:a", "pcm_s16le", da)
            audio.append(da); carillon = True
    ff.stdin.close(); ff.wait()
    open(f"{tmp}/al.txt", "w").write("".join(f"file '{a}'\n" for a in audio))
    run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/al.txt", "-c:a", "pcm_s16le", f"{tmp}/a.wav")
    run("ffmpeg", "-y", "-loglevel", "error", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/a.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", "loudnorm=I=-15:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out)
    print("ok", out, round(frames_total / FPS, 2), "s")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
