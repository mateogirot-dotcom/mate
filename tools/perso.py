"""Filou le renard — le personnage des vidéos « on t'apprend un truc » du Studio @reyzinhoia (31 oct. 2026).

Remplace le Prof Marius (refusé par l'utilisateur le 31 oct. : « trop robot »). Filou est un renard dessiné ORIGINAL
du Studio. Animation fluide : les bras bougent en continu (cinématique inverse + ressorts), la tête penche, les
oreilles frémissent, la queue se balance, le corps respire et rebondit, les yeux regardent le tableau ou le
spectateur et clignent en douceur, la bouche s'ouvre selon le volume de la voix (ouverture continue).

Usage : python3 tools/perso.py plan.json sortie.mp4      (même plan.json que tools/prof.py)
Poses : "explique", "montre", "question", "wow", "neutre". Tableau : voir tools/prof.py (question, choix, explication,
chiffre, fin ; icônes ; {mot-clé}). INTERDIT : logo, marque, personnage connu, badge IA, écran Sources.
"""
import json, math, os, random, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prof
from prof import tableau, _badge, _pcm, run, FPS, W, H

S = 2
CW, CH = 800, 1000
X0, Y0 = 470 - 400, 900
INK = (46, 26, 30)
FUR = (240, 128, 48); FUR_D = (214, 98, 30); CREAM = (255, 244, 228); PAW = (74, 42, 38)
EYE = (44, 26, 30); IRIS = (150, 78, 34); WHITE = (255, 255, 255); BLUSH = (255, 140, 150, 120)
TONGUE = (240, 110, 125); MOUTH = (110, 30, 42)

def P(x, y): return (x * S, y * S)

# ---------------------------------------------------------------- poses (cibles)
POSES = {
    "neutre":   dict(L=(236, 870), R=(564, 870), tilt=0, look=(0, 0), brow=0, jump=0, eyes=1.0, ears=0),
    "explique": dict(L=(240, 790), R=(560, 790), tilt=-2, look=(0, 0), brow=-3, jump=0, eyes=1.0, ears=0),
    "montre":   dict(L=(140, 360), R=(560, 860), tilt=-9, look=(-10, -12), brow=-8, jump=0, eyes=1.0, ears=4),
    "question": dict(L=(420, 790), R=(456, 628), tilt=11, look=(8, -10), brow=10, jump=0, eyes=1.0, ears=-4),
    "wow":      dict(L=(205, 470), R=(595, 470), tilt=0, look=(0, 0), brow=-14, jump=26, eyes=1.18, ears=10),
}

def ik(sh, tg, l1=138, l2=132, side=-1):
    dx, dy = tg[0] - sh[0], tg[1] - sh[1]; d = max(1e-3, math.hypot(dx, dy))
    if d > l1 + l2 - 1: tg = (sh[0] + dx / d * (l1 + l2 - 1), sh[1] + dy / d * (l1 + l2 - 1)); dx, dy = tg[0] - sh[0], tg[1] - sh[1]; d = l1 + l2 - 1
    a = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    base = math.atan2(dy, dx); ang = base + side * a
    el = (sh[0] + math.cos(ang) * l1, sh[1] + math.sin(ang) * l1)
    return el, tg

def limb(d, pts, w, col, ow=10):
    pts = [P(*q) for q in pts]
    d.line(pts, fill=INK, width=(w + ow) * S, joint="curve")
    for q in pts:
        r = (w + ow) * S / 2; d.ellipse((q[0]-r, q[1]-r, q[0]+r, q[1]+r), fill=INK)
    d.line(pts, fill=col, width=w * S, joint="curve")
    for q in pts:
        r = w * S / 2; d.ellipse((q[0]-r, q[1]-r, q[0]+r, q[1]+r), fill=col)

def blob(d, c, rx, ry, col, ow=8):
    x, y = P(*c); o = ow * S
    d.ellipse((x - rx*S - o, y - ry*S - o, x + rx*S + o, y + ry*S + o), fill=INK)
    d.ellipse((x - rx*S, y - ry*S, x + rx*S, y + ry*S), fill=col)

def poly(d, pts, col, ow=8):
    pp = [P(*q) for q in pts]
    d.polygon(pp, fill=col, outline=INK, width=ow * S)

# ---------------------------------------------------------------- tête (dessinée seule puis tournée)
HW, HH = 800, 720   # canevas de la tête, pivot du cou en (400, 600)

