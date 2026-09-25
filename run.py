"""Uso:  python run.py daily   (segnali + portfolio, 2 volte al giorno)
       python run.py learn   (auto-miglioramento settimanale)"""
import math
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
from engine import data, features, learner, news as newsmod, notify, portfolio as pf, storage

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def journal_add(brain, lines, date):
    for l in lines:
        print("  ·", l)
        brain["journal"].append({"date": date, "text": l})
    brain["journal"] = brain["journal"][-150:]


def score_today(brain, feats, news):
    rows, date_of = {}, {}
    w, scale = brain["weights"], brain["rule_scale"] or 0.3
    for t, f in feats.items():
        last = f.dropna(subset=["close"]).iloc[-1]
        date_of[t] = f.dropna(subset=["close"]).index[-1]
        sig = {s: float(last[s]) for s in config.SIGNALS}
        sig["news"] = float(news.get(t, {}).get("score", 0.0))
        raw = sum(w[s] * sig[s] for s in config.SIGNALS)
        rows[t] = {"sig": sig, "rule": float(np.tanh(raw / (2 * scale))), "contrib":
                   {s: w[s] * sig[s] / (2 * scale) for s in config.SIGNALS}, "last": last}
    ml = {}
    for d in set(date_of.values()):
        ml.update({t: p for t, p in learner.ml_predict(feats, d).items() if date_of.get(t) == d})
    b = brain["ml"].get("blend", 0) if ml else 0
    for t, r in rows.items():
        p = ml.get(t)
        r["ml_prob"] = None if p is None else round(float(p), 3)
        ms = 0.0 if p is None else float(np.clip((p - 0.5) * 4, -1, 1))
        r["score"] = round((1 - b) * r["rule"] + b * ms if p is not None else r["rule"], 3)
        top = sorted(r["contrib"].items(), key=lambda kv: -abs(kv[1]))[:3]
        r["reasons"] = [f"{config.SIGNAL_LABELS[s]} {'▲' if v > 0 else '▼'}" for s, v in top if abs(v) > 0.03]
        if p is not None and b > 0 and abs(ms) > 0.2:
            r["reasons"].append(f"Modello ML {p:.0%} prob. di battere l'indice")
    return rows


def run_daily(trade=True, brain=None):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    brain = brain or storage.load_json("brain.json", None)
    if brain is None:
        print("Primo avvio: addestramento iniziale...")
        return run_learn(then_trade=True)
    state = storage.load_json("portfolio.json", pf.new_state())
    seen = storage.load_json("news_seen.json", {})
    log = storage.load_log()

    prices = data.load_prices("3y")
    feats = features.build_all(prices)
    mdate = prices[config.BENCH_US].index[-1]
    dstr = str(mdate.date())

    print("Notizie...")
    news = newsmod.fetch_news(seen)
    engine = news.pop("_engine", "nessuno")
    journal_add(brain, learner.update_live(brain, log, prices), dstr)

    rows = score_today(brain, feats, news)
    eur = data.to_eur(data.close_panel(prices))
    px = {t: float(eur[t].dropna().iloc[-1]) for t in rows if t in eur}
    atr = {t: float(r["last"]["atr_pct"]) for t, r in rows.items() if not math.isnan(r["last"]["atr_pct"])}
    regime_ok = bool(feats[config.BENCH_US]["bench_trend"].iloc[-1] > 0)
    score = {t: r["score"] for t, r in rows.items()}
    reasons = {t: ", ".join(r["reasons"][:2]) for t, r in rows.items()}

    trades = []
    if state["start"] is None:
        state["start"] = dstr
        state["bench_start"] = {t: float(eur[t].dropna().iloc[-1]) for t in config.bench_mix(eur.columns)}
    if trade:
        trades = pf.decide(state, dstr, score, px, atr, regime_ok, brain["params"], reasons)
        for tr in trades:
            tr["name"] = config.WATCHLIST[tr["ticker"]][0]
        state["trades"] = (state["trades"] + trades)[-500:]
    eq = pf.equity(state, px)
    bm = {t: w for t, w in config.bench_mix([c for c in eur.columns if c in state["bench_start"]]).items()}
    bench_eq = config.START_CAPITAL * sum(w * float(eur[t].dropna().iloc[-1]) / state["bench_start"][t]
                                          for t, w in bm.items())
    state["history"] = [h for h in state["history"] if h[0] != dstr] + [[dstr, round(eq, 2), round(bench_eq, 2)]]

    # registro segnali (per imparare quando si conosce l'esito)
    new = pd.DataFrame([{"date": dstr, "ticker": t, **{s: round(r["sig"][s], 4) for s in config.SIGNALS},
                         "score": r["score"], "ml_prob": r["ml_prob"], "price_eur": round(px.get(t, np.nan), 4)}
                        for t, r in rows.items()])
    log = pd.concat([log[log["date"] != dstr] if not log.empty else log, new], ignore_index=True)
    brain["weight_history"] = [h for h in brain["weight_history"] if h["date"] != dstr] + \
                              [{"date": dstr, **brain["weights"], "ml": brain["ml"].get("blend", 0)}]
    brain["weight_history"] = brain["weight_history"][-400:]

    storage.save_json("portfolio.json", state)
    storage.save_json("brain.json", brain)
    storage.save_json("news_seen.json", seen)
    storage.save_log(log)

    from engine import report
    report.write(now, dstr, state, px, rows, news, brain, regime_ok, engine, log)

    # Telegram
    top = sorted(rows.items(), key=lambda kv: -kv[1]["score"])[:5]
    msg = [f"<b>Segnali {dstr}</b> — portfolio {eq:,.0f}€ ({(eq / config.START_CAPITAL - 1) * 100:+.1f}%)"]
    msg += [f"{'🟢' if t['side'] == 'COMPRA' else '🔴'} {t['side']} {t['name']} {t['value']:.0f}€ — {t['why']}" for t in trades]
    msg += ["Migliori punteggi:"] + [f"• {config.WATCHLIST[t][0]} {r['score']:+.2f}" for t, r in top]
    if trades or os.environ.get("NOTIFY_ALWAYS"):
        notify.send("\n".join(msg))
    print("\n".join(msg))


def run_learn(then_trade=False):
    brain = storage.load_json("brain.json", None) or learner.new_brain()
    log = storage.load_log()
    print("Scarico 5 anni di dati...")
    prices = data.load_prices("5y")
    feats = features.build_all(prices)
    eur = data.to_eur(data.close_panel(prices))
    dstr = str(prices[config.BENCH_US].index[-1].date())
    print("Apprendimento...")
    journal_add(brain, learner.learn(brain, feats, prices, eur, log), dstr)
    storage.save_json("brain.json", brain)
    run_daily(trade=then_trade, brain=brain)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    run_learn() if mode == "learn" else run_daily()
