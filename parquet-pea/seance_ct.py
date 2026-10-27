"""Pas de décision des agents COURT TERME (argent fictif, aucun ordre réel, pas un conseil).
Usage : python3 parquet-pea/seance_ct.py cours.json agents_ct.json sortie_dir
- cours.json : parquet-pea/data/cours_live.json (prix vérifiés à 2 sources + signaux des bougies 5 min)
- agents_ct.json : liste des documents des agents court terme (champ "_id" = id du document)
Écrit un fichier par agent (document complet mis à jour) + resume_ct.txt."""
import json, os, sys, datetime as dt
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import court_terme as CT
C = json.load(open(sys.argv[1])); A = json.load(open(sys.argv[2])); out = sys.argv[3]; os.makedirs(out, exist_ok=True)
fx = C.get("eurusd"); P = C.get("prix_usd", {}); SIG = C.get("signaux", {})
if not fx: print("pas d'EUR/USD vérifié : rien à faire"); sys.exit(0)
PEA = {"SPY": ("SP500", "Fonds PEA S&P 500"), "QQQ": ("NASDAQ", "Fonds PEA Nasdaq-100"), "VGK": ("EUROPE", "Fonds PEA Europe"), "EWQ": ("FRANCE", "Fonds PEA CAC 40 / France"), "EEM": ("EMERGENTS", "Fonds PEA pays émergents")}
NOMS = {"SPY": "S&P 500 (ETF SPY)", "QQQ": "Nasdaq 100 (ETF QQQ)", "IWM": "Petites entreprises US (ETF IWM)", "EFA": "Pays développés hors US (ETF EFA)", "EEM": "Pays émergents (ETF EEM)", "GLD": "Or (ETF GLD)", "IEF": "Obligations d'État US 7-10 ans (ETF IEF)"}
UNIV = {"parquet": ["SPY", "QQQ", "IWM", "EFA", "EEM", "GLD", "IEF"], "pea": list(PEA)}
paris = dt.datetime.fromisoformat(C["maj_utc"].replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Paris"))
stamp = paris.strftime("%Y-%m-%d %H:%M"); jour = (SIG.get("SPY") or {}).get("date") or C.get("date") or paris.strftime("%Y-%m-%d")
ouvert = bool(SIG) and "clos" not in str(C.get("marche", "")).lower()
res = []
for a in A:
    lg = a["ligue_ct"]; U = UNIV[lg]; e = a.setdefault("etat", {})
    if e.get("jour") != jour: e["jour"] = jour; e["faits"] = []
    pos = {}
    for x in a.get("positions", []):
        t = x["ticker_us"]; pos[t] = dict(qte=x["quantite"], prix_achat=x["prix_achat_us"])
    sig = {t: SIG.get(t) for t in U if t in P and SIG.get(t) and SIG[t].get("date") == jour}
    peur = {t: P[t] / fx for t in U if t in P}
    def val(): return a["cash"] + sum(q["qte"] * peur.get(t, q["prix_achat"] / fx) for t, q in pos.items())
    ordres = []
    if sig and (ouvert or pos):
        st = dict(positions=pos, cash=a["cash"], faits=e["faits"])
        ordres = CT.pas(a["ct_style"], a["ct_params"], st, sig, peur, val())
        a["cash"] = round(st["cash"], 2); pos = st["positions"]; e["faits"] = st["faits"]
    for o in ordres:
        t = o["t"]; h = dict(date=jour, moment=f"{stamp} (heure de Paris)", action=o["action"], actif=(PEA[t][1] if lg == "pea" else NOMS.get(t, t)), ticker=t,
                             quantite=round(o["qte"], 4), prix=round(peur[t] if lg == "pea" else P[t], 4), montant=round(o["montant"], 2), raison=o["raison"],
                             source=C.get("sources", "Nasdaq + Yahoo Finance ; EUR/USD Yahoo + BCE"))
        if o["action"] == "vente":
            ach = next((x for x in reversed(a.get("historique", [])) if x.get("ticker") == t and x["action"] == "achat"), None)
            if ach: h["resultat"] = round(o["montant"] * (1 - CT.FEE) - ach["montant"] * (1 + CT.FEE), 2)
        a.setdefault("historique", []).append(h)
    a["historique"] = a.get("historique", [])[-200:]
    newpos = []
    for t, q in pos.items():
        pe = peur.get(t, q["prix_achat"] / fx)
        x = dict(ticker_us=t, quantite=round(q["qte"], 6), prix_achat_us=q["prix_achat"], valeur=round(q["qte"] * pe, 2))
        if lg == "pea": x.update(code=PEA[t][0], actif=PEA[t][1], prix_achat=round(q["prix_achat"] / fx, 4), dernier_prix=round(pe, 4))
        else: x.update(ticker=t, actif=NOMS.get(t, t), prix_achat=q["prix_achat"], dernier_prix=round(P.get(t, q["prix_achat"]), 4), devise="USD")
        newpos.append(x)
    a["positions"] = newpos; v = round(val(), 2); a["valeur"] = v
    a["pic"] = max(a.get("pic", a["depart"]), v); a["mdd"] = round(max(a.get("mdd", 0), 1 - v / a["pic"]), 4)
    c = a.setdefault("courbe", [])
    if not c or c[-1]["date"] != stamp: c.append(dict(date=stamp, valeur=v))
    a["courbe"] = c[-300:]; a["maj"] = jour; a["moment"] = f"{stamp} (heure de Paris)"
    gains = [x.get("resultat", 0) for x in a["historique"] if x.get("date") == jour and "resultat" in x]
    a["jour_bilan"] = dict(date=jour, ordres=sum(1 for x in a["historique"] if x.get("date") == jour), resultat_ventes=round(sum(gains), 2))
    json.dump(a, open(os.path.join(out, a["_id"] + ".json"), "w"), ensure_ascii=False)
    res.append(f'{a["agent"]}: {v:.2f} € ({len(ordres)} ordre(s), {len(pos)} position(s))')
open(os.path.join(out, "resume_ct.txt"), "w").write("\n".join(res)); print("\n".join(res))
