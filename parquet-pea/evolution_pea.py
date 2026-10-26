"""Tour PEA : 200 générations (argent fictif). Apprentissage 2006-2015, test honnête 2016-2026 (jamais vu)."""
import sys, json, random, copy, math
import numpy as np, pandas as pd
MATE = "/home/claude/mate"; sys.path.insert(0, MATE + "/parquet-pea")
import strategie_pea as SP
random.seed(26102026); np.random.seed(26102026)
D = MATE + "/parquet-pea/data/"
fx = pd.read_csv(D + "eurusd.csv", index_col=0, parse_dates=True)["close"]
src = {"SP500": "sp500_usd", "NASDAQ": "nasdaq100_usd", "EUROPE": "europe_usd", "FRANCE": "france_usd", "EMERGENTS": "emergents_usd"}
px = pd.DataFrame({k: pd.read_csv(D + v + ".csv", index_col=0, parse_dates=True)["close"] for k, v in src.items()}).div(fx, axis=0).dropna()
px = px.loc["2004-04-30":"2026-09-30"]; A = SP.ASSETS; P = px[A].values; T = len(P); dates = px.index
RET = np.vstack([np.zeros(5), P[1:] / P[:-1] - 1]); FEE = 0.001; TER = 0.003 / 12; CAP = 0.5
MA = {w: np.array([P[max(0, i - w + 1):i + 1].mean(0) for i in range(T)]) for w in range(3, 13)}
MA10 = MA[10]; HI12 = np.array([P[max(0, i - 11):i + 1].max(0) for i in range(T)])
VOL = np.array([np.std(RET[max(1, i - 11):i + 1], axis=0, ddof=1) if i >= 13 else np.full(5, np.nan) for i in range(T)])

def cible_np(g, i, etat, val, pic):
    last = P[i]; on = g["on"]
    if on["stop"]:
        if pic > 0 and val / pic - 1 < -g["stop"]: etat["abri"] = True
        if etat.get("abri"):
            if last[0] > MA10[i][0]: etat["abri"] = False
            else: return np.zeros(5)
    w = np.array([g["w0"][a] for a in A]); w = w / (w.sum() or 1)
    if on["elan"] and i > g["mom_w"]:
        r = last / P[i - g["mom_w"]] - 1; order = np.argsort(-r, kind="stable")
        for k in order[:g["mom_top"]]:
            if r[k] > 0: w[k] += g["mom_boost"]
    if on["volatilite"] and i > 12:
        inv = 1 / np.clip(VOL[i], 1e-4, None); inv = inv / inv.sum(); w = (1 - g["vol_mix"]) * w + g["vol_mix"] * inv
    if on["rachat"]:
        dd = last / HI12[i] - 1; w = w + np.where(dd < -g["dip_thr"], g["dip_boost"], 0)
    w = w / (w.sum() or 1)
    if on["tendance"]: w = w * np.where(last < MA[g["trend_w"]][i], g["trend_keep"], 1)
    w = w * g["invest"]; w = np.where(w > 0.005, np.minimum(w, CAP), 0)
    return w

def fixed(name, i, etat, val, pic):
    last = P[i]
    if name == "paresseux": return np.array([1, 0, 0, 0, 0.])
    if name == "prudent": return np.array([.3, 0, .18, 0, .12])
    if name in ("tortue", "vigilante"):
        if name == "vigilante":
            if val / pic - 1 < -0.15: etat["abri"] = True
            if etat.get("abri"):
                if last[0] > MA10[i][0]: etat["abri"] = False
                else: return np.zeros(5)
        return np.array([.5, 0, .3, 0, .2])
    if name == "boussole":
        up = last > MA10[i]; n = up.sum(); return np.where(up, min(CAP, 1 / n), 0) if n else np.zeros(5)
    if name == "fusee":
        r = last / P[i - 12] - 1; o = np.argsort(-r, kind="stable")[:2]; w = np.zeros(5)
        for k in o:
            if r[k] > 0: w[k] = .5
        return w
    if name == "chineur":
        dd = last / HI12[i] - 1; w = np.zeros(5); w[np.argsort(dd, kind="stable")[:2]] = .5; return w
    if name == "equilibriste":
        inv = 1 / VOL[i]; w = inv / inv.sum()
        for _ in range(5):
            over = w > CAP
            if not over.any(): break
            extra = (w[over] - CAP).sum(); w[over] = CAP; free = w < CAP; w[free] += extra * w[free] / w[free].sum()
        return w
    raise ValueError(name)

