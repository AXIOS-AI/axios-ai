#!/usr/bin/env python3
"""
Instagram Discover — Tool come ofacebook per Instagram senza credenziali
Strategia: ricerca Google + DuckDuckGo + terze parti.
IG non permette più verifica diretta senza login (stessa pagina per tutti).

Usage:
  python3 ig_discover.py "Farmacia Lauro di Incardona" --citta Comiso
  python3 ig_discover.py --batch farmacie.json -o report.md
"""

import argparse, json, os, re, sys, urllib.parse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] pip install requests beautifulsoup4")
    sys.exit(1)

VERSION = "2.0.0"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def gen_username_variants(nome_raw):
    """Genera varianti username IG da nome farmacia"""
    nome = nome_raw.lower().strip()
    senza_farmacia = re.sub(r'^farmacia\s+', '', nome, flags=re.IGNORECASE)
    
    variants = []
    seen = set()
    
    def add(v):
        v = v.strip().replace(' ', '').replace('-', '').replace('.', '').replace("'", '')
        v = re.sub(r'[^a-z0-9._]', '', v)[:30]
        if v and v not in seen and len(v) >= 2:
            seen.add(v)
            variants.append(v)
    
    clean_full = re.sub(r'[^a-zA-Z0-9]', '', nome)
    clean_base = re.sub(r'[^a-zA-Z0-9]', '', senza_farmacia)
    
    add(clean_base)
    add(clean_full)
    add(senza_farmacia.replace(' ', '_'))
    add(nome.replace(' ', '_').replace('farmacia_', '', 1))
    add(senza_farmacia.replace(' ', '.'))
    add(nome.replace(' ', '.'))
    add('farmacia' + clean_base)
    
    # Short
    if len(clean_base) > 8: add(clean_base[:8])
    if len(clean_full) > 8: add(clean_full[:8])
    
    # Remove SRL/SNC
    for suffix in ['srl', 'snc', 'spa']:
        for v in list(variants):
            if v.endswith(suffix) and len(v) > len(suffix) + 1:
                add(v[:-len(suffix)])
            idx = v.rfind(suffix)
            if idx > 3: add(v[:idx])
    
    # Numeri
    for base in list(variants)[:3]:
        for s in ['1', '2', 'rg', 'official', 'ufficiale']:
            add(base + s)
    
    return variants[:12]


def search_google_ig(nome, citta=''):
    """Cerca profilo IG via DuckDuckGo con site:instagram.com"""
    nome_pulito = nome.replace('Farmacia ', '', 1)
    if citta:
        query = f'site:instagram.com "{nome}" {citta}'
    else:
        query = f'site:instagram.com "{nome}" farmacia'
    
    try:
        r = requests.get('https://html.duckduckgo.com/html/', params={'q': query},
                        headers={'User-Agent': UA}, timeout=10)
        if r.status_code != 200 or 'captcha' in r.text.lower():
            return []
        
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        
        for res in soup.select('.result')[:10]:
            a = res.select_one('.result__a')
            snippet = res.select_one('.result__snippet')
            if not a: continue
            
            url = a.get('href', '')
            m = re.search(r'uddg=([^&]+)', url)
            if m:
                url = urllib.parse.unquote(m.group(1))
            
            title = a.get_text(strip=True)[:120]
            desc = snippet.get_text(strip=True)[:300] if snippet else ''
            
            # Solo URL Instagram
            if 'instagram.com/' in url:
                parts = url.split('instagram.com/')
                if len(parts) > 1:
                    username = parts[1].split('/')[0].split('?')[0]
                    if username and username not in ['p', 'explore', 'accounts', 'stories', 'reel']:
                        results.append({
                            "username": username,
                            "url": f"https://www.instagram.com/{username}/",
                            "title": title,
                            "description": desc,
                            "source": "google_ddg"
                        })
        
        # Rimuovi duplicati
        seen = set()
        deduped = []
        for r2 in results:
            if r2['username'] not in seen:
                seen.add(r2['username'])
                deduped.append(r2)
        return deduped[:5]
    
    except:
        return []


