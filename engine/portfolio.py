"""Portfolio virtuale. La stessa funzione 'decide' è usata dal vivo e nei backtest (così i test sono onesti)."""
import math
import config


def equity(state, px):
    return state["cash"] + sum(p["shares"] * px.get(t, p["last_px"]) for t, p in state["positions"].items())


def decide(state, date, score, px, atr, regime_ok, params, reasons=None):
    """Aggiorna 'state' in place. score/px/atr: dict ticker -> valore (px in EUR). Ritorna lista operazioni."""
    trades = []
    pos = state["positions"]
    # 1) uscite: trailing stop o segnale negativo
    for t in list(pos):
        p = pos[t]
        if t not in px or px[t] is None or math.isnan(px[t]):
            continue
        price = px[t]
        p["last_px"] = price
        p["high"] = max(p["high"], price)
        stop = p["high"] * (1 - params["atr_stop"] * max(atr.get(t, 0.02), 0.005))
        why = None
        if price < stop:
            why = f"trailing stop ({params['atr_stop']}×ATR)"
        elif score.get(t, 0) < params["sell_th"]:
            why = f"punteggio sceso a {score.get(t, 0):+.2f}"
        if why:
            value = p["shares"] * price * (1 - config.COST)
            state["cash"] += value
            trades.append({"date": date, "ticker": t, "side": "VENDI", "shares": round(p["shares"], 4),
                           "price": round(price, 4), "value": round(value, 2),
                           "pnl_pct": round((price / p["entry"] - 1) * 100 - config.COST * 200, 2), "why": why})
            del pos[t]
    # 2) entrate: i migliori punteggi sopra soglia (soglia più alta se il mercato è in calo)
    eq = equity(state, px)
    th = params["buy_th"] + (0 if regime_ok else 0.15)
    cands = sorted((s, t) for t, s in score.items() if s > th and t not in pos and t in px
                   and px[t] and not math.isnan(px[t]))
    for s, t in reversed(cands):
        if len(pos) >= params["max_positions"]:
            break
        a = max(atr.get(t, 0.02), 0.005)
        size = min(params["max_weight"] * eq, params["risk_per_trade"] * eq / (params["atr_stop"] * a))
        size = min(size, state["cash"] / (1 + config.COST))
        if size < config.MIN_TRADE_EUR:
            continue
        shares = size / px[t]
        state["cash"] -= size * (1 + config.COST)
        pos[t] = {"shares": shares, "entry": px[t], "entry_date": date, "high": px[t], "last_px": px[t]}
        why = f"punteggio {s:+.2f}" + (f" — {reasons[t]}" if reasons and t in reasons else "")
        trades.append({"date": date, "ticker": t, "side": "COMPRA", "shares": round(shares, 4),
                       "price": round(px[t], 4), "value": round(size, 2), "why": why})
    return trades


def new_state():
    return {"cash": config.START_CAPITAL, "positions": {}, "trades": [], "history": [], "start": None}
