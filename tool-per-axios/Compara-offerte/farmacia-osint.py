#!/usr/bin/env python3
"""
Farmacia OSINT Tool v1.0
========================
OSINT automation tool for Italian pharmacies.
Scopre: dati dominio, presenza web, profili social, email, offerte attive.

Usage:
  python3 farmacia-osint.py "Nome Farmacia" [--city Città] [--domain dominio.it] [--output DIR]
  python3 farmacia-osint.py "Farmacia Calì Mancuso" --city Vittoria --domain farmaciacalimancuso.it
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

# Optional imports
try:
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    print("[!] Install requests e beautifulsoup4: pip install requests beautifulsoup4 lxml")
    sys.exit(1)

VERSION = "1.0.0"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQ_TIMEOUT = (12, 15)  # (connect, read) timeout HTTP

# ──────────────────────────────────────────────
#  UTILITY
# ──────────────────────────────────────────────

def log(msg, level="+"):
    """Stampa log colorato."""
    colors = {"+": "\033[92m", "-": "\033[93m", "!": "\033[91m", "*": "\033[94m"}
    c = colors.get(level, "\033[0m")
    print(f"  {c}[{level}]\033[0m {msg}")

def run_cmd(cmd, timeout=30):
    """Esegue un comando shell e restituisce (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", f"TIMEOUT ({timeout}s)", -1
    except Exception as e:
        return "", str(e), -1

def save_json(path, data):
    """Salva dati JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log(f"JSON salvato: {path}")

def append_report(report_path, section, content):
    """Appende una sezione al report di testo."""
    with open(report_path, "a", encoding="utf-8") as f:
        f.write(f"\n{'─'*70}\n")
        f.write(f"  {section}\n")
        f.write(f"{'─'*70}\n")
        f.write(content)
        f.write("\n")

# ──────────────────────────────────────────────
#  FASE 1 — RICOGNIZIONE DOMINIO
# ──────────────────────────────────────────────

def phase1_domain(name, domain, output_dir):
    """Whois, DNS, subdomains, tech detection."""
    log(f"── FASE 1: Ricognizione dominio ──", "*")
    results = {"domain": domain, "whois": {}, "dns": {}, "subdomains": [], "tech": {}}
    report_path = os.path.join(output_dir, "report.txt")

    # 1.1 WHOIS
    log(f"Whois {domain}...")
    out, err, rc = run_cmd(f"whois {domain}")
    if out:
        whois_data = {}
        for line in out.split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                whois_data[k.strip()] = v.strip()
        results["whois"] = whois_data
        append_report(report_path, "WHOIS", out[:2000])

    # 1.2 DNS records
    log(f"DNS records {domain}...")
    dns_data = {}
    for rec_type in ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]:
        out, err, rc = run_cmd(f"dig +short {rec_type} {domain}")
        if out:
            dns_data[rec_type] = out.split("\n")
    results["dns"] = dns_data
    append_report(report_path, "DNS RECORDS", json.dumps(dns_data, indent=2))

    # 1.3 Subdomains via fierce (veloce)
    log(f"Subdomain scan (fierce)...")
    out, err, rc = run_cmd(f"timeout 15 fierce --domain {domain} 2>/dev/null | grep -i 'Found\\|Subdomain\\|www\\|mail\\|ftp' | head -20", timeout=25)
    if out:
        results["subdomains_fierce"] = out.split("\n")

    # 1.4 Amass (subdomains, veloce)
    log(f"Subdomain enum via amass...")
    out, err, rc = run_cmd(f"timeout 15 amass enum -d {domain} -timeout 2 2>/dev/null | head -20", timeout=30)
    if out:
        subs = [s.strip() for s in out.split("\n") if s.strip() and "." in s]
        results["subdomains_amass"] = subs

    # 1.5 Tech detection via httpx
    log(f"Tech detection {domain}...")
    out, err, rc = run_cmd(f"httpx -u https://www.{domain} -tech-detect -json 2>/dev/null", timeout=15)
    if out:
        try:
            results["tech"] = json.loads(out)
        except json.JSONDecodeError:
            results["tech_raw"] = out
    else:
        # fallback su http
        out, err, rc = run_cmd(f"httpx -u http://{domain} -tech-detect -json 2>/dev/null", timeout=15)
        if out:
            try:
                results["tech"] = json.loads(out)
            except:
                results["tech_raw"] = out

    save_json(os.path.join(output_dir, "phase1_domain.json"), results)
    return results


# ──────────────────────────────────────────────
#  FASE 2 — PRESENZA WEB
# ──────────────────────────────────────────────

def phase2_web(name, domain, output_dir, variants):
    """Web scraping, email discovery, URL discovery."""
    log(f"── FASE 2: Presenza Web ──", "*")
    results = {"pages": {}, "emails": [], "urls_discovered": [], "social_links": []}
    report_path = os.path.join(output_dir, "report.txt")

    # 2.1 Scraping pagine principali
    urls_to_check = [
        f"https://www.{domain}",
        f"https://www.{domain}/offerte.aspx",
        f"https://www.{domain}/offerte",
        f"https://www.{domain}/promozioni",
        f"https://{domain}",
        f"http://www.{domain}",
    ]
    # Aggiungi solo 2 varianti extra
    for v in variants[:3]:
        if v != domain and f"https://{v}" not in urls_to_check:
            urls_to_check.append(f"https://{v}")

    pages_data = {}
    for url in urls_to_check[:8]:  # max 8
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, verify=False, timeout=REQ_TIMEOUT, allow_redirects=True)
            soup = BeautifulSoup(r.text, "lxml")
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            meta_desc = ""
            m = soup.find("meta", attrs={"name": "description"})
            if m and m.get("content"):
                meta_desc = m["content"]

            # Estrai link
            links = []
            for a in soup.find_all("a", href=True):
                h = a["href"]
                if h.startswith("http") or h.startswith("/"):
                    links.append(h)

            # Cerca offerte
            offers_raw = []
            offer_keywords = ["offert", "sconto", "prezzo", "€", "eur", "promo"]
            for el in soup.find_all(["div", "span", "p", "h1", "h2", "h3", "h4", "a", "li"]):
                txt = el.get_text(strip=True)
                if any(kw in txt.lower() for kw in offer_keywords):
                    offers_raw.append(txt[:200])

            pages_data[url] = {
                "status": r.status_code,
                "title": title,
                "meta_description": meta_desc,
                "content_length": len(r.text),
                "offers_raw": offers_raw[:20],
                "links": links[:50],
            }
            log(f"  [{r.status_code}] {url}")
        except Exception as e:
            log(f"  [!] {url} → {str(e)[:60]}", "!")
            pages_data[url] = {"error": str(e)[:200]}

    results["pages"] = pages_data

    # 2.2 Email extraction da pagine
    emails_found = set()
    for url, data in pages_data.items():
        if "error" not in data:
            try:
                r = requests.get(url, headers={"User-Agent": USER_AGENT}, verify=False, timeout=REQ_TIMEOUT)
                found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
                emails_found.update(found)
            except:
                pass
    results["emails"] = sorted(emails_found)
    if emails_found:
        append_report(report_path, "EMAIL TROVATE", "\n".join(emails_found))

    # 2.3 theHarvester (se disponibile)
    log(f"theHarvester su {domain}...")
    out, err, rc = run_cmd(f"theHarvester -d {domain} -b google 2>/dev/null | grep -A999 'Hosts found\\|Emails found' | head -50", timeout=30)
    if out:
        results["theharvester"] = out.split("\n")
        append_report(report_path, "theHarvester OUTPUT", out)

    # 2.4 Social links da scraping
    social_patterns = [
        (r'instagram\.com/([a-zA-Z0-9_.]+)', "instagram"),
        (r'facebook\.com/([a-zA-Z0-9_.]+)', "facebook"),
        (r'twitter\.com/([a-zA-Z0-9_.]+)', "twitter"),
        (r'linkedin\.com/([a-zA-Z0-9_.]+)', "linkedin"),
        (r'youtube\.com/(@?[a-zA-Z0-9_.]+)', "youtube"),
        (r'tiktok\.com/(@?[a-zA-Z0-9_.]+)', "tiktok"),
        (r'wa\.me/(\d+)', "whatsapp"),
        (r'whatsapp\.com/(\d+)', "whatsapp"),
    ]
    social_links = {}
    for url in urls_to_check[:5]:
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, verify=False, timeout=REQ_TIMEOUT)
            for pattern, platform in social_patterns:
                matches = re.findall(pattern, r.text)
                for m in matches:
                    full_url = ""
                    if platform == "instagram":
                        full_url = f"https://instagram.com/{m}"
                    elif platform == "facebook":
                        full_url = f"https://facebook.com/{m}"
                    elif platform == "whatsapp":
                        full_url = f"https://wa.me/{m}"
                    else:
                        full_url = f"https://{platform}.com/{m}"
                    if platform not in social_links:
                        social_links[platform] = []
                    if full_url not in social_links[platform]:
                        social_links[platform].append(full_url)
        except:
            pass
    results["social_links"] = social_links

    # 2.5 Ofacebook (generazione URL Facebook)
    name_slug = re.sub(r'[^a-zA-Z0-9]', '', name.lower().replace(" ", ""))
    fb_variants = [
        f"https://www.facebook.com/{name_slug}",
        f"https://www.facebook.com/farmacia.{name_slug}",
        f"https://www.facebook.com/{name_slug}.farmacia",
        f"https://www.facebook.com/{domain.replace('.it','').replace('.','')}",
        f"https://www.facebook.com/people/{name.replace(' ','-')}",
    ]
    results["facebook_variants"] = fb_variants

    save_json(os.path.join(output_dir, "phase2_web.json"), results)
    return results


# ──────────────────────────────────────────────
#  FASE 3 — SOCIAL & EMAIL OSINT
# ──────────────────────────────────────────────

def phase3_social(name, domain, emails, output_dir, social_links=None):
    """Maigret, holehe, social presence."""
    log(f"── FASE 3: Social & Email OSINT ──", "*")
    results = {"maigret": {}, "holehe": {}}
    report_path = os.path.join(output_dir, "report.txt")

    # Username variants generati dal nome farmacia
    name_clean = re.sub(r'[^a-zA-Z0-9]', '', name.lower().replace(" ", ""))
    # Rimuovi parole comuni
    for w in ["farmacia", "farmacie", "cali", "mancuso", "di", "del", "della", "san", "santa", "nuova"]:
        name_clean = name_clean.replace(w, "")
    name_clean = name_clean.strip()[:15] or re.sub(r'[^a-zA-Z0-9]', '', name.lower().replace(" ", ""))[:15]
    
    name_short = name_clean[:10]
    name_under = re.sub(r'[^a-zA-Z0-9]', '_', name.lower().replace(" ", ""))
    
    username_variants = [
        name_clean,
        name_short,
        f"farmacia{name_clean}",
        f"farmacia.{name_clean}",
        f"{name_clean}.farmacia",
        name_under,
        re.sub(r'[^a-zA-Z0-9]', '', name.lower().replace(" ", "")),
    ]
    
    # Aggiungi handle estratti dai social link
    if social_links:
        for platform, links in social_links.items():
            for link in links:
                # Estrai username da URL social
                parts = link.rstrip('/').split('/')
                if parts:
                    handle = parts[-1].split('?')[0]
                    if handle and handle not in username_variants:
                        username_variants.append(handle)
                        log(f"  Aggiunto handle da {platform}: {handle}")

    # 3.1 Maigret
    log(f"Maigret username scan...")
    for username in username_variants[:3]:
        log(f"  Checking username: {username}")
        out, err, rc = run_cmd(f"maigret {username} --json --timeout 10 2>/dev/null", timeout=60)
        if out:
            try:
                data = json.loads(out)
                found_sites = {k: v for k, v in data.get("sites", {}).items() if v.get("status") and v["status"].get("ok")}
                if found_sites:
                    results["maigret"][username] = found_sites
                    for site, info in found_sites.items():
                        username_found = info.get("username", username)
                        url_user = info.get("url_user", "")
                        log(f"    ✓ {site}: {url_user}")
                        append_report(report_path, f"MAIGRET - {username} su {site}", f"{url_user}")
            except json.JSONDecodeError:
                pass

    # 3.2 Holehe (email check su servizi)
    log(f"Holehe email check...")
    for email in emails[:3]:  # max 3 email
        log(f"  Checking email: {email}")
        out, err, rc = run_cmd(f"holehe {email} 2>/dev/null", timeout=45)
        if out:
            # Pulisci output: estrai solo risultati utili
            parsed = parse_holehe_output(out)
            results["holehe"][email] = parsed
            if parsed.get("email_used", []):
                append_report(report_path, f"HOLEHE - {email} - EMAIL USATA SU",
                    "\n".join(parsed["email_used"]))
            if parsed.get("email_not_used", []):
                append_report(report_path, f"HOLEHE - {email} - NON TROVATA SU",
                    "\n".join(parsed["email_not_used"][:20]))
            log(f"    {len(parsed.get('email_used',[]))} servizi confermati, "
                 f"{len(parsed.get('email_not_used',[]))} non trovata")

    save_json(os.path.join(output_dir, "phase3_social.json"), results)
    return results


def parse_holehe_output(output):
    """Parsa output holehe estraendo risultati strutturati."""
    parsed = {"raw": output, "email_used": [], "email_not_used": [], "rate_limited": []}
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("[+]"):
            service = line.split("[-]")[0] if "[-]" in line else line[3:].strip()
            if service and service not in parsed["email_used"]:
                parsed["email_used"].append(service)
        elif line.startswith("[-]"):
            service = line[3:].strip()
            if service and service not in parsed["email_not_used"]:
                parsed["email_not_used"].append(service)
        elif line.startswith("[x]"):
            service = line[3:].strip()
            if service and service not in parsed["rate_limited"]:
                parsed["rate_limited"].append(service)
    return parsed

    save_json(os.path.join(output_dir, "phase3_social.json"), results)
    return results


# ──────────────────────────────────────────────
#  FASE 4 — OFFERTE & E-COMMERCE
# ──────────────────────────────────────────────

def phase4_offers(name, domain, output_dir, pages_from_phase2=None):
    """Ricerca offerte su sito, e-commerce, motori di ricerca."""
    log(f"── FASE 4: Offerte & E-commerce ──", "*")
    name_clean_local = re.sub(r'[^a-zA-Z0-9]', '', name.lower().replace(" ", ""))
    results = {
        "site_offers": [],
        "apoteca_natura": [],
        "google_search_offers": [],
        "ecommerce_platforms": [],
    }
    report_path = os.path.join(output_dir, "report.txt")

    # Se abbiamo offers_raw dalle pagine phase2, le includiamo
    if pages_from_phase2:
        log(f"Usando {len(pages_from_phase2)} pagine da fase 2 per estrazione offerte...")
    
    # 4.1 Estrai offerte dai dati phase2 (offers_raw) se disponibili
    # (le pagine sono già state scaricate in fase 2)
    
    # 4.1 Funzione estrazione offerte da HTML
    def extract_offers_from_html(html_text, source_url):
        """Estrae prodotti/offerte da HTML."""
        offers = []
        soup = BeautifulSoup(html_text, "lxml")
        
        # Pattern 1: Elementi con struttura tipica offerte Apoteca Natura
        # Nome prodotto in div#NomeProdotto o h4
        for prod_el in soup.select('[id*="NomeProdotto"], .h4, h4, h3'):
            txt = prod_el.get_text(strip=True)
            if len(txt) > 10 and re.search(r'[A-Z]{3,}', txt):
                # Cerca prezzi vicini
                parent = prod_el.parent
                if not parent:
                    continue
                parent_html = str(parent)
                # Cerca sconto: - € X oppure -€ X
                sconto_m = re.search(r'-\s*€\s*(\d+(?:[.,]\d{1,2})?)', parent_html)
                # Cerca prezzo barrato: del>€ X,XX</del>
                vecchio_m = re.search(r'<del[^>]*>\s*€\s*(\d+(?:[.,]\d{1,2})?)\s*<', parent_html)
                # Cerca prezzo finale
                finale_m = re.search(r'prezzo-finale[^>]*>\s*€\s*(\d+(?:[.,]\d{1,2})?)', parent_html)
                
                offer = {"product": txt, "source": source_url}
                if sconto_m:
                    offer["sconto"] = f"-€{sconto_m.group(1)}"
                if vecchio_m:
                    offer["prezzo_vecchio"] = vecchio_m.group(1).replace(",", ".")
                if finale_m:
                    offer["prezzo_nuovo"] = finale_m.group(1).replace(",", ".")
                if "prezzo_nuovo" in offer or "prezzo_vecchio" in offer:
                    offers.append(offer)
        
        # Pattern 2: Regex fallback su tutto il testo
        if not offers:
            # Cerca "- €X ... € Y,YY ... € Z,ZZ" (sconto + vecchio + nuovo)
            sconti = re.findall(r'-\s*€\s*(\d+(?:[.,]\d{1,2})?).*?€\s*(\d+(?:[.,]\d{1,2})?).*?€\s*(\d+(?:[.,]\d{1,2})?)', html_text, re.DOTALL)
            for sconto, pv, pn in sconti:
                offers.append({"sconto": f"-€{sconto}", "prezzo_vecchio": pv.replace(",","."),
                              "prezzo_nuovo": pn.replace(",","."), "source": source_url})
        return offers

    # 4.2 Scraping pagine offerte note
    offer_pages = [
        f"https://www.{domain}/offerte.aspx",
        f"https://www.{domain}/offerte",
        f"https://www.{domain}/promozioni",
        f"https://www.{domain}/promozioni.aspx",
        f"https://www.{domain}/sconti",
        f"https://www.{domain}/prodotti-in-offerta",
    ]
    for url in offer_pages:
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, verify=False, timeout=REQ_TIMEOUT, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 500:
                offers = extract_offers_from_html(r.text, url)
                if offers:
                    results["site_offers"].extend(offers)
                    log(f"  [{r.status_code}] {url} → {len(offers)} offerte")
                    lines = []
                    for o in offers[:20]:
                        prod = o.get('product', '?')
                        pv = o.get('prezzo_vecchio', '')
                        pn = o.get('prezzo_nuovo', '')
                        sc = o.get('sconto', '')
                        if pn:
                            line = f"  {prod}: €{pv} → €{pn}" if pv else f"  {prod}: €{pn}"
                            if sc:
                                line += f" ({sc})"
                        else:
                            line = f"  {prod}: €{o.get('price', '?')}"
                        lines.append(line)
                    append_report(report_path, f"OFFERTE - {url}", "\n".join(lines))
        except Exception as e:
            log(f"  [!] {url} → {str(e)[:50]}", "!")

    # 4.2 Ricerca e-commerce Apoteca Natura
    apoteca_variants = [
        f"https://farmacia{name_clean_local}.apotecanatura.it",
        f"https://{name_clean_local}.apotecanatura.it",
    ]
    # Prova anche varianti dal dominio
    domain_base = domain.replace("www.", "").replace(".it", "").replace(".com", "")
    apoteca_variants.append(f"https://farmacia{domain_base}.apotecanatura.it")
    apoteca_variants.append(f"https://{domain_base}.apotecanatura.it")

    for url in apoteca_variants:
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, verify=False, timeout=REQ_TIMEOUT)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "lxml")
                results["apoteca_natura"].append({"url": url, "reachable": True})
                log(f"  ✓ Apoteca Natura: {url}")

                # Cerca offerte nella pagina
                offers_raw = []
                offer_keywords = ["offert", "sconto", "%", "promo", "€"]
                for el in soup.find_all(["div", "span", "p", "h3", "a"]):
                    txt = el.get_text(strip=True)
                    if any(kw in txt.lower() for kw in offer_keywords) and re.search(r'\d+[.,]\d{2}', txt):
                        offers_raw.append(txt[:200])
                if offers_raw:
                    results["apoteca_natura"][-1]["offers_raw"] = offers_raw[:20]
                    append_report(report_path, f"OFFERTE APOTECA - {url}",
                        "\n".join(offers_raw[:20]))
        except:
            pass

    # 4.3 Ricerca Google (web search) per offerte
    # Nota: richiede API, usiamo fallback via URLs noti
    results["offers_summary"] = {
        "total_offers_found": len(results["site_offers"]),
        "apoteca_reachable": len(results["apoteca_natura"]) > 0,
        "note": "Per offerte social (FB/IG) serve autenticazione. Per Google Shopping servono API."
    }

    # 4.4 E-commerce platform detection
    platforms_found = []
    if any(a.get("reachable") for a in results.get("apoteca_natura", [])):
        platforms_found.append({"platform": "Apoteca Natura (Aboca)", "type": "e-commerce", "free": True})

    # Controlla PharmaFulcri nei dati phase2
    if pages_from_phase2:
        for url in pages_from_phase2:
            if "pharmafulcri" in url.lower():
                platforms_found.append({"platform": "PharmaFulcri", "type": "sito_istituzionale", "free": True, "url": url})

    results["ecommerce_platforms"] = platforms_found

    save_json(os.path.join(output_dir, "phase4_offers.json"), results)
    return results


# ──────────────────────────────────────────────
#  FASE 5 — GOOGLE SHOPING PRICE COMPARISON
# ──────────────────────────────────────────────

def phase5_shopping(offers, api_key, output_dir):
    """Confronta prezzi offerte su Google Shopping via SearchAPI.io."""
    log(f"── FASE 5: Google Shopping Price Comparison ──", "*")
    results = {"comparisons": [], "api": "searchapi.io", "requests_used": 0}
    report_path = os.path.join(output_dir, "report.txt")

    if not api_key:
        log(f"Nessuna API key per Google Shopping. Usa --shopping-api-key", "-")
        results["error"] = "No API key provided"
        return results

    if not offers:
        log(f"Nessuna offerta da confrontare", "-")
        return results

    # Prepara prodotti da cercare
    products = []
    for of in offers:
        prod = of.get("product", "")
        pn = of.get("prezzo_nuovo", "")
        if prod and len(prod) > 5:
            products.append({"name": prod, "prezzo": pn, "sconto": of.get("sconto", "")})

    if not products:
        log(f"Nessun prodotto valido da cercare", "-")
        return results

    append_report(report_path, "GOOGLE SHOPPING PRICE COMPARISON",
        f"Confronto prezzi per {len(products)} prodotti via SearchAPI.io\n")

    for prod in products[:5]:  # max 5 richieste (delle 100 free)
        q = prod["name"][:60]
        log(f"  Ricerca Google Shopping: {q[:50]}...")

        try:
            r = requests.get("https://www.searchapi.io/api/v1/search", params={
                "engine": "google_shopping",
                "q": q,
                "gl": "it",
                "hl": "it",
                "api_key": api_key,
            }, timeout=15)

            results["requests_used"] += 1

            if r.status_code == 200:
                data = r.json()
                shopping_results = data.get("shopping_results", [])

                comparison = {
                    "product": prod["name"],
                    "prezzo_farmacia": prod["prezzo"],
                    "sconto": prod["sconto"],
                    "results": [],
                    "total_results": len(shopping_results),
                }

                for item in shopping_results[:8]:
                    seller = item.get("seller", "")
                    price = item.get("extracted_price", "")
                    old_price = item.get("old_price", "")
                    title = item.get("title", "")
                    link = item.get("link", "")
                    rating = item.get("rating", "")
                    delivery = item.get("delivery", "")

                    comparison["results"].append({
                        "seller": seller,
                        "price": str(price) if price else "",
                        "old_price": str(old_price) if old_price else "",
                        "title": title[:80],
                        "link": link,
                        "rating": rating,
                        "delivery": delivery,
                    })

                results["comparisons"].append(comparison)

                # Report text
                text = f"\nProdotto: {prod['name']}\n"
                if prod['prezzo']:
                    text += f"Prezzo in farmacia: €{prod['prezzo']}"
                    if prod['sconto']:
                        text += f" ({prod['sconto']})"
                    text += "\n"
                text += f"Risultati Google Shopping: {len(shopping_results)}\n"
                for item in comparison["results"][:5]:
                    text += f"  - {item['seller']}: €{item['price']}"
                    if item['old_price']:
                        text += f" (era €{item['old_price']})"
                    text += "\n"
                append_report(report_path, f"SHOPPING - {prod['name'][:40]}", text)

                log(f"    → {len(shopping_results)} risultati")

            elif r.status_code == 429:
                log(f"    Rate limit! Aspetto...", "!")
                time.sleep(5)
            else:
                log(f"    API error: {r.status_code}", "!")

        except Exception as e:
            log(f"    Errore: {str(e)[:60]}", "!")

    save_json(os.path.join(output_dir, "phase5_shopping.json"), results)
    return results


# ──────────────────────────────────────────────
#  FASE 6 — GENERAZIONE REPORT HTML
# ──────────────────────────────────────────────

def generate_html_report(name, domain, output_dir, all_results, phase5_data=None):
    """Genera un report HTML completo e leggibile."""
    log(f"Generazione report HTML...", "*")
    
    # Prepara dati principali
    phase1 = all_results.get("phase1", {})
    phase2 = all_results.get("phase2", {})
    phase3 = all_results.get("phase3", {})
    phase4 = all_results.get("phase4", {})

    # Statistiche
    emails = phase2.get("emails", [])
    social_links = phase2.get("social_links", {})
    maigret_found = sum(len(v) for v in phase3.get("maigret", {}).values())
    offers_count = len(phase4.get("site_offers", []))
    subdomains = phase1.get("subdomains_amass", []) or phase1.get("subdomains_fierce", [])
    tech = phase1.get("tech", {})

    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Farmacia OSINT Report — {name}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: #0f0f1a; color: #e0e0e0; line-height: 1.6; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
  h1 {{ font-size: 2rem; color: #fff; margin: 30px 0 5px; }}
  h2 {{ font-size: 1.4rem; color: #7c8aff; margin: 25px 0 15px; padding-bottom: 8px;
        border-bottom: 2px solid #2a2a40; }}
  h3 {{ color: #b0b8ff; margin: 15px 0 10px; }}
  .meta {{ color: #888; font-size: 0.9rem; margin-bottom: 20px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 15px; margin: 20px 0; }}
  .card {{ background: #1a1a2e; border-radius: 10px; padding: 20px; border: 1px solid #2a2a40; }}
  .card .num {{ font-size: 2rem; font-weight: bold; color: #7c8aff; }}
  .card .label {{ font-size: 0.85rem; color: #888; margin-top: 5px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #2a2a40; font-size: 0.9rem; }}
  th {{ color: #7c8aff; font-weight: 600; }}
  tr:hover {{ background: #1e1e35; }}
  .tag {{ display: inline-block; background: #2a2a50; color: #b0b8ff; padding: 2px 10px; border-radius: 12px;
         font-size: 0.8rem; margin: 2px; }}
  .platform {{ display: inline-block; background: #1a3a2e; color: #5f0; padding: 2px 10px; border-radius: 12px;
              font-size: 0.8rem; margin: 2px; }}
  .url {{ color: #7c8aff; word-break: break-all; }}
  .section {{ background: #1a1a2e; border-radius: 10px; padding: 20px; margin: 20px 0; border: 1px solid #2a2a40; }}
  .offer {{ background: #1a2a1a; border-left: 3px solid #5f0; padding: 8px 12px; margin: 5px 0; border-radius: 0 5px 5px 0; }}
  .error {{ color: #ff6b6b; }}
  footer {{ text-align: center; color: #555; padding: 30px; font-size: 0.8rem; }}
  @media print {{ body {{ background: #fff; color: #222; }}
    .card, .section {{ background: #f5f5ff; border-color: #ccc; }}
    h2 {{ color: #446; }} th {{ color: #446; }} .url {{ color: #00f; }}
    .tag {{ background: #ddd; color: #333; }} }}
</style>
</head>
<body>
<div class="container">

<h1>🏥 Farmacia OSINT Report</h1>
<p class="meta">
  <strong>{name}</strong> — {domain}<br>
  Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — Tool v{VERSION}
</p>

<!-- STATS CARDS -->
<div class="grid">
  <div class="card"><div class="num">{len(emails)}</div><div class="label">Email trovate</div></div>
  <div class="card"><div class="num">{len(social_links)}</div><div class="label">Piattaforme social</div></div>
  <div class="card"><div class="num">{maigret_found}</div><div class="label">Profili (Maigret)</div></div>
  <div class="card"><div class="num">{offers_count}</div><div class="label">Offerte trovate</div></div>
  <div class="card"><div class="num">{len(subdomains)}</div><div class="label">Subdomini</div></div>
  <div class="card"><div class="num">{len(tech) if isinstance(tech, dict) else '?'}</div><div class="label">Tecnologie</div></div>
</div>

<!-- FASE 1: DOMINIO -->
<h2>🌐 Fase 1 — Ricognizione Dominio</h2>
<div class="section">
  <h3>DNS Records</h3>
  <table>
    <tr><th>Tipo</th><th>Valore</th></tr>
"""
    dns = phase1.get("dns", {})
    for rtype, values in dns.items():
        val = "<br>".join(values[:5]) if isinstance(values, list) else str(values)[:200]
        html += f"    <tr><td>{rtype}</td><td>{val}</td></tr>\n"
    html += "  </table>\n"

    if subdomains:
        html += "  <h3>Subdomini</h3><p>"
        for s in subdomains[:15]:
            html += f'<span class="tag">{s}</span> '
        html += "</p>\n"

    tech_info = phase1.get("tech", {})
    if tech_info and isinstance(tech_info, dict):
        html += "  <h3>Tecnologie Rilevate</h3>\n  <table><tr><th>Rilevazione</th><th>Valore</th></tr>\n"
        for k, v in tech_info.items():
            html += f"    <tr><td>{k}</td><td>{v}</td></tr>\n"
        html += "  </table>\n"

    whois_data = phase1.get("whois", {})
    if whois_data:
        interesting = ["Registrant Organization", "Registrant Email", "Creation Date", "Registrar", "Name Server", "Organization"]
        html += "  <h3>Whois (campi principali)</h3>\n  <table><tr><th>Campo</th><th>Valore</th></tr>\n"
        for key in interesting:
            if key in whois_data:
                html += f"    <tr><td>{key}</td><td>{whois_data[key][:100]}</td></tr>\n"
        html += "  </table>\n"

    html += """
</div>

<!-- FASE 2: PRESENZA WEB -->
<h2>🌍 Fase 2 — Presenza Web</h2>
<div class="section">
"""
    pages = phase2.get("pages", {})
    for url, data in list(pages.items())[:8]:
        status = data.get("status", "ERR")
        title = data.get("title", "")
        html += f'  <p><strong>{status}</strong> <span class="url">{url}</span>'
        if title:
            html += f'<br><small>{title[:100]}</small>'
        html += '</p>\n'

    if emails:
        html += "  <h3>Email trovate</h3>\n  <table><tr><th>Email</th></tr>\n"
        for e in emails:
            html += f'    <tr><td><span class="url">{e}</span></td></tr>\n'
        html += "  </table>\n"

    if social_links:
        html += "  <h3>Social Links</h3>\n"
        for platform, links in social_links.items():
            html += f"  <p><strong>{platform}:</strong><br>\n"
            for link in links:
                html += f'    <span class="url">{link}</span><br>\n'
            html += "  </p>\n"

    fb_variants = phase2.get("facebook_variants", [])
    if fb_variants:
        html += "  <h3>Facebook URL candidates (da testare)</h3>\n"
        for fb in fb_variants:
            html += f'  <p><span class="url">{fb}</span></p>\n'

    html += """
</div>

<!-- FASE 3: SOCIAL OSINT -->
<h2>👤 Fase 3 — Social & Email OSINT</h2>
<div class="section">
"""
    maigret = phase3.get("maigret", {})
    if maigret:
        html += "  <h3>Maigret — Profili trovati</h3>\n"
        for username, sites in maigret.items():
            html += f"  <p><strong>Username: {username}</strong></p>\n"
            for site, info in list(sites.items())[:20]:
                url_user = info.get("url_user", "")
                html += f'  <p><span class="tag">{site}</span> '
                if url_user:
                    html += f'<span class="url">{url_user}</span>'
                html += '</p>\n'

    holehe = phase3.get("holehe", {})
    if holehe:
        html += "  <h3>Holehe — Email su servizi</h3>\n"
        for email, data in holehe.items():
            html += f"  <p><strong>{email}</strong></p>\n"
            used = data.get("email_used", []) if isinstance(data, dict) else []
            not_used = data.get("email_not_used", []) if isinstance(data, dict) else []
            if used:
                html += "  <p><span style=\"color:#5f0\">✓ Registrata su:</span></p>\n  <p>"
                for s in used[:15]:
                    html += f'<span class="tag">{s}</span> '
                html += "</p>\n"
            if not_used:
                html += f"  <p><span style=\"color:#888\">Non trovata su {len(not_used)} servizi</span></p>\n"

    html += """
</div>

<!-- FASE 4: OFFERTE -->
<h2>🏷 Fase 4 — Offerte & E-commerce</h2>
<div class="section">
"""
    site_offers = phase4.get("site_offers", [])
    if site_offers:
        html += f"  <h3>Offerte trovate: {len(site_offers)}</h3>\n"
        # Raggruppa per source
        by_source = {}
        for of in site_offers:
            src = of.get("source", "N/D")
            if src not in by_source:
                by_source[src] = []
            by_source[src].append(of)
        for src, offers in by_source.items():
            html += f'  <p><span class="url">{src}</span></p>\n'
            for of in offers[:20]:
                prod = of.get("product", "")
                pn = of.get("prezzo_nuovo", "")
                pv = of.get("prezzo_vecchio", "")
                sc = of.get("sconto", "")
                if prod and pn:
                    if pv:
                        html += f'  <div class="offer">{prod}<br><small>€{pv} → </small><strong>€{pn}</strong>'
                        if sc:
                            html += f' <span style="color:#5f0">{sc}</span>'
                        html += '</div>\n'
                    else:
                        html += f'  <div class="offer">{prod} — <strong>€{pn}</strong></div>\n'
                elif sc and pn:
                    html += f'  <div class="offer">Sconto {sc}: €{pv or "?"} → €{pn}</div>\n'
    else:
        html += "  <p class=\"error\">Nessuna offerta trovata direttamente sul sito.</p>\n"

    apoteca = phase4.get("apoteca_natura", [])
    if apoteca:
        html += "  <h3>E-commerce Apoteca Natura</h3>\n"
        for entry in apoteca:
            html += f'  <p><span class="platform">Apoteca Natura</span> <span class="url">{entry["url"]}</span></p>\n'
            for of in entry.get("offers_raw", [])[:10]:
                html += f'  <div class="offer">{of[:150]}</div>\n'

    ecom = phase4.get("ecommerce_platforms", [])
    if ecom:
        html += "  <h3>Piattaforme E-commerce rilevate</h3>\n"
        for p in ecom:
            html += f'  <p><span class="platform">{p["platform"]}</span> — {p["type"]}</p>\n'

    # FASE 5: Google Shopping
    shopping = phase5_data
    comparisons = shopping.get("comparisons", []) if isinstance(shopping, dict) else []
    if comparisons:
        html += """
</div>

<!-- FASE 5: GOOGLE SHOPPING -->
<h2>🛒 Fase 5 — Google Shopping Price Comparison</h2>
<div class="section">
"""
        for comp in comparisons:
            html += f'  <h3>{comp["product"]}</h3>\n'
            if comp.get("prezzo_farmacia"):
                html += f'  <p>Prezzo in farmacia: <strong>€{comp["prezzo_farmacia"]}</strong>'
                if comp.get("sconto"):
                    html += f' <span style="color:#5f0">{comp["sconto"]}</span>'
                html += '</p>\n'
            html += f'  <p>Risultati Google Shopping: {comp.get("total_results", 0)}</p>\n'
            html += '  <table><tr><th>Venditore</th><th>Prezzo</th><th>Spedizione</th></tr>\n'
            for item in comp.get("results", [])[:8]:
                seller = item.get("seller", "?")
                price = item.get("price", "")
                delivery = item.get("delivery", "-")
                html += f'    <tr><td>{seller}</td><td>€{price or "?"}</td><td>{delivery or "-"}</td></tr>\n'
            html += '  </table>\n'

    html += """
</div>

<!-- LINK UTILI -->
<h2>🔗 Link Rapidi</h2>
<div class="section">
  <table>
    <tr><th>Tipo</th><th>URL</th></tr>
"""
    # Link utili
    ph1 = phase1.get("domain", domain)
    all_urls = set()
    for url in list(pages.keys())[:5]:
        all_urls.add(url)
    for plist in phase2.get("social_links", {}).values():
        for link in plist:
            all_urls.add(link)
    for fb in fb_variants:
        all_urls.add(fb)

    for url in sorted(all_urls)[:15]:
        domain_clean = domain.replace("www.", "")
        if domain_clean in url or "facebook" in url or "instagram" in url or "apoteca" in url:
            tipo = "Sito" if domain_clean in url else "Social" if "facebook" in url or "instagram" in url else "E-commerce"
            html += f'    <tr><td>{tipo}</td><td><span class="url">{url}</span></td></tr>\n'

    html += """
  </table>
</div>

<footer>
  Generato da <strong>Farmacia OSINT Tool v""" + VERSION + """</strong> —
  <a style="color:#7c8aff" href="phase1_domain.json">JSON Fase 1</a> ·
  <a style="color:#7c8aff" href="phase2_web.json">JSON Fase 2</a> ·
  <a style="color:#7c8aff" href="phase3_social.json">JSON Fase 3</a> ·
  <a style="color:#7c8aff" href="phase4_offers.json">JSON Fase 4</a> ·
  <a style="color:#7c8aff" href="phase5_shopping.json">JSON Fase 5</a>
</footer>

</div>
</body>
</html>"""

    html_path = os.path.join(output_dir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"Report HTML: {html_path}")
    return html_path


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Farmacia OSINT Tool — Ricerca OSINT su farmacie italiane")
    parser.add_argument("name", help="Nome della farmacia (es. 'Farmacia Calì Mancuso')")
    parser.add_argument("--city", "-c", help="Città (es. Vittoria)", default="")
    parser.add_argument("--domain", "-d", help="Dominio (es. farmaciacalimancuso.it)", default="")
    parser.add_argument("--output", "-o", help="Directory output", default="")
    parser.add_argument("--skip-social", action="store_true", help="Salta fase social (maigret/holehe)")
    parser.add_argument("--fast", action="store_true", help="Modalità veloce (salta amass, dnsenum)")
    parser.add_argument("--shopping", action="store_true", help="Confronta prezzi su Google Shopping")
    parser.add_argument("--shopping-api-key", help="API key per SearchAPI.io (Google Shopping)", default="")
    parser.add_argument("--shopping-no-api", action="store_true", help="Usa SerpAPI invece di SearchAPI.io")
    args = parser.parse_args()

    name = args.name.strip()
    city = args.city.strip()
    domain = args.domain.strip()
    output_dir = args.output.strip()

    # Se non specificato, genera output dir
    if not output_dir:
        slug = re.sub(r'[^a-z0-9]', '-', name.lower().strip())
        slug = re.sub(r'-+', '-', slug).strip('-')
        output_dir = f"./output_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Se non specificato, genera dominio candidato
    if not domain:
        name_clean = re.sub(r'[^a-zA-Z0-9]', '', name.lower().replace(" ", ""))
        domain = f"{name_clean}.it"
        log(f"Nessun dominio specificato, uso candidato: {domain}", "-")

    # Crea directory output
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    report_path = os.path.join(output_dir, "report.txt")

    # Header report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"{'='*70}\n")
        f.write(f"  FARMACIA OSINT REPORT\n")
        f.write(f"  Target: {name}\n")
        f.write(f"  Dominio: {domain}\n")
        f.write(f"  Città: {city or 'N/D'}\n")
        f.write(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Tool v{VERSION}\n")
        f.write(f"{'='*70}\n")

    log(f"{'='*50}")
    log(f"FARMACIA OSINT TOOL v{VERSION}")
    log(f"Target: {name}")
    log(f"Dominio: {domain}")
    log(f"Output: {output_dir}")
    log(f"{'='*50}")

    all_results = {"name": name, "domain": domain, "city": city, "timestamp": datetime.now().isoformat()}

    # Varianti dominio
    domain_base = domain.replace("www.", "").replace(".it", "").replace(".com", "").replace(".net", "")
    domain_variants = [
        f"www.{domain}",
        f"{domain_base}.it",
        f"www.{domain_base}.it",
        f"farmacia{domain_base}.it",
        f"www.farmacia{domain_base}.it",
    ]
    all_results["domain_variants"] = list(set(domain_variants))

    # ── FASE 1 ──
    try:
        r1 = phase1_domain(name, domain, output_dir)
        all_results["phase1"] = r1
    except Exception as e:
        log(f"FASE 1 ERRORE: {e}", "!")
        all_results["phase1"] = {"error": str(e)}

    # ── FASE 2 ──
    try:
        r2 = phase2_web(name, domain, output_dir, domain_variants)
        all_results["phase2"] = r2
    except Exception as e:
        log(f"FASE 2 ERRORE: {e}", "!")
        all_results["phase2"] = {"error": str(e)}

    # ── FASE 3 ──
    if not args.skip_social:
        try:
            emails = all_results.get("phase2", {}).get("emails", [])
            social_links = all_results.get("phase2", {}).get("social_links", {})
            r3 = phase3_social(name, domain, emails, output_dir, social_links)
            all_results["phase3"] = r3
        except Exception as e:
            log(f"FASE 3 ERRORE: {e}", "!")
            all_results["phase3"] = {"error": str(e)}
    else:
        all_results["phase3"] = {"skipped": True}

    # ── FASE 4 ──
    try:
        pages_from_phase2 = list(all_results.get("phase2", {}).get("pages", {}).keys())
        r4 = phase4_offers(name, domain, output_dir, pages_from_phase2)
        all_results["phase4"] = r4
    except Exception as e:
        log(f"FASE 4 ERRORE: {e}", "!")
        all_results["phase4"] = {"error": str(e)}

    # ── FASE 5 (opzionale) ──
    phase5_result = None
    if args.shopping or args.shopping_api_key:
        api_key = args.shopping_api_key or os.environ.get("SEARCHAPI_KEY", "")
        offers = all_results.get("phase4", {}).get("site_offers", [])
        try:
            phase5_result = phase5_shopping(offers, api_key, output_dir)
        except Exception as e:
            log(f"FASE 5 ERRORE: {e}", "!")
            phase5_result = {"error": str(e)}
    else:
        log(f"FASE 5 saltata. Usa --shopping per confronto prezzi Google Shopping", "-")

    # ── REPORT HTML ──
    try:
        html_path = generate_html_report(name, domain, output_dir, all_results, phase5_result)
    except Exception as e:
        log(f"Report HTML ERRORE: {e}", "!")
        html_path = ""

    # ── REPORT FINALE JSON ──
    if phase5_result:
        all_results["phase5"] = phase5_result
    save_json(os.path.join(output_dir, "report_completo.json"), all_results)

    # ── RIEPILOGO ──
    log(f"\n{'='*50}")
    log(f"✅ REPORT COMPLETATO", "+")
    log(f"📁 Output: {output_dir}/")
    log(f"📄 Report HTML: {html_path or 'N/A'}")
    log(f"📄 Report TXT: {report_path}")
    log(f"📄 JSON completo: {output_dir}/report_completo.json")
    log(f"{'='*50}")

    # Stampa riepilogo a video
    print(f"\n{'─'*60}")
    print(f"  RIEPILOGO — {name}")
    print(f"{'─'*60}")
    r1 = all_results.get("phase1", {})
    r2 = all_results.get("phase2", {})
    r3 = all_results.get("phase3", {})
    r4 = all_results.get("phase4", {})
    print(f"  🌐 DNS records:      {len(r1.get('dns', {}))} tipi")
    print(f"  🌍 Pagine scansionate: {len(r2.get('pages', {}))}")
    print(f"  📧 Email:             {len(r2.get('emails', []))}")
    print(f"  🔗 Social links:     {sum(len(v) for v in r2.get('social_links', {}).values())}")
    print(f"  👤 Profili (Maigret): {sum(len(v) for v in r3.get('maigret', {}).values())}")
    print(f"  🏷 Offerte sito:     {len(r4.get('site_offers', []))}")
    print(f"  🛒 Apoteca Natura:   {'✓' if r4.get('apoteca_natura') else '✗'}")
    print(f"{'─'*60}")

if __name__ == "__main__":
    main()
