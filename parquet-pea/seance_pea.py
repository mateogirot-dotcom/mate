"""Séance HEBDOMADAIRE de la Tour PEA — ARGENT FICTIF, pour apprendre. Aucun ordre réel, pas un conseil.
Usage : python3 parquet-pea/seance_pea.py marche_pea.json portefeuilles_pea.json sortie_dir
marche_pea.json = {"date":"AAAA-MM-JJ","moment":"...","eurusd":1.08,"eurusd_sources":"...",
   "prix_usd":{"SPY":..,"QQQ":..,"VGK":..,"EWQ":..,"EEM":..},"sources":{"SPY":"stockanalysis + digrin",...},"exclus":{}}
Les signaux (moyenne 10 mois, élan 12 mois, plus haut 12 mois, volatilité) utilisent l'historique mensuel
parquet-pea/data/*.csv (converti en euros) + le prix du jour.
"""
import json, sys, os, math
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strategie_pea
ROOT = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(ROOT, "data") + "/"
MAP = {"SP500": ("SPY", "sp500_usd", "Fonds PEA S&P 500"), "NASDAQ": ("QQQ", "nasdaq100_usd", "Fonds PEA Nasdaq-100"),
       "EUROPE": ("VGK", "europe_usd", "Fonds PEA Europe"), "FRANCE": ("EWQ", "france_usd", "Fonds PEA CAC 40 / France"),
       "EMERGENTS": ("EEM", "emergents_usd", "Fonds PEA pays émergents")}
CAP, FEE = 0.5, 0.001
mk = json.load(open(sys.argv[1])); pf = [a for a in json.load(open(sys.argv[2])) if not a.get("court_terme")]; out = sys.argv[3]; os.makedirs(out, exist_ok=True)
fx = pd.read_csv(D+"eurusd.csv", index_col=0, parse_dates=True)["close"]
hist = pd.DataFrame({k: pd.read_csv(D+v[1]+".csv", index_col=0, parse_dates=True)["close"] for k, v in MAP.items()}).div(fx, axis=0).dropna()
today = pd.Timestamp(mk["date"])
hist = hist[hist.index < today.to_period("M").to_timestamp("M")]          # mois complets seulement
prix = {a: mk["prix_usd"][MAP[a][0]]/mk["eurusd"] for a in MAP if MAP[a][0] in mk["prix_usd"] and MAP[a][0] not in mk.get("exclus", {})}
ok = list(prix)
cur = pd.Series(prix); p = pd.concat([hist, cur.to_frame(today).T])[ok]
ma10 = p.iloc[-10:].mean(); r12 = p.iloc[-1]/p.iloc[-13]-1; dd = p.iloc[-1]/p.iloc[-12:].max()-1
vol = p.pct_change().iloc[-12:].std()

def cible(style, agent):
    s = agent.setdefault("etat", {})
    if style == "evolue": return strategie_pea.cible(agent["genome"], p, s, agent.get("valeur", agent["depart"]), agent.get("pic", agent["depart"]))
    if style == "paresseux": return {"SP500": 1.0}
    if style == "prudent": return {"SP500": .30, "EUROPE": .18, "EMERGENTS": .12}
    if style in ("tortue", "vigilante"):
        w = {"SP500": .5, "EUROPE": .3, "EMERGENTS": .2}
        if style == "vigilante":
            if agent.get("valeur", 1e9) / max(agent.get("pic", agent.get("depart", 10000)), 1) - 1 < -0.15: s["abri"] = True
            if s.get("abri"):
                if p.iloc[-1]["SP500"] > ma10["SP500"]: s["abri"] = False
                else: return {}
        return w
    if style == "boussole":
        up = [a for a in ok if p.iloc[-1][a] > ma10[a]]
        return {a: min(CAP, 1/len(up)) for a in up} if up else {}
    if style == "fusee":
        top = [a for a in r12.sort_values(ascending=False).index[:2] if r12[a] > 0]
        return {a: .5 for a in top}
    if style == "chineur":
        return {a: .5 for a in dd.sort_values().index[:2]}
    if style == "equilibriste":
        inv = (1/vol); w = (inv/inv.sum()).to_dict()
        for _ in range(5):
            over = [k for k in w if w[k] > CAP]
            if not over: break
            extra = sum(w[k]-CAP for k in over); free = [k for k in w if w[k] < CAP]; tot = sum(w[k] for k in free)
            for k in over: w[k] = CAP
            for k in free: w[k] += extra*w[k]/tot
        return w
    raise ValueError(style)

