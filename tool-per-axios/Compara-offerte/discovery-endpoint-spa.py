#!/usr/bin/env python3
"""
discovery-endpoint-spa.py — Scopre endpoint JSON per SPA farmacia
================================================================
Usa pyppeteer (async) per aprire pagina ricerca, intercettare XHR/fetch
JSON, e salvare pattern endpoint in SQLite.

Approccio:
  1. Apre pagina di ricerca del dominio con pyppeteer headless
  2. Intercetta risposte di rete (XHR/fetch) durante caricamento
  3. Individua endpoint JSON risposta con keyword hints
  4. Salva pattern in indice_endpoint.db
  5. Query live successive chiamano endpoint direttamente con httpx

Uso:
  python3 discovery-endpoint-spa.py --domini lista.txt          # Discovery batch
  python3 discovery-endpoint-spa.py --dominio farmaciaXY.it     # Singolo
  python3 discovery-endpoint-spa.py --query "tachipirina" --dominio farmaciaXY.it  # Interroga

Concorrenza: asyncio.Semaphore(2-3) — browser headless pesa.
"""

import argparse
import asyncio
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "indice_endpoint.db"
QTEST = "tachipirina"

# Keywords che suggeriscono endpoint di ricerca prodotto
KW = ["search", "cerca", "ricerca", "product", "prodott",
      "catalog", "catalogsearch", "api/search", "query", "filter",
      "suggest", "json"]

# Pagine di ricerca da provare per triggerare XHR
SEARCH = [
    "/cerca?q={q}", "/search?q={q}", "/ricerca?q={q}",
    "/catalogsearch/result/?q={q}", "/search/{q}", "/?s={q}",
    "/search/suggest.json?q={q}",    # Shopify AJAX
    "/api/search?q={q}",             # API generica
    "/api/products/search?q={q}",
    "/ajax/search?q={q}",            # PrestaShop
]


def conn_db():
    c = sqlite3.connect(DB_PATH)
    c.execute("""
        CREATE TABLE IF NOT EXISTS endpoint_discovery (
            dominio TEXT PRIMARY KEY,
            endpoint_pattern TEXT, metodo TEXT,
            content_type TEXT, trovato INTEGER,
            data_verifica TEXT, note TEXT
        )
    """)
    c.commit(); return c


def salva(dominio, ep, metodo, ctype, trovato, note=""):
    c = conn_db()
    c.execute("""
        INSERT OR REPLACE INTO endpoint_discovery
        VALUES (?,?,?,?,?,?,?)
    """, (dominio, ep or "", metodo or "", ctype or "",
          int(trovato), str(time.time()), note or ""))
    c.commit(); c.close()


def gia_verificato(dominio, giorni=30):
    c = conn_db()
    r = c.execute(
        "SELECT endpoint_pattern, trovato, data_verifica FROM endpoint_discovery WHERE dominio=?",
        (dominio,)
    ).fetchone()
    c.close()
    if not r: return None
    ep, trov, dv = r
    eta = (time.time() - float(dv)) / 86400 if dv else 999
    if eta > giorni: return None
    return {"endpoint_pattern": ep, "trovato": bool(trov)}


