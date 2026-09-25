"""Il 'cervello': impara quali segnali funzionano, allena un modello ML e ottimizza le regole.
Tutto con validazione su dati mai visti, per non illudersi (overfitting)."""
import itertools
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

import config
from engine import portfolio as pf
from engine.features import ML_FEATURES

PRICE_SIGNALS = [s for s in config.SIGNALS if s != "news"]
MODEL_PATH = "data/model.pkl"


def new_brain():
    return {"ic": {s: 0.0 for s in config.SIGNALS}, "n": {s: 0 for s in config.SIGNALS},
            "hit": {s: None for s in config.SIGNALS}, "weights": {s: 1 / len(config.SIGNALS) for s in config.SIGNALS},
            "rule_scale": 0.3, "params": dict(config.DEFAULT_PARAMS),
            "ml": {"auc": None, "blend": 0.0, "trained": None}, "evaluated": [], "weight_history": [],
            "journal": [], "backtest": None, "live_ic": {s: None for s in config.SIGNALS},
            "n_live": {s: 0 for s in config.SIGNALS}}


def weights_from_ic(ic, n, old=None, keep=0.0):
    """Peso = IC x fiducia statistica. Fiducia 0 se l'IC non si distingue dal caso (t<1.2), piena se t>=3.
    Segno negativo = il segnale viene invertito. 'keep' ammorbidisce i cambi rispetto ai pesi precedenti."""
    raw = {}
    for s in ic:
        # i rendimenti a 5 giorni si sovrappongono: le osservazioni indipendenti sono meno di quelle contate
        n_eff = min(max(n[s], 1), 350 if s != "news" else 99) / 1.5
        t = abs(ic[s]) * np.sqrt(n_eff) / 0.2  # dev. std tipica dell'IC giornaliero ~0.2
        raw[s] = ic[s] * float(np.clip((t - 1.2) / 1.8, 0, 1))
        if s == "news":  # fiducia crescente: piena solo dopo ~6 mesi di borsa valutati dal vivo
            raw[s] *= min(1.0, n[s] / 120)
    tot = sum(abs(v) for v in raw.values())
    if tot == 0:  # nessun segnale dimostrato: tengo i pesi precedenti (o uguali)
        return old or {s: round(1 / len(ic), 4) for s in ic}
    w = {s: v / tot for s, v in raw.items()}
    if old:
        w = {s: keep * old.get(s, 0) + (1 - keep) * w[s] for s in w}
        tot = sum(abs(v) for v in w.values()) or 1.0
        w = {s: v / tot for s, v in w.items()}
    return {s: round(v, 4) for s, v in w.items()}


# ---------- punteggi ----------
def panel(feats, col):
    return pd.DataFrame({t: f[col] for t, f in feats.items()})


def rule_raw(feats, weights, news=None):
    out = 0
    for s in config.SIGNALS:
        p = panel(feats, s)
        if s == "news" and news is not None:
            p = p.copy()
            for t, v in news.items():
                if t in p.columns:
                    p.iloc[-1, p.columns.get_loc(t)] = v
        out = out + weights.get(s, 0) * p
    return out


def ml_frame(feats):
    rows = []
    for t, f in feats.items():
        d = f[ML_FEATURES].copy()
        d["ticker"] = t
        d.index.name = "date"
        rows.append(d)
    return pd.concat(rows).reset_index()


def daily_ic(feats, fwd, sig):
    """Correlazione di rango giornaliera tra segnale e rendimento successivo (Information Coefficient)."""
    s = panel(feats, sig).reindex(fwd.index)
    ics = s.rank(axis=1).corrwith(fwd.rank(axis=1), axis=1)
    return ics.dropna()


