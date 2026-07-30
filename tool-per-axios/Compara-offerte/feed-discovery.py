#!/usr/bin/env python3
"""
feed-discovery.py — Scopre feed XML prodotto per domini farmacia
================================================================
Strategia a cascata:
  1. robots.txt → Sitemap: + feed pattern
  2. Path comuni (HEAD, GET solo su 200)
  3. HTML homepage → <link>/meta feed
  4. Fallback

SANITY: ogni feed scaricato viene verificato:
  - Redirect non devono uscire dal dominio originale
  - Contenuto deve essere XML (non HTML/redirect)

Usage:
  python3 feed-discovery.py                    # Tutti i domini
  python3 feed-discovery.py --stats            # Statistiche cache
  python3 feed-discovery.py --refresh-old      # Riverifica >30gg
"""

import argparse
import gzip
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = Path(__file__).parent
SITI_FILE = SCRIPT_DIR / "siti.md"
CACHE_DB = SCRIPT_DIR / "feed_cache.db"

UA = "Mozilla/5.0 (compatible; AxiosCrawler/2.0; +https://axios-ai.it)"
TIMEOUT_HEAD = 3
TIMEOUT_GET = 10
MAX_WORKERS = 16
MAX_BYTES = 10 * 1024 * 1024

FEED_PATHS = [
    "/feed/google_shopping.xml",
    "/sitemap-google-shopping.xml",
    "/feeds/product.xml",
    "/media/feed/google_shopping.xml",
    "/feed.xml", "/export/feed.xml",
    "/google-feed.xml",
    "/prestashop-catalog-feed.xml",
    "/feeds/googleshopping.xml",
    "/rss/products.xml", "/products.xml",
    "/feed/", "/sitemap_products_1.xml",
    "/google_shopping.xml",
]


def log(msg, level="+"):
    c = {"+": "\033[92m", "-": "\033[93m", "!": "\033[91m", "*": "\033[94m", "~": "\033[96m"}
    print(f"  {c.get(level, '')}[{level}]\033[0m {datetime.now().strftime('%H:%M:%S')} {msg}")


# ─── Caricamento domini ─────────────────────────────

def carica_domini():
    domini = []
    if not SITI_FILE.exists():
        log(f"File non trovato: {SITI_FILE}", "!"); return domini
    with open(SITI_FILE) as f:
        for line in f:
            m = re.search(r'https?://([^/\s)]+)', line.strip())
            if m:
                d = m.group(1).lower().replace("www.", "").strip()
                if d: domini.append(d)
    log(f"Caricati {len(domini)} domini da siti.md", "+")
    return domini


