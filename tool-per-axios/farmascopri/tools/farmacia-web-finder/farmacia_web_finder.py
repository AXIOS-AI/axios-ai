#!/usr/bin/env python3
"""
Farmacia Web Finder — Tool per scoprire siti web di farmacie italiane
Struttura simile a ofacebook: prefix library di domini + directory + patterns

Usage:
  python3 farmacia_web_finder.py "Farmacia Amica" --citta Vittoria
  python3 farmacia_web_finder.py --batch farmacie.txt
  python3 farmacia_web_finder.py "Farmacia Calì Mancuso" --citta Vittoria --domain farmaciacalimancuso.it --check
"""

import argparse, json, os, re, sys, time
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
    import dns.resolver
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] pip install requests beautifulsoup4 dnspython")
    sys.exit(1)

VERSION = "1.0.0"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# =============================================================================
# DOMAIN PREFIX LIBRARY — come ofacebook ma per domini farmacia
# =============================================================================

# Pattern 1: Domini diretti (tentativi automatici)
DOMAIN_PATTERNS = [
    # Pattern per varianti SENZA prefisso 'farmacia' (es. depasquale)
    # expects_farmacia = False → usato per varianti base
    ("farmacia{NOME}.it", "sito_ufficiale", "Farmacia + nome dominio .it", "alta", False),
    ("www.farmacia{NOME}.it", "sito_ufficiale", "WWW Farmacia + nome dominio .it", "alta", False),
    ("{NOME}.it", "sito_ufficiale", "Solo nome dominio .it", "media", False),
    ("www.{NOME}.it", "sito_ufficiale", "WWW + nome dominio .it", "media", False),
    ("farmacia{NOME}.com", "sito_ufficiale", "Farmacia + nome dominio .com", "media", False),
    ("{NOME}.com", "sito_ufficiale", "Solo nome dominio .com", "bassa", False),
    ("{NOME}.net", "sito_ufficiale", "Solo nome dominio .net", "bassa", False),
    
    # Apoteca Natura (e-commerce Aboca) per basi
    ("farmacia{NOME}.apotecanatura.it", "ecommerce", "Apoteca Natura e-commerce", "media", False),
    ("{NOME}.apotecanatura.it", "ecommerce", "Apoteca Natura (short)", "media", False),
    
    # Subdomini su farmacia.it per basi
    ("{NOME}.farmacia.it", "sito_ufficiale", "Subdomain su farmacia.it", "media", False),
    ("{NOME}.farmacie.it", "sito_ufficiale", "Subdomain su farmacie.it", "bassa", False),
    
    # Pattern per varianti CON prefisso 'farmacia' (es. farmaciadepasquale)
    # expects_farmacia = True → usato per varianti complete
    ("{NOME}.it", "sito_ufficiale", "Solo nome dominio .it", "alta", True),
    ("www.{NOME}.it", "sito_ufficiale", "WWW + nome dominio .it", "alta", True),
    ("{NOME}.com", "sito_ufficiale", "Solo nome dominio .com", "media", True),
    ("{NOME}.apotecanatura.it", "ecommerce", "Apoteca Natura (short)", "media", True),
    ("{NOME}.net", "sito_ufficiale", "Solo nome dominio .net", "bassa", True),
    ("{NOME}.org", "sito_ufficiale", "Solo nome dominio .org", "bassa", True),
]