def search_direct_ig(nome, citta=''):
    """Cerca username farmacia su IG — query alternativa"""
    nome_pulito = nome.replace('Farmacia ', '', 1)
    if citta:
        query = f'"{nome_pulito}" {citta} instagram'
    else:
        query = f'"{nome_pulito}" farmacia instagram'
    
    try:
        r = requests.get('https://html.duckduckgo.com/html/', params={'q': query},
                        headers={'User-Agent': UA}, timeout=10)
        if r.status_code != 200 or 'captcha' in r.text.lower():
            return []
        
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        
        for res in soup.select('.result')[:10]:
            a = res.select_one('.result__a')
            if not a: continue
            
            url = a.get('href', '')
            m = re.search(r'uddg=([^&]+)', url)
            if m:
                url = urllib.parse.unquote(m.group(1))
            
            if 'instagram.com/' in url and '/p/' not in url:
                parts = url.split('instagram.com/')
                if len(parts) > 1:
                    username = parts[1].split('/')[0].split('?')[0]
                    if username and username not in ['p', 'explore', 'accounts', 'stories', 'reel', '']:
                        title = a.get_text(strip=True)[:120]
                        results.append({
                            "username": username,
                            "url": f"https://www.instagram.com/{username}/",
                            "title": title,
                            "source": "google_direct"
                        })
        
        seen = set()
        deduped = []
        for r2 in results:
            if r2['username'] not in seen:
                seen.add(r2['username'])
                deduped.append(r2)
        return deduped[:5]
    
    except:
        return []


def check_via_imginn(username):
    """Verifica profilo via imginn.com (viewer senza login)"""
    try:
        r = requests.get(f'https://imginn.com/p/{username}/',
                        headers={'User-Agent': UA}, timeout=8)
        if r.status_code == 200 and 'Page not found' not in r.text[:500]:
            soup = BeautifulSoup(r.text, 'html.parser')
            title = soup.title.string[:150] if soup.title else ''
            # Prova estratte info
            bio_el = soup.select_one('.bio')
            bio = bio_el.get_text(strip=True)[:500] if bio_el else ''
            return {"exists": True, "title": title, "bio": bio}
    except:
        pass
    return {"exists": False}


