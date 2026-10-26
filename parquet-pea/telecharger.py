# Télécharge des prix MENSUELS ajustés (dividendes réinvestis) pour simuler un PEA (argent fictif).
# Sources : Yahoo Finance via yfinance ; secours : Stooq (CSV). Résultat : parquet-pea/data/*.csv
import os, io, urllib.request
import pandas as pd, yfinance as yf
os.makedirs("parquet-pea/data", exist_ok=True)
TICKERS = {"SPY":"sp500_usd","QQQ":"nasdaq100_usd","VGK":"europe_usd","EWQ":"france_usd","EEM":"emergents_usd","ACWI":"monde_usd","EURUSD=X":"eurusd"}
rapport = []
for t, nom in TICKERS.items():
    try:
        df = yf.download(t, start="1993-01-01", interval="1mo", auto_adjust=True, progress=False)
        s = df["Close"].squeeze().dropna()
        s.index = pd.to_datetime(s.index).to_period("M").to_timestamp("M")
        s.rename("close").to_csv(f"parquet-pea/data/{nom}.csv", index_label="date")
        rapport.append(f"{t} yahoo {len(s)} mois {s.index.min().date()} -> {s.index.max().date()}")
    except Exception as e:
        rapport.append(f"{t} yahoo ERREUR {e}")
# secours EUR/USD long (Stooq) si Yahoo commence trop tard
try:
    raw = urllib.request.urlopen("https://stooq.com/q/d/l/?s=eurusd&i=m", timeout=30).read().decode()
    d = pd.read_csv(io.StringIO(raw)); d["date"] = pd.to_datetime(d["Date"]).dt.to_period("M").dt.to_timestamp("M")
    d[["date","Close"]].rename(columns={"Close":"close"}).to_csv("parquet-pea/data/eurusd_stooq.csv", index=False)
    rapport.append(f"eurusd stooq {len(d)} mois {d['date'].min().date()} -> {d['date'].max().date()}")
except Exception as e:
    rapport.append(f"eurusd stooq ERREUR {e}")
open("parquet-pea/data/rapport.txt","w").write("\n".join(rapport)+"\n")
print("\n".join(rapport))
