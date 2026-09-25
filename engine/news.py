"""Notizie gratuite da feed RSS (Yahoo Finance + Google News), deduplicate e con sentiment.
Sentiment: Gemini (gratis, opzionale con GEMINI_API_KEY) oppure dizionario finanziario IT/EN."""
import json
import math
import os
import re
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import requests
import config

UA = {"User-Agent": "Mozilla/5.0 (segnali-bot)"}

POS = """beat beats beating surge surges soar soars jump jumps rally rallies record upgrade upgraded upgrades
outperform buy raises raised boost boosts strong growth profit profits gain gains rise rises rising higher
tops exceeds exceeded bullish breakthrough approval approved wins win partnership expands expansion dividend
buyback optimistic rebound recovers recovery milestone accelerate accelerates
rialzo rialzi balzo balza vola sale salgono crescita utile utili record promozione promuove acquistare
dividendo buyback supera superano positivo positivi forte forti accordo espansione ottimismo rimbalzo""".split()
NEG = """miss misses missed plunge plunges plummet drop drops fall falls falling slump slumps tumble tumbles
downgrade downgraded downgrades underperform sell cut cuts lower weak weakness loss losses decline declines
lawsuit probe investigation recall warning warns bearish fraud layoffs layoff bankruptcy default fine fined
halt delay delays concern concerns fears risk slowdown tariff tariffs
ribasso ribassi crollo crolla cala calano scende scendono perdita perdite taglio tagli bocciatura vendere
debole deboli negativo negativi indagine multa allarme timori rischio rallentamento dazi licenziamenti""".split()
POS, NEG = set(POS), set(NEG)
NEGATORS = {"not", "no", "non", "without", "senza"}


def lexicon_score(text):
    words = re.findall(r"[a-zà-ù]+", text.lower())
    s, n = 0, 0
    for i, w in enumerate(words):
        v = 1 if w in POS else -1 if w in NEG else 0
        if v:
            if i > 0 and words[i - 1] in NEGATORS:
                v = -v
            s += v
            n += 1
    return 0.0 if n == 0 else max(-1.0, min(1.0, s / (n + 1) * 1.5))


def _fetch_rss(url):
    try:
        r = requests.get(url, headers=UA, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception:
        return []
    items = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        try:
            dt = parsedate_to_datetime(it.findtext("pubDate") or "")
            dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            dt = datetime.now(timezone.utc)
        if title:
            items.append({"title": title, "link": link, "date": dt})
    return items


def _fingerprint(title):
    t = re.sub(r"\s+-\s+[^-]+$", "", title.lower())  # toglie " - Reuters"
    words = re.findall(r"[a-z0-9à-ù]+", t)[:8]
    return hashlib.md5(" ".join(words).encode()).hexdigest()[:12]


def _gemini_scores(headlines):
    key = os.environ.get("GEMINI_API_KEY")
    if not key or not headlines:
        return None
    prompt = ("Sei un analista finanziario. Per ogni titolo di notizia valuta l'impatto probabile sul prezzo "
              "dell'azione citata nei prossimi giorni, da -1 (molto negativo) a 1 (molto positivo); 0 se irrilevante "
              "o gia' noto. Rispondi SOLO con un array JSON di numeri, nello stesso ordine.\n\n"
              + "\n".join(f"{i+1}. [{h['ticker']}] {h['title']}" for i, h in enumerate(headlines)))
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    for model in config.GEMINI_MODELS:  # se un modello non esiste più, provo il successivo
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        try:
            r = requests.post(url, json=body, headers={"x-goog-api-key": key}, timeout=90)
            if r.status_code in (400, 404):
                continue
            r.raise_for_status()
            txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            vals = json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
            if len(vals) == len(headlines):
                return [max(-1.0, min(1.0, float(v))) for v in vals]
        except Exception as e:
            print(f"Gemini ({model}) non disponibile, uso il dizionario:", str(e)[:120])
            return None
    return None


def fetch_news(seen):
    """Ritorna {ticker: {score, n, headlines}} e aggiorna 'seen' (fingerprint -> data prima vista)."""
    if os.environ.get("SIMULATE"):
        import random
        rnd = random.Random(os.environ.get("SIM_DATE"))
        res = {t: {"score": round(rnd.uniform(-0.6, 0.6), 3), "n": 3, "headlines": [
            {"title": f"Notizia simulata su {n}", "link": "#", "sent": 0.1, "date": "2026-01-01"}]}
               for t, (n, _) in config.WATCHLIST.items()}
        res["_engine"] = "simulato"
        return res
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=72)
    per_ticker, all_heads = {}, []
    from concurrent.futures import ThreadPoolExecutor
    jobs = {}
    for t, (name, market) in config.WATCHLIST.items():
        urls = [f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={t}&region=US&lang=en-US"]
        if market == "Italia":
            urls.append(f"https://news.google.com/rss/search?q={quote(name + ' azioni')}&hl=it&gl=IT&ceid=IT:it")
        else:
            urls.append(f"https://news.google.com/rss/search?q={quote(name + ' stock')}&hl=en-US&gl=US&ceid=US:en")
        jobs[t] = urls
    with ThreadPoolExecutor(8) as ex:
        fetched = {t: list(ex.map(_fetch_rss, urls)) for t, urls in jobs.items()}
    for t in config.WATCHLIST:
        uniq = {}
        for items in fetched.get(t, []):
            for it in items:
                if it["date"] < cutoff:
                    continue
                fp = _fingerprint(it["title"])
                if fp not in uniq:  # la stessa notizia su 50 siti conta una volta
                    uniq[fp] = it
        heads = sorted(uniq.values(), key=lambda x: x["date"], reverse=True)[:8]
        for h in heads:
            fp = _fingerprint(h["title"])
            h["new"] = fp not in seen
            seen.setdefault(fp, now.isoformat())
            h["ticker"] = t
        per_ticker[t] = heads
        all_heads += heads

    engine = "dizionario"
    for h in all_heads:
        h["sent"] = lexicon_score(h["title"])
    if os.environ.get("GEMINI_API_KEY") and all_heads:
        import time
        # le notizie nuove prima; a blocchi da 150, max 6 chiamate (limiti del piano gratuito)
        order = sorted(all_heads, key=lambda h: (not h["new"], -h["date"].timestamp()))[:900]
        for i in range(0, len(order), 150):
            chunk = order[i:i + 150]
            sc = _gemini_scores(chunk)
            if sc is None:
                break
            for h, v in zip(chunk, sc):
                h["sent"] = v
            engine = "gemini"
            time.sleep(6)

    result = {}
    for t, heads in per_ticker.items():
        if not heads:
            result[t] = {"score": 0.0, "n": 0, "headlines": []}
            continue
        num = den = 0.0
        for h in heads:
            age_h = (now - h["date"]).total_seconds() / 3600
            w = math.exp(-age_h / 24) * (1.0 if h["new"] else 0.4)  # notizie fresche e nuove pesano di più
            num += w * h["sent"]
            den += w
        raw = num / den if den else 0.0
        conf = 1 - math.exp(-len(heads) / 4)
        result[t] = {"score": round(max(-1, min(1, raw * conf * 1.5)), 3), "n": len(heads),
                     "headlines": [{"title": h["title"], "link": h["link"], "sent": round(h["sent"], 2),
                                    "date": h["date"].isoformat()} for h in heads[:5]]}
    # pulizia memoria notizie viste (> 10 giorni)
    old = (now - timedelta(days=10)).isoformat()
    for k in [k for k, v in seen.items() if v < old]:
        del seen[k]
    result["_engine"] = engine
    return result