def head(st, t):
    img = Image.new("RGBA", (HW * S, HH * S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    e = st["ears"]; flick = st["flick"]
    for side in (-1, 1):   # oreilles
        rot = math.radians(side * (6 - e * 0.6) + (flick if side == 1 else 0))
        bx, by = 400 + side * 120, 250
        def R(px, py):
            px, py = px - bx, py - by
            return (bx + px * math.cos(rot) - py * math.sin(rot), by + px * math.sin(rot) + py * math.cos(rot))
        tip = (400 + side * 175, 70 - e)
        outer = [R(400 + side * 40, 240), R(*tip), R(400 + side * 225, 300)]
        poly(d, outer, FUR)
        inner = [R(400 + side * 70, 236), R(400 + side * 168, 112 - e * 0.8), R(400 + side * 200, 278)]
        d.polygon([P(*q) for q in inner], fill=CREAM)
        tipz = [R(tip[0] - side * 22, tip[1] + 50), R(*tip), R(tip[0] + side * 30, tip[1] + 62)]
        d.polygon([P(*q) for q in tipz], fill=PAW)
    # visage : grosse tête ronde + touffes des joues
    for side in (-1, 1):
        poly(d, [(400 + side * 150, 470), (400 + side * 238, 512), (400 + side * 196, 430), (400 + side * 232, 420), (400 + side * 180, 360)], FUR)
    blob(d, (400, 380), 205, 180, FUR)
    for side in (-1, 1):
        d.polygon([P(400 + side * 152, 468), P(400 + side * 226, 506), P(400 + side * 190, 430), P(400 + side * 222, 422), P(400 + side * 176, 366)], fill=FUR)
    # masque crème (museau + joues), sans contour pour la douceur
    d.ellipse((*P(300, 405), *P(500, 545)), fill=CREAM)
    for side in (-1, 1): d.ellipse((*P(400 + side * 95 - 80, 395), *P(400 + side * 95 + 80, 520)), fill=CREAM)
    # yeux (grands, brillants, regard mobile, paupières douces)
    lx, ly = st["look"]; es = st["eyes"]; cl = st["blink"]
    for side in (-1, 1):
        cx, cy = 400 + side * 78, 380
        rx, ry = 38 * es, 50 * es
        d.ellipse((*P(cx - rx, cy - ry), *P(cx + rx, cy + ry)), fill=EYE)
        ix, iy = cx + lx * 0.9, cy + ly * 0.8 + 6
        d.ellipse((*P(ix - rx * 0.72, iy - ry * 0.55), *P(ix + rx * 0.72, iy + ry * 0.78)), fill=IRIS)
        d.ellipse((*P(ix - rx * 0.42, iy - ry * 0.3), *P(ix + rx * 0.42, iy + ry * 0.5)), fill=EYE)
        d.ellipse((*P(ix - rx * 0.55 - 4, iy - ry * 0.62), *P(ix - rx * 0.55 + 22, iy - ry * 0.62 + 26)), fill=WHITE)
        d.ellipse((*P(ix + rx * 0.3, iy + ry * 0.28), *P(ix + rx * 0.3 + 10, iy + ry * 0.28 + 10)), fill=WHITE)
        if cl > 0.02:   # paupière qui descend
            top = cy - ry - 4; bot = top + (2 * ry + 8) * cl
            d.rectangle((*P(cx - rx - 6, top - 10), *P(cx + rx + 6, bot)), fill=FUR)
            d.chord((*P(cx - rx - 6, bot - 18), *P(cx + rx + 6, bot + 18)), 0, 180, fill=FUR)
            d.arc((*P(cx - rx, bot - 14), *P(cx + rx, bot + 14)), 10, 170, fill=INK, width=6 * S)
        # sourcils flottants
        b = st["brow"]; up = max(0, -b) + (b * 1.4 if (b > 0 and side == 1) else 0)
        by_ = cy - ry - 24 - up
        d.arc((*P(cx - 28, by_ - 6), *P(cx + 28, by_ + 22)), 200, 340, fill=PAW, width=10 * S)
    for side in (-1, 1):   # joues roses
        bl = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(bl).ellipse((*P(400 + side * 122 - 34, 450), *P(400 + side * 122 + 34, 476)), fill=BLUSH)
        img.alpha_composite(bl); d = ImageDraw.Draw(img)
    # nez
    d.ellipse((*P(378, 432), *P(422, 462)), fill=EYE); d.ellipse((*P(388, 436), *P(402, 444)), fill=(140, 120, 130))
    # bouche (ouverture continue 0..1)
    o = st["mouth"]
    if o < 0.08:
        for side in (-1, 1): d.arc((*P(400 + side * 20 - 22, 448), *P(400 + side * 20 + 22, 486)), 20, 160, fill=INK, width=6 * S)
        d.line([P(400, 462), P(400, 470)], fill=INK, width=6 * S)
    else:
        w = 30 + 16 * o; h = 14 + 56 * o; y = 470
        d.line([P(400, 462), P(400, y)], fill=INK, width=6 * S)
        d.chord((*P(400 - w - 6, y - h * 0.35 - 6), *P(400 + w + 6, y + h + 6)), 0, 180, fill=INK)
        d.chord((*P(400 - w, y - h * 0.35), *P(400 + w, y + h)), 0, 180, fill=MOUTH)
        if o > 0.3: d.chord((*P(400 - w * 0.6, y + h * 0.35), *P(400 + w * 0.6, y + h * 0.95)), 180, 360, fill=TONGUE)
    return img

# ---------------------------------------------------------------- personnage entier
def draw(st, t):
    img = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    jy = -st["jump"]; br = math.sin(t * 2 * math.pi / 2.6)
    # queue (derrière), balancement
    sw = math.radians(9 * math.sin(t * 1.7) + st["tailx"])
    base = (540, 840 + jy)
    pts = []
    for k in range(14):
        u = k / 13
        x = base[0] + 170 * u; y = base[1] - 300 * u * u - 40 * u
        dx, dy = x - base[0], y - base[1]
        pts.append((base[0] + dx * math.cos(sw * u) - dy * math.sin(sw * u), base[1] + dx * math.sin(sw * u) + dy * math.cos(sw * u), 46 + 60 * math.sin(math.pi * min(1, u * 1.1))))
    for x, y, r in pts: d.ellipse((*P(x - r - 8, y - r - 8), *P(x + r + 8, y + r + 8)), fill=INK)
    for k, (x, y, r) in enumerate(pts): d.ellipse((*P(x - r, y - r), *P(x + r, y + r)), fill=CREAM if k > 10 else FUR)
    # corps (respiration + rebond)
    sy = 1 + 0.012 * br - 0.04 * st["squash"]; sx = 1 - 0.008 * br + 0.04 * st["squash"]
    cy = 805 + jy
    blob(d, (400, cy), 190 * sx, 215 * sy, FUR)
    d.ellipse((*P(400 - 118 * sx, cy - 140 * sy + 40), *P(400 + 118 * sx, cy + 180 * sy)), fill=CREAM)
    # foulard jaune (signe distinctif)
    sc_y = 30
    d.chord((*P(258, 560 + jy + sc_y), *P(542, 690 + jy + sc_y)), 0, 180, fill=INK)
    d.chord((*P(266, 566 + jy + sc_y), *P(534, 680 + jy + sc_y)), 0, 180, fill=(255, 200, 40))
    poly(d, [(430, 640 + jy + sc_y), (480, 720 + jy + sc_y), (455, 728 + jy + sc_y), (420, 668 + jy + sc_y)], (255, 200, 40), 6)
    # tête tournée autour du cou
    hd = head(st, t).rotate(-st["tilt"], resample=Image.BICUBIC, center=(400 * S, 600 * S))
    img.alpha_composite(hd, (0, int((jy + 58 + 3 * br - 4 * st["mouth"]) * S)))
    d = ImageDraw.Draw(img)
    # bras (cinématique inverse) + pattes sombres
    for side, key, sh in ((-1, "L", (286, 676 + jy)), (1, "R", (514, 676 + jy))):
        tg = st[key]; tg = (tg[0], tg[1] + jy)
        el, hand = ik(sh, tg, side=(1 if side < 0 else -1))
        limb(d, [sh, el, hand], 50, FUR)
        blob(d, hand, 33, 31, PAW, 8)
        d.ellipse((*P(hand[0] - 14, hand[1] - 20), *P(hand[0] - 2, hand[1] - 8)), fill=(110, 70, 64))
    return img.reduce(S)

# ---------------------------------------------------------------- état animé (ressorts)
class Anim:
    def __init__(s):
        p = POSES["neutre"]; s.st = {k: (tuple(v) if isinstance(v, tuple) else v) for k, v in p.items()}
        s.st.update(blink=0.0, mouth=0.0, flick=0.0, squash=0.0, tailx=0.0)
        s.next_blink = 1.5; s.next_flick = 3.0; s.rnd = random.Random(11); s.prev_o = 0
    def step(s, pose, o, t, talk_phase):
        tg = dict(POSES[pose]); k = 0.2
        if pose == "explique" and o > 0.05:   # mains qui gesticulent en parlant
            tg["L"] = (tg["L"][0] - 22 * math.sin(t * 5.1), tg["L"][1] - 30 * abs(math.sin(t * 3.3)))
            tg["R"] = (tg["R"][0] + 22 * math.sin(t * 4.3 + 1), tg["R"][1] - 30 * abs(math.sin(t * 2.9 + 0.7)))
            tg["tilt"] = 5 * math.sin(t * 1.3)
        if pose == "montre": tg["L"] = (tg["L"][0] + 8 * math.sin(t * 6), tg["L"][1] + 6 * math.sin(t * 6))
        if pose == "question": tg["tilt"] += 3 * math.sin(t * 1.1)
        st = s.st
        for key in ("L", "R", "look"):
            st[key] = (st[key][0] + (tg[key][0] - st[key][0]) * k, st[key][1] + (tg[key][1] - st[key][1]) * k)
        for key in ("tilt", "brow", "jump", "eyes", "ears"):
            st[key] += (tg[key] - st[key]) * k
        st["tilt"] += 1.6 * o * math.sin(t * 9)          # petits hochements en parlant
        st["mouth"] += (o - st["mouth"]) * 0.55
        st["squash"] += ((max(0, o - s.prev_o) * 3) - st["squash"]) * 0.3; s.prev_o = o
        if t >= s.next_blink:
            ph = (t - s.next_blink) / 0.16
            st["blink"] = math.sin(min(1, ph) * math.pi)
            if ph >= 1: st["blink"] = 0; s.next_blink = t + s.rnd.uniform(2.2, 4.4)
        if t >= s.next_flick:
            ph = (t - s.next_flick) / 0.25
            st["flick"] = 14 * math.sin(min(1, ph) * math.pi)
            if ph >= 1: st["flick"] = 0; s.next_flick = t + s.rnd.uniform(3, 6)
        return st

def _ouverture(x, n, delay):
    sr = 44100; hop = sr // FPS
    rms = np.array([np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)) if i*hop < len(x) else 0 for i in range(n)])
    ref = np.percentile(rms[rms > 0], 92) if np.any(rms > 0) else 1
    off = int(round(delay * FPS)); out = np.zeros(n)
    for i in range(n):
        j = i - off; v = rms[j] / ref if 0 <= j < n else 0
        out[i] = 0 if v < 0.1 else min(1, (v - 0.1) / 0.8)
    return out