# Pattern 2: Varianti nome per generazione username/dominio
def gen_name_variants(nome_raw):
    """Genera varianti del nome per tentativi dominio"""
    nome = nome_raw.lower().strip()
    # Rimuovi "Farmacia" dall'inizio
    senza_farmacia = re.sub(r'^farmacia\s+', '', nome, flags=re.IGNORECASE)
    
    variants = []
    seen = set()
    
    def add(v):
        v = v.strip()
        if v and v not in seen:
            seen.add(v)
            variants.append(v)
    
    raw = nome
    
    # Senza Farmacia prefix (base pulita)
    clean_base = re.sub(r'[^a-zA-Z0-9]', '', senza_farmacia)
    add(clean_base)
    
    # Con Farmacia prefix (nome originale pulito)
    clean_full = re.sub(r'[^a-zA-Z0-9]', '', raw)
    add(clean_full)
    
    # Rimuovi SRL/SNC/SPA da tutte le varianti
    for suffix in ['srl', 'snc', 's.p.a', 'spa']:
        for v in [clean_base, clean_full]:
            if v.endswith(suffix):
                add(v[:-len(suffix)])
        # Cerca suffix in mezzo (es. 'puglisiacatesrl')
        for v in [clean_base, clean_full]:
            idx = v.rfind(suffix)
            if idx > 3:
                add(v[:idx])
    
    # Trattini (senza farmacia) — compatta dash multipli
    dashed = re.sub(r'[^a-zA-Z0-9]', '-', senza_farmacia).strip('-')
    dashed = re.sub(r'-+', '-', dashed)
    add(dashed)
    dashed_full = re.sub(r'[^a-zA-Z0-9]', '-', raw).strip('-')
    dashed_full = re.sub(r'-+', '-', dashed_full)
    add(dashed_full)
    
    # Prime 10 lettere (base e full)
    if len(clean_base) > 10:
        add(clean_base[:10])
    if len(clean_full) > 10:
        add(clean_full[:10])
    
    return variants[:8]  # max 8 varianti

# Pattern 3: Directory farmacia conosciute
FARMACY_DIRECTORIES = [
    {
        "name": "FarmaciaDinamica",
        "url": "https://www.farmaciadinamica.net/farmacie/{CITTA_SLUG}/farmacia-{NOME_SLUG}/",
        "search_url": "https://www.farmaciadinamica.net/risultati-ricerca?search={NOME}",
        "type": "directory",
    },
    {
        "name": "FarmacieMedici",
        "url": "https://www.farmaciemedici.it/farmacie/{CITTA_SLUG}/farmacia-{NOME_SLUG}",
        "type": "directory",
    },
    {
        "name": "OrariApertura24",
        "search_url": "https://www.oraridiapertura24.it/risultati-ricerca?search={NOME}+{CITTA}",
        "type": "directory",
    },
    {
        "name": "ValoreSalute",
        "search_url": "https://ordinionline.valoresalute.it/farmacie?search={NOME}",
        "type": "directory",
    },
    {
        "name": "PuntaseccaLive",
        "url": "https://www.puntaseccalive.it/farmacia-{NOME_SLUG}/",
        "type": "directory",
    },
    {
        "name": "Infoisinfo",
        "search_url": "https://vittoria.infoisinfo.it/search/{NOME}+farmacia",
        "type": "directory",
    },
    {
        "name": "ReteImprese",
        "search_url": "https://www.reteimprese.it/farmacie/{CITTA}/azienda/{NOME}",
        "type": "directory",
    },
]

# =============================================================================
# FUNZIONI
# =============================================================================

def slugify(text):
    """Converte testo in slug URL-friendly"""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

# Pattern per rilevare domini parcheggiati / in costruzione
PARKED_KEYWORDS = [
    'parking', 'nidoma', 'sito in costruzione', 'sito in manutenzione',
    'sito in allestimento', 'domain is parked', 'domain parking',
    'this domain is for sale', 'acquista questo dominio',
    'aruba.it/cart', 'managehosting', 'register.it',
    'nic.it/sospeso', 'hosting', 'pagina in costruzione',
    'under construction', 'coming soon', 'website coming soon',
    'this website is under construction', 'parcheggiato',
    'sedo.com', 'afternic', 'buydomain',
]

def check_dns(domain, timeout=5):
    """Verifica se un dominio ha record DNS"""
    if not domain: return False
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        try:
            resolver.resolve(domain, 'A')
            return True
        except:
            try:
                resolver.resolve(domain, 'AAAA')
                return True
            except:
                return False
    except:
        return False

