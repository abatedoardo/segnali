"""Configurazione. Modifica qui watchlist e regole: il resto si adatta da solo."""

# ticker Yahoo Finance -> (nome, mercato)
WATCHLIST = {
    # USA
    "AAPL": ("Apple", "USA"), "MSFT": ("Microsoft", "USA"), "NVDA": ("Nvidia", "USA"),
    "AMZN": ("Amazon", "USA"), "GOOGL": ("Alphabet", "USA"), "META": ("Meta Platforms", "USA"),
    "TSLA": ("Tesla", "USA"), "AVGO": ("Broadcom", "USA"), "AMD": ("AMD", "USA"),
    "NFLX": ("Netflix", "USA"), "JPM": ("JPMorgan", "USA"), "V": ("Visa", "USA"),
    "LLY": ("Eli Lilly", "USA"), "COST": ("Costco", "USA"),
    # Italia (FTSE MIB)
    "ENI.MI": ("Eni", "Italia"), "ISP.MI": ("Intesa Sanpaolo", "Italia"),
    "UCG.MI": ("UniCredit", "Italia"), "ENEL.MI": ("Enel", "Italia"),
    "RACE.MI": ("Ferrari", "Italia"), "STLAM.MI": ("Stellantis", "Italia"),
    "G.MI": ("Generali", "Italia"), "LDO.MI": ("Leonardo", "Italia"),
    "PRY.MI": ("Prysmian", "Italia"), "STMMI.MI": ("STMicroelectronics", "Italia"),
    # ETF globali
    "SPY": ("ETF S&P 500", "ETF"), "QQQ": ("ETF Nasdaq 100", "ETF"),
    "IWM": ("ETF Russell 2000", "ETF"), "EEM": ("ETF Mercati emergenti", "ETF"),
    "GLD": ("ETF Oro", "ETF"), "TLT": ("ETF Treasury 20+ anni", "ETF"),
}

BENCH_US = "SPY"          # benchmark per USA ed ETF
BENCH_IT = "FTSEMIB.MI"   # benchmark per Italia
FX = "EURUSD=X"           # dollari per 1 euro
BENCH_MIX = {BENCH_US: 0.6, BENCH_IT: 0.4}  # benchmark del portfolio (in EUR)

START_CAPITAL = 10_000.0  # euro virtuali
COST = 0.0015             # commissioni + slippage per operazione (0,15%)
HORIZON = 5               # giorni di borsa dopo cui si giudica un segnale
MIN_TRADE_EUR = 200.0

# Parametri di partenza: l'ottimizzatore settimanale li può cambiare da solo
DEFAULT_PARAMS = {
    "buy_th": 0.25,        # punteggio minimo per comprare
    "sell_th": -0.05,      # sotto questo punteggio si vende
    "atr_stop": 3.0,       # trailing stop = massimo - atr_stop * ATR
    "max_positions": 8,
    "max_weight": 0.15,    # peso massimo per titolo
    "risk_per_trade": 0.01 # rischio per operazione (1% del capitale)
}
PARAM_GRID = {"buy_th": [0.15, 0.25, 0.35], "atr_stop": [2.0, 3.0, 4.0], "max_positions": [6, 8, 10]}

SIGNALS = ["momentum", "trend", "mean_reversion", "breakout", "volume", "rel_strength", "news"]
SIGNAL_LABELS = {
    "momentum": "Momentum 3 mesi", "trend": "Trend (medie mobili)", "mean_reversion": "Ipervenduto/ipercomprato (RSI)",
    "breakout": "Breakout massimi 20gg", "volume": "Volume anomalo", "rel_strength": "Forza relativa vs indice",
    "news": "Sentiment notizie",
}

GEMINI_MODEL = "gemini-2.5-flash"  # usato solo se imposti il secret GEMINI_API_KEY (gratis)


def currency(t):
    return "EUR" if t.endswith(".MI") else "USD"


def bench_for(t):
    return BENCH_IT if t.endswith(".MI") else BENCH_US


def bench_mix(available):
    """Pesi del benchmark limitati ai dati disponibili."""
    m = {t: w for t, w in BENCH_MIX.items() if t in available}
    tot = sum(m.values()) or 1
    return {t: w / tot for t, w in m.items()}