def verify_username(username):
    """Verifica username IG via terze parti + indizi"""
    # 1. Prova imginn
    result = check_via_imginn(username)
    if result['exists']:
        return result
    
    # 2. Prova API pubblica (some third parties still expose)
    try:
        r = requests.get(f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
                        headers={'User-Agent': UA}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            user = data.get('data', {}).get('user', {})
            if user and user.get('username'):
                return {"exists": True, "username": user['username'], "full_name": user.get('full_name', '')}
    except:
        pass
    
    return {"exists": False}


def discover(nome, citta=''):
    """Pipeline discovery IG senza credenziali"""
    result = {
        "farmacia": nome,
        "citta": citta,
        "found_profiles": [],
        "username_attempts": [],
        "web_searches": [],
        "best_username": "",
        "best_url": "",
        "profile_summary": {},
    }
    
    variants = gen_username_variants(nome)
    
    # STEP 1: Ricerca Google su IG (site:instagram.com)
    google_results = search_google_ig(nome, citta)
    result['web_searches'].append({"method": "site_instagram", "results": google_results})
    
    # STEP 2: Ricerca diretta
    direct_results = search_direct_ig(nome, citta)
    result['web_searches'].append({"method": "direct_query", "results": direct_results})
    
    # STEP 3: Filtra profili trovati (considera validi quelli da Google/DuckDuckGo)
    checked = set()
    all_found = []
    
    for wr in google_results + direct_results:
        uname = wr['username']
        if uname in checked: continue
        checked.add(uname)
        
        # Salta risultati fake ("popular", "explore", etc.)
        if uname in ['popular', 'explore', 'accounts', 'stories', 'reel', 'p']:
            continue
        if len(uname) < 3:
            continue
        
        attempt = {
            "username": uname,
            "source": wr.get('source', 'search'),
            "title": wr.get('title', '')[:100],
            "verified": True,  # Fidati dell'indicizzazione Google
            "details": wr.get('description', '')[:200],
        }
        result['username_attempts'].append(attempt)
        
        all_found.append({
            "username": uname,
            "url": f"https://www.instagram.com/{uname}/",
            "source": wr.get('source', 'search'),
            "title": wr.get('title', '')[:100],
            "description": wr.get('description', '')[:300],
        })
    
    # STEP 4: Se nessun profilo trovato via web, prova username variants su imginn
    if not all_found:
        for variant in variants:
            if variant in checked: continue
            checked.add(variant)
            v = check_via_imginn(variant)
            result['username_attempts'].append({
                "username": variant,
                "source": "variant_imginn",
                "verified": v['exists'],
                "details": v.get('title', '')[:100],
            })
            if v['exists']:
                all_found.append({
                    "username": variant,
                    "url": f"https://www.instagram.com/{variant}/",
                    "source": "imginn",
                    "title": v.get('title', '')[:100],
                })
                break
    
    result['found_profiles'] = all_found
    if all_found:
        result['best_username'] = all_found[0]['username']
        result['best_url'] = all_found[0]['url']
    
    return result


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=f"Instagram Discover v{VERSION} — IG OSINT senza login")
    parser.add_argument("nome", nargs='?', help="Nome farmacia")
    parser.add_argument("--citta", "-c", help="Città")
    parser.add_argument("--batch", "-b", help="File JSON batch")
    parser.add_argument("--output", "-o", default="./output_ig", help="Output dir")
    parser.add_argument("--format", "-f", choices=['txt', 'md', 'json'], default='md')
    args = parser.parse_args()
    
    farmacie = []
    if args.batch:
        with open(args.batch) as f:
            data = json.load(f)
            farmacie = data if isinstance(data, list) else [data]
    elif args.nome:
        farmacie = [{"nome": args.nome, "citta": args.citta or ''}]
    else:
        print("[!] Specifica nome farmacia o --batch file.json")
        sys.exit(1)
    
    os.makedirs(args.output, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"  INSTAGRAM DISCOVER v{VERSION}")
    print(f"  Strategia: Google + DuckDuckGo + imginn")
    print(f"  Farmacie: {len(farmacie)}")
    print(f"{'='*60}")
    
    all_results = []
    for idx, f in enumerate(farmacie, 1):
        nome = f.get('nome', f.get('farmacia', ''))
        citta = f.get('citta', f.get('comune', ''))
        
        print(f"\n[{idx}/{len(farmacie)}] {nome} ({citta or '?'})")
        
        r = discover(nome, citta)
        all_results.append(r)
        
        if r['found_profiles']:
            for p in r['found_profiles']:
                src = p.get('source', '?')
                uname = p.get('username', '?')
                print(f"  ✅ @{uname:25s} | via {src:15s} | {p.get('title','')[:50]}")
        else:
            print(f"  ❌ Nessun profilo trovato")
        
        with open(os.path.join(args.output, 'partial.json'), 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # Report
    found = sum(1 for r in all_results if r['found_profiles'])
    print(f"\n{'='*60}")
    print(f"  COMPLETATO: {found}/{len(all_results)} profili trovati")
    print(f"{'='*60}")
    
    if args.format == 'json':
        with open(os.path.join(args.output, 'report.json'), 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
    else:
        lines = []
        lines.append(f"# Instagram Discover Report v{VERSION}")
        lines.append(f"**Farmacie:** {len(all_results)} | **Trovati:** {found}")
        lines.append(f"")
        for idx, r in enumerate(all_results, 1):
            lines.append(f"## {idx}. {r['farmacia']} ({r.get('citta','?')})")
            if r['found_profiles']:
                for p in r['found_profiles']:
                    src = p.get('source', '?')
                    lines.append(f"- ✅ **@{p['username']}** — via {src} | {p.get('title','')[:80]}")
            else:
                lines.append(f"- ❌ Non trovato")
            lines.append(f"")
        
        with open(os.path.join(args.output, f'report.md'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    print(f"  Report: {args.output}/report.{args.format}")
