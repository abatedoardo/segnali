"""Scrive docs/data.json, letto dalla dashboard (GitHub Pages)."""
import json
import os
import numpy as np
import config
from engine import portfolio as pf


def _num(x, nd=3):
    try:
        x = float(x)
        return None if np.isnan(x) else round(x, nd)
    except Exception:
        return None


def write(now, dstr, state, px, rows, news, brain, regime_ok, engine, log):
    eq = pf.equity(state, px)
    positions = []
    for t, p in state["positions"].items():
        price = px.get(t, p["last_px"])
        positions.append({"ticker": t, "name": config.WATCHLIST[t][0], "market": config.WATCHLIST[t][1],
                          "shares": round(p["shares"], 4), "entry": round(p["entry"], 2), "price": round(price, 2),
                          "value": round(p["shares"] * price, 2), "pnl_pct": round((price / p["entry"] - 1) * 100, 2),
                          "since": p["entry_date"], "score": rows.get(t, {}).get("score")})
    signals = []
    for t, r in sorted(rows.items(), key=lambda kv: -kv[1]["score"]):
        last = r["last"]
        signals.append({"ticker": t, "name": config.WATCHLIST[t][0], "market": config.WATCHLIST[t][1],
                        "score": r["score"], "rule": round(r["rule"], 3), "ml_prob": r["ml_prob"],
                        "reasons": r["reasons"], "sig": {k: round(v, 2) for k, v in r["sig"].items()},
                        "rsi": _num(last["rsi14"], 1), "ret20": _num(last["ret20"] * 100, 1),
                        "price": _num(px.get(t), 2), "held": t in state["positions"],
                        "news": news.get(t, {}).get("headlines", [])[:3]})
    # esiti reali dei segnali forti registrati (quanto ci ha preso finora)
    live = None
    if log is not None and not log.empty and len(log["date"].unique()) > config.HORIZON:
        dates = sorted(log["date"].unique())
        L = log.pivot_table(index="date", columns="ticker", values="price_eur")
        fwd = L.shift(-config.HORIZON) / L - 1
        S = log.pivot_table(index="date", columns="ticker", values="score")
        m = (S > brain["params"]["buy_th"]) & fwd.notna()
        if m.values.sum() >= 5:
            live = {"n": int(m.values.sum()), "avg_ret": round(float(fwd[m].stack().dropna().mean() * 100), 2),
                    "hit": round(float((fwd[m].stack().dropna() > 0).mean() * 100), 1),
                    "all_avg": round(float(fwd.stack().dropna().mean() * 100), 2), "days": len(dates)}
    out = {
        "updated": now, "market_date": dstr, "regime_ok": regime_ok, "news_engine": engine,
        "capital": config.START_CAPITAL, "equity": round(eq, 2), "cash": round(state["cash"], 2),
        "start": state["start"], "history": state["history"], "positions": positions,
        "trades": state["trades"][-60:][::-1], "signals": signals,
        "brain": {"weights": brain["weights"], "ic": brain["ic"], "n": brain["n"], "hit": brain["hit"],
                  "live_ic": brain["live_ic"], "ml": brain["ml"], "params": brain["params"],
                  "weight_history": brain["weight_history"][-180:], "journal": brain["journal"][-60:][::-1],
                  "backtest": brain["backtest"]},
        "labels": config.SIGNAL_LABELS, "live_results": live, "horizon": config.HORIZON,
    }
    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w") as fh:
        json.dump(out, fh, ensure_ascii=False, default=str)
