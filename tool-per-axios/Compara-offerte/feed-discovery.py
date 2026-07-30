#!/usr/bin/env python3
"""
feed-discovery.py — Scopre feed XML prodotto per domini farmacia
================================================================
Strategia a cascata per ogni dominio:
  1. robots.txt → grep "Sitemap:" e pattern feed
  2. Path comuni diretti (HEAD, poi GET solo su 200)
  3. HTML homepage → <link> o meta tag con feed
  4. Fallback: nessun feed pubblico

Salva esito in SQLite (feed_cache.db) per non ripetere la scoperta.

Usage:
  python3 feed-discovery.py                              # Discovery su tutti i 194 domini
  python3 feed-discovery.py --domini lista.txt            # Discovery su lista custom
  python3 feed-discovery.py --stats                       # Statistiche cache
  python3 feed-discovery.py --refresh-old                 # Riverifica discovery >30gg

Integrazione: chiamato prima del crawler sitemap.
Se un dominio ha feed XML, si usa QUELLO (più ricco, prezzo incluso).
"""

import argparse
import gzip
import os
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    print("[!] pip install requests")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
SITI_FILE = SCRIPT_DIR / "siti.md"
CACHE_DB = SCRIPT_DIR / "feed_cache.db"

USER_AGENT = "Mozilla/5.0 (compatible; AxiosCrawler/2.0; +https://axios-ai.it)"
TIMEOUT_HEAD = 3
TIMEOUT_GET = 10
MAX_WORKERS = 16
MAX_FEED_BYTES = 10 * 1024 * 1024  # 10MB max per feed

# Path comuni feed XML — ordinati per probabilità
FEED_PATHS = [
    "/feed/google_shopping.xml",
    "/sitemap-google-shopping.xml",
    "/feeds/product.xml",
    "/media/feed/google_shopping.xml",  # Magento
    "/feed.xml",
    "/export/feed.xml",
    "/google-feed.xml",
    "/prestashop-catalog-feed.xml",  # PrestaShop
    "/feeds/googleshopping.xml",
    "/rss/products.xml",
    "/products.xml",
    "/feed/",
    "/sitemap_products_1.xml",
    "/google_shopping.xml",
]

# Namespace Google Shopping per parsing XML
GS_NS = {'g': 'http://base.google.com/ns/1.0'}


# ─── Logging ────────────────────────────────────────

