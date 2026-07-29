#!/usr/bin/env python3
"""
Compara-offerte v3.0 — Confronto prezzi farmaci
================================================
Cerca il miglior prezzo per un farmaco:
1. Siti farmacie da Farmascopri (verifica siti up/down)
2. Ricerca web (DuckDuckGo) per altri siti con prezzi
3. Google Shopping (SearchAPI.io) per confronto online
4. Scraping pagine per trovare il prezzo specifico
5. Output a schermo, report HTML solo se richiesto

Usage:
  python3 compara-offerte.py "Tachipirina 1000"
  python3 compara-offerte.py "Brufen 600" --report
  python3 compara-offerte.py --solo-web "Oki task"
  python3 compara-offerte.py --aggiorna-siti

Dipendenze: pip install requests beautifulsoup4 lxml duckduckgo_search
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import logging
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

try:
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    from duckduckgo_search import DDGS
except ImportError:
    print("[!] pip install requests beautifulsoup4 lxml duckduckgo_search")
    sys.exit(1)

# Sopprime TUTTI i warnings (SSL, urllib3)
import warnings as _warnings
_warnings.filterwarnings("ignore", category=Warning)
logging.captureWarnings(True)

VERSION = "3.0.0"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

FARMACOPRI_DATA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "farmascopri", "pipeline", "farmacie_complete.json"
)
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


# ─── Utility ────────────────────────────────────────

def log(msg, level="+"):
    c = {"+": "\033[92m", "-": "\033[93m", "!": "\033[91m", "*": "\033[94m", "~": "\033[96m"}
    print(f"  {c.get(level, '')}[{level}]\033[0m {msg}")


def load_env():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def normalizza_url(url):
    """Rimuove tracking params."""
    parsed = urlparse(url)
    from urllib.parse import parse_qs, urlencode
    qs = parse_qs(parsed.query)
    skip = {"msockid", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref"}
    keep = {k: v for k, v in qs.items() if k not in skip and not k.startswith("utm_")}
    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if keep:
        clean += "?" + urlencode(keep, doseq=True)
    return clean


def estrai_dominio(url):
    return urlparse(url).netloc.lower() if url else ""


def prezzo_in_testo(testo):
    """Estrae primo prezzo € da testo."""
    m = re.search(r'€\s*\d+[.,]\d{2}', testo)
    return m.group(0) if m else "(€ presente)"


DOMINI_INFO = ["oraridiapertura24", "lemalo", "ragusawelcome", "travelnostop",
               "my-personaltrainer", "policliniconews", "torrinomedica",
               "melarossa", "greenme", "cure-naturali", "riza"]
TITOLI_INFO = ["funziona", "opinioni", "controindicazioni", "a cosa serve",
               "bugiardino", "foglietto", "urologo", "prostatite", "erezione",
               "efficacia", "per quanto tempo", "cos'è", "recensioni"]


def e_info(url, titolo):
    titolo_l = titolo.lower() if titolo else ""
    for k in TITOLI_INFO:
        if k in titolo_l:
            return True
    return False


def sito_scraperabile(url):
    if not url:
        return False
    dom = estrai_dominio(url)
    for e in DOMINI_INFO:
        if e in dom:
            return False
    return True


# ─── FASE 1: Carica Farmascopri + verifica siti ─────

def carica_farmacie():
    """Carica farmacie con sito web valido."""
    if not os.path.exists(FARMACOPRI_DATA):
        log(f"File non trovato: {FARMACOPRI_DATA}", "!")
        return []
    with open(FARMACOPRI_DATA) as f:
        data = json.load(f)
    farmacie = [f for f in data if sito_scraperabile(f.get("sito", ""))]
    log(f"Caricate {len(farmacie)} farmacie con sito web", "+")
    return farmacie


def _verifica_sito_wrapper(f):
    url = f["sito"]
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT},
                         timeout=4, verify=False, allow_redirects=True)
        if r.status_code < 400:
            return ("up", f)
        return ("down", {"nome": f["nome"], "url": url, "status": r.status_code})
    except Exception as ex:
        return ("down", {"nome": f["nome"], "url": url, "status": str(type(ex).__name__)})


def verifica_siti(farmacie):
    """Verifica siti in parallelo."""
    log("Verifica siti farmacie...", "*")
    from concurrent.futures import ThreadPoolExecutor, as_completed
    up, down = [], []
    with ThreadPoolExecutor(max_workers=30) as pool:
        futuri = [pool.submit(_verifica_sito_wrapper, f) for f in farmacie]
        for f in as_completed(futuri):
            try:
                stato, dato = f.result()
                if stato == "up":
                    up.append(dato)
                else:
                    down.append(dato)
            except:
                pass
    if down:
        log(f"  Up: {len(up)}, Down: {len(down)}", "~")
        for d in down[:5]:
            log(f"  ✗ {d['nome']}: {d['status']}", "-")
    return up, down


# ─── FASE 2: Ricerca web (finder-siti integrato) ────

QUERY_TEMPLATES = [
    "{farmaco} prezzo farmacia",
    "{farmaco} prezzo online",
    "acquista {farmaco} online",
    "comprare {farmaco}",
    "{farmaco} in offerta",
    "farmacia online {farmaco}",
    "{farmaco} miglior prezzo",
    "{farmaco} spedizione gratuita",
]


SITI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "siti.md")

# Pattern di ricerca per ogni dominio (Magento, WordPress, WooCommerce, custom)
SEARCH_PATTERNS = [
    "/catalogsearch/result/?q={slug}",
    "/search?q={slug}",
    "/?s={slug}",
]  # soli 3 pattern, ordinati per frequenza


def carica_siti_md():
    """Legge siti.md e restituisce lista di (nome, dominio)."""
    siti = []
    if not os.path.exists(SITI_FILE):
        log(f"File siti.md non trovato", "!")
        return []
    with open(SITI_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                m = re.search(r'https?://([^/\s)]+)', line)
                if m:
                    dom = m.group(1).lower().replace("www.", "")
                    nome = dom.split(".")[0].capitalize()
                    siti.append((nome, dom))
    log(f"Caricati {len(siti)} domini da siti.md", "+")
    return siti


import urllib.parse

# Pattern URL per ricerca su domini e-commerce
URL_PATTERNS = [
    "/catalogsearch/result/?q={q}",
    "?s={q}",
    "/search?q={q}",
    "/{slug}.html",
    "/{slug}",
]

PREFIXES = ["", "www."]
NON_ECOMMERCE = {"facebook", "instagram", "twitter", "youtube", "linkedin",
                 "whatsapp", "telegram", "google", "amazon", "ebay",
                 "subito", "aranzulla", "telehealth", "hhs.gov",
                 "microsoft", "wordpress", "blogger", "tumblr"}


def _cerca_form_e_cerca(soup, base, farmaco_q):
    """Trova form di ricerca nella homepage e prova a cercare."""
    for form in soup.find_all("form", action=True)[:3]:
        action = form["action"]
        # Trova input di testo
        inp = form.find("input", type="text") or form.find("input", type="search") or form.find("input", type="submit") is not None
        # Costruisci URL di ricerca
        if action.startswith("/"):
            search_url = base.rstrip("/") + action
        elif action.startswith("http"):
            search_url = action
        else:
            continue
        # Prova parametri GET comuni
        for param in ["s", "q", "search", "query", "keywords", "cerca"]:
            sep = "&" if "?" in search_url else "?"
            url = f"{search_url}{sep}{param}={farmaco_q}"
            try:
                r = requests.get(url, headers={"User-Agent": USER_AGENT},
                                 timeout=3, verify=False)
                if r.status_code < 400 and len(r.text) > 500:
                    return r
            except:
                pass
    return None


def _cerca_dominio_wrapper(args):
    """Crawler intelligente: trova form + pattern + follow link."""
    dom, slug, q_encoded, parole, aic = args
    dom_clean = dom.replace("www.", "").strip()
    prefix_opts = ["www.", ""] if not dom.startswith("www.") else [""]
    
    for prefix in prefix_opts:
        base = f"https://{prefix}{dom}"
        
        try:
            # 1) Scarica homepage per trovare form di ricerca
            rh = requests.get(base, headers={"User-Agent": USER_AGENT},
                              timeout=3, verify=False)
            if rh.status_code < 400 and len(rh.text) > 500:
                soup = BeautifulSoup(rh.text[:100000], "lxml")
                res = _cerca_form_e_cerca(soup, base, q_encoded)
                if res:
                    txt = res.text[:80000].lower()
                    if any(p in txt for p in parole) or (aic and aic.lower() in txt):
                        # Prova prezzo nella pagina
                        prezzi = list(re.finditer(r"€\s*\d+[.,]\d{2}", txt))
                        for m in prezzi[:3]:
                            v = float(m.group(0).replace("€","").replace(",",".").strip())
                            if 3.0 < v < 2000.0:
                                return {"url": res.url, "titolo": dom, "fonte": "siti.md",
                                        "_prezzo": m.group(0), "_dom": dom}
                        # Segui link prodotto dalla search
                        for a in soup.find_all("a", href=True):
                            ht = a.get("href", "")
                            at = a.get_text(strip=True).lower()
                            if any(p in at for p in parole) and ht not in ["#", "/", ""]:
                                pu = ht if ht.startswith("http") else base.rstrip("/") + ht
                                try:
                                    r2 = requests.get(pu, headers={"User-Agent": USER_AGENT},
                                                      timeout=4, verify=False)
                                    if r2.status_code < 400:
                                        txt2 = r2.text[:80000].lower()
                                        for m in re.finditer(r"€\s*\d+[.,]\d{2}", txt2):
                                            v = float(m.group(0).replace("€","").replace(",",".").strip())
                                            if 3.0 < v < 2000.0:
                                                return {"url": pu, "titolo": dom,
                                                        "fonte": "siti.md",
                                                        "_prezzo": m.group(0), "_dom": dom}
                                except:
                                    pass        
        except:
            pass
        
        # 2) Prova pattern URL predefiniti
        for pat in URL_PATTERNS:
            url = base + pat.format(q=q_encoded, slug=slug)
            try:
                r = requests.get(url, headers={"User-Agent": USER_AGENT},
                                 timeout=3, verify=False, allow_redirects=True)
                if r.status_code >= 400 or len(r.text) < 500:
                    continue
                txt = r.text[:80000].lower()
                if not any(p in txt for p in parole):
                    if not aic or aic.lower() not in txt:
                        continue
                prezzi = list(re.finditer(r"€\s*\d+[.,]\d{2}", txt))
                for m in prezzi[:3]:
                    v = float(m.group(0).replace("€","").replace(",",".").strip())
                    if 3.0 < v < 2000.0:
                        return {"url": url, "titolo": dom, "fonte": "siti.md",
                                "_prezzo": m.group(0), "_dom": dom}
            except:
                pass
    return None


def cerca_siti_web(farmaco, max_siti=20, codice_aic=None):
    """Cerca su tutti i domini siti.md con pattern URL multipli."""
    slug = re.sub(r'[^a-z0-9]+', '-', farmaco.lower()).strip("-")
    q_encoded = urllib.parse.quote(farmaco.lower())
    parole = farmaco.lower().split()[:3]
    if codice_aic:
        parole.append(codice_aic.lower())

    domini = carica_siti_md()
    log(f"\nCrawler su {len(domini)} domini con {len(URL_PATTERNS)} pattern...", "*")
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    n_w = min(100, len(domini))
    
    siti = []
    with ThreadPoolExecutor(max_workers=n_w) as pool:
        futuri = {pool.submit(_cerca_dominio_wrapper,
                  (d, slug, q_encoded, parole, codice_aic)): d for d, _ in domini}
        done = 0
        for f in as_completed(futuri):
            done += 1
            try:
                ris = f.result()
                if ris:
                    siti.append(ris)
            except:
                pass
            if done % 50 == 0:
                log(f"  {done}/{len(domini)} completati, {len(siti)} con prezzo", "~")
            if len(siti) >= max_siti:
                pass  # let workers finish gracefully
    
    if siti:
        siti.sort(key=lambda r: float(r["_prezzo"].replace("€","").replace(",",".")))
    log(f"  {len(domini)} domini, {len(siti)} con prezzo trovato", "+")

    # DuckDuckGo fallback
    if len(siti) < max_siti:
        from duckduckgo_search import DDGS
        url_visti = {s["_dom"] for s in siti}
        log(f"  DuckDuckGo fallback...", "~")
        parole = farmaco.lower().split()[:2]
        qs = [
            f'"{farmaco}" prezzo',
            f'"{farmaco}" farmacia online',
            f'"{farmaco}" comprare',
            f'{" ".join(parole)} trovaprezzi',
            f'{" ".join(parole)} farmacia prezzo',
            f'site:amazon.it "{farmaco}"',
        ]
        for q in qs:
            try:
                with DDGS() as ddgs:
                    for r_dict in ddgs.text(q, region="it-it", max_results=5):
                        url = r_dict.get("href", "")
                        dom = estrai_dominio(url)
                        if not url or dom in url_visti:
                            continue
                        url_visti.add(dom)
                        siti.append({"url": url, "titolo": (r_dict.get("title","") or "")[:80],
                                    "fonte": "web"})
            except:
                pass
            if len(siti) >= max_siti:
                break

    log(f"  Totale {len(siti)} siti", "+")
    return siti[:max_siti]


PRICE_MIN = 3.0
PRICE_MAX = 2000.0


def cerca_prezzo_sito(url, farmaco, tipo="web", aic=None):
    """Cerca il prezzo del farmaco in una pagina web."""
    parole = farmaco.lower().split()[:3]
    timeout = 4 if tipo == "farmacia" else 10

    def _valido(v):
        return PRICE_MIN < v < PRICE_MAX

    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT},
                         timeout=timeout, verify=False, allow_redirects=True)
        if r.status_code >= 400 or len(r.text) < 500:
            return None
    except:
        return None

    if tipo == "farmacia":
        testo_rapido = r.text[:20000].lower()
        if not any(p in testo_rapido for p in parole[:2]):
            return None

    html = r.text
    prezzi_trovati = []

    # 1) Prezzo da meta tag (product:price:amount)
    for m in re.finditer(r'<meta[^>]*property="(?:product:)?price:amount"[^>]*content="([0-9.,]+)"', html, re.I):
        prezzi_trovati.append(float(m.group(1).replace(",", ".")))

    # 2) Prezzo da JSON-LD (schema.org)
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL | re.I):
        try:
            data = json.loads(m.group(1))
            if isinstance(data, dict):
                offers = data.get("offers", {})
                if isinstance(offers, dict):
                    for k in ["price", "lowPrice", "highPrice"]:
                        p = offers.get(k)
                        if p:
                            prezzi_trovati.append(float(p))
                elif isinstance(offers, list):
                    for off in offers:
                        if isinstance(off, dict) and off.get("price"):
                            prezzi_trovati.append(float(off["price"]))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        offers = item.get("offers", {})
                        if isinstance(offers, dict) and offers.get("price"):
                            prezzi_trovati.append(float(offers["price"]))
        except:
            pass

    # 3) Prezzo da variabili JS (product_price, prezzovend, ecc)
    for m in re.finditer(r"(?:product_price|prezzovend|price|prezzo|costo|prezzofinale)\s*(?::|=)\s*['\"]?\s*(\d+[.,]\d{2})", html[:80000], re.I):
        try:
            prezzi_trovati.append(float(m.group(1).replace(",", ".")))
        except:
            pass

    # 4) Prezzo da HTML standard
    soup = BeautifulSoup(html, "lxml")
    testo = soup.get_text(separator=" ", strip=True)
    esc_name = re.escape(farmaco)

    # Pattern 4a: trova prezzi con € nel contesto del nome farmaco
    for match in re.finditer(r'([^.]{0,80}?' + esc_name + r'[^.]{0,80}\.?)', testo, re.IGNORECASE):
        ctx = match.group(1)
        for p in re.findall(r'€\s*(\d+[.,]\d{2})', ctx):
            v = float(p.replace(",", "."))
            if _valido(v):
                prezzi_trovati.append(v)

    # Pattern 4b: trova prezzi con "prezzo" o "listino" vicino al farmaco
    for match in re.finditer(r'(?:prezzo|listino|price|sconto|costo|eur)\s*[:]?\s*€?\s*(\d+[.,]\d{2})(?!\s*%)', testo[:40000], re.I):
        v = float(match.group(1).replace(",", "."))
        if _valido(v):
            prezzi_trovati.append(v)

    for el in soup.select("[class*=\"prezzo\"], [class*=\"price\"], [class*=\"costo\"], [id*=\"prezzo\"]"):
        txt = el.get_text(strip=True)
        if not txt or '%' in txt:
            continue
        has_farmaco = any(p in txt.lower() for p in parole)
        for p in re.findall(r'€?\s*(\d+[.,]\d{2})', txt):
            v = float(p.replace(",", "."))
            if 1.0 < v < 5000.0 and (has_farmaco or len(prezzi_trovati) < 5):
                prezzi_trovati.append(v)

    if not prezzi_trovati:
        return None

    # Fallback: se aic presente e nessun prezzo, cerca AIC + prezzo nel testo
    if not prezzi_trovati and aic:
        for m in re.finditer(r'aic[^<]{0,40}?(\d{6,})', testo[:80000], re.I):
            near = testo[max(0, m.end()-20):min(len(testo), m.end()+200)]
            for p in re.findall(r'€\s*(\d+[.,]\d{2})', near):
                v = float(p.replace(",", "."))
                if _valido(v):
                    prezzi_trovati.append(v)

    prezzi_trovati = [p for p in prezzi_trovati if _valido(p)]
    if not prezzi_trovati:
        return None

    return {
        "url": url,
        "farmaco": farmaco,
        "prezzo": min(prezzi_trovati),
        "prezzo_minimo": min(prezzi_trovati),
        "prezzo_max": max(prezzi_trovati),
        "num_prezzi": len(prezzi_trovati),
    }


# ─── FASE 4: Google Shopping ────────────────────────

def cerca_farmacia_online(farmaco, dominio, search_path):
    """Cerca farmaco su una farmacia online specifica."""
    url = f"https://www.{dominio}{search_path}{farmaco.replace(' ', '+')}"
    parole = farmaco.lower().split()[:2]
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT},
                         timeout=5, verify=False, allow_redirects=True)
        if r.status_code < 400 and len(r.text) > 500:
            testo = r.text[:30000].lower()
            if any(p in testo for p in parole) and ("€" in testo or "prezzo" in testo):
                return (url, dominio)
    except:
        pass
    return None


def cerca_google_shopping(farmaco, api_key):
    """Cerca prezzo su Google Shopping via SearchAPI.io."""
    if not api_key:
        return None
    try:
        r = requests.get("https://www.searchapi.io/api/v1/search", params={
            "engine": "google_shopping",
            "q": f"{farmaco}",
            "gl": "it",
            "hl": "it",
            "api_key": api_key,
        }, timeout=15)
        if r.status_code == 200:
            data = r.json()
            shopping = data.get("shopping_results", [])
            return [{
                "venditore": s.get("seller", s.get("title", "?")),
                "prezzo": s.get("extracted_price", ""),
                "link": s.get("link", ""),
            } for s in shopping[:10]]
    except:
        pass
    return None


# ─── MAIN ──────────────────────────────────────────

def main():
    load_env()
    api_key = os.environ.get("SEARCHAPI_KEY", "")

    parser = argparse.ArgumentParser(description="Compara-offerte v3 — Trova il miglior prezzo per un farmaco")
    parser.add_argument("farmaco", nargs="?", help="Nome del farmaco (es. 'Tachipirina 1000')")
    parser.add_argument("--report", action="store_true", help="Genera report HTML")
    parser.add_argument("--solo-web", action="store_true", help="Solo ricerca web, salta farmacie")
    parser.add_argument("--aggiorna-siti", action="store_true", help="Solo verifica siti farmacie, senza ricerca")
    parser.add_argument("--no-shopping", action="store_true", help="Salta Google Shopping")
    parser.add_argument("--max-siti", type=int, default=20, help="Max siti da analizzare")
    parser.add_argument("--citta", type=str, help="Filtra farmacie per città (es. Vittoria, Acate)")
    parser.add_argument("--aic", type=str, help="Codice AIC (ministeriale) per ricerca piu precisa")
    args = parser.parse_args()

    farmaco = args.farmaco
    risultati_report = {
        "timestamp": datetime.now().isoformat(),
        "farmaco": farmaco,
        "farmacie": [],
        "web": [],
        "shopping": [],
    }

    # ─── MODALITÀ: aggiorna-siti ───
    if args.aggiorna_siti:
        log(f"{'='*55}")
        log("VERIFICA SITI FARMACIE")
        log(f"{'='*55}")
        farmacie = carica_farmacie()
        if not farmacie:
            return
        up, down = verifica_siti(farmacie)
        print(f"\n{'─'*55}")
        print(f"  ✅ Siti attivi: {len(up)}")
        print(f"  ❌ Siti down:   {len(down)}")
        if down:
            print(f"\n  Siti non raggiungibili:")
            for d in down:
                print(f"    • {d['nome']}: {d['url']} (HTTP {d['status']})")
        print(f"{'─'*55}")
        return

    if not farmaco:
        parser.print_help()
        return

    # ─── FLUSSO PRINCIPALE ───
    log(f"{'='*55}")
    log(f"COMPARA-OFFERTE v{VERSION}")
    log(f"Farmaco: {farmaco}")
    log(f"{'='*55}")

    # Siti da analizzare
    siti_da_analizzare = []
    domini_visti = set()

    # 1. Farmacie da Farmascopri
    if not args.solo_web:
        farmacie = carica_farmacie()
        # Filtra per città se specificato
        if args.citta and farmacie:
            citta_filtro = args.citta.lower()
            filt = [f for f in farmacie if f.get("comune", "").lower() == citta_filtro]
            log(f"Filtrate {len(filt)}/{len(farmacie)} farmacie per '{args.citta}'", "~")
            farmacie = filt
        if farmacie:
            up, down = verifica_siti(farmacie)
            if up:
                log(f"Aggiungo {len(up)} siti farmacie...", "+")
                for f in up:
                    dom = estrai_dominio(f["sito"])
                    if dom not in domini_visti:
                        domini_visti.add(dom)
                        siti_da_analizzare.append({
                            "url": f["sito"],
                            "nome": f["nome"],
                            "tipo": "farmacia",
                        })

    # 2. Ricerca web (finder-siti integrato)
    siti_web = cerca_siti_web(farmaco, args.max_siti, codice_aic=args.aic)
    for s in siti_web:
        dom = estrai_dominio(s["url"])
        if dom not in domini_visti:
            domini_visti.add(dom)
            siti_da_analizzare.append({
                "url": s["url"],
                "nome": s.get("titolo", dom)[:60],
                "tipo": "web",
            })

    if not siti_da_analizzare:
        log("Nessun sito da analizzare!", "!")
        return

    log(f"\n{'─'*55}")
    log(f"ANALISI PREZZI su {len(siti_da_analizzare)} siti")
    log(f"{'─'*55}")

    # 3. Cerca prezzo su ogni sito (parallelo)
    risultati_prezzi = []
    from concurrent.futures import ThreadPoolExecutor, as_completed

    log(f"Analisi {len(siti_da_analizzare)} siti in parallelo...", "*")
    with ThreadPoolExecutor(max_workers=30) as pool:
        futuri = {}
        for sito in siti_da_analizzare:
            f = pool.submit(cerca_prezzo_sito, sito["url"], farmaco, sito.get("tipo", "web"), args.aic)
            futuri[f] = sito

        for f in as_completed(futuri):
            sito = futuri[f]
            try:
                result = f.result()
                if result:
                    prezzo = result["prezzo_minimo"]
                    risultati_prezzi.append(result)
                    risultati_report["farmacie" if sito["tipo"] == "farmacia" else "web"].append(result)
                    log(f"  ✓ {sito['nome'][:40]:40s} €{prezzo:.2f}", "+")
                else:
                    log(f"  . {sito['nome'][:40]:40s} (vuoto)", "~")
            except Exception as ex:
                log(f"  ✗ {sito['nome'][:40]:40s} {str(ex)[:30]}", "-")

    # 4. Google Shopping
    prezzi_shopping = None
    if not args.no_shopping:
        log(f"\nGoogle Shopping...", "*")
        prezzi_shopping = cerca_google_shopping(farmaco, api_key)
        if prezzi_shopping:
            risultati_report["shopping"] = prezzi_shopping
        else:
            log("  Nessun risultato o API key mancante", "-")

    # ─── OUTPUT A SCHERMO ───
    print(f"\n{'═'*55}")
    print(f"  RISULTATI PER: {farmaco}")
    print(f"{'═'*55}")

    if risultati_prezzi:
        print(f"\n  🏪 Prezzi trovati sui siti:")
        ordinati = sorted(risultati_prezzi, key=lambda r: r["prezzo_minimo"])
        for r in ordinati:
            dom = estrai_dominio(r["url"])
            print(f"    €{r['prezzo_minimo']:>6.2f}  {dom}")
    else:
        print(f"\n  ❌ Nessun prezzo trovato sui siti analizzati")

    if prezzi_shopping:
        print(f"\n  🛒 Google Shopping:")
        for s in prezzi_shopping[:5]:
            p = s.get("prezzo", "")
            v = s.get("venditore", "?")
            print(f"    €{p:>6}  {v[:40]}" if p else f"    {'?':>6}  {v[:40]}")

    # Prezzo migliore
    if risultati_prezzi:
        miglior_prezzo = ordinati[0]["prezzo_minimo"]
        miglior_sito = ordinati[0]["url"]
        print(f"\n  {'─'*55}")
        print(f"  🏆 MIGLIOR PREZZO: €{miglior_prezzo:.2f}")
        print(f"     {miglior_sito}")

        if prezzi_shopping:
            prezzi_shop = [float(s["prezzo"]) for s in prezzi_shopping if s.get("prezzo")]
            if prezzi_shop:
                min_shop = min(prezzi_shop)
                if min_shop < miglior_prezzo:
                    print(f"  ⚡ Google Shopping ha prezzi piu bassi: da €{min_shop:.2f}")

    # Statistiche
    tot_farmacie = len([r for r in risultati_prezzi if any(
        s["tipo"] == "farmacia" for s in siti_da_analizzare if s["url"] == r["url"])])
    print(f"\n  📊 Hotel: {len(risultati_prezzi)} siti con prezzo trovato"
          f" su {len(siti_da_analizzare)} analizzati")
    print(f"{'═'*55}")

    # ─── REPORT HTML (solo su richiesta) ───
    if args.report:
        output_dir = f"report_{farmaco.lower().replace(' ', '_')[:30]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)

        html = genera_html(risultati_report, farmaco)
        path = os.path.join(output_dir, "report.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        with open(os.path.join(output_dir, "report.json"), "w") as f:
            json.dump(risultati_report, f, indent=2, ensure_ascii=False)

        log(f"Report: {path}", "+")


def genera_html(data, farmaco):
    """Genera report HTML."""
    prezzi = data["farmacie"] + data["web"]
    prezzi_ord = sorted(prezzi, key=lambda r: r["prezzo_minimo"])

    html = f"""<!DOCTYPE html><html lang="it"><head>
