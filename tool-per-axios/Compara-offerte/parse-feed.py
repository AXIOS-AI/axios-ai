#!/usr/bin/env python3
"""
parse-feed.py — Estrae prodotti + prezzi da feed XML farmacia
==============================================================
Supporta:
  - Google Shopping feed (namespace g:)
  - Feed WooCommerce/WordPress standard
  - Feed PrestaShop
  - Sitemap prodotto (solo URL, da incrociare con JSON-LD)

Uso:
  python3 parse-feed.py --dominio farmacosmo.it           # Feed singolo
  python3 parse-feed.py --feed https://.../feed.xml       # URL diretto
  python3 parse-feed.py --domini domini_con_feed.txt      # Batch
  python3 parse-feed.py --stats                           # Statistiche DB prezzi

Integrazione: chiamato dopo feed-discovery.py per popolare indice_prezzi.db
con prezzi reali dai feed Google Shopping.
"""

import argparse
import json
import re
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = Path(__file__).parent
CACHE_FEED_DB = SCRIPT_DIR / "feed_cache.db"
PREZZI_DB = SCRIPT_DIR / "indice_prezzi.db"
USER_AGENT = "Mozilla/5.0 (compatible; AxiosCrawler/2.0; +https://axios-ai.it)"
TIMEOUT = 30

# Namespace Google Shopping
GS = {
    'g': 'http://base.google.com/ns/1.0',
    'c': 'http://base.google.com/cns/1.0',
}


