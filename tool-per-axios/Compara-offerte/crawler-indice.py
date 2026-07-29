#!/usr/bin/env python3
"""
crawler-indice.py — Crawler sitemap per indice locale prezzi farmaci
====================================================================
Scarica sitemap da domini in siti.md (max 3-4 worker paralleli),
estrae URL prodotto, salva in SQLite FTS5 per ricerca veloce.

Usage:
  python3 crawler-indice.py                           # Crawl completo 36 domini
  python3 crawler-indice.py --workers 2               # Crawl con 2 worker
  python3 crawler-indice.py --stats                   # Statistiche indice
  python3 crawler-indice.py --query "miflor"          # Cerca nell'indice
  python3 crawler-indice.py --reset                   # Reset indice

Architettura:
  - Worker paralleli scaricano sitemap (max 5MB, timeout 6s)
  - Restituiscono risultati al main thread (NO scrittura concorrente)
  - Main thread scrive serialmente su SQLite (nessun lock)
  - Supporta If-Modified-Since via meta_sitemap table
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
from urllib.parse import urlparse

try:
    import requests
    from lxml import etree
except ImportError:
    print("[!] pip install requests lxml")
    sys.exit(1)

# ─── Config ─────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SITI_FILE = os.path.join(SCRIPT_DIR, "siti.md")
INDICE_FILE = os.path.join(SCRIPT_DIR, "indice_prezzi.db")

USER_AGENT = "Mozilla/5.0 (compatible; AxiosCrawler/1.0; +https://axios-ai.it)"
MAX_WORKERS = 3
TIMEOUT = 6
MAX_BYTES = 5 * 1024 * 1024
VERSION = "1.1.0"

SITEMAP_PATHS = ["/sitemap.xml", "/sitemap_index.xml"]

# ─── Logging ────────────────────────────────────────

def log(msg, level="+"):
    c = {"+": "\033[92m", "-": "\033[93m", "!": "\033[91m", "*": "\033[94m", "~": "\033[96m"}
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {c.get(level, '')}[{level}]\033[0m {ts} {msg}")

# ─── Caricamento domini ─────────────────────────────

def carica_domini():
    """Legge domini da siti.md."""
    domini = []
    if not os.path.exists(SITI_FILE):
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

# ─── SQLite (solo main thread) ──────────────────────

def init_db(db_path=INDICE_FILE):
    """Crea/apre database. Chiamata SOLO dal main thread."""
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")  # piu veloce per batch insert
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS indice USING fts5(
            dominio, url_prodotto, slug, aic, nome_estratto,
            data_indicizzazione UNINDEXED
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta_sitemap (
            dominio TEXT PRIMARY KEY,
            last_modified TEXT,
            etag TEXT,
            ultimo_crawl TEXT
        )
    """)
    conn.commit()
    return conn


def svuota_indice(conn, dominio=None):
    if dominio:
        conn.execute("DELETE FROM indice WHERE dominio = ?", (dominio,))
    else:
        conn.execute("DELETE FROM indice")
    conn.commit()


def inserisci_url_multi(conn, entries):
    """Inserisce batch di URL. entries: [(dominio, url, slug, aic, nome), ...]"""
    conn.executemany(
        "INSERT INTO indice (dominio, url_prodotto, slug, aic, nome_estratto, data_indicizzazione) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(d, u, s or "", a or "", n or "",
          datetime.now(timezone.utc).isoformat())
         for d, u, s, a, n in entries]
    )


def aggiorna_meta(conn, dominio, last_modified, etag):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO meta_sitemap (dominio, last_modified, etag, ultimo_crawl) "
        "VALUES (?, ?, ?, ?)",
        (dominio, last_modified or "", etag or "", now)
    )


def query_indice(conn, termine, limit=20):
    termine_pulito = re.sub(r'[^\w\s]', ' ', termine).strip()
    if not termine_pulito:
        return []
    cursor = conn.execute(
        "SELECT dominio, url_prodotto, slug, aic, nome_estratto, data_indicizzazione "
        "FROM indice WHERE indice MATCH ? ORDER BY rowid LIMIT ?",
        (f'"{termine_pulito}" OR slug:{termine_pulito}*', limit)
    )
    return cursor.fetchall()

# ─── Download sitemap (thread-safe) ─────────────────

def scarica_sitemap(url):
    """Scarica sitemap, restituisce testo o None."""
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT},
                         timeout=TIMEOUT, verify=False, stream=True)
        if r.status_code >= 400:
            return None
        
        chunks = []
        total = 0
        for chunk in r.iter_content(32768, decode_unicode=False):
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_BYTES:
                break
        
        data = b"".join(chunks)
        try:
            data = gzip.decompress(data)
        except:
            pass
        
        return data.decode("utf-8", errors="ignore")
    except:
        return None


