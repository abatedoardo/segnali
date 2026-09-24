"""Indicatori tecnici e segnali di regola (ognuno tra -1 e +1), calcolati su tutta la storia."""
import numpy as np
import pandas as pd
import config

ML_FEATURES = ["ret5", "ret20", "ret60", "rsi14", "dist_sma50", "dist_sma200", "vol_ratio", "brk20",
               "atr_pct", "rs20", "vola20", "bench_trend", "bench_vola"]


def _rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def indicators(df, bench_close):
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    b = bench_close.reindex(c.index).ffill()
    f = pd.DataFrame(index=c.index)
    f["close"] = c
    r1 = c.pct_change()
    f["ret1"] = r1
    for n in (5, 20, 60):
        f[f"ret{n}"] = c.pct_change(n)
    f["rsi14"] = _rsi(c)
    sma50, sma200 = c.rolling(50).mean(), c.rolling(200, min_periods=120).mean()
    f["dist_sma50"] = c / sma50 - 1
    f["dist_sma200"] = c / sma200 - 1
    f["trend_up"] = ((c > sma50) & (sma50 > sma200)).astype(float) - ((c < sma50) & (sma50 < sma200)).astype(float)
    avgv = v.rolling(20).mean()
    f["vol_ratio"] = (v / avgv).where(avgv > 0, 1.0).fillna(1.0) if v.sum() > 0 else 1.0
    f["brk20"] = c / h.rolling(20).max().shift(1) - 1
    f["brk20_low"] = c / l.rolling(20).min().shift(1) - 1
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    f["atr_pct"] = tr.rolling(14).mean() / c
    f["vola20"] = r1.rolling(20).std()
    f["rs20"] = f["ret20"] - b.pct_change(20)
    bsma = b.rolling(200, min_periods=120).mean()
    f["bench_trend"] = (b / bsma - 1)
    f["bench_vola"] = b.pct_change().rolling(20).std()
    return f


def rule_signals(f):
    s = pd.DataFrame(index=f.index)
    vol60 = (f["vola20"] * np.sqrt(60)).replace(0, np.nan)
    s["momentum"] = np.tanh(f["ret60"] / vol60 * 0.7)
    s["trend"] = (0.6 * f["trend_up"] + 0.4 * np.tanh(f["dist_sma200"] * 5)).clip(-1, 1)
    rsi = f["rsi14"]
    s["mean_reversion"] = np.where(rsi < 30, (30 - rsi) / 20, np.where(rsi > 70, -(rsi - 70) / 20, 0.0)).clip(-1, 1)
    vr = f["vol_ratio"]
    s["breakout"] = np.where(f["brk20"] > -0.005, np.tanh((vr - 0.8) * 1.5).clip(0, 1),
                             np.where(f["brk20_low"] < 0.005, -np.tanh((vr - 0.8) * 1.5).clip(0, 1), 0.0))
    s["volume"] = np.where(vr > 1.5, np.sign(f["ret1"]) * np.tanh(vr - 1.5), 0.0)
    s["rel_strength"] = np.tanh(f["rs20"] * 8)
    s["news"] = 0.0  # le notizie storiche non sono gratis: questo segnale impara solo dal vivo
    return s.astype(float).fillna(0.0)


def build_all(prices):
    """dict ticker -> DataFrame con indicatori + segnali. Solo i titoli della watchlist."""
    out = {}
    for t in config.WATCHLIST:
        if t not in prices:
            continue
        bench = config.bench_for(t)
        bc = prices[bench]["Close"] if bench in prices else prices[t]["Close"]
        f = indicators(prices[t], bc)
        out[t] = pd.concat([f, rule_signals(f)], axis=1)
    return out


def forward_excess(prices, horizon=config.HORIZON):
    """Rendimento a 'horizon' giorni meno quello del benchmark: è l'esito con cui si giudica un segnale."""
    out = {}
    for t in config.WATCHLIST:
        if t not in prices:
            continue
        c = prices[t]["Close"]
        bench = config.bench_for(t)
        b = prices[bench]["Close"].reindex(c.index).ffill() if bench in prices else c
        fwd = c.shift(-horizon) / c - 1
        fb = b.shift(-horizon) / b - 1
        out[t] = fwd - (fb if t != bench else 0)
    return pd.DataFrame(out)