def log(msg, level="+"):
    c = {"+": "\033[92m", "-": "\033[93m", "!": "\033[91m", "*": "\033[94m", "~": "\033[96m"}
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {c.get(level, '')}[{level}]\033[0m {ts} {msg}")


# ─── Caricamento domini ─────────────────────────────

def carica_domini():
    """Legge domini da siti.md."""
    domini = []
    if not SITI_FILE.exists():
        log(f"File non trovato: {SITI_FILE}", "!")
        return domini
    with open(SITI_FILE) as f:
        for line in f:
            m = re.search(r'https?://([^/\s)]+)', line.strip())
            if m:
                dom = m.group(1).lower().replace("www.", "").strip()
                if dom:
                    domini.append(dom)
    log(f"Caricati {len(domini)} domini da siti.md", "+")
    return domini


# ─── SQLite cache ───────────────────────────────────

def init_db():
    conn = sqlite3.connect(CACHE_DB, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feed_cache (
            dominio TEXT PRIMARY KEY,
            feed_url TEXT,
            tipo TEXT,
            trovato INTEGER,
            status_code INTEGER,
            bytes INTEGER,
            data_verifica TEXT,
            error TEXT
        )
    """)
    conn.commit()
    return conn


def carica_cache(conn):
    """Carica esiti precedenti in un dict."""
    cache = {}
    for row in conn.execute("SELECT dominio, feed_url, trovato, data_verifica FROM feed_cache"):
        cache[row[0]] = {
            "feed_url": row[1],
            "trovato": bool(row[2]),
            "data_verifica": row[3],
        }
    return cache


def salva_esito(conn, dominio, feed_url, tipo, trovato, status_code, bytes_n, error=""):
    conn.execute("""
        INSERT OR REPLACE INTO feed_cache
        (dominio, feed_url, tipo, trovato, status_code, bytes, data_verifica, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (dominio, feed_url or "", tipo or "", int(trovato), status_code or 0, bytes_n or 0,
          datetime.now(timezone.utc).isoformat(), error or ""))
    conn.commit()


def e_vecchio(cache_entry, giorni=30):
    if not cache_entry:
        return True
    dv = cache_entry.get("data_verifica", "")
    if not dv:
        return True
    try:
        dt = datetime.fromisoformat(dv)
        return (datetime.now(timezone.utc) - dt).days > giorni
    except:
        return True


# ─── FASE 1: robots.txt ────────────────────────────

def controlla_robots(dominio):
    """Cerca sitemap e feed in robots.txt."""
    feed_trovati = []
    for base in [f"https://www.{dominio}", f"https://{dominio}"]:
        try:
            r = requests.get(f"{base}/robots.txt", headers={"User-Agent": USER_AGENT},
                             timeout=TIMEOUT_HEAD, verify=False, allow_redirects=True)
            if r.status_code < 400:
                txt = r.text
                # Cerca Sitemap:
                for m in re.finditer(r'(?i)^\s*Sitemap:\s*(\S+)', txt, re.MULTILINE):
                    feed_trovati.append(m.group(1).strip())
                # Cerca feed
                for m in re.finditer(r'(?i)^\s*(?:Feed|ProductFeed|GoogleShopping):\s*(\S+)', txt, re.MULTILINE):
                    feed_trovati.append(m.group(1).strip())
                if feed_trovati:
                    return feed_trovati
        except:
            pass
    return feed_trovati


# ─── FASE 2: HEAD request su path comuni ───────────

def controlla_path_head(dominio, path):
    """HEAD veloce per verificare esistenza path."""
    for base in [f"https://www.{dominio}", f"https://{dominio}"]:
        url = f"{base}{path}"
        try:
            r = requests.head(url, headers={"User-Agent": USER_AGENT},
                              timeout=TIMEOUT_HEAD, verify=False, allow_redirects=True)
            if r.status_code < 400:
                # HEAD 200 → GET per scaricare
                return url, r.status_code
            if r.status_code == 301 or r.status_code == 302:
                # Segui redirect
                return url, r.status_code
        except:
            pass
    return None, 0


def scarica_feed(url):
    """Scarica feed XML, gestisce gzip, max MAX_FEED_BYTES."""
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT},
                         timeout=TIMEOUT_GET, verify=False, stream=True)
        if r.status_code >= 400:
            return None, 0
        chunks = []
        total = 0
        for chunk in r.iter_content(65536, decode_unicode=False):
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_FEED_BYTES:
                break
        data = b"".join(chunks)
        try:
            data = gzip.decompress(data)
        except:
            pass
        return data, total
    except:
        return None, 0


# ─── FASE 3: HTML homepage ─────────────────────────

def cerca_feed_in_html(dominio):
    """Cerca link a feed nell'HTML della homepage."""
    for base in [f"https://www.{dominio}", f"https://{dominio}"]:
        try:
            r = requests.get(base, headers={"User-Agent": USER_AGENT},
                             timeout=TIMEOUT_HEAD, verify=False)
            if r.status_code >= 400:
                continue
            txt = r.text
            feed_urls = []

            # <link> tag con type="application/rss+xml" o "application/atom+xml"
            for m in re.finditer(r'<link[^>]*?\bhref=["\']([^"\']+)["\'][^>]*?>', txt, re.IGNORECASE):
                link_html = m.group(0).lower()
                href = m.group(1)
                if any(t in link_html for t in ["rss", "atom", "feed", "xml"]):
                    # Risolvi URL relativo
                    if href.startswith("/"):
                        feed_urls.append(base.rstrip("/") + href)
                    elif href.startswith("http"):
                        feed_urls.append(href)

            # WooCommerce/Shopify a volte linkano feed nei meta
            for m in re.finditer(r'<meta[^>]*?\bcontent=["\']([^"\']+feed[^"\']*)["\']', txt, re.IGNORECASE):
                href = m.group(1)
                if href.startswith("/"):
                    feed_urls.append(base.rstrip("/") + href)
                elif href.startswith("http"):
                    feed_urls.append(href)

            if feed_urls:
                return feed_urls
        except:
            pass
    return []


# ─── Worker per dominio ─────────────────────────────