def check_http(url, timeout=10):
    """Verifica se un URL è raggiungibile e restituisce info"""
    if not url: return {"status": "NO_URL"}
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        r = requests.get(url, headers={'User-Agent': USER_AGENT},
                        timeout=timeout, allow_redirects=True, verify=True)
        
        result = {
            "status": r.status_code,
            "final_url": r.url,
            "redirect_count": len(r.history),
        }
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            result['title'] = soup.title.string.strip() if soup.title and soup.title.string else ''
            
            # Meta description
            m = soup.find('meta', attrs={'name': 'description'})
            if m and m.get('content'):
                result['meta_desc'] = m['content'][:200]
            
            # Tecnologie rilevate
            tech = []
            if 'wp-content' in r.text or 'wp-json' in r.text:
                tech.append('WordPress')
            if 'elementor' in r.text:
                tech.append('Elementor')
            if 'shopify' in r.text:
                tech.append('Shopify')
            if 'apotecanatura' in r.text:
                tech.append('ApotecaNatura')
            if 'pharmafulcri' in r.text:
                tech.append('PharmaFulcri')
            result['tech'] = tech
            
            # Rileva dominio parcheggiato
            parked = False
            text_lower = r.text.lower()
            for kw in PARKED_KEYWORDS:
                if kw in text_lower or kw in result.get('title', '').lower():
                    parked = True
                    break
            # Final URL contiene domini di parking
            parked_domains = ['nidoma.com', 'sedo.com', 'afternic.com', 'register.it', 'aruba.it']
            for pd in parked_domains:
                if pd in result.get('final_url', ''):
                    parked = True
                    break
            if parked:
                result['status'] = 'PARKED'
                result['parked'] = True
                return result
            
            # Email nella pagina
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text))
            emails = {e for e in emails if not any(x in e.lower() for x in
                      ['example', 'jquery', '.png', '.jpg', '.css', '.js', '.svg'])}
            if emails:
                result['emails'] = list(emails)[:5]
            
            # Telefono
            phones = re.findall(r'(?:\+39)?[\s.-]?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}', r.text)
            phones = [p.strip() for p in set(phones) if len(re.sub(r'[\s.-]', '', p)) >= 7]
            if phones:
                result['phones'] = phones[:3]
            
        return result
    except requests.exceptions.SSLError:
        # Ritenta con HTTP
        try:
            r = requests.get(url.replace('https://', 'http://'), headers={'User-Agent': USER_AGENT},
                           timeout=timeout, allow_redirects=True)
            result = {"status": r.status_code, "final_url": r.url, "ssl_error": True}
            if r.status_code == 200:
                result['title'] = 'SSL Error - HTTP fallback'
            return result
        except:
            return {"status": "SSL_ERR"}
    except requests.exceptions.ConnectionError:
        return {"status": "CONN_REFUSED"}
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT"}
    except Exception as e:
        return {"status": "ERR", "error": str(e)[:100]}

def search_directory(farmacia_nome, citta, timeout=15):
    """Cerca farmacia nelle directory conosciute"""
    results = []
    slug_nome = slugify(farmacia_nome.replace('Farmacia ', '', 1))
    slug_citta = slugify(citta) if citta else ''
    
    for directory in FARMACY_DIRECTORIES:
        # Prova URL diretto
        if 'url' in directory:
            url = directory['url'].replace('{NOME_SLUG}', slug_nome).replace('{CITTA_SLUG}', slug_citta)
            try:
                r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=10)
                if r.status_code == 200:
                    # Estrai link al sito ufficiale dalla directory
                    soup = BeautifulSoup(r.text, 'html.parser')
                    # Cerca link esterni
                    site_link = None
                    for a in soup.find_all('a', href=True):
                        h = a['href']
                        if h.startswith('http') and 'farmacia' in h.lower() and 'facebook' not in h and 'instagram' not in h:
                            site_link = h
                            break
                    
                    results.append({
                        "directory": directory['name'],
                        "url": url,
                        "status": r.status_code,
                        "site_link_found": site_link,
                    })
            except:
                pass
        
        # Prova search URL
        if 'search_url' in directory:
            search_url = directory['search_url'].replace('{NOME}', slug_nome).replace('{CITTA}', slug_citta)
            try:
                r = requests.get(search_url, headers={'User-Agent': USER_AGENT}, timeout=10)
                if r.status_code == 200:
                    results.append({
                        "directory": directory['name'],
                        "search_url": search_url,
                        "status": r.status_code,
                    })
            except:
                pass
    
    return results