ANNUEL = {"paresseux", "prudent", "tortue"}
def run(strat, a, b):
    """strat = génome (dict) ou nom de style fixe ; simulation mensuelle de l'indice a à b."""
    v = 1.0; hold = np.zeros(5); cash = 1.0; peak = 1.0; mdd = 0; etat = {}; trades = 0; ly = None; first = True
    for i in range(a, b + 1):
        if i > a: hold = hold * (1 + RET[i] - TER)
        v = cash + hold.sum(); peak = max(peak, v); mdd = max(mdd, 1 - v / peak)
        if isinstance(strat, str):
            if strat in ANNUEL and ly == dates[i].year and not first: continue
            w = fixed(strat, i, etat, v, peak); ly = dates[i].year; act = True
        else:
            w = cible_np(strat, i, etat, v, peak); cur = hold / v if v > 0 else hold
            act = first or np.abs(w - cur).max() > strat["band"]
        if act:
            tgt = v * w; turn = np.abs(tgt - hold).sum(); v -= turn * FEE
            if turn > 1e-9: trades += 1
            hold = v * w; cash = v - hold.sum(); first = False
    yrs = (b - a) / 12
    return v ** (1 / yrs) - 1, mdd, v, trades

def score(s, starts, L=60): r = [run(s, a, a + L) for a in starts]; return sum(c - 0.3 * m for c, m, _, _ in r) / len(r)
i0 = list(dates).index(pd.Timestamp("2006-04-30")); i1 = list(dates).index(pd.Timestamp("2015-12-31")); i2 = T - 1
STARTS = list(range(i0, i1 - 60 + 1))   # fenêtres de 5 ans entièrement dans 2006-2015

RULES = ["tendance", "elan", "rachat", "volatilite", "stop"]
RNG = dict(invest=(0.5, 1), trend_w=(3, 12), trend_keep=(0, 1), mom_w=(3, 12), mom_top=(1, 3), mom_boost=(0, 1), dip_thr=(0.05, 0.3), dip_boost=(0, 0.5), vol_mix=(0, 1), stop=(0.08, 0.3), band=(0.02, 0.15))
INTS = {"trend_w", "mom_w", "mom_top"}
def clip(k, x): lo, hi = RNG[k]; x = max(lo, min(hi, x)); return int(round(x)) if k in INTS else x
def base(**kw):
    g = dict(invest=1.0, trend_w=10, trend_keep=0.0, mom_w=12, mom_top=2, mom_boost=0.5, dip_thr=0.1, dip_boost=0.3, vol_mix=1.0, stop=0.15, band=0.05,
             w0={a: 0.2 for a in A}, on={r: False for r in RULES}); g.update(kw); return g
SEEDS = {"tortue": base(w0=dict(SP500=.5, NASDAQ=0, EUROPE=.3, FRANCE=0, EMERGENTS=.2)),
         "boussole": base(on=dict(tendance=True, elan=False, rachat=False, volatilite=False, stop=False)),
         "fusee": base(w0={a: 0.01 for a in A}, on=dict(tendance=False, elan=True, rachat=False, volatilite=False, stop=False), mom_boost=1.0),
         "chineur": base(w0={a: 0.01 for a in A}, on=dict(tendance=False, elan=False, rachat=True, volatilite=False, stop=False), dip_thr=0.05, dip_boost=0.5),
         "vigilante": base(w0=dict(SP500=.5, NASDAQ=0, EUROPE=.3, FRANCE=0, EMERGENTS=.2), on=dict(tendance=False, elan=False, rachat=False, volatilite=False, stop=True)),
         "equilibriste": base(on=dict(tendance=False, elan=False, rachat=False, volatilite=True, stop=False))}
