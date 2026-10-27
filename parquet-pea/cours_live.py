# Cours EN DIRECT pour la ville (argent fictif) : dernier prix de chaque fonds, 2 sources (Yahoo 1 minute + Nasdaq), et EUR/USD.
# Résultat : parquet-pea/data/cours_live.json — sert seulement à mettre à jour l'affichage des valeurs, jamais à passer un ordre.
import json, urllib.request, datetime as dt, sys, os
import yfinance as yf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import court_terme
TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "GLD", "IEF", "VGK", "EWQ"]
out = {"maj_utc": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "prix_usd": {}, "detail": {}, "ecartes": {}, "signaux": {}}
def nasdaq(t):
    req = urllib.request.Request(f"https://api.nasdaq.com/api/quote/{t}/info?assetclass=etf", headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    j = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())["data"]
    pd_ = j["primaryData"]; return float(pd_["lastSalePrice"].replace("$", "").replace(",", "")), pd_.get("lastTradeTimestamp", ""), j.get("marketStatus", "")
for t in TICKERS:
    d = {}
    try:
        h = yf.Ticker(t).history(period="1d", interval="1m", prepost=False)["Close"].dropna()
        if len(h) == 0: h = yf.Ticker(t).history(period="5d", interval="1d")["Close"].dropna()
        d["yahoo"] = round(float(h.iloc[-1]), 4); d["yahoo_heure"] = str(h.index[-1])
        # signaux court terme : bougies de 5 minutes TERMINÉES du jour (heure de New York)
        m1 = yf.Ticker(t).history(period="1d", interval="1m", prepost=False)
        if len(m1):
            m1.index = m1.index.tz_convert("America/New_York")
            b5 = m1.resample("5min", label="left", closed="left").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
            now = dt.datetime.now(dt.timezone.utc).astimezone(m1.index.tz)
            b5 = b5[b5.index + dt.timedelta(minutes=5) <= now] if (now - b5.index[-1].to_pydatetime()).total_seconds() < 6 * 3600 else b5
            bars = [(i.hour * 60 + i.minute, r.Open, r.High, r.Low, r.Close, r.Volume) for i, r in b5.iterrows()]
            sg = court_terme.signaux(bars)
            if sg: sg["date"] = str(b5.index[-1].date()); out["signaux"][t] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in sg.items()}
    except Exception as e: d["yahoo_err"] = str(e)[:100]
    try: d["nasdaq"], d["nasdaq_heure"], out["marche"] = nasdaq(t)
    except Exception as e: d["nasdaq_err"] = str(e)[:100]
    out["detail"][t] = d
    if "yahoo" in d and "nasdaq" in d and abs(d["yahoo"] / d["nasdaq"] - 1) < 0.01: out["prix_usd"][t] = d["nasdaq"]
    else: out["ecartes"][t] = "les 2 sources ne concordent pas ou une manque"
fx = {}
try:
    h = yf.Ticker("EURUSD=X").history(period="1d", interval="1m")["Close"].dropna()
    if len(h) == 0: h = yf.Ticker("EURUSD=X").history(period="5d")["Close"].dropna()
    fx["yahoo"] = round(float(h.iloc[-1]), 5)
except Exception as e: fx["yahoo_err"] = str(e)[:100]
try: fx["bce"] = float(json.loads(urllib.request.urlopen("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=20).read().decode())["rates"]["USD"])
except Exception as e: fx["bce_err"] = str(e)[:100]
out["eurusd_detail"] = fx
if "yahoo" in fx and "bce" in fx and abs(fx["yahoo"] / fx["bce"] - 1) < 0.01: out["eurusd"] = fx["yahoo"]
json.dump(out, open("parquet-pea/data/cours_live.json", "w"), indent=1)
print(json.dumps(out)[:1500])