def init_prezzi_db():
    conn = sqlite3.connect(PREZZI_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prezzi_feed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dominio TEXT NOT NULL,
            aic TEXT,
            nome TEXT NOT NULL,
            prezzo REAL,
            url_prodotto TEXT,
            disponibilita TEXT,
            marca TEXT,
            categoria TEXT,
            sourced_from TEXT,
            data_verifica TEXT,
            UNIQUE(dominio, url_prodotto)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pf_dominio ON prezzi_feed(dominio)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pf_nome ON prezzi_feed(nome)")
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS prezzi_fts USING fts5(
            nome, marca, categoria, dominio,
            content='prezzi_feed',
            content_rowid='id'
        )
    """)
    conn.commit()
    return conn


def get_feed_for_domain(dominio):
    """Recupera feed_url da feed_cache.db."""
    if not CACHE_FEED_DB.exists():
        return None
    try:
        conn = sqlite3.connect(CACHE_FEED_DB)
        row = conn.execute(
            "SELECT feed_url, tipo FROM feed_cache WHERE dominio = ? AND trovato = 1",
            (dominio,),
        ).fetchone()
        conn.close()
        if row:
            url, tipo = row
            return url, tipo
    except:
        pass
    return None


def scarica_feed(url):
    """Scarica feed XML."""
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT},
                         timeout=TIMEOUT, verify=False)
        if r.status_code >= 400:
            return None
        # Gestisci gzip
        content = r.content
        try:
            import gzip
            content = gzip.decompress(content)
        except:
            pass
        return content
    except Exception as e:
        print(f"  ERR download {url}: {e}")
        return None


def parse_google_shopping(xml_data, dominio):
    """Parsing Google Shopping XML feed (namespace g:)."""
    prodotti = []
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"  ERR parse XML {dominio}: {e}")
        return prodotti

    # Google Shopping usa <item> dentro <channel> (come RSS)
    channel = root.find('channel')
    items = channel.findall('item') if channel is not None else root.findall('.//item')
    
    if not items:
        # Prova formato diverso: <entry> (Atom) o diretto
        items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
        # Se ancora niente, prova tutti i tag child
        if not items:
            items = list(root)

    for item in items:
        try:
            title_el = item.find('title')
            if title_el is None:
                continue
            title = title_el.text or ""
            title = unescape(title.strip())

            # Google Shopping: g:price, g:link, g:availability
            price_el = item.find('g:price', GS)
            if price_el is None:
                price_el = item.find('price')  # fallback
            price_raw = price_el.text if price_el is not None else ""

            # Estrai numero da "EUR 12.50" o "12.50 EUR" o "12.50"
            prezzo = None
            if price_raw:
                m = re.search(r'(\d+[.,]\d{2})', price_raw.replace(',', '.'))
                if m:
                    prezzo = float(m.group(1))

            link = None
            link_el = item.find('g:link', GS)
            if link_el is None:
                link_el = item.find('link')
            if link_el is not None:
                link = link_el.text or link_el.get('href', '')

            # Disponibilità
            disp = ""
            disp_el = item.find('g:availability', GS)
            if disp_el is not None:
                disp = disp_el.text or ""

            # Marca
            marca = ""
            for tag in ['g:brand', 'g:manufacturer', 'brand']:
                el = item.find(tag, GS)
                if el is not None and el.text:
                    marca = el.text.strip()
                    break

            # Categoria
            cat = ""
            for tag in ['g:product_type', 'g:google_product_category']:
                el = item.find(tag, GS)
                if el is not None and el.text:
                    cat = el.text.strip()
                    break

            # AIC (codice farmaco)
            aic = ""
            for tag in ['g:mpn', 'g:id', 'g:gtin']:
                el = item.find(tag, GS)
                if el is not None and el.text:
                    aic = el.text.strip()
                    break

            prodotti.append({
                'nome': title,
                'prezzo': prezzo,
                'url': link or "",
                'disponibilita': disp,
                'marca': marca,
                'categoria': cat,
                'aic': aic,
                'dominio': dominio,
            })
        except Exception as e:
            continue

    return prodotti


def parse_sitemap(xml_data, dominio):
    """Parsing sitemap XML: estrae solo URL, niente prezzo."""
    urls = []
    try:
        root = ET.fromstring(xml_data)
    except:
        return urls
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    for loc in root.findall('.//s:loc', ns):
        if loc.text:
            urls.append({
                'nome': loc.text.strip().split('/')[-1].replace('-', ' ').replace('_', ' '),
                'prezzo': None,
                'url': loc.text.strip(),
                'dominio': dominio,
                'aic': '',
            })
    # Se senza namespace (sitemap flat)
    if not urls:
        for loc in root.findall('.//loc'):
            if loc.text:
                urls.append({
                    'nome': loc.text.strip().split('/')[-1].replace('-', ' ').replace('_', ' '),
                    'prezzo': None,
                    'url': loc.text.strip(),
                    'dominio': dominio,
                    'aic': '',
                })
    # Se è sitemap index (contiene altre sitemap), segnala
    sitemap_tags = root.findall('.//s:sitemap', ns) or root.findall('.//sitemap')
    url_tags = root.findall('.//s:url', ns) or root.findall('.//url')
    return {
        'urls': urls,
        'is_index': bool(sitemap_tags) and not url_tags,
    }


def processa_dominio(dominio):
    """Processa un dominio: scarica feed, parse, salva."""
    result = get_feed_for_domain(dominio)
    if not result:
        return dominio, 0, "nessun feed"
    
    feed_url, tipo = result
    data = scarica_feed(feed_url)
    if not data:
        return dominio, 0, f"download fallito {feed_url[:60]}"
    
    size_kb = len(data) // 1024

    # Tenta Google Shopping prima (più ricco)
    prodotti = parse_google_shopping(data, dominio)
    
    if not prodotti:
        # Fallback: sitemap
        parsed = parse_sitemap(data, dominio)
        if isinstance(parsed, dict) and parsed.get('is_index'):
            return dominio, size_kb, "sitemap index (contiene sub-sitemap)"
        prodotti = parsed if isinstance(parsed, list) else []

    if not prodotti:
        return dominio, size_kb, f"parse fallito ({size_kb}KB)"

    # Salva in DB
    conn = init_prezzi_db()
    inseriti = 0
    for p in prodotti:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO prezzi_feed
                (dominio, aic, nome, prezzo, url_prodotto, disponibilita, marca, categoria, sourced_from, data_verifica)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (dominio, p.get('aic', ''),
                  p.get('nome', ''),
                  p.get('prezzo'),
                  p.get('url', ''),
                  p.get('disponibilita', ''),
                  p.get('marca', ''),
                  p.get('categoria', ''),
                  'feed',
                  datetime.now(timezone.utc).isoformat()))
            inseriti += 1
        except Exception as e:
            pass
    
    conn.commit()
    
    # Sincronizza FTS
    if inseriti > 0:
        conn.execute("""
            INSERT INTO prezzi_fts(rowid, nome, marca, categoria, dominio)
            SELECT id, nome, marca, categoria, dominio FROM prezzi_feed
            WHERE dominio = ? AND id NOT IN (SELECT rowid FROM prezzi_fts)
        """, (dominio,))
        conn.commit()

    conn.close()
    
    con_prezzo = sum(1 for p in prodotti if p.get('prezzo') is not None)
    return dominio, inseriti, f"{inseriti} prodotti ({con_prezzo} con prezzo)"


def stats():
    conn = init_prezzi_db()
    tot = conn.execute("SELECT COUNT(*) FROM prezzi_feed").fetchone()[0]
    con_prezzo = conn.execute("SELECT COUNT(*) FROM prezzi_feed WHERE prezzo IS NOT NULL").fetchone()[0]
    domini = conn.execute("SELECT COUNT(DISTINCT dominio) FROM prezzi_feed").fetchone()[0]
    print(f"Prodotti in DB:     {tot}")
    print(f"Con prezzo:         {con_prezzo}")
    print(f"Domini:             {domini}")
    print()
    print("Top domini per prodotti:")
    for row in conn.execute("""
        SELECT dominio, COUNT(*), SUM(CASE WHEN prezzo IS NOT NULL THEN 1 ELSE 0 END)
        FROM prezzi_feed GROUP BY dominio ORDER BY COUNT(*) DESC LIMIT 10
    """):
        print(f"  {row[0]:25s} {row[1]:6d} prodotti ({row[2]} con prezzo)")
    print()
    print("Ricerca 'tachipirina':")
    for row in conn.execute("""
        SELECT dominio, nome, prezzo, url_prodotto
        FROM prezzi_feed WHERE LOWER(nome) LIKE '%tachipirina%' AND prezzo IS NOT NULL
        LIMIT 20
    """):
        print(f"  {row[0]:25s} €{row[2]:>7.2f} {row[1][:50]}")
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dominio", type=str, help="Processa un singolo dominio")
    parser.add_argument("--domini", type=str, help="File lista domini")
    parser.add_argument("--feed", type=str, help="URL feed diretto")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    if args.stats:
        stats()
        return

    if args.feed:
        # URL feed diretto
        print(f"Download feed {args.feed}...")
        data = scarica_feed(args.feed)
        if data:
            prodotti = parse_google_shopping(data, "diretto")
            if not prodotti:
                prodotti = parse_sitemap(data, "diretto")
            if isinstance(prodotti, dict):
                print(f"Sitemap index, {len(prodotti['urls'])} URL")
            else:
                print(json.dumps(prodotti[:5], indent=2, ensure_ascii=False))
        return

    domini = []
    if args.dominio:
        domini = [args.dominio]
    elif args.domini:
        with open(args.domini) as f:
            domini = [line.strip() for line in f if line.strip()]
    else:
        # Prendi tutti i domini con feed da feed_cache.db
        if not CACHE_FEED_DB.exists():
            print("Esegui prima feed-discovery.py")
            return
        conn = sqlite3.connect(CACHE_FEED_DB)
        for row in conn.execute(
            "SELECT dominio FROM feed_cache WHERE trovato = 1 ORDER BY dominio"
        ):
            domini.append(row[0])
        conn.close()

    if not domini:
        print("Nessun dominio da processare")
        return

    t0 = time.time()
    print(f"Parse feed per {len(domini)} domini ({args.workers} workers)...")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futuri = {pool.submit(processa_dominio, d): d for d in domini}
        for f in as_completed(futuri):
            d = futuri[f]
            try:
                dominio, inseriti, msg = f.result(timeout=60)
                if inseriti > 0:
                    print(f"  [{dominio:25s}] {msg}")
                else:
                    print(f"  [{dominio:25s}] {msg}")
            except Exception as e:
                print(f"  [{d:25s}] ERR: {e}")

    t1 = time.time()
    print(f"\nCompletato in {t1-t0:.0f}s")
    stats()


if __name__ == "__main__":
    main()