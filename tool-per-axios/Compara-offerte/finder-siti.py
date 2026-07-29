#!/usr/bin/env python3
"""
finder-siti.py — Cerca siti con prezzi per un farmaco
=====================================================
Cerca su DuckDuckGo con 5 query (come farebbe un utente):
  1. "farmaco prezzo"
  2. "farmaco costo"
  3. "farmaco quanto costa"
  4. "farmaco prezzo farmacia"
  5. "farmaco prezzo online"

Prende primi 20 siti unici tra tutte le query, salva JSON.
Poi i siti possono essere passati a compara-offerte.py per estrarre prezzi.

Usage:
  python3 finder-siti.py "Tachipirina 1000"
  python3 finder-siti.py "Oki task" --max 30
  python3 finder-siti.py "Moment 400" --output ./dati_ricerca.json
  python3 finder-siti.py "Brufen 600" --verbose

Dipendenze: pip install requests beautifulsoup4 lxml
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import quote_plus, urlparse, urljoin

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")

try:
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    print("[!] pip install requests beautifulsoup4 lxml")
    sys.exit(1)

VERSION = "1.0.0"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# ─── Query template ───────────────────────────────

QUERY_TEMPLATES = [
    "{farmaco} prezzo",
    "{farmaco} costo",
    "{farmaco} quanto costa",
    "{farmaco} prezzo farmacia",
    "{farmaco} prezzo online",
]


# ─── Utility ──────────────────────────────────────

def log(msg, level="+"):
    colors = {"+": "\033[92m", "-": "\033[93m", "!": "\033[91m", "*": "\033[94m", "~": "\033[96m"}
    c = colors.get(level, "\033[0m")
    print(f"  {c}[{level}]\033[0m {msg}")


def decodifica_bing(url):
    """Estrae URL reale da link tracking Bing."""
    parsed = urlparse(url)
    if "bing.com" not in parsed.netloc:
        return url
    from urllib.parse import parse_qs
    qs = parse_qs(parsed.query)
    u_param = qs.get("u", [None])[0]
    if u_param:
        # Bing usa prefisso 'a1' + base64 dell'URL
        import base64
        b64 = u_param
        if b64.startswith("a1"):
            b64 = b64[2:]
        # Aggiungi padding
        pad = (4 - len(b64) % 4) % 4
        try:
            decoded = base64.urlsafe_b64decode(b64 + "=" * pad).decode("utf-8")
            return decoded
        except:
            return None
    return None


def pulisci_url(url):
    """Pulisce URL (filtra tracking/redirect)."""
    # Prima decodifica tracking Bing
    url = decodifica_bing(url)
    if not url:
        return None

    parsed = urlparse(url)
    dom = parsed.netloc.lower()

    # Salta annunci/redirect
    skip_domains = ["duckduckgo.com", "google.com", "google.it",
                    "youtube.com", "facebook.com", "instagram.com"]
    for s in skip_domains:
        if s in dom:
            return None

    # DuckDuckGo redirect annunci
    if "y.js" in url or "/aclick" in url:
        return None

    # Bing tracking non decodificabile
    if "bing.com" in dom:
        return None

    return url.rstrip("/")


def normalizza_url(url):
    """Rimuove tracking params (msockid, utm_*)."""
    parsed = urlparse(url)
    from urllib.parse import parse_qs, urlencode
    qs = parse_qs(parsed.query)
    # Parametri da rimuovere
    skip = {"msockid", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}
    keep = {k: v for k, v in qs.items() if k not in skip}
    if keep:
        new_qs = urlencode(keep, doseq=True)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_qs}"
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def estrai_dominio(url):
    """Estrae dominio base."""
    parsed = urlparse(url)
    return parsed.netloc.lower()


def is_sito_farmacia(url):
    """Controlla se URL sembra una farmacia (utile per filtraggio)."""
    dom = estrai_dominio(url)
    keywords = ["farmacia", "farma", "apoteca", "pharma", "farmaco", "sanita", "salute",
                "parafarmacia", "farmacie", "dottore", "medicina"]
    for k in keywords:
        if k in dom or k in url.lower():
            return True
    return False


# ─── Google Scraper ──────────────────────────────

def cerca_google(query, num_results=20):
    """
    Cerca su DuckDuckGo via duckduckgo_search (no API, gratis, robusto).
    Restituisce lista di dict con {url, title, snippet}.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        log("duckduckgo_search non installato. pip install duckduckgo_search", "!")
        return []

    risultati = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, region="it-it", max_results=num_results):
                href = pulisci_url(r.get("href", ""))
                if not href:
                    continue
                risultati.append({
                    "url": href,
                    "title": (r.get("title", "") or "")[:200],
                    "snippet": (r.get("body", "") or "")[:300],
                    "query": query,
                })
    except Exception as e:
        log(f"DuckDuckGo errore: {str(e)[:80]}", "!")
        return []

    log(f"  Trovati {len(risultati)} risultati", "+")
    return risultati


