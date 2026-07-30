#!/usr/bin/env python3
"""
discovery-endpoint-spa.py

Scopre l'endpoint JSON interno usato dalle pagine di ricerca delle farmacie
online costruite come SPA (React/Vue/Angular), dove l'HTML statico non
contiene i link prodotto e il crawler sitemap classico non basta.

Approccio:
  1. Apre la pagina di ricerca del dominio con un browser headless (Playwright)
  2. Intercetta tutte le risposte di rete (XHR/fetch) durante il caricamento
  3. Individua, con un'euristica su URL/content-type, quale risposta è
     l'endpoint di ricerca prodotti
  4. Salva il pattern trovato in indice_endpoint.db, cosi' le query successive
     per quel dominio possono chiamare l'endpoint direttamente con requests/httpx,
     SENZA piu' bisogno del browser

Uso tipico (una tantum o mensile, NON per ogni query live):
    python3 discovery-endpoint-spa.py --domini domini_spa.txt --workers 3

Poi, per interrogare un dominio gia' scoperto:
    python3 discovery-endpoint-spa.py --query "tachipirina" --dominio farmaciaXY.it

Note:
- Va eseguito a bassa concorrenza (2-4 worker): un browser headless pesa
  molto di piu' di una singola richiesta HTTP.
- Richiede: pip install playwright httpx && playwright install chromium
"""

import argparse
import json
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

DB_PATH = Path(__file__).parent / "indice_endpoint.db"
QUERY_TEST_DEFAULT = "tachipirina"

KEYWORD_HINTS = [
    "search", "cerca", "ricerca", "product", "prodott",
    "catalog", "catalogsearch", "api/search", "query",
]