def mutate(g, rate=0.25):
    g = copy.deepcopy(g)
    for k, (lo, hi) in RNG.items():
        if random.random() < rate: g[k] = clip(k, g[k] + random.gauss(0, (hi - lo) * 0.12))
    for a in A:
        if random.random() < rate: g["w0"][a] = max(0.0, min(1.0, g["w0"][a] + random.gauss(0, 0.15)))
    if sum(g["w0"].values()) < 0.05: g["w0"]["SP500"] = 0.5
    for r in RULES:
        if random.random() < 0.06: g["on"][r] = not g["on"][r]
    return g
def cross(a, b):
    g = {k: (a[k] if random.random() < .5 else b[k]) for k in RNG}
    g["w0"] = {x: (a["w0"][x] if random.random() < .5 else b["w0"][x]) for x in A}
    g["on"] = {r: (a["on"][r] if random.random() < .5 else b["on"][r]) for r in RULES}; return g
def dom(g):
    for r in ["stop", "tendance", "elan", "rachat", "volatilite"]:
        if g["on"][r]: return r
    return "fixe"

# Contrôle : la version rapide = la version de la séance en direct
for st, g in list(SEEDS.items()):
    for _ in range(3):
        gg = mutate(g, 0.8); i = random.randint(30, T - 1)
        a1 = cible_np(gg, i, {}, 1.0, 1.0); a2 = SP.cible(gg, px.iloc[:i + 1], {}, 1.0, 1.0)
        assert np.allclose(a1, [a2.get(a, 0) for a in A], atol=1e-9), (st, a1, a2)
print("Contrôle OK : simulation identique au moteur en direct")

CUR = ["tortue", "boussole", "fusee", "chineur", "vigilante", "equilibriste"]
pop = [dict(nom=f"graine-{s}", g=SEEDS[s], ne=0) for s in CUR]
courbe = []; crees = 0
for gen in range(1, 201):
    wins = random.sample(STARTS, 6)
    for x in pop: x["s"] = score(x["g"], wins)
    pop.sort(key=lambda x: -x["s"]); sc = [x["s"] for x in pop]
    courbe.append(dict(gen=gen, meilleur=round(sc[0], 4), median=round(float(np.median(sc)), 4), styles=len({dom(x["g"]) for x in pop})))
    keep = pop[:3]; kids = []
    for _ in range(2):
        p1, p2 = random.sample(keep, 2); kids.append(dict(g=mutate(cross(p1["g"], p2["g"])), ne=gen))
    have = {dom(x["g"]) for x in keep + kids}; absent = [r for r in RULES if r not in have]
    g = mutate(random.choice(keep)["g"], 0.5)
    if absent:
        r = random.choice(absent); g["on"] = {k: False for k in RULES}; g["on"][r] = True
    kids.append(dict(g=g, ne=gen, diff=True)); crees += len(kids)
    pop = keep + kids

res = []
for x in pop:
    c, m, mult, tr = run(x["g"], i1, i2)
    res.append(dict(g=x["g"], ne=x["ne"], diff=x.get("diff", False), dom=dom(x["g"]), train=round(score(x["g"], STARTS), 4), test=dict(rendement=round(c, 4), chute=round(m, 4), multiplie=round(mult, 3), echanges=tr)))
cur = []
for s in CUR + ["paresseux", "prudent"]:
    c, m, mult, tr = run(s, i1, i2); cur.append(dict(style=s, train=round(score(s, STARTS), 4), test=dict(rendement=round(c, 4), chute=round(m, 4), multiplie=round(mult, 3), echanges=tr)))
json.dump(dict(courbe=courbe, crees=crees, evolues=res, actuels=cur), open("/tmp/claude-0/-home-claude/1a7d381c-7c90-5af1-b96c-1d17c003cbb7/scratchpad/evo/resultat_pea.json", "w"), ensure_ascii=False, indent=1)
print("Actuels :"); [print(f"  {x['style']:13s} score {x['train']:+.4f} test {x['test']}") for x in sorted(cur, key=lambda x: -x["train"])]
print("Évolués :"); [print(f"  {x['dom']:10s} né {x['ne']:3d} score {x['train']:+.4f} test {x['test']} on={[k for k,v in x['g']['on'].items() if v]}") for x in sorted(res, key=lambda x: -x["train"])]
print(courbe[0], courbe[-1])