<meta charset="UTF-8"><title>Compara-offerte — {farmaco}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        background:#0f0f1a;color:#e0e0e0;line-height:1.6;padding:20px;max-width:1000px;margin:auto}}
  h1{{color:#fff;margin:20px 0 5px}}
  h2{{color:#7c8aff;margin:20px 0 10px;padding-bottom:5px;border-bottom:2px solid #2a2a40}}
  .price{{color:#5f0;font-weight:bold}}
  .url{{color:#7c8aff;word-break:break-all;font-size:0.85rem}}
  .result{{background:#1a1a2e;border-radius:8px;padding:12px;margin:8px 0;border:1px solid #2a2a40}}
  .win{{background:#0a2a0a;border:1px solid #5f0}}
  table{{width:100%;border-collapse:collapse;margin:10px 0}}
  th,td{{padding:8px 12px;border-bottom:1px solid #2a2a40;text-align:left}}
  th{{color:#7c8aff}}
  .sh{{background:#1a1a2e;border-left:3px solid #ffd700;padding:8px 12px;margin:5px 0}}
  .meta{{color:#888;font-size:0.85rem}}
</style></head><body>
<h1>🛒 {farmaco}</h1>
<p class="meta">{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
"""
    if prezzi_ord:
        html += "<h2>🏆 Prezzi trovati</h2>\n"
        for r in prezzi_ord:
            w = " win" if r == prezzi_ord[0] else ""
            dom = estrai_dominio(r["url"])
            html += f'<div class="result{w}"><strong>€{r["prezzo_minimo"]:.2f}</strong>'
            html += f' <span class="url">{dom}</span>'
            if r.get("prezzo_max") and r["prezzo_max"] != r["prezzo_minimo"]:
                html += f'<br><small>da €{r["prezzo_minimo"]:.2f} a €{r["prezzo_max"]:.2f}</small>'
            html += "</div>\n"

    if data["shopping"]:
        html += "<h2>🛒 Google Shopping</h2>\n"
        for s in data["shopping"][:5]:
            html += f'<div class="sh"><strong>€{s.get("prezzo","?")}</strong>'
            html += f' — {s.get("venditore","?")[:40]}</div>\n'

    html += "</body></html>"
    return html


if __name__ == "__main__":
    main()