def main(plan_path, out):
    plan = json.load(open(plan_path)); son = plan.get("son_decompte"); tmp = tempfile.mkdtemp()
    A = Anim(); audio = []; tg = 0.0; carillon = False
    tmpv = f"{tmp}/v.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                           "-pix_fmt", "yuv420p", tmpv], stdin=subprocess.PIPE)
    def emit(pose, ouv, n, fond, lay, badge=None, intro=True):
        nonlocal tg
        static = fond.copy(); static.alpha_composite(lay)
        for i in range(n):
            t = tg + i / FPS
            if intro and i < 8:
                a = (i + 1) / 8; img = fond.copy(); l2 = lay.copy()
                l2.putalpha(l2.getchannel("A").point(lambda v: int(v * a))); img.alpha_composite(l2, (0, int((1 - a) * 40)))
            else: img = static.copy()
            if badge is not None: _badge(img, badge[i])
            st = A.step(pose, float(ouv[i]), t, 0)
            img.alpha_composite(draw(st, t), (X0, Y0))
            ff.stdin.write(img.convert("RGB").tobytes())
        tg += n / FPS
    for k, sc in enumerate(plan["scenes"]):
        v = f"{tmp}/v{k}.wav"
        run("ffmpeg", "-y", "-loglevel", "error", "-i", sc["voix"], "-af",
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,aresample=44100",
            "-ac", "1", "-c:a", "pcm_s16le", v)
        x = _pcm(v); delay = 0.25 if carillon else 0.0
        n = int(round((len(x) / 44100 + delay + 0.35) * FPS)); d = n / FPS
        fond, lay = tableau(sc.get("tableau", {}), seed=k * 31 + 5)
        emit(sc.get("pose", "explique"), _ouverture(x, n, delay), n, fond, lay)
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
            emit("question", np.zeros(nd), nd, fond, lay, [m - i // FPS for i in range(nd)], intro=False)
            da = f"{tmp}/d{k}.wav"; st0 = max(0, m - 2.0)
            if son:
                run("ffmpeg", "-y", "-loglevel", "error", "-i", son, "-af", f"atrim=0:2.0,adelay={int(st0*1000)}|{int(st0*1000)},apad,atrim=0:{m}",
                    "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", da)
            else:
                run("ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", str(m), "-c:a", "pcm_s16le", da)
            audio.append(da); carillon = True
    ff.stdin.close()
    if ff.wait() != 0: raise SystemExit("échec de l'encodage vidéo")
    open(f"{tmp}/al.txt", "w").write("".join(f"file '{a}'\n" for a in audio))
    run("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/al.txt", "-c:a", "pcm_s16le", f"{tmp}/a.wav")
    part = out[:-4] + ".part.mp4"
    run("ffmpeg", "-y", "-loglevel", "error", "-i", tmpv, "-i", f"{tmp}/a.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", "loudnorm=I=-15:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", part)
    os.replace(part, out)
    print("ok", out, round(tg, 2), "s")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
