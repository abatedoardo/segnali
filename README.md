# Segnali di Mercato

App gratuita che analizza ogni giorno prezzi e notizie di titoli USA, FTSE MIB ed ETF. Assegna un punteggio a ogni titolo, gestisce un portfolio virtuale da 10.000 € e si auto-migliora ogni settimana.

## Come funziona

1. **Dati**: prezzi da Yahoo Finance e notizie dai feed RSS di Yahoo e Google News. Tutto gratis.
2. **7 segnali**: momentum, trend, RSI, breakout, volume anomalo, forza relativa e sentiment delle notizie. La stessa notizia ripresa da più siti viene contata una volta sola.
3. **Punteggio**: è la somma pesata dei segnali più un modello di machine learning (gradient boosting).
4. **Portfolio virtuale**: compra i punteggi migliori con una dimensione basata sul rischio (ATR), usa un trailing stop e diventa più prudente quando l'S&P 500 è sotto la media a 200 giorni. Costi inclusi: 0,15% a operazione.

## Come impara da sola

- **Ogni giorno** confronta i segnali di 5 giorni fa con cosa è successo davvero e aggiorna la fiducia in ciascuno (Information Coefficient). Un segnale conta solo quando è statisticamente distinguibile dal caso. Uno che sbaglia sistematicamente direzione viene invertito.
- **Ogni sabato**:
  - ricalcola i pesi su 5 anni di dati;
  - riallena il modello ML e lo valuta su un anno che non ha mai visto (AUC): il modello pesa di più solo se batte il caso;
  - prova 27 combinazioni di regole (soglia d'acquisto, stop, numero di titoli) e adotta le nuove solo se migliorano sia sul periodo di validazione sia su quello di test, altrimenti le scarta come probabile overfitting;
  - fa un backtest onesto dell'ultimo anno.
- Ogni cambiamento viene scritto nel **Diario** della dashboard.

## Opzionali (gratis), in Settings → Secrets and variables → Actions

- `GEMINI_API_KEY`: chiave di Google AI Studio. Le notizie vengono giudicate da un'IA invece che da un dizionario.
- `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID`: ricevi un messaggio a ogni operazione.

## Personalizzare

Watchlist, capitale e regole di partenza sono in `config.py`.

Avvio manuale: tab Actions → Segnali → Run workflow (`daily` o `learn`).

Solo a scopo di studio e test: non è un consiglio d'investimento.