def lavora_dominio(dominio, forza=False):
    conn = init_db()
    """Esegue discovery feed per un dominio, salva esito in DB."""

    cache = carica_cache(conn)
    entry = cache.get(dominio)

    if not forza and not e_vecchio(entry):
        return dominio, "skip", entry.get("feed_url", "")

    # FASE 1: robots.txt
    feed_urls = controlla_robots(dominio)
    if feed_urls:
        url = feed_urls[0]
        data, size = scarica_feed(url)
        if data:
            salva_esito(conn, dominio, url, "robots.txt", True, 200, size)
            return dominio, "trovato", url
        else:
            salva_esito(conn, dominio, url, "robots.txt", False, 0, 0, "scarica fallita")
            return dominio, "trovato_url_ma_non_scaricabile", url

    # FASE 2: HEAD su path comuni
    for path in FEED_PATHS:
        url, status = controlla_path_head(dominio, path)
        if url and status < 400:
            data, size = scarica_feed(url)
            if data and len(data) > 500:
                salva_esito(conn, dominio, url, "head", True, 200, size)
                return dominio, "trovato", url
            elif data:
                salva_esito(conn, dominio, url, "head", True, status, size, "feed piccolo")
                return dominio, "trovato", url

    # FASE 3: HTML homepage
    feed_urls = cerca_feed_in_html(dominio)
    if feed_urls:
        url = feed_urls[0]
        data, size = scarica_feed(url)
        if data:
            salva_esito(conn, dominio, url, "html", True, 200, size)
            return dominio, "trovato", url

    salva_esito(conn, dominio, None, None, False, 0, 0, "nessun feed trovato")
    return dominio, "non_trovato", ""


# ─── Statistiche ────────────────────────────────────

def stampa_stats(conn):
    cur = conn.execute("""
        SELECT trovato, COUNT(*), 
               SUM(CASE WHEN trovato=1 THEN bytes ELSE 0 END) as tot_bytes
        FROM feed_cache GROUP BY trovato
    """)
    for trovato, count, tot_bytes in cur.fetchall():
        label = "Con feed" if trovato else "Senza feed"
        log(f"{label}: {count} domini ({tot_bytes//1024//1024}MB)" if trovato else f"{label}: {count} domini", "~")
    
    # Dettaglio domini con feed
    log(f"\nDomini con feed XML:", "*")
    for row in conn.execute("""
        SELECT dominio, feed_url, bytes, data_verifica 
        FROM feed_cache WHERE trovato=1 ORDER BY bytes DESC
    """):
        dom, url, size, dv = row
        log(f"  {dom:30s} {url[:60]} ({size//1024}KB)", "+")


# ─── Main ───────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="feed-discovery — Scopre feed XML prodotto per domini farmacia")
    parser.add_argument("--domini", type=str, help="File di testo con un dominio per riga (default: siti.md)")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--stats", action="store_true", help="Statistiche cache")
    parser.add_argument("--refresh-old", action="store_true", help="Riverifica discovery >30gg")
    parser.add_argument("--forza", action="store_true", help="Riverifica anche se fresco")
    args = parser.parse_args()

    conn = init_db()

    if args.stats:
        stampa_stats(conn)
        conn.close()
        return

    domini = []
    if args.domini:
        with open(args.domini) as f:
            domini = [line.strip() for line in f if line.strip()]
    else:
        domini = carica_domini()

    if not domini:
        log("Nessun dominio da processare", "!")
        conn.close()
        return

    t0 = time.time()
    trovati, non_trovati, skippati = 0, 0, 0

    log(f"Discovery feed su {len(domini)} domini ({args.workers} workers)...", "*")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futuri = {pool.submit(lavora_dominio, d, args.forza): d for d in domini}
        for f in as_completed(futuri):
            d = futuri[f]
            try:
                dominio, esito, feed_url = f.result(timeout=30)
                if esito == "skip":
                    skippati += 1
                elif esito == "trovato" or esito == "trovato_url_ma_non_scaricabile":
                    trovati += 1
                    log(f"  ✅ {dominio}: {esito}", "+")
                else:
                    non_trovati += 1
                    if non_trovati < 5:
                        log(f"  . {dominio}: {esito}", "~")
            except Exception as e:
                non_trovati += 1
                log(f"  ERR {d}: {str(e)[:60]}", "-")

    t1 = time.time()
    log(f"\nCompletato in {t1-t0:.0f}s", "+")
    log(f"  Con feed: {trovati}, Senza: {non_trovati}, Skippati: {skippati}", "+")
    conn.close()


if __name__ == "__main__":
    main()