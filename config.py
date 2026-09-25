"""Configurazione. Modifica qui watchlist e regole: il resto si adatta da solo."""

# ticker Yahoo Finance -> (nome, mercato). Se un ticker non esiste più viene semplicemente saltato.
WATCHLIST = {
    # USA: S&P 100
    "AAPL": ("Apple", "USA"),
    "ABBV": ("AbbVie", "USA"),
    "ABT": ("Abbott", "USA"),
    "ACN": ("Accenture", "USA"),
    "ADBE": ("Adobe", "USA"),
    "AIG": ("AIG", "USA"),
    "AMD": ("AMD", "USA"),
    "AMGN": ("Amgen", "USA"),
    "AMT": ("American Tower", "USA"),
    "AMZN": ("Amazon", "USA"),
    "AVGO": ("Broadcom", "USA"),
    "AXP": ("American Express", "USA"),
    "BA": ("Boeing", "USA"),
    "BAC": ("Bank of America", "USA"),
    "BK": ("BNY Mellon", "USA"),
    "BKNG": ("Booking", "USA"),
    "BLK": ("BlackRock", "USA"),
    "BMY": ("Bristol-Myers", "USA"),
    "BRK-B": ("Berkshire Hathaway", "USA"),
    "C": ("Citigroup", "USA"),
    "CAT": ("Caterpillar", "USA"),
    "CHTR": ("Charter", "USA"),
    "CL": ("Colgate-Palmolive", "USA"),
    "CMCSA": ("Comcast", "USA"),
    "COF": ("Capital One", "USA"),
    "COP": ("ConocoPhillips", "USA"),
    "COST": ("Costco", "USA"),
    "CRM": ("Salesforce", "USA"),
    "CSCO": ("Cisco", "USA"),
    "CVS": ("CVS Health", "USA"),
    "CVX": ("Chevron", "USA"),
    "DE": ("Deere", "USA"),
    "DHR": ("Danaher", "USA"),
    "DIS": ("Disney", "USA"),
    "DUK": ("Duke Energy", "USA"),
    "EMR": ("Emerson", "USA"),
    "F": ("Ford", "USA"),
    "FDX": ("FedEx", "USA"),
    "GD": ("General Dynamics", "USA"),
    "GE": ("GE Aerospace", "USA"),
    "GILD": ("Gilead", "USA"),
    "GM": ("General Motors", "USA"),
    "GOOGL": ("Alphabet", "USA"),
    "GS": ("Goldman Sachs", "USA"),
    "HD": ("Home Depot", "USA"),
    "HON": ("Honeywell", "USA"),
    "IBM": ("IBM", "USA"),
    "INTC": ("Intel", "USA"),
    "INTU": ("Intuit", "USA"),
    "ISRG": ("Intuitive Surgical", "USA"),
    "JNJ": ("Johnson & Johnson", "USA"),
    "JPM": ("JPMorgan", "USA"),
    "KHC": ("Kraft Heinz", "USA"),
    "KO": ("Coca-Cola", "USA"),
    "LIN": ("Linde", "USA"),
    "LLY": ("Eli Lilly", "USA"),
    "LMT": ("Lockheed Martin", "USA"),
    "LOW": ("Lowe's", "USA"),
    "MA": ("Mastercard", "USA"),
    "MCD": ("McDonald's", "USA"),
    "MDLZ": ("Mondelez", "USA"),
    "MDT": ("Medtronic", "USA"),
    "MET": ("MetLife", "USA"),
    "META": ("Meta Platforms", "USA"),
    "MMM": ("3M", "USA"),
    "MO": ("Altria", "USA"),
    "MRK": ("Merck", "USA"),
    "MS": ("Morgan Stanley", "USA"),
    "MSFT": ("Microsoft", "USA"),
    "NEE": ("NextEra Energy", "USA"),
    "NFLX": ("Netflix", "USA"),
    "NKE": ("Nike", "USA"),
    "NOW": ("ServiceNow", "USA"),
    "NVDA": ("Nvidia", "USA"),
    "ORCL": ("Oracle", "USA"),
    "PEP": ("PepsiCo", "USA"),
    "PFE": ("Pfizer", "USA"),
    "PG": ("Procter & Gamble", "USA"),
    "PLTR": ("Palantir", "USA"),
    "PM": ("Philip Morris", "USA"),
    "PYPL": ("PayPal", "USA"),
    "QCOM": ("Qualcomm", "USA"),
    "RTX": ("RTX", "USA"),
    "SBUX": ("Starbucks", "USA"),
    "SCHW": ("Charles Schwab", "USA"),
    "SO": ("Southern Company", "USA"),
    "SPG": ("Simon Property", "USA"),
    "T": ("AT&T", "USA"),
    "TGT": ("Target", "USA"),
    "TMO": ("Thermo Fisher", "USA"),
    "TMUS": ("T-Mobile", "USA"),
    "TSLA": ("Tesla", "USA"),
    "TXN": ("Texas Instruments", "USA"),
    "UBER": ("Uber", "USA"),
    "UNH": ("UnitedHealth", "USA"),
    "UNP": ("Union Pacific", "USA"),
    "UPS": ("UPS", "USA"),
    "USB": ("US Bancorp", "USA"),
    "V": ("Visa", "USA"),
    "VZ": ("Verizon", "USA"),
    "WFC": ("Wells Fargo", "USA"),
    "WMT": ("Walmart", "USA"),
    "XOM": ("ExxonMobil", "USA"),
    # Italia: FTSE MIB
    "A2A.MI": ("A2A", "Italia"),
    "AMP.MI": ("Amplifon", "Italia"),
    "AZM.MI": ("Azimut", "Italia"),
    "BAMI.MI": ("Banco BPM", "Italia"),
    "BMED.MI": ("Banca Mediolanum", "Italia"),
    "BMPS.MI": ("Monte dei Paschi", "Italia"),
    "BPE.MI": ("BPER Banca", "Italia"),
    "BGN.MI": ("Banca Generali", "Italia"),
    "BZU.MI": ("Buzzi", "Italia"),
    "CPR.MI": ("Campari", "Italia"),
    "DIA.MI": ("DiaSorin", "Italia"),
    "ENEL.MI": ("Enel", "Italia"),
    "ENI.MI": ("Eni", "Italia"),
    "ERG.MI": ("ERG", "Italia"),
    "RACE.MI": ("Ferrari", "Italia"),
    "FBK.MI": ("FinecoBank", "Italia"),
    "G.MI": ("Generali", "Italia"),
    "HER.MI": ("Hera", "Italia"),
    "IP.MI": ("Interpump", "Italia"),
    "INW.MI": ("Inwit", "Italia"),
    "IG.MI": ("Italgas", "Italia"),
    "IVG.MI": ("Iveco", "Italia"),
    "ISP.MI": ("Intesa Sanpaolo", "Italia"),
    "LDO.MI": ("Leonardo", "Italia"),
    "LTMC.MI": ("Lottomatica", "Italia"),
    "MB.MI": ("Mediobanca", "Italia"),
    "MONC.MI": ("Moncler", "Italia"),
    "NEXI.MI": ("Nexi", "Italia"),
    "PIRC.MI": ("Pirelli", "Italia"),
    "PST.MI": ("Poste Italiane", "Italia"),
    "PRY.MI": ("Prysmian", "Italia"),
    "REC.MI": ("Recordati", "Italia"),
    "SPM.MI": ("Saipem", "Italia"),
    "SRG.MI": ("Snam", "Italia"),
    "STLAM.MI": ("Stellantis", "Italia"),
    "STMMI.MI": ("STMicroelectronics", "Italia"),
    "TIT.MI": ("Telecom Italia", "Italia"),
    "TEN.MI": ("Tenaris", "Italia"),
    "TRN.MI": ("Terna", "Italia"),
    "UCG.MI": ("UniCredit", "Italia"),
    "UNI.MI": ("Unipol", "Italia"),
    # ETF globali e settoriali
    "SPY": ("ETF S&P 500", "ETF"),
    "QQQ": ("ETF Nasdaq 100", "ETF"),
    "IWM": ("ETF Russell 2000", "ETF"),
    "VGK": ("ETF Europa", "ETF"),
    "EEM": ("ETF Mercati emergenti", "ETF"),
    "EWJ": ("ETF Giappone", "ETF"),
    "GLD": ("ETF Oro", "ETF"),
    "SLV": ("ETF Argento", "ETF"),
    "TLT": ("ETF Treasury 20+ anni", "ETF"),
    "HYG": ("ETF Obbligazioni high yield", "ETF"),
    "XLK": ("ETF Tecnologia", "ETF"),
    "XLF": ("ETF Finanza", "ETF"),
    "XLE": ("ETF Energia", "ETF"),
    "XLV": ("ETF Salute", "ETF"),
    "XLI": ("ETF Industria", "ETF"),
    "XLY": ("ETF Consumi discrezionali", "ETF"),
    "XLP": ("ETF Beni di prima necessita", "ETF"),
    "XLU": ("ETF Utility", "ETF"),
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
    "max_positions": 10,
    "max_weight": 0.12,    # peso massimo per titolo
    "risk_per_trade": 0.01 # rischio per operazione (1% del capitale)
}
PARAM_GRID = {"buy_th": [0.15, 0.25, 0.35], "atr_stop": [2.0, 3.0, 4.0], "max_positions": [8, 10, 12]}

SIGNALS = ["momentum", "trend", "mean_reversion", "breakout", "volume", "rel_strength", "news"]
SIGNAL_LABELS = {
    "momentum": "Momentum 3 mesi", "trend": "Trend (medie mobili)", "mean_reversion": "Ipervenduto/ipercomprato (RSI)",
    "breakout": "Breakout massimi 20gg", "volume": "Volume anomalo", "rel_strength": "Forza relativa vs indice",
    "news": "Sentiment notizie",
}

# usati solo se imposti il secret GEMINI_API_KEY (piano gratuito). "latest" = sempre l'ultima versione
GEMINI_MODELS = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-3.5-flash"]


def currency(t):
    return "EUR" if t.endswith(".MI") else "USD"


def bench_for(t):
    return BENCH_IT if t.endswith(".MI") else BENCH_US


def bench_mix(available):
    """Pesi del benchmark limitati ai dati disponibili."""
    m = {t: w for t, w in BENCH_MIX.items() if t in available}
    tot = sum(m.values()) or 1
    return {t: w / tot for t, w in m.items()}