RAISON = {"paresseux": "Témoin : tout sur le S&P 500, il ne bouge jamais.", "prudent": "Témoin : 60 % en actions, 40 % en liquidités, rééquilibré une fois par an.",
          "tortue": "Répartition fixe 50 % S&P 500, 30 % Europe, 20 % émergents, rééquilibrée une fois par an.",
          "boussole": "Garde seulement les fonds au-dessus de leur moyenne des 10 derniers mois.",
          "fusee": "Prend les 2 fonds qui ont le plus monté sur 12 mois (s'ils sont en hausse).",
          "chineur": "Prend les 2 fonds les plus en baisse par rapport à leur plus haut sur 12 mois.",
          "vigilante": "Comme la Tortue, mais se met à l'abri après une chute de 15 % et revient quand le S&P 500 repasse au-dessus de sa moyenne.",
          "equilibriste": "Met plus d'argent sur les fonds qui bougent le moins (12 derniers mois), 50 % maximum par fonds.",
          "evolue": "Applique les règles apprises en 200 générations de simulation (voir ses règles)."}
resume = []
for a in pf:
    st = a["style_code"]; first = not a.get("positions") and not a.get("historique")
    annuel = st in ("paresseux", "prudent", "tortue")
    last_rebal = a.get("etat", {}).get("dernier_reequilibrage", "")
    # valeur actuelle
    val = a["cash"] + sum(x["quantite"]*prix.get(x["code"], x["dernier_prix"]) for x in a.get("positions", []))
    for x in a.get("positions", []):
        if x["code"] in prix: x["dernier_prix"] = round(prix[x["code"]], 4); x["valeur"] = round(x["quantite"]*x["dernier_prix"], 2)
    a["valeur"] = round(val, 2); a["pic"] = max(a.get("pic", a["depart"]), val)
    a["mdd"] = round(max(a.get("mdd", 0), 1 - val/a["pic"]), 4)
    agir = first or not annuel or (annuel and last_rebal[:4] != mk["date"][:4])
    ordres = []
    if agir:
        w = cible(st, a)
        if a.get("plafond", True): w = {k: min(v, CAP) for k, v in w.items()}
        w = {k: v for k, v in w.items() if k in ok and v > 0}
        if st == "evolue" and not first and val > 0:      # ne bouge que si l'écart dépasse sa marge
            held0 = {x["code"]: x["quantite"]*prix.get(x["code"], x["dernier_prix"])/val for x in a.get("positions", [])}
            if max([abs(w.get(k, 0) - held0.get(k, 0)) for k in MAP] or [0]) <= a["genome"]["band"]: w = None
        if w is None: agir = False
    if agir:
        base = val*(1-FEE*sum(w.values())); target = {k: base*w.get(k, 0) for k in MAP}
        held = {x["code"]: x for x in a.get("positions", [])}
        for k in MAP:
            if k not in prix: continue
            now = held[k]["quantite"]*prix[k] if k in held else 0.0; diff = target[k] - now
            if abs(diff) < max(50, 0.02*val): continue      # on ne bouge pas pour quelques euros
            q = diff/prix[k]; fee = abs(diff)*FEE
            if k in held: held[k]["quantite"] = round(held[k]["quantite"] + q, 6)
            else: held[k] = {"code": k, "actif": MAP[k][2], "quantite": round(q, 6), "prix_achat": round(prix[k], 4), "dernier_prix": round(prix[k], 4)}
            if diff > 0 and k in held and held[k]["quantite"] > 0:
                old_q = held[k]["quantite"] - q
                held[k]["prix_achat"] = round(((old_q*held[k].get("prix_achat", prix[k])) + q*prix[k]) / held[k]["quantite"], 4)
            a["cash"] = round(a["cash"] - diff - fee, 2)
            ordres.append({"date": mk["date"], "moment": mk.get("moment", ""), "action": "achat" if diff > 0 else "vente", "actif": MAP[k][2],
                           "quantite": round(abs(q), 4), "prix": round(prix[k], 4), "montant": round(abs(diff), 2), "raison": RAISON[st],
                           "source": mk.get("sources", {}).get(MAP[k][0], "") + " ; EUR/USD : " + mk.get("eurusd_sources", "")})
        a["positions"] = [dict(x, valeur=round(x["quantite"]*x["dernier_prix"], 2)) for x in held.values() if x["quantite"] > 1e-6]
        if annuel: a.setdefault("etat", {})["dernier_reequilibrage"] = mk["date"]
    a.setdefault("historique", []).extend(ordres)
    a["valeur"] = round(a["cash"] + sum(x["quantite"]*x["dernier_prix"] for x in a["positions"]), 2)
    a.setdefault("courbe", []).append({"date": mk["date"], "valeur": a["valeur"]})
    a["maj"] = mk["date"]; a["moment"] = mk.get("moment", ""); a["exclus_seance"] = mk.get("exclus", {})
    json.dump(a, open(os.path.join(out, a["_id"] + ".json"), "w"), ensure_ascii=False, indent=1)
    resume.append(f'{a["agent"]}: {a["valeur"]:.2f} € ({len(ordres)} ordre(s))')
open(os.path.join(out, "resume.txt"), "w").write("\n".join(resume)); print("\n".join(resume))
