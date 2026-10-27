"""Agents « court terme » de la ville (ARGENT FICTIF, pour apprendre ; aucun ordre réel ; pas un conseil).
Ils décident toutes les ~10 minutes pendant la bourse de New York, à partir des bougies de 5 minutes du jour.
Même code pour l'entraînement (backtest) et pour le direct (cours_live.py + seance_ct.py)."""
import math
FEE = 0.001           # 0,1 % par achat ou vente
MAXPOS, PART = 2, 0.5 # 2 positions au plus, 50 % de la valeur chacune
FIN = 15 * 60 + 40    # 15h40 à New York : tout est revendu (on finit la journée sans position)
DEBUT = 9 * 60 + 45   # pas d'achat avant 9h45 (laisser passer l'ouverture)

def signaux(bars):
    """bars = liste de bougies 5 min du jour [(minute_ny, open, high, low, close, volume)], dans l'ordre. Renvoie un dict de signaux."""
    if not bars: return None
    c = [b[4] for b in bars]; last = c[-1]; m = bars[-1][0]
    def ret(k):  # rendement sur k minutes
        n = k // 5
        return last / c[-1 - n] - 1 if len(c) > n else last / bars[0][1] - 1
    pv = sum((b[2] + b[3] + b[4]) / 3 * b[5] for b in bars); vol = sum(b[5] for b in bars)
    vwap = pv / vol if vol > 0 else sum(c) / len(c)
    g = [max(0, c[i] - c[i - 1]) for i in range(1, len(c))][-14:]; l = [max(0, c[i - 1] - c[i]) for i in range(1, len(c))][-14:]
    rsi = 50.0 if not g else (100.0 if sum(l) == 0 else 100 - 100 / (1 + (sum(g) / len(g)) / (sum(l) / len(l))))
    orb = [b for b in bars if b[0] < 10 * 60]
    return dict(minute=m, last=last, open=bars[0][1], ret15=ret(15), ret30=ret(30), ret60=ret(60), ret_jour=last / bars[0][1] - 1,
                vwap=vwap, rsi=rsi, or_high=max(b[2] for b in orb) if orb else None, or_low=min(b[3] for b in orb) if orb else None, n=len(bars))

STYLES = {
    "eclair":    dict(nom="élan du moment", params=dict(thr=0.003, tp=0.008, sl=0.004)),
    "elastique": dict(nom="rebond après un excès", params=dict(rsi_lo=28, rsi_hi=55, dev=0.003, tp=0.006, sl=0.006)),
    "starter":   dict(nom="cassure du haut de l'ouverture", params=dict(buf=0.0005, tp=0.01, sl=0.005)),
}

def sortie(style, p, pos, s):
    """Raison de vendre une position ouverte, ou None."""
    ch = s["last"] / pos["prix_achat"] - 1
    if s["minute"] >= FIN: return "fin de journée : on revend tout"
    if ch >= p["tp"]: return f"objectif atteint (+{ch*100:.2f} %)"
    if ch <= -p["sl"]: return f"coupe la perte ({ch*100:.2f} %)"
    if style == "elastique" and s["rsi"] > p["rsi_hi"]: return "le rebond a eu lieu"
    if style == "starter" and s["or_low"] and s["last"] < s["or_low"]: return "repasse sous le bas de l'ouverture"
    return None

def entree(style, p, sig, deja):
    """Liste ordonnée des achats possibles [(ticker, raison)]."""
    c = []
    for t, s in sig.items():
        if s is None or t in deja or s["minute"] < DEBUT or s["minute"] >= FIN - 20: continue
        if style == "eclair" and s["ret30"] > p["thr"] and s["last"] > s["vwap"] and s["rsi"] < 75:
            c.append((s["ret30"], t, f"monte fort : +{s['ret30']*100:.2f} % en 30 min, au-dessus de son prix moyen du jour"))
        if style == "elastique" and s["rsi"] < p["rsi_lo"] and s["last"] < s["vwap"] * (1 - p["dev"]):
            c.append((-s["rsi"], t, f"a trop baissé d'un coup (RSI {s['rsi']:.0f}), {(1-s['last']/s['vwap'])*100:.2f} % sous son prix moyen du jour"))
        if style == "starter" and s["minute"] >= 10 * 60 and s["or_high"] and s["last"] > s["or_high"] * (1 + p["buf"]) and s["ret15"] > 0:
            c.append((s["last"] / s["or_high"], t, f"dépasse le plus haut de la première demi-heure ({s['or_high']:.2f})"))
    return [(t, r) for _, t, r in sorted(c, reverse=True)]

def pas(style, p, etat, sig, prix_eur, valeur_eur):
    """Un pas de décision. etat = {"positions": {t: {qte, prix_achat(USD), achat_eur}}, "cash": €, "faits": [tickers déjà joués aujourd'hui]}.
    prix_eur[t] = prix en euros. Renvoie la liste des ordres."""
    ordres = []
    for t in list(etat["positions"]):
        s = sig.get(t)
        if s is None: continue
        why = sortie(style, p, etat["positions"][t], s)
        if why:
            q = etat["positions"].pop(t)["qte"]; m = q * prix_eur[t]; etat["cash"] += m * (1 - FEE)
            ordres.append(dict(action="vente", t=t, qte=q, montant=m, raison=why))
    if sig and min((s["minute"] for s in sig.values() if s), default=0) < FIN:
        for t, why in entree(style, p, sig, set(etat["positions"]) | set(etat["faits"])):
            if len(etat["positions"]) >= MAXPOS: break
            m = min(PART * valeur_eur, etat["cash"] / (1 + FEE))
            if m < 100: break
            q = m / prix_eur[t]; etat["cash"] -= m * (1 + FEE)
            etat["positions"][t] = dict(qte=q, prix_achat=sig[t]["last"]); etat["faits"].append(t)
            ordres.append(dict(action="achat", t=t, qte=q, montant=m, raison=why))
    return ordres