def search_web(farmacia_nome, citta=''):
    """Cerca su web tramite DuckDuckGo (senza API key)"""
    query = f'farmacia {farmacia_nome} {citta} sito web' if citta else f'farmacia {farmacia_nome} sito web'
    
    try:
        r = requests.get('https://html.duckduckgo.com/html/', params={'q': query},
                        headers={'User-Agent': USER_AGENT}, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            results = []
            for result in soup.select('.result'):
                a = result.select_one('.result__a')
                snippet = result.select_one('.result__snippet')
                if a:
                    url = a.get('href', '')
                    # DuckDuckGo URLs are redirects, extract real URL
                    m = re.search(r'uddg=(https?://[^&]+)', url)
                    if m:
                        url = urllib.parse.unquote(m.group(1))
                    title = a.get_text(strip=True)
                    desc = snippet.get_text(strip=True)[:200] if snippet else ''
                    if url and 'duckduckgo.com' not in url:
                        results.append({
                            "title": title,
                            "url": url,
                            "description": desc,
                            "source": "duckduckgo"
                        })
            return results[:5]
    except:
        pass
    return []

def find_website(nome, citta='', domain_hint='', check=True):
    """Trova sito web per una farmacia - pipeline completa"""
    results = {
        "farmacia": nome,
        "citta": citta,
        "domain_attempts": [],
        "directories": [],
        "search_results": [],
        "working_urls": [],
        "found": False,
        "best_url": "",
    }
    
    # STEP 0: Se domain_hint fornito (da dataset), verifica PRIORITARIO
    if domain_hint and check:
        http_result = check_http(domain_hint)
        if http_result.get('status') == 200:
            results['working_urls'].append({
                "url": domain_hint.rstrip('/'),
                "type": "sito_ufficiale",
                "source": "dataset",
                "title": http_result.get('title', '')[:80],
                "emails": http_result.get('emails', []),
                "phones": http_result.get('phones', []),
            })
            results['found'] = True
            results['best_url'] = domain_hint.rstrip('/')
            return results
        else:
            # Segna domain_hint come tentato ma fallito
            results['domain_attempts'].append({
                "domain": domain_hint,
                "pattern": "domain_hint",
                "type": "sito_ufficiale",
                "priority": "alta",
                "dns": True,
                "http": http_result,
            })
    
    # Genera varianti nome per domini
    variants = gen_name_variants(nome)
    
    # STEP 1: Prova pattern dominio diretti
    for variant in variants:
        has_farmacia_prefix = variant.startswith('farmacia')
        for pattern, tipo, desc, priorita, expects_farmacia in DOMAIN_PATTERNS:
            # Usa solo pattern che corrispondono al tipo di variante
            if expects_farmacia != has_farmacia_prefix:
                continue
            domain = pattern.replace('{NOME}', variant)
            dns_ok = check_dns(domain)
            
            attempt = {
                "domain": domain,
                "pattern": pattern,
                "type": tipo,
                "priority": priorita,
                "dns": dns_ok,
                "http": None,
            }
            
            if dns_ok and check:
                http_result = check_http(f'https://{domain}')
                attempt['http'] = http_result
                if http_result.get('status') == 200:
                    results['working_urls'].append({
                        "url": f'https://{domain}',
                        "type": tipo,
                        "title": http_result.get('title', ''),
                        "emails": http_result.get('emails', []),
                        "phones": http_result.get('phones', []),
                        "tech": http_result.get('tech', []),
                        "source": f"dominio_{priorita}"
                    })
            
            results['domain_attempts'].append(attempt)
    
    # STEP 2: Cerca nelle directory farmacia
    if citta:
        dir_results = search_directory(nome, citta)
        results['directories'] = dir_results
        for d in dir_results:
            if d.get('site_link_found'):
                # Verifica il link trovato
                if check:
                    http_result = check_http(d['site_link_found'])
                    if http_result.get('status') == 200:
                        results['working_urls'].append({
                            "url": d['site_link_found'],
                            "type": "sito_ufficiale",
                            "source": f"directory_{d['directory']}",
                            "title": http_result.get('title', ''),
                            "emails": http_result.get('emails', []),
                            "phones": http_result.get('phones', []),
                        })
    
    # STEP 3: Cerca su web
    web_results = search_web(nome, citta)
    results['search_results'] = web_results
    if web_results and check:
        for wr in web_results[:3]:
            # Non verificare FB/IG links
            if 'facebook.com' in wr['url'] or 'instagram.com' in wr['url']:
                continue
            http_result = check_http(wr['url'])
            if http_result.get('status') == 200:
                # Evita duplicati
                if not any(w['url'] == wr['url'] for w in results['working_urls']):
                    results['working_urls'].append({
                        "url": wr['url'],
                        "title": wr['title'],
                        "description": wr['description'],
                        "source": "duckduckgo",
                    })
    
    # STEP 4: Deduplica e determina best URL
    if results['working_urls']:
        # Deduplica per URL
        seen_urls = set()
        deduped = []
        for w in results['working_urls']:
            u = w.get('url', '').rstrip('/')
            if u and u not in seen_urls:
                seen_urls.add(u)
                w['url'] = u
                deduped.append(w)
        results['working_urls'] = deduped
        
        results['found'] = True
        # Preferisci sito ufficiale
        official = [w for w in results['working_urls'] if w.get('type') == 'sito_ufficiale']
        if official:
            results['best_url'] = official[0]['url']
        else:
            results['best_url'] = results['working_urls'][0]['url']
    
    return results

def generate_report(results_list, output_format='txt'):
    """Genera report in formato TXT o MD"""
    lines = []
    lines.append("# Report Farmacia Web Finder")
    lines.append(f"Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Tool v{VERSION}")
    lines.append("")
    lines.append(f"## Riepilogo")
    found = sum(1 for r in results_list if r.get('found'))
    total = len(results_list)
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Totale farmacie | {total} |")
    lines.append(f"| Sito trovato | {found} |")
    lines.append(f"| Non trovato | {total - found} |")
    lines.append(f"| Copertura | {found/total*100:.0f}% |")
    lines.append("")
    
    for idx, r in enumerate(results_list, 1):
        lines.append(f"")
        lines.append(f"## {idx}. {r['farmacia']} ({r['citta'] or 'N/D'})")
        
        if r['found']:
            lines.append(f"**✅ Sito trovato:** {r['best_url']}")
        else:
            lines.append(f"**❌ Sito non trovato**")
        
        # Working URLs
        if r.get('working_urls'):
            lines.append(f"### URL Funzionanti")
            lines.append(f"| URL | Fonte | Info |")
            lines.append(f"|-----|-------|------|")
            for w in r['working_urls']:
                info = w.get('title', '')[:60]
                src = w.get('source', '?')
                lines.append(f"| {w['url']} | {src} | {info} |")
        
        # Domain attempts (solo quelli con DNS ok)
        dns_ok = [d for d in r.get('domain_attempts', []) if d.get('dns')]
        if dns_ok:
            lines.append(f"### Domini con DNS")
            for d in dns_ok:
                http = d.get('http', {})
                status = http.get('status', 'DNS_OK')
                lines.append(f"- {d['domain']} → HTTP {status}")
        
        # Directory matches
        if r.get('directories'):
            lines.append(f"### Directory")
            for d in r['directories']:
                lines.append(f"- {d['directory']}: HTTP {d.get('status', '?')}")
                if d.get('site_link_found'):
                    lines.append(f"  → Link sito: {d['site_link_found']}")
        
        # Search results
        if r.get('search_results'):
            lines.append(f"### Ricerca Web")
            for s in r['search_results'][:3]:
                lines.append(f"- [{s['title'][:60]}]({s['url']})")
    
    return '\n'.join(lines)


# =============================================================================
# MAIN CLI
# =============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Farmacia Web Finder v" + VERSION)
    parser.add_argument("nome", nargs='?', help="Nome della farmacia")
    parser.add_argument("--citta", "-c", help="Città")
    parser.add_argument("--domain", "-d", help="Dominio conosciuto (skip ricerca)")
    parser.add_argument("--batch", "-b", help="File JSON con lista farmacie")
    parser.add_argument("--no-check", action="store_true", help="Salta verifica HTTP (solo DNS)")
    parser.add_argument("--output", "-o", help="Directory output", default="./output")
    parser.add_argument("--format", "-f", choices=['txt', 'md', 'json'], default='md')
    args = parser.parse_args()
    
    farmacie = []
    
    if args.batch:
        with open(args.batch) as f:
            data = json.load(f)
            if isinstance(data, list):
                farmacie = data
            else:
                farmacie = [data]
    elif args.nome:
        farmacie = [{"nome": args.nome, "citta": args.citta or '', "domain_hint": args.domain or ''}]
    else:
        print("[!] Specifica nome farmacia o --batch file.json")
        parser.print_help()
        sys.exit(1)
    
    os.makedirs(args.output, exist_ok=True)
    check = not args.no_check
    
    print(f"\n{'='*60}")
    print(f"  FARMACIA WEB FINDER v{VERSION}")
    print(f"  Farmacie: {len(farmacie)}")
    print(f"{'='*60}")
    
    all_results = []
    for idx, f in enumerate(farmacie, 1):
        nome = f.get('nome', f.get('farmacia', ''))
        citta = f.get('citta', f.get('comune', ''))
        domain_hint = f.get('domain_hint', f.get('domain', ''))
        
        print(f"\n[{idx}/{len(farmacie)}] {nome} ({citta or '?'})")
        
        if domain_hint:
            print(f"  Dominio fornito: {domain_hint}")
            result = {
                "farmacia": nome,
                "citta": citta,
                "found": True,
                "best_url": f"https://{domain_hint}" if not domain_hint.startswith('http') else domain_hint,
                "working_urls": [],
                "domain_attempts": [],
                "directories": [],
                "search_results": [],
            }
            if check:
                http = check_http(result['best_url'])
                result['domain_attempts'].append({"domain": domain_hint, "dns": True, "http": http})
                if http.get('status') == 200:
                    result['working_urls'].append({
                        "url": result['best_url'],
                        "type": "sito_ufficiale",
                        "source": "fornito",
                        "title": http.get('title', ''),
                        "emails": http.get('emails', []),
                        "phones": http.get('phones', []),
                    })
                    print(f"  ✅ {result['best_url']}")
                else:
                    print(f"  ⚠️ HTTP {http.get('status', 'ERR')}")
        else:
            result = find_website(nome, citta, '', check=check)
            if result['found']:
                print(f"  ✅ {result['best_url']}")
                for w in result['working_urls'][:3]:
                    print(f"     {w['url']}")
            else:
                print(f"  ❌ Nessun sito trovato")
        
        all_results.append(result)
        
        # Salva risultati parziali
        with open(os.path.join(args.output, 'results_partial.json'), 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # Report finale
    if args.format == 'json':
        with open(os.path.join(args.output, 'report.json'), 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
    else:
        ext = 'md' if args.format == 'md' else 'txt'
        report = generate_report(all_results, args.format)
        with open(os.path.join(args.output, f'report.{ext}'), 'w', encoding='utf-8') as f:
            f.write(report)
    
    print(f"\n{'='*60}")
    found = sum(1 for r in all_results if r.get('found'))
    print(f"  COMPLETATO: {found}/{len(all_results)} siti trovati")
    print(f"  Report: {args.output}/report.{args.format or 'md'}")
    print(f"{'='*60}")
