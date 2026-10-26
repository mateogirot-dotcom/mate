"""Stratégie « évoluée » de la Tour PEA (argent fictif) : un génome de règles simples, appris par simulation.
Utilisée à la fois par l'entraînement (evolution_pea.py) et par la séance en direct (seance_pea.py)."""
ASSETS = ["SP500", "NASDAQ", "EUROPE", "FRANCE", "EMERGENTS"]
CAP = 0.5

def cible(g, p, etat, val, pic):
    """g = génome ; p = DataFrame des prix mensuels en euros (dernière ligne = maintenant) ; renvoie {fonds: poids} (le reste en liquidités)."""
    ok = [a for a in ASSETS if a in p.columns]
    last = p.iloc[-1]
    if g["on"]["stop"]:
        if pic > 0 and val / pic - 1 < -g["stop"]: etat["abri"] = True
        if etat.get("abri"):
            if "SP500" in ok and last["SP500"] > p["SP500"].iloc[-10:].mean(): etat["abri"] = False
            else: return {}
    w = {a: g["w0"][a] for a in ok}; s = sum(w.values()) or 1; w = {a: v / s for a, v in w.items()}
    if g["on"]["elan"] and len(p) > g["mom_w"]:
        r = (last / p.iloc[-1 - g["mom_w"]] - 1)[ok].sort_values(ascending=False)
        for a in r.index[:g["mom_top"]]:
            if r[a] > 0: w[a] += g["mom_boost"]
    if g["on"]["volatilite"] and len(p) > 12:
        vol = p[ok].pct_change().iloc[-12:].std(); inv = 1 / vol.clip(lower=1e-4); inv = inv / inv.sum()
        w = {a: (1 - g["vol_mix"]) * w[a] + g["vol_mix"] * float(inv[a]) for a in ok}
    if g["on"]["rachat"]:
        dd = last[ok] / p[ok].iloc[-12:].max() - 1
        for a in ok:
            if dd[a] < -g["dip_thr"]: w[a] += g["dip_boost"]
    s = sum(w.values()) or 1; w = {a: v / s for a, v in w.items()}
    if g["on"]["tendance"]:
        ma = p[ok].iloc[-g["trend_w"]:].mean()
        w = {a: v * (g["trend_keep"] if last[a] < ma[a] else 1) for a, v in w.items()}
    return {a: min(CAP, v * g["invest"]) for a, v in w.items() if v * g["invest"] > 0.005}

NOMS_REGLES = {"tendance": "suivre la tendance", "elan": "élan récent", "rachat": "racheter après une chute", "volatilite": "préférer ce qui bouge le moins", "stop": "se mettre à l'abri après une perte"}
FONDS = {"SP500": "S&P 500", "NASDAQ": "Nasdaq-100", "EUROPE": "Europe", "FRANCE": "France", "EMERGENTS": "pays émergents"}

def regles(g):
    p = lambda x: f"{round(x * 100)} %"
    w = sorted(g["w0"].items(), key=lambda kv: -kv[1]); s = sum(g["w0"].values()) or 1
    L = [f"Part investie visée : {p(g['invest'])} (le reste en liquidités). Répartition de base : " + ", ".join(f"{FONDS[a]} {p(v / s)}" for a, v in w if v / s >= 0.05) + "."]
    on = g["on"]
    if on["elan"]: L.append(f"Ajoute du poids aux {g['mom_top']} fonds qui ont le plus monté sur {g['mom_w']} mois (+{round(g['mom_boost'] * 100)} points chacun).")
    if on["volatilite"]: L.append(f"Mélange à {p(g['vol_mix'])} avec une répartition qui favorise les fonds les plus calmes.")
    if on["rachat"]: L.append(f"Un fonds tombé de plus de {p(g['dip_thr'])} sous son plus haut sur 12 mois reçoit +{round(g['dip_boost'] * 100)} points.")
    if on["tendance"]: L.append(f"Un fonds sous sa moyenne des {g['trend_w']} derniers mois : garde seulement {p(g['trend_keep'])} de sa part.")
    if on["stop"]: L.append(f"Si le portefeuille perd plus de {p(g['stop'])} depuis son plus haut : tout en liquidités, jusqu'à ce que le S&P 500 repasse au-dessus de sa moyenne de 10 mois.")
    L.append(f"Jamais plus de 50 % sur un fonds. Ne rééquilibre que si l'écart dépasse {round(g['band'] * 100)} points.")
    return L
