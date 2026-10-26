"""Ligue PEA du Parquet — simulation en ARGENT FICTIF, pour apprendre. Pas un conseil d'investissement.
Univers PEA (fonds indiciels « éligibles PEA » simulés par leurs indices, convertis en euros) :
  SP500, NASDAQ, EUROPE, FRANCE, EMERGENTS + liquidités (0 %). Pas d'obligations ni d'or (interdits en PEA).
Décision 1 fois par mois. Frais : 0,1 % par achat/vente + 0,3 %/an de frais de fonds.
Règle de Gaspard : jamais plus de 50 % sur un seul fonds (sauf le témoin « Paresseux »).
Test honnête : période d'apprentissage 2006-04 → 2015-12, période inconnue 2016-01 → 2026-09.
"""
import pandas as pd, numpy as np, json, sys
D = "parquet-pea/data/"
fx = pd.read_csv(D+"eurusd.csv", index_col=0, parse_dates=True)["close"]
src = {"SP500":"sp500_usd","NASDAQ":"nasdaq100_usd","EUROPE":"europe_usd","FRANCE":"france_usd","EMERGENTS":"emergents_usd"}
px = pd.DataFrame({k: pd.read_csv(D+v+".csv", index_col=0, parse_dates=True)["close"] for k,v in src.items()})
px = px.div(fx, axis=0).dropna()            # prix en euros
px = px.loc["2004-04-30":"2026-09-30"]       # 12 mois d'historique avant le départ (2005-04)
ret = px.pct_change()
ASSETS = list(px.columns); CAP = 0.5; FEE = 0.001; TER = 0.003/12

def w_cap(w):
    w = {k: min(v, CAP) for k, v in w.items() if v > 0}
    return w  # le reste part en liquidités

def strat(name, t, hist, state):
    p = hist; last = p.iloc[-1]
    ma10 = p.iloc[-10:].mean(); r12 = p.iloc[-1]/p.iloc[-13]-1 if len(p)>12 else p.iloc[-1]*0
    hi12 = p.iloc[-12:].max(); dd = last/hi12-1
    if name == "Paresseux":  return {"SP500": 1.0}
    if name == "Prudent":    return {"SP500": .30, "EUROPE": .18, "EMERGENTS": .12}   # 60 % actions, 40 % liquidités
    if name == "Tortue":     return {"SP500": .5, "EUROPE": .3, "EMERGENTS": .2}
    if name == "Boussole":
        up = [a for a in ASSETS if last[a] > ma10[a]]
        return w_cap({a: 1/len(up) for a in up}) if up else {}
    if name == "Fusee":
        top = r12.sort_values(ascending=False)
        top = [a for a in top.index[:2] if top[a] > 0]
        return {a: .5 for a in top}
    if name == "Chineur":
        worst = dd.sort_values().index[:2]
        return {a: .5 for a in worst}
    if name == "Vigilante":
        if state.get("abri"):
            if last["SP500"] > ma10["SP500"]: state["abri"] = False
            else: return {}
        return {"SP500": .5, "EUROPE": .3, "EMERGENTS": .2}
    if name == "Equilibriste":
        vol = ret.loc[:t].iloc[-12:].std()
        inv = 1/vol; w = (inv/inv.sum()).to_dict()
        for _ in range(5):  # plafonner à 50 % et redistribuer
            over = {k: v for k, v in w.items() if v > CAP}
            if not over: break
            extra = sum(v-CAP for v in over.values()); free = [k for k in w if w[k] < CAP]
            for k in over: w[k] = CAP
            tot = sum(w[k] for k in free)
            for k in free: w[k] += extra*w[k]/tot
        return w
    raise ValueError(name)

NOMS = {"Paresseux":"Le Paresseux (témoin : tout S&P 500, ne bouge jamais)","Prudent":"Le Prudent (témoin : 60 % actions, 40 % liquidités)",
        "Tortue":"La Tortue (répartit et garde)","Boussole":"La Boussole (suit la tendance)","Fusee":"La Fusée (suit l'élan des 12 derniers mois)",
        "Chineur":"Le Chineur (achète ce qui a le plus baissé)","Vigilante":"La Vigilante (se met à l'abri après -15 %)",
        "Equilibriste":"L'Équilibriste (plus d'argent sur ce qui bouge le moins)"}

def run(name, start, end):
    idx = px.loc[start:end].index; cash = 10000.0; hold = {a: 0.0 for a in ASSETS}
    vals = []; state = {}; peak = 10000.0; trades = 0; last_year = None
    for i, t in enumerate(idx):
        if i > 0:
            for a in ASSETS: hold[a] *= (1 + ret.loc[t, a] - TER)
        v = cash + sum(hold.values()); peak = max(peak, v)
        if name == "Vigilante" and v/peak - 1 < -0.15: state["abri"] = True
        rebal = not (name in ("Paresseux","Prudent","Tortue") and last_year == t.year and i > 0)
        if rebal:
            w = strat(name, t, px.loc[:t], state)
            target = {a: v*w.get(a, 0) for a in ASSETS}
            turn = sum(abs(target[a]-hold[a]) for a in ASSETS)
            if turn > 1: trades += 1
            v -= turn*FEE
            hold = {a: v*w.get(a, 0) for a in ASSETS}; cash = v - sum(hold.values())
            last_year = t.year
        vals.append(cash + sum(hold.values()))
    s = pd.Series(vals, idx); yrs = (len(s)-1)/12
    mdd = (s/s.cummax()-1).min(); cagr = (s.iloc[-1]/10000)**(1/yrs)-1
    vol = s.pct_change().std()*np.sqrt(12)
    gain = s.iloc[-1]-10000; net = s.iloc[-1] - max(gain, 0)*0.186
    return {"final": round(s.iloc[-1]), "net_apres_prelevements": round(net), "par_an_pct": round(cagr*100,1),
            "pire_chute_pct": round(mdd*100,1), "volatilite_pct": round(vol*100,1), "note": round(cagr/abs(mdd),2) if mdd<0 else None, "decisions_actives": trades}

out = {}
for per, (a, b) in {"apprentissage_2006_2015": ("2006-04-30","2015-12-31"), "inconnue_2016_2026": ("2015-12-31","2026-09-30"), "total_2006_2026": ("2006-04-30","2026-09-30")}.items():
    out[per] = {NOMS[n]: run(n, a, b) for n in NOMS}
json.dump(out, open("parquet-pea/resultats.json","w"), ensure_ascii=False, indent=1)
for per, r in out.items():
    print("\n==", per)
    for n, m in sorted(r.items(), key=lambda kv: -kv[1]["final"]):
        print(f"{n[:58]:58s} {m['final']:>8} € | {m['par_an_pct']:>5}%/an | chute {m['pire_chute_pct']:>6}% | note {m['note']}")