async def scopri(dominio, query=QTEST, timeout_ms=10000):
    """
    Apre dominio con pyppeteer, carica pagina ricerca, cattura endpoint JSON.
    """
    from pyppeteer import launch

    candidati = []

    # Domini terze parti da escludere (tracking/telemetry/CDN)
    EXCLUDE_DOM = {"shopifysvc.com", "shop.app", "google-analytics.com",
                   "googletagmanager.com", "facebook.com", "doubleclick.net",
                   "hotjar.com", "cookielaw.org", "optanon"}

    async def on_response(res):
        try:
            ct = res.headers.get("content-type", "").lower()
            if "json" not in ct:
                return
            url = res.url.lower()

            # Escludi tracking/telemetry di terze parti
            from urllib.parse import urlparse
            dom = urlparse(url).netloc.replace("www.", "")
            if any(x in dom for x in EXCLUDE_DOM):
                return
            # Preferisci endpoint sullo stesso dominio
            if dom != dominio.lower() and not dom.endswith("." + dominio.lower()):
                return

            if any(k.replace("*","") in url for k in KW if k != "*"):
                try:
                    body = await res.json()
                    has_body = body is not None
                except:
                    has_body = False
                candidati.append({
                    "url": res.url, "method": res.request.method,
                    "ctype": ct, "has_body": has_body,
                })
        except:
            pass

    browser = await launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox",
              "--disable-dev-shm-usage", "--single-process"],
        handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
    )
    page = await browser.newPage()
    page.on("response", lambda r: asyncio.ensure_future(on_response(r)))

    for tmpl in SEARCH:
        url = f"https://{dominio}{tmpl.format(q=query)}"
        try:
            resp = await page.goto(url, timeout=timeout_ms, waitUntil="domcontentloaded")
            await asyncio.sleep(3)
        except:
            continue
        if candidati:
            break

    await browser.close()

    if candidati:
        scelto = next((c for c in candidati if c["has_body"]), candidati[0])
        pattern = re.sub(re.escape(query), "{q}", scelto["url"], flags=re.IGNORECASE)
        return {"trovato": True, "endpoint_pattern": pattern,
                "metodo": scelto["method"], "content_type": scelto["ctype"]}

    return {"trovato": False, "endpoint_pattern": None,
            "metodo": None, "content_type": None,
            "note": "nessun endpoint JSON con keyword hints"}


async def processa(dominio, forza=False):
    if not forza:
        v = gia_verificato(dominio)
        if v: return dominio, "skip", v.get("trovato")

    esito = await scopri(dominio)
    salva(dominio, esito["endpoint_pattern"], esito["metodo"],
          esito["content_type"], esito["trovato"], esito.get("note", ""))
    return dominio, "ok", esito["trovato"]


async def batch(domini, workers=3, forza=False):
    sem = asyncio.Semaphore(workers)
    trov, miss, skip = 0, 0, 0

    async def limit(d):
        async with sem:
            return await processa(d, forza)

    tasks = [limit(d) for d in domini]
    for coro in asyncio.as_completed(tasks):
        d, esito, ok = await coro
        if esito == "skip":
            skip += 1; print(f"[SKIP] {d} ({'ok' if ok else 'miss'})")
        elif ok:
            trov += 1; print(f"[OK]   {d}: endpoint trovato")
        else:
            miss += 1; print(f"[MISS] {d}")

    print(f"\nBatch: {trov} ok, {miss} miss, {skip} skip")
    return trov, miss, skip


def interroga(dominio, query):
    """Chiama endpoint scoperto direttamente con httpx."""
    import httpx
    c = conn_db()
    r = c.execute(
        "SELECT endpoint_pattern, metodo FROM endpoint_discovery WHERE dominio=? AND trovato=1",
        (dominio,)
    ).fetchone()
    c.close()
    if not r:
        print(f"Nessun endpoint per {dominio}. Esegui prima discovery.")
        return None

    url = r[0].replace("{q}", query)
    try:
        resp = httpx.get(url, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"ERR: {e}")
        return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--domini", type=str, help="File con un dominio per riga")
    p.add_argument("--workers", type=int, default=3, help="Browser paralleli (default 3)")
    p.add_argument("--forza", action="store_true")
    p.add_argument("--query", type=str, help="Interroga endpoint scoperto")
    p.add_argument("--dominio", type=str, help="Dominio singolo per discovery o interrogaz.")
    args = p.parse_args()

    if args.query and args.dominio:
        r = interroga(args.dominio, args.query)
        if r:
            print(json.dumps(r, indent=2, ensure_ascii=False)[:2000])
        return

    if args.dominio and not args.domini:
        domini = [args.dominio]
    elif args.domini:
        domini = [l.strip() for l in Path(args.domini).read_text().splitlines() if l.strip()]
    else:
        p.error("Serve --domini (file), --dominio (singolo), o --query + --dominio")

    print(f"Endpoint discovery su {len(domini)} domini ({args.workers} workers)...")
    asyncio.run(batch(domini, args.workers, args.forza))


if __name__ == "__main__":
    main()