# Prix de clôture du jour pour la Tour PEA (argent fictif), avec 2 sources indépendantes.
# Source 1 : Yahoo Finance (yfinance). Source 2 : Stooq (CSV). Résultat : parquet-pea/data/prix_jour.json
import io, json, urllib.request, datetime as dt
import yfinance as yf, pandas as pd
T = {"SPY": "spy.us", "QQQ": "qqq.us", "VGK": "vgk.us", "EWQ": "ewq.us", "EEM": "eem.us", "EURUSD": "eurusd"}
out = {"genere_le": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "prix": {}}
for t, s in T.items():
    r = {}
    try:
        h = yf.Ticker("EURUSD=X" if t == "EURUSD" else t).history(period="7d", interval="1d", auto_adjust=False)["Close"].dropna()
        r["yahoo"] = {"date": str(h.index[-1].date()), "prix": round(float(h.iloc[-1]), 6)}
    except Exception as e:
        r["yahoo"] = {"erreur": str(e)[:120]}
    try:
        raw = urllib.request.urlopen(f"https://stooq.com/q/l/?s={s}&f=sd2t2ohlcv&h&e=csv", timeout=30).read().decode()
        d = pd.read_csv(io.StringIO(raw)).iloc[0]
        r["stooq"] = {"date": str(d["Date"]), "prix": round(float(d["Close"]), 6)}
    except Exception as e:
        r["stooq"] = {"erreur": str(e)[:120]}
    out["prix"][t] = r
open("parquet-pea/data/prix_jour.json", "w").write(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