SEARCH_PATH_TEMPLATES = [
    "/cerca?q={q}",
    "/search?q={q}",
    "/ricerca?q={q}",
    "/catalogsearch/result/?q={q}",
    "/search/{q}",
    "/?s={q}",
]


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS endpoint_discovery (
            dominio TEXT PRIMARY KEY,
            endpoint_pattern TEXT,
            metodo TEXT,
            content_type TEXT,
            trovato INTEGER,
            data_verifica TEXT,
            note TEXT
        )
    """)
    conn.commit()
    return conn


def gia_verificato(conn, dominio, giorni_validita=30):
    row = conn.execute(
        "SELECT endpoint_pattern, trovato, data_verifica FROM endpoint_discovery WHERE dominio = ?",
        (dominio,),
    ).fetchone()
    if not row:
        return None
    endpoint_pattern, trovato, data_verifica = row
    eta_giorni = (time.time() - float(data_verifica)) / 86400 if data_verifica else 999
    if eta_giorni > giorni_validita:
        return None
    return {"endpoint_pattern": endpoint_pattern, "trovato": bool(trovato)}


def salva_esito(conn, dominio, endpoint_pattern, metodo, content_type, trovato, note=""):
    conn.execute("""
        INSERT INTO endpoint_discovery (dominio, endpoint_pattern, metodo, content_type, trovato, data_verifica, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(dominio) DO UPDATE SET
            endpoint_pattern=excluded.endpoint_pattern,
            metodo=excluded.metodo,
            content_type=excluded.content_type,
            trovato=excluded.trovato,
            data_verifica=excluded.data_verifica,
            note=excluded.note
    """, (dominio, endpoint_pattern, metodo, content_type, int(trovato), str(time.time()), note))
    conn.commit()


def scopri_endpoint(dominio, query_test=QUERY_TEST_DEFAULT, timeout_ms=8000):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright non installato. pip install playwright && playwright install chromium")
        sys.exit(1)

    risultato = {"trovato": False, "endpoint_pattern": None, "metodo": None, "content_type": None, "note": ""}
    candidati = []

    def on_response(response):
        try:
            ctype = response.headers.get("content-type", "")
            if "json" not in ctype:
                return
            url_lower = response.url.lower()
            if any(k in url_lower for k in KEYWORD_HINTS):
                try:
                    body = response.json()
                except:
                    body = None
                candidati.append({
                    "url": response.url,
                    "metodo": response.request.method,
                    "content_type": ctype,
                    "ha_body_json": body is not None,
                })
        except:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("response", on_response)

        for template in SEARCH_PATH_TEMPLATES:
            url = f"https://{dominio}{template.format(q=query_test)}"
            try:
                page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                page.wait_for_timeout(2500)
            except:
                continue
            if candidati:
                break

        browser.close()

    if candidati:
        scelto = next((c for c in candidati if c["ha_body_json"]), candidati[0])
        pattern = re.sub(re.escape(query_test), "{q}", scelto["url"], flags=re.IGNORECASE)
        risultato.update({
            "trovato": True,
            "endpoint_pattern": pattern,
            "metodo": scelto["metodo"],
            "content_type": scelto["content_type"],
        })
    else:
        risultato["note"] = "nessun endpoint JSON con le euristiche correnti"

    return risultato


def processa_dominio(dominio, conn, forza=False):
    if not forza:
        esistente = gia_verificato(conn, dominio)
        if esistente:
            return dominio, {"skip": True, **esistente}

    esito = scopri_endpoint(dominio)
    salva_esito(conn, dominio, esito["endpoint_pattern"], esito["metodo"],
                esito["content_type"], esito["trovato"], esito["note"])
    return dominio, esito


def esegui_discovery_batch(domini, workers=3, forza=False):
    conn = init_db()
    trovati, non_trovati, skippati = 0, 0, 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(processa_dominio, dominio, init_db(), forza): dominio for dominio in domini}
        for future in as_completed(futures):
            dominio = futures[future]
            try:
                _, esito = future.result()
            except Exception as e:
                print(f"[ERRORE] {dominio}: {e}")
                continue

            if esito.get("skip"):
                skippati += 1
                print(f"[SKIP] {dominio}: {'trovato' if esito.get('trovato') else 'non trovato'}")
            elif esito.get("trovato"):
                trovati += 1
                print(f"[OK]   {dominio}: {esito['endpoint_pattern']}")
            else:
                non_trovati += 1
                print(f"[MISS] {dominio}: {esito.get('note', '')}")

    print(f"\nRiepilogo: {trovati} trovati, {non_trovati} non trovati, {skippati} skippati")


def interroga_endpoint_scoperto(dominio, query):
    import httpx

    conn = init_db()
    row = conn.execute(
        "SELECT endpoint_pattern, metodo FROM endpoint_discovery WHERE dominio = ? AND trovato = 1",
        (dominio,),
    ).fetchone()
    if not row:
        print(f"Nessun endpoint scoperto per {dominio}")
        return None

    pattern, metodo = row
    url = pattern.replace("{q}", query)

    try:
        resp = httpx.get(url, timeout=6.0) if metodo == "GET" else httpx.post(url, timeout=6.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Errore endpoint {dominio}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Discovery endpoint JSON per farmacie online SPA")
    parser.add_argument("--domini", type=str, help="File con un dominio per riga")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--forza", action="store_true")
    parser.add_argument("--query", type=str, help="Interroga endpoint scoperto con query")
    parser.add_argument("--dominio", type=str, help="Dominio singolo")
    args = parser.parse_args()

    if args.query and args.dominio:
        risultato = interroga_endpoint_scoperto(args.dominio, args.query)
        if risultato:
            print(json.dumps(risultato, indent=2, ensure_ascii=False)[:2000])
        return

    if args.dominio and not args.domini:
        domini = [args.dominio]
    elif args.domini:
        domini = [line.strip() for line in Path(args.domini).read_text().splitlines() if line.strip()]
    else:
        parser.error("Serve --domini (file), --dominio (singolo), o --query + --dominio")
        return

    esegui_discovery_batch(domini, workers=args.workers, forza=args.forza)


if __name__ == "__main__":
    main()