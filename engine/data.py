"""Prezzi giornalieri da Yahoo Finance (gratis, via yfinance). SIMULATE=1 usa dati finti per i test."""
import os
import numpy as np
import pandas as pd
import config

ALL = list(dict.fromkeys(list(config.WATCHLIST) + [config.BENCH_US, config.BENCH_IT, config.FX]))


def _simulated(tickers, as_of):
    idx = pd.bdate_range(end="2027-06-30", periods=2200)
    out = {}
    mkt = np.random.default_rng(1).normal(0.0003, 0.011, len(idx))
    for i, t in enumerate(tickers):
        rng = np.random.default_rng(100 + i)
        drift = rng.normal(0.0002, 0.0004)
        beta = 0.3 if t == config.FX else rng.uniform(0.6, 1.4)
        e = rng.normal(0, 0.015, len(idx))
        r = np.zeros(len(idx))
        for k in range(1, len(idx)):  # un po' di momentum: così c'è qualcosa da imparare
            r[k] = drift + beta * mkt[k] + 0.08 * r[k - 1] + e[k]
        close = (1.1 if t == config.FX else rng.uniform(20, 400)) * np.exp(np.cumsum(r))
        hi = close * (1 + np.abs(rng.normal(0, 0.008, len(idx))))
        lo = close * (1 - np.abs(rng.normal(0, 0.008, len(idx))))
        vol = rng.lognormal(15, 0.3, len(idx)) * (1 + 5 * np.abs(r))
        df = pd.DataFrame({"Open": close, "High": hi, "Low": lo, "Close": close, "Volume": vol}, index=idx)
        out[t] = df[df.index <= pd.Timestamp(as_of)]
    return out


def load_prices(period="3y"):
    """dict ticker -> DataFrame(Open, High, Low, Close, Volume)."""
    if os.environ.get("SIMULATE"):
        return _simulated(ALL, os.environ.get("SIM_DATE", "2026-09-24"))
    import time
    import yfinance as yf
    out, todo = {}, list(ALL)
    for attempt in range(3):  # Yahoo a volte limita le richieste: riprovo solo i mancanti
        try:
            raw = yf.download(todo, period=period, interval="1d", auto_adjust=True, group_by="ticker",
                              progress=False, threads=True)
        except Exception as e:
            print("Download fallito:", e)
            time.sleep(20 * (attempt + 1))
            continue
        _parse(raw, todo, out)
        todo = [t for t in ALL if t not in out]
        if not todo:
            break
        time.sleep(20 * (attempt + 1))
    missing = [t for t in ALL if t not in out]
    if missing:
        print("ATTENZIONE: dati mancanti per", missing)
    if config.BENCH_US not in out or config.FX not in out:
        raise SystemExit("Dati essenziali (SPY o cambio EUR/USD) non disponibili: riprovo alla prossima esecuzione.")
    return out


def _parse(raw, tickers, out):
    for t in tickers:
        try:
            df = raw[t][["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
        except (KeyError, TypeError):
            continue
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        if len(df) > 60:
            out[t] = df[~df.index.duplicated(keep="last")]


def close_panel(prices):
    """Tabella date x ticker dei prezzi di chiusura (buchi riempiti max 3 giorni)."""
    return pd.DataFrame({t: d["Close"] for t, d in prices.items()}).sort_index().ffill(limit=3)


def to_eur(panel):
    """Converte i prezzi USD in EUR."""
    fx = panel[config.FX]
    eur = panel.copy()
    for t in eur.columns:
        if t != config.FX and config.currency(t) == "USD":
            eur[t] = panel[t] / fx
    return eur