# ─── SQLite ─────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(CACHE_DB, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feed_cache (
            dominio TEXT PRIMARY KEY,
            feed_url TEXT, tipo TEXT,
            trovato INTEGER, status_code INTEGER,
            bytes INTEGER, data_verifica TEXT, error TEXT
        )
    """)
    conn.commit(); return conn


def salva_esito(conn, dominio, feed_url, tipo, trovato, status_code, bytes_n, error=""):
    conn.execute("""
        INSERT OR REPLACE INTO feed_cache
        VALUES (?,?,?,?,?,?,?,?)
    """, (dominio, feed_url or "", tipo or "", int(trovato),
          status_code or 0, bytes_n or 0,
          datetime.now(timezone.utc).isoformat(), error or ""))
    conn.commit()


def e_vecchio(cache_entry, giorni=30):
    if not cache_entry: return True
    dv = cache_entry.get("data_verifica", "")
    if not dv: return True
    try:
        eta = (datetime.now(timezone.utc) - datetime.fromisoformat(dv)).days
        return eta > giorni
    except: return True


# ─── FASE 1: robots.txt ────────────────────────────

def controlla_robots(dominio):
    feed_trovati = []
    for base in [f"https://www.{dominio}", f"https://{dominio}"]:
        try:
            r = requests.get(f"{base}/robots.txt", headers={"User-Agent": UA},
                             timeout=TIMEOUT_HEAD, verify=False, allow_redirects=True)
            if r.status_code >= 400: continue
            txt = r.text
            for m in re.finditer(r'(?i)^\s*Sitemap:\s*(\S+)', txt, re.MULTILINE):
                feed_trovati.append(m.group(1).strip())
            for m in re.finditer(r'(?i)^\s*(?:Feed|ProductFeed|GoogleShopping):\s*(\S+)', txt, re.MULTILINE):
                feed_trovati.append(m.group(1).strip())
            if feed_trovati: return feed_trovati
        except: pass
    return feed_trovati


# ─── FASE 2: HEAD + GET con sanity ─────────────────

def scarica_feed(url, dominio_atteso=None):
    """
    GET feed con sanity check:
    - follow redirects
    - dominio finale deve matchare dominio_atteso
    - contenuto deve iniziare con <?xml (no HTML)
    """
    try:
        r = requests.get(url, headers={"User-Agent": UA},
                         timeout=TIMEOUT_GET, verify=False,
                         stream=True, allow_redirects=True)
        if r.status_code >= 400: return None, 0

        # SANITY: dominio finale dopo redirect
        if dominio_atteso:
            final = urlparse(r.url).netloc.lower().replace("www.", "")
            atteso = dominio_atteso.lower()
            if final != atteso and not final.endswith("." + atteso):
                return None, 0

        chunks = []; total = 0
        for chunk in r.iter_content(65536, decode_unicode=False):
            if not chunk: break
            chunks.append(chunk); total += len(chunk)
            if total > MAX_BYTES: break
        data = b"".join(chunks)

        # De-gzip
        try: data = gzip.decompress(data)
        except: pass

        # SANITY: deve iniziare con <?xml o <feed o <rss o <urlset
        head = data[:100].strip()
        if not any(head.startswith(p) for p in [b'<?xml', b'<feed', b'<rss', b'<urlset', b'<sitemap']):
            return None, 0

        return data, total
    except:
        return None, 0


def controlla_path_head(dominio, path):
    """HEAD + check dominio finale."""
    for base in [f"https://www.{dominio}", f"https://{dominio}"]:
        url = f"{base}{path}"
        try:
            r = requests.head(url, headers={"User-Agent": UA},
                              timeout=TIMEOUT_HEAD, verify=False, allow_redirects=True)
            if r.status_code < 400:
                final = urlparse(r.url).netloc.lower().replace("www.", "")
                if final == dominio.lower() or final.endswith("." + dominio.lower()):
                    return url, r.status_code
        except: pass
    return None, 0


# ─── FASE 3: HTML homepage ─────────────────────────

def cerca_feed_in_html(dominio):
    for base in [f"https://www.{dominio}", f"https://{dominio}"]:
        try:
            r = requests.get(base, headers={"User-Agent": UA},
                             timeout=TIMEOUT_HEAD, verify=False)
            if r.status_code >= 400: continue
            txt = r.text; feed_urls = []
            for m in re.finditer(r'<link[^>]*?\bhref=["\']([^"\']+)["\'][^>]*?>', txt, re.IGNORECASE):
                a = m.group(0).lower(); h = m.group(1)
                if any(t in a for t in ["rss", "atom", "feed", "xml"]):
                    feed_urls.append(f"{base.rstrip('/')}{h}" if h.startswith("/") else h)
            for m in re.finditer(r'<meta[^>]*?\bcontent=["\']([^"\']+feed[^"\']*)["\']', txt, re.IGNORECASE):
                h = m.group(1)
                feed_urls.append(f"{base.rstrip('/')}{h}" if h.startswith("/") else h)
            if feed_urls: return feed_urls
        except: pass
    return []


# ─── Worker ─────────────────────────────────────────

def lavora_dominio(dominio, forza=False):
    conn = init_db()
    cache = {}
    for row in conn.execute("SELECT dominio, feed_url, trovato, data_verifica FROM feed_cache"):
        cache[row[0]] = {"feed_url": row[1], "trovato": bool(row[2]), "data_verifica": row[3]}
    entry = cache.get(dominio)

    if not forza and not e_vecchio(entry):
        return dominio, "skip", entry.get("feed_url", "")

    # FASE 1: robots.txt
    urls = controlla_robots(dominio)
    if urls:
        data, size = scarica_feed(urls[0], dominio)
        if data:
            salva_esito(conn, dominio, urls[0], "robots.txt", True, 200, size)
            return dominio, "trovato", urls[0]
        salva_esito(conn, dominio, urls[0], "robots.txt", False, 0, 0, "scarica/redirect/invalido")
        return dominio, "trovato_url_ma_non_scaricabile", urls[0]

    # FASE 2: path feed comuni
    for path in FEED_PATHS:
        url, status = controlla_path_head(dominio, path)
        if url and status < 400:
            data, size = scarica_feed(url, dominio)
            if data:
                salva_esito(conn, dominio, url, "head", True, 200, size)
                return dominio, "trovato", url

    # FASE 3: HTML homepage
    urls = cerca_feed_in_html(dominio)
    if urls:
        data, size = scarica_feed(urls[0], dominio)
        if data:
            salva_esito(conn, dominio, urls[0], "html", True, 200, size)
            return dominio, "trovato", urls[0]

    salva_esito(conn, dominio, None, None, False, 0, 0, "nessun feed trovato")
    return dominio, "non_trovato", ""


# ─── Statistiche ────────────────────────────────────

def stampa_stats(conn):
    for trovato, count, tot_bytes in conn.execute(
        "SELECT trovato, COUNT(*), SUM(CASE WHEN trovato=1 THEN bytes ELSE 0 END) FROM feed_cache GROUP BY trovato"
    ):
        if trovato: log(f"Con feed XML valido: {count} domini ({tot_bytes//1024//1024}MB)", "~")
        else: log(f"Senza feed: {count} domini", "~")
    log("\nDomini con feed:", "*")
    for row in conn.execute(
        "SELECT dominio, feed_url, tipo, bytes FROM feed_cache WHERE trovato=1 ORDER BY bytes DESC LIMIT 20"
    ):
        log(f"  {row[0]:25s} {row[1][:55]:55s} [{row[2]}] {row[3]//1024}KB", "+")


# ─── Main ───────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--domini", type=str)
    p.add_argument("--workers", type=int, default=MAX_WORKERS)
    p.add_argument("--stats", action="store_true")
    p.add_argument("--refresh-old", action="store_true")
    p.add_argument("--forza", action="store_true")
    args = p.parse_args()

    conn = init_db()
    if args.stats: stampa_stats(conn); conn.close(); return

    domini = [line.strip() for line in open(args.domini) if line.strip()] if args.domini else carica_domini()
    if not domini: log("Nessun dominio", "!"); conn.close(); return

    t0 = time.time(); trovati = non_trovati = skippati = 0
    log(f"Discovery feed su {len(domini)} domini ({args.workers} workers)...", "*")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futuri = {pool.submit(lavora_dominio, d, args.forza): d for d in domini}
        for f in as_completed(futuri):
            d = futuri[f]
            try:
                dom, esito, url = f.result(timeout=30)
                if esito == "skip": skippati += 1
                elif esito == "trovato": trovati += 1; log(f"  ✅ {dom}: {url[:60]}", "+")
                else: non_trovati += 1
            except Exception as e:
                non_trovati += 1; log(f"  ERR {d}: {str(e)[:60]}", "-")

    log(f"\nFatto in {time.time()-t0:.0f}s: {trovati} feed validi, {non_trovati} no, {skippati} skip", "+")
    conn.close()

if __name__ == "__main__":
    main()