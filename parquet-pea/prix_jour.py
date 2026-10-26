# Prix de clôture du jour pour la Tour PEA (argent fictif), avec 2 sources indépendantes.
# Source 1 : Yahoo Finance (yfinance). Source 2 : Nasdaq (fonds) et BCE via Frankfurter (EUR/USD). Résultat : parquet-pea/data/prix_jour.json
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
        if t == "EURUSD":
            j = json.loads(urllib.request.urlopen("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=30).read().decode())
            r["bce"] = {"date": j["date"], "prix": float(j["rates"]["USD"])}
        else:
            req = urllib.request.Request(f"https://api.nasdaq.com/api/quote/{t}/info?assetclass=etf", headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["data"]["primaryData"]
            r["nasdaq"] = {"date": j.get("lastTradeTimestamp", ""), "prix": float(j["lastSalePrice"].replace("$", "").replace(",", ""))}
    except Exception as e:
        r["source2"] = {"erreur": str(e)[:120]}
    out["prix"][t] = r
open("parquet-pea/data/prix_jour.json", "w").write(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