def estrai_urls(text):
    """Estrae URL <loc> da XML con CDATA."""
    urls = []
    try:
        text_no_ns = re.sub(r'\s+xmlns[^=]*="[^"]*"', '', text, count=1)
        root = etree.fromstring(text_no_ns.encode("utf-8"))
        for loc in root.iter("loc"):
            if loc.text:
                urls.append(loc.text.strip())
    except:
        for m in re.finditer(r'<loc[^>]*>\s*(?:<!\[CDATA\[)?\s*(.*?)\s*(?:\]\]>)?\s*</loc>',
                             text, re.IGNORECASE | re.DOTALL):
            u = m.group(1).strip()
            if u:
                urls.append(u)
    return urls


def e_index(text):
    return '<sitemapindex' in text[:2000].lower() or '<sitemap>' in text[:2000].lower()


def estrai_slug(url):
    path = urlparse(url).path.strip("/")
    parts = [p for p in path.split("/") if p and not p.startswith("_") and not p.startswith(".")]
    if parts:
        slug = re.sub(r'\.(html?|php|asp|jsp)$', '', parts[-1])
        return slug
    return ""


def processa(text, dominio):
    """Processa sitemap XML, restituisce [(dominio, url, slug, aic, nome), ...]."""
    risultati = []
    
    if e_index(text):
        children = estrai_urls(text)
        log(f"  Index con {len(children)} child", "~")
        child_list = [c for c in children if 'product' in c.lower()][:3]
        if len(child_list) < 3:
            child_list += [c for c in children if 'product' not in c.lower()][:5]
        for cu in child_list[:5]:
            log(f"  Seguo: {cu.split('/')[-1][:50]}", "~")
            child_text = scarica_sitemap(cu)
            if child_text:
                risultati.extend(processa(child_text, dominio))
        return risultati
    
    urls = estrai_urls(text)
    log(f"  {len(urls)} URL", "~")
    
    entries = []
    for url in urls:
        slug = estrai_slug(url)
        if not slug:
            continue
        nome = re.sub(r'[-_+]', ' ', slug).strip()
        aic = re.search(r'/(\d{6})\b', url)
        entries.append((dominio, url, slug, aic.group(1) if aic else "", nome))
    
    return entries

# ─── Worker (nessuna scrittura DB) ──────────────────

def lavora_dominio(dominio):
    """Processa dominio, restituisce (dominio, entries, crawled_ok)."""
    for sm_path in SITEMAP_PATHS:
        for base in [f"https://www.{dominio}", f"https://{dominio}"]:
            text = scarica_sitemap(f"{base}{sm_path}")
            if text:
                log(f"  OK {dominio} ({len(text)//1024}KB)", "+")
                entries = processa(text, dominio)
                if entries:
                    log(f"  {len(entries)} URL", "~")
                return (dominio, entries, True)
    return (dominio, [], False)

# ─── Main ───────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="crawler-indice v" + VERSION)
    parser.add_argument("--db", default=INDICE_FILE)
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--query", type=str)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    
    conn = init_db(args.db)
    
    if args.stats:
        tot = conn.execute("SELECT COUNT(*) FROM indice").fetchone()[0]
        dom = conn.execute("SELECT COUNT(DISTINCT dominio) FROM indice").fetchone()[0]
        log(f"DB: {tot} URL, {dom} domini")
        conn.close()
        return
    
    if args.query:
        for r in query_indice(conn, args.query, 20):
            print(f"  {r[0]:30s} {r[3] or '--':8s} {r[2][:35]:35s} {r[1][:60]}")
        conn.close()
        return
    
    if args.reset:
        svuota_indice(conn)
        conn.execute("DELETE FROM meta_sitemap")
        conn.commit()
        log("Indice resettato", "+")
        conn.close()
        return
    
    domini = carica_domini()
    if not domini:
        conn.close()
        return
    
    log(f"Crawl {len(domini)} domini ({args.workers} workers)...", "*")
    t0 = time.time()
    total_entries = 0
    crawlati = 0
    falliti = 0
    
    # Fase 1: worker paralleli scaricano sitemap (NO scrittura DB)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futuri = {pool.submit(lavora_dominio, d): d for d in domini}
        for f in as_completed(futuri):
            d = futuri[f]
            try:
                dominio, entries, ok = f.result()
                if entries:
                    # Fase 2: main thread scrive su DB (serialmente, no lock)
                    svuota_indice(conn, dominio)
                    inserisci_url_multi(conn, entries)
                    conn.commit()
                    total_entries += len(entries)
                    log(f"  Scritti {len(entries)} URL per {dominio}", "+")
                    crawlati += 1
                elif ok:
                    # Sitemap trovata ma senza URL prodotto
                    crawlati += 1
                    log(f"  Nessun URL prodotto in {dominio}", "~")
                else:
                    falliti += 1
            except Exception as e:
                falliti += 1
                log(f"  ERR {d}: {str(e)[:60]}", "-")
    
    t1 = time.time()
    log(f"Crawl: {t1-t0:.0f}s", "+")
    log(f"  Domini: {len(domini)}, Crawlati: {crawlati}, Falliti: {falliti}, URL: {total_entries}", "+")
    
    conn.close()


if __name__ == "__main__":
    main()
