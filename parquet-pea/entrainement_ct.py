import sys, itertools, json, random
sys.path.insert(0, "/home/claude/mate/parquet-pea"); import court_terme as CT
import pandas as pd
df = pd.read_csv("/home/claude/mate/parquet-pea/data/intraday_5m.csv.gz", parse_dates=["heure"])
df["heure"] = pd.to_datetime(df["heure"], utc=True).dt.tz_convert("America/New_York")
df["jour"] = df["heure"].dt.date; df["min"] = df["heure"].dt.hour * 60 + df["heure"].dt.minute
U = {"parquet": ["SPY", "QQQ", "IWM", "EFA", "EEM", "GLD", "IEF"], "pea": ["SPY", "QQQ", "VGK", "EWQ", "EEM"]}
days = sorted(df[df.ticker == "SPY"]["jour"].unique()); print(len(days), days[0], days[-1])
B = {}  # (jour, ticker) -> bars
for (j, t), g in df.groupby(["jour", "ticker"]):
    B[(j, t)] = [(r.min, r.Open, r.High, r.Low, r.Close, r.Volume) for r in g.itertuples()]
def run_day(style, p, univ, j):
    etat = dict(positions={}, cash=10000.0, faits=[]); trades = 0
    for m in range(9 * 60 + 35, 16 * 60, 10):
        sig = {}
        for t in univ:
            bars = [b for b in B.get((j, t), []) if b[0] + 5 <= m]   # bougies terminées
            sig[t] = CT.signaux(bars) if bars else None
        px = {t: s["last"] for t, s in sig.items() if s}
        v = etat["cash"] + sum(pos["qte"] * px.get(t, pos["prix_achat"]) for t, pos in etat["positions"].items())
        o = CT.pas(style, p, etat, sig, px, v); trades += len(o)
    v = etat["cash"] + sum(pos["qte"] * pos["prix_achat"] for pos in etat["positions"].values())
    return v / 10000 - 1, trades
def run(style, p, univ, ds):
    eq = 1.0; peak = 1.0; mdd = 0; tr = 0; win = 0; act = 0
    for j in ds:
        r, n = run_day(style, p, univ, j); eq *= 1 + r; peak = max(peak, eq); mdd = max(mdd, 1 - eq / peak); tr += n
        if n: act += 1; win += r > 0
    return eq - 1, mdd, tr, (win / act if act else 0)
split = int(len(days) * 0.65); TR, TE = days[:split], days[split:]
GRID = {"eclair": dict(thr=[0.002, 0.003, 0.005], tp=[0.004, 0.008, 0.015], sl=[0.003, 0.006]),
        "elastique": dict(rsi_lo=[20, 25, 30], rsi_hi=[50, 60], dev=[0.002, 0.004], tp=[0.004, 0.008], sl=[0.005, 0.01]),
        "starter": dict(buf=[0.0, 0.001], tp=[0.006, 0.012, 0.02], sl=[0.003, 0.006])}
out = {}
for lg, univ in U.items():
    for st, grid in GRID.items():
        best = None
        for vals in itertools.product(*grid.values()):
            p = dict(zip(grid.keys(), vals)); r, m, tr, w = run(st, p, univ, TR); sc = r - 0.5 * m
            if best is None or sc > best[0]: best = (sc, p, r, m, tr, w)
        r2, m2, tr2, w2 = run(st, best[1], univ, TE)
        out[f"{lg}-{st}"] = dict(params=best[1], train=dict(gain=round(best[2], 4), chute=round(best[3], 4), ordres=best[4], jours_gagnants=round(best[5], 2)),
                                  test=dict(gain=round(r2, 4), chute=round(m2, 4), ordres=tr2, jours_gagnants=round(w2, 2)))
        print(lg, st, out[f"{lg}-{st}"])
    for t in univ[:2]:
        a = B[(TE[0], t)][0][1]; z = B[(TE[-1], t)][-1][4]; print("  achat-conservation", t, f"{z/a-1:+.4f}")
json.dump(dict(jours=[str(days[0]), str(days[-1])], apprentissage=[str(TR[0]), str(TR[-1])], test=[str(TE[0]), str(TE[-1])], res=out), open("/tmp/claude-0/-home-claude/1a7d381c-7c90-5af1-b96c-1d17c003cbb7/scratchpad/evo/bt_ct.json", "w"), ensure_ascii=False, indent=1)