# ─── Main ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="finder-siti — Cerca siti con prezzi per un farmaco"
    )
    parser.add_argument("farmaco", help="Nome del farmaco (es. 'Tachipirina 1000')")
    parser.add_argument("--output", "-o", help="File output JSON", default="")
    parser.add_argument("--max", type=int, help="Max risultati per query", default=20)
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostra tutti i risultati")
    parser.add_argument("--solo-farmacie", action="store_true",
                        help="Filtra solo siti di farmacie")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Delay tra query (default 2s, evita blocco)")

    args = parser.parse_args()
    farmaco = args.farmaco.strip()

    # Genera queries
    queries = [qt.format(farmaco=farmaco) for qt in QUERY_TEMPLATES]

    log(f"{'='*50}")
    log(f"FINDER-SITI v{VERSION}")
    log(f"Farmaco: {farmaco}")
    log(f"Query: {len(queries)}")
    log(f"{'='*50}")

    # Cerca per ogni query
    tutti_risultati = []
    url_visti = set()

    for i, q in enumerate(queries):
        log(f"\n[{i+1}/{len(queries)}] {q}", "*")
        risultati = cerca_google(q, args.max)
        if not risultati:
            log("  Nessun risultato", "-")

        # Normalizza e filtra duplicati per URL
        nuovi = 0
        for r in risultati:
            r["url"] = normalizza_url(r["url"])
            if r["url"] not in url_visti:
                url_visti.add(r["url"])
                tutti_risultati.append(r)
                nuovi += 1
        log(f"  Nuovi unici: {nuovi}", "+")

        # Delay tra query
        if i < len(queries) - 1:
            time.sleep(args.delay)

    # Filtra solo farmacie se richiesto
    if args.solo_farmacie:
        farmacie = [r for r in tutti_risultati if is_sito_farmacia(r["url"])]
        log(f"\nFiltrati solo siti farmacia: {len(farmacie)}/{len(tutti_risultati)}", "~")
        tutti_risultati = farmacie

    # Prendi max 20 unici
    finali = tutti_risultati[:20]

    # Output JSON
    output = {
        "farmaco": farmaco,
        "timestamp": datetime.now().isoformat(),
        "version": VERSION,
        "query_utilizzate": queries,
        "totale_risultati_grezzi": len(tutti_risultati),
        "siti_trovati": [
            {
                "pos": i + 1,
                "url": r["url"],
                "dominio": estrai_dominio(r["url"]),
                "title": r["title"],
                "snippet": r["snippet"],
                "query_trovata": r.get("query", ""),
                "tipo": "farmacia" if is_sito_farmacia(r["url"]) else "altro",
            }
            for i, r in enumerate(finali)
        ],
    }

    # Salva
    output_path = args.output
    if not output_path:
        slug = re.sub(r'[^a-z0-9]', '-', farmaco.lower()).strip('-')
        slug = re.sub(r'-+', '-', slug)
        output_path = f"siti_{slug}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Stampa riepilogo
    log(f"\n{'='*50}")
    log(f"✅ COMPLETATO — {len(finali)} siti trovati", "+")
    log(f"📄 Salvato: {output_path}")
    log(f"{'='*50}")

    print(f"\n{'─'*60}")
    print(f"  SITI TROVATI PER: {farmaco}")
    print(f"{'─'*60}")
    for r in finali:
        tipo = "🏥" if is_sito_farmacia(r["url"]) else "🌐"
        print(f"  {tipo} {r['title'][:70]}")
        print(f"     {r['url']}")
        if args.verbose and r["snippet"]:
            print(f"     {r['snippet'][:100]}")
    print(f"{'─'*60}")

    # Suggerisci prossimo step
    print(f"\n  >> Usa con Compara-offerte:")
    print(f"     python3 compara-offerte.py --siti {output_path}")
    print()


if __name__ == "__main__":
    main()