def hit_rate(feats, fwd, sig, lo=None, hi=None):
    s = panel(feats, sig).reindex(fwd.index)
    if lo is not None:
        s, f = s.loc[lo:hi], fwd.loc[lo:hi]
    else:
        f = fwd
    m = (s.abs() > 0.4) & f.notna()
    if m.values.sum() < 30:
        return None
    return round(float(((np.sign(s) == np.sign(f)) & m).values.sum() / m.values.sum()), 3)


# ---------- backtest ----------
def backtest(score, px_eur, atr, regime, params, reasons=None):
    st = pf.new_state()
    eqs, ntr = [], 0
    for d in score.index:
        sc = score.loc[d].dropna().to_dict()
        px = px_eur.loc[d].dropna().to_dict() if d in px_eur.index else {}
        at = atr.loc[d].dropna().to_dict() if d in atr.index else {}
        ntr += len(pf.decide(st, str(d.date()), sc, px, at, bool(regime.get(d, True)), params))
        eqs.append(pf.equity(st, px))
    eq = pd.Series(eqs, index=score.index)
    return eq, ntr


def stats(eq):
    r = eq.pct_change().dropna()
    if len(r) < 5:
        return {"ret": 0, "sharpe": 0, "maxdd": 0}
    sharpe = float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else 0.0
    dd = float((eq / eq.cummax() - 1).min())
    return {"ret": round(float(eq.iloc[-1] / eq.iloc[0] - 1) * 100, 2), "sharpe": round(sharpe, 2),
            "maxdd": round(dd * 100, 2)}


def bench_equity(px_eur, idx):
    b = sum(w * px_eur[t].reindex(idx).ffill() / px_eur[t].reindex(idx).ffill().iloc[0]
            for t, w in config.bench_mix(px_eur.columns).items())
    return b * config.START_CAPITAL


# ---------- apprendimento settimanale ----------
def learn(brain, feats, prices, px_eur, log):
    from engine.features import forward_excess
    fwd = forward_excess(prices)
    dates = fwd.dropna(how="all").index
    dates = dates[dates >= dates[0] + pd.Timedelta(days=300)]  # salta il riscaldamento delle medie
    N = len(dates)
    test_len = min(250, N // 4)
    T1 = dates[N - test_len]  # inizio periodo di test (mai visto in allenamento)
    V0 = dates[max(0, N - 2 * test_len)]
    journal = []
    atr = panel(feats, "atr_pct")
    bench = config.BENCH_US
    regime = (feats[bench]["bench_trend"] > 0) if bench in feats else pd.Series(dtype=bool)

    # 1) IC storico dei segnali di prezzo (media esponenziale: il passato recente conta di più)
    ic_train, ic_full, n_full = {}, {}, {}
    for s in PRICE_SIGNALS:
        d = daily_ic(feats, fwd.loc[dates], s)
        ic_train[s] = float(d.loc[:V0].ewm(halflife=120).mean().iloc[-1]) if len(d.loc[:V0]) > 20 else 0.0
        ic_full[s] = float(d.ewm(halflife=120).mean().iloc[-1]) if len(d) > 20 else 0.0
        n_full[s] = len(d)
        brain["hit"][s] = hit_rate(feats, fwd.loc[dates], s)
    old_w = dict(brain["weights"])
    for s in PRICE_SIGNALS:
        live, nl = brain["live_ic"].get(s), brain["n_live"].get(s, 0)
        lw = nl / (nl + 250)  # i risultati dal vivo contano di più man mano che si accumulano
        brain["ic"][s] = round(ic_full[s] if live is None else (1 - lw) * ic_full[s] + lw * live, 4)
        brain["n"][s] = n_full[s]
    first = brain["ml"]["trained"] is None
    brain["weights"] = weights_from_ic(brain["ic"], brain["n"], None if first else old_w, keep=0.5)
    for s in config.SIGNALS:
        o, n = old_w.get(s, 0), brain["weights"][s]
        if abs(n - o) > 0.03:
            journal.append(f"Peso '{config.SIGNAL_LABELS[s]}' {o:+.2f} → {n:+.2f} (IC {brain['ic'][s]:+.3f})")

    raw_all = rule_raw(feats, brain["weights"]).loc[dates]
    brain["rule_scale"] = round(float(np.nanstd(raw_all.values)) or 0.3, 5)

    # 2) modello ML con validazione walk-forward
    mf = ml_frame(feats)
    fs = fwd.stack().rename("y")
    fs.index.names = ["date", "ticker"]
    mf = mf.merge(fs.reset_index(), on=["date", "ticker"], how="left")
    mf = mf.dropna(subset=ML_FEATURES + ["y"])
    mf = mf[mf["date"].isin(dates)]
    gap = pd.Timedelta(days=config.HORIZON * 2)
    tr, te = mf[mf["date"] < T1 - gap], mf[mf["date"] >= T1]
    mk = lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150,
                                                l2_regularization=1.0, min_samples_leaf=100, random_state=0)
    ml_oos = None
    if len(tr) > 2000 and len(te) > 200:
        m = mk().fit(tr[ML_FEATURES], tr["y"] > 0)
        p = m.predict_proba(te[ML_FEATURES])[:, 1]
        auc = float(roc_auc_score(te["y"] > 0, p))
        te = te.assign(p=p)
        ml_oos = te.pivot_table(index="date", columns="ticker", values="p")
        blend = float(np.clip((auc - 0.505) * 8, 0, 0.5))
        final = mk().fit(mf[ML_FEATURES], mf["y"] > 0)
        os.makedirs("data", exist_ok=True)
        with open(MODEL_PATH, "wb") as fh:
            pickle.dump(final, fh)
        prev = brain["ml"].get("auc")
        brain["ml"] = {"auc": round(auc, 4), "blend": round(blend, 3), "trained": str(pd.Timestamp.now().date()),
                       "n_train": int(len(mf))}
        journal.append(f"Modello ML riallenato su {len(mf):,} esempi: AUC su dati mai visti {auc:.3f}"
                       + (f" (prima {prev:.3f})" if prev else "") + f" → peso ML {blend:.0%}")

    # 3) punteggio finale storico (per backtest)
    def final_score(weights, scale, lo, hi):
        rs = np.tanh(rule_raw(feats, weights).loc[lo:hi] / (2 * scale))
        if ml_oos is not None and brain["ml"]["blend"] > 0:
            ms = ((ml_oos.reindex(rs.index) - 0.5) * 4).clip(-1, 1)
            b = brain["ml"]["blend"]
            rs = rs.where(ms.isna(), (1 - b) * rs + b * ms)
        return rs

    # pesi calcolati solo sul passato del periodo di validazione/test
    w_train = weights_from_ic({**brain["ic"], **ic_train}, brain["n"])
    sc_train = float(np.nanstd(rule_raw(feats, w_train).loc[:V0].values)) or 0.3

    # 4) ottimizzazione regole: scelgo su validazione, confermo su test
    val_score = final_score(w_train, sc_train, V0, dates[N - test_len - 1])
    cur = brain["params"]
    def sharpe_of(pr, sc):
        return stats(backtest(sc, px_eur, atr, regime, pr)[0])["sharpe"]
    cur_val = sharpe_of(cur, val_score)
    best, best_val = cur, cur_val
    for combo in itertools.product(*config.PARAM_GRID.values()):
        pr = {**cur, **dict(zip(config.PARAM_GRID, combo))}
        v = sharpe_of(pr, val_score)
        if v > best_val:
            best, best_val = pr, v
    test_score = final_score(w_train, sc_train, T1, dates[-1])
    if best is not cur and best_val > cur_val + 0.15:
        t_new, t_cur = sharpe_of(best, test_score), sharpe_of(cur, test_score)
        if t_new >= t_cur:
            changed = {k: f"{cur[k]}→{best[k]}" for k in config.PARAM_GRID if cur[k] != best[k]}
            journal.append(f"Regole aggiornate {changed}: Sharpe validazione {cur_val:.2f}→{best_val:.2f}, "
                           f"test {t_cur:.2f}→{t_new:.2f}")
            brain["params"] = best
        else:
            journal.append(f"Trovate regole migliori in validazione ({best_val:.2f}) ma peggiori sul test "
                           f"({t_new:.2f} vs {t_cur:.2f}): scartate (probabile overfitting)")

    # 5) backtest onesto ultimo anno (pesi e modello non hanno mai visto questi dati)
    eq, ntr = backtest(test_score, px_eur, atr, regime, brain["params"])
    be = bench_equity(px_eur, eq.index)
    brain["backtest"] = {"from": str(T1.date()), "to": str(dates[-1].date()), "trades": ntr,
                         "strategy": stats(eq), "benchmark": stats(be),
                         "curve": [[str(d.date()), round(float(a), 2), round(float(b), 2)]
                                   for d, a, b in zip(eq.index[::3], eq.values[::3], be.values[::3])]}
    journal.append(f"Backtest onesto {brain['backtest']['from']}→{brain['backtest']['to']}: "
                   f"strategia {brain['backtest']['strategy']['ret']:+.1f}% vs benchmark "
                   f"{brain['backtest']['benchmark']['ret']:+.1f}%")
    return journal


# ---------- apprendimento giornaliero dai propri segnali ----------
def update_live(brain, log, prices):
    """Valuta i segnali registrati >= HORIZON giorni fa e aggiorna l'IC 'dal vivo' (unico modo per le notizie)."""
    from engine.features import forward_excess
    if log is None or log.empty:
        return []
    fwd = forward_excess(prices)
    done = set(brain["evaluated"])
    journal = []
    new_dates = sorted(d for d in log["date"].unique() if d not in done)
    for d in new_dates:
        ts = pd.Timestamp(d)
        if ts not in fwd.index or fwd.loc[ts].isna().all():
            continue  # esito non ancora noto
        day = log[log["date"] == d].set_index("ticker")
        f = fwd.loc[ts].reindex(day.index)
        if f.notna().sum() < 8:
            continue
        for s in config.SIGNALS:
            if s not in day or day[s].abs().sum() == 0:
                continue
            ic = day[s].rank().corr(f.rank())
            if pd.isna(ic):
                continue
            prev = brain["live_ic"].get(s)
            brain["n_live"][s] = nl = brain["n_live"].get(s, 0) + 1
            a = max(1 / nl, 0.02)  # media semplice all'inizio, poi memoria di ~100 giorni
            brain["live_ic"][s] = round(float(ic if prev is None else (1 - a) * prev + a * ic), 4)
            if s == "news":  # le notizie imparano solo dal vivo
                brain["n"]["news"] = brain["n_live"]["news"]
                brain["ic"]["news"] = brain["live_ic"]["news"]
        brain["evaluated"].append(d)
    if new_dates:
        old = dict(brain["weights"])
        brain["weights"] = weights_from_ic(brain["ic"], brain["n"], old, keep=0.8)
        if abs(brain["weights"]["news"] - old.get("news", 0)) > 0.02:
            journal.append(f"Peso notizie {old.get('news', 0):+.2f} → {brain['weights']['news']:+.2f} "
                           f"dopo {brain['n']['news']} giorni valutati (IC {brain['ic']['news']:+.3f})")
    brain["evaluated"] = brain["evaluated"][-400:]
    return journal


def ml_predict(feats, date):
    try:
        with open(MODEL_PATH, "rb") as fh:
            m = pickle.load(fh)
    except Exception:
        return {}
    rows = {t: f.loc[date, ML_FEATURES] for t, f in feats.items() if date in f.index}
    X = pd.DataFrame(rows).T.astype(float).dropna()
    if X.empty:
        return {}
    return dict(zip(X.index, m.predict_proba(X[ML_FEATURES])[:, 1]))
