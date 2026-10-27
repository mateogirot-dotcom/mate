# Historique intraday (bougies de 5 minutes, ~60 jours) pour entraîner les agents « court terme » (argent fictif).
import yfinance as yf, pandas as pd
T = ["SPY", "QQQ", "IWM", "EFA", "EEM", "GLD", "IEF", "VGK", "EWQ", "EURUSD=X"]
frames = []
for t in T:
    df = yf.Ticker(t).history(period="60d", interval="5m", prepost=False)
    if len(df) == 0: print(t, "vide"); continue
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy(); df["ticker"] = t.replace("=X", "")
    df.index = df.index.tz_convert("America/New_York"); frames.append(df)
    print(t, len(df), df.index.min(), df.index.max())
pd.concat(frames).to_csv("parquet-pea/data/intraday_5m.csv.gz", index_label="heure", compression="gzip")
