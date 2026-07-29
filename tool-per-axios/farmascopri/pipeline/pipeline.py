#!/usr/bin/env python3
"""
Pipeline Multi-Piattaforma — Farmacie Provincia Ragusa
=====================================================
Step 1: ofacebook → Verifica FB link, genera URL variants
Step 2: Osintgram → Estrae dati Instagram
Step 3: Web Finder → Scopre siti web da nome farmacia
Step 4: Report → Unifica tutto in report MD + JSON

Usage:
  python3 pipeline.py --batch farmacie.json
  python3 pipeline.py --single "Farmacia De Pasquale" --citta Vittoria
  python3 pipeline.py --all  # usa farmacie_data.json esistente
"""

import argparse, json, os, re, sys, time
from datetime import datetime

# Path tool
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFACEBOOK_DIR = os.path.join(BASE_DIR, 'tools', 'ofacebook')
OSINTGRAM_DIR = os.path.join(BASE_DIR, 'tools', 'osintgram')
WEBFINDER_DIR = os.path.join(BASE_DIR, 'tools', 'farmacia-web-finder')

# === STEP 1: FB CHECK via ofacebook prefix library ===
def step1_facebook(nome, citta, fb_known=''):
    """Verifica link FB noto + genera URL variants via ofacebook prefix"""
    result = {
        "farmacia": nome,
        "citta": citta,
        "fb_known": fb_known,
        "fb_status": "",
        "fb_working": False,
        "fb_variants": [],
        "fb_info": {},
    }

    # Verifica FB noto
    if fb_known:
        try:
            import requests
            r = requests.get(fb_known, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            }, timeout=10, allow_redirects=True)
            
            result['fb_status'] = r.status_code
            result['fb_working'] = r.status_code == 200
            result['fb_final_url'] = r.url
            
            if r.status_code == 200:
                # Estrai info base
                import re
                html = r.text[:5000]
                m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
                if m: result['fb_info']['title'] = m.group(1).strip()[:100]
                m = re.search(r'"pageID"\s*:\s*"(\d+)"', html)
                if m: result['fb_info']['page_id'] = m.group(1)
        except Exception as e:
            result['fb_status'] = f"ERR: {str(e)[:60]}"

    # Genera URL variants via ofacebook prefix library (se disponibile)
    prefix_path = os.path.join(OFACEBOOK_DIR, 'src', 'prefix-library.js')
    if os.path.exists(prefix_path):
        # Usa Node per eseguire la prefix library e generare variants
        import subprocess, tempfile
        script = f"""
        import {{ buildUrl, THUMPERSECURE_PREFIXES, METHOD_COMBINATIONS }} from '{prefix_path}';
        
        const nome = '{nome.lower().replace("'", "").replace(" ", "")}';
        const username = nome.replace(/[^a-z0-9]/g, '').replace(/^farmacia/, '');
        
        // Profile discovery prefixes
        const searchPrefixes = ['mbasic', 'm', 'touch', 'www', 'mobile', 'lite'];
        for (const p of searchPrefixes) {{
            const url = buildUrl(p.includes('.') ? p : p + '.facebook.com', '/' + username);
            console.log(url);
        }}
        // Try with farmacia prefix
        const username2 = 'farmacia' + nome.replace(/[^a-z0-9]/g, '');
        for (const p of searchPrefixes) {{
            const url = buildUrl(p.includes('.') ? p : p + '.facebook.com', '/' + username2);
            console.log(url);
        }}
        """
        try:
            r = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=10)
            if r.stdout:
                result['fb_variants'] = [u.strip() for u in r.stdout.strip().split('\n') if u.strip()]
        except:
            pass

    return result


# === STEP 2: IG EXTRACTION ===
def step2_instagram(nome, ig_username=''):
    """Estrae dati profilo Instagram"""
    result = {
        "ig_username": ig_username,
        "ig_status": "",
        "ig_working": False,
        "ig_info": {},
    }
    
    if not ig_username:
        return result

    try:
        import requests
        session = requests.Session()
        
        # Prova a caricare sessione salvata
        settings_path = os.path.join(OSINTGRAM_DIR, 'config', 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path) as f:
                settings = json.load(f)
                if 'sessionid' in settings:
                    session.cookies.set('sessionid', settings['sessionid'], domain='.instagram.com')
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'X-IG-App-ID': '936619743392459',
        })
        
        r = session.get(f'https://i.instagram.com/api/v1/users/web_profile_info/?username={ig_username}')
        result['ig_status'] = r.status_code
        
        if r.status_code == 200:
            user = r.json().get('data', {}).get('user', {})
            result['ig_working'] = True
            result['ig_info'] = {
                'username': user.get('username'),
                'full_name': user.get('full_name'),
                'bio': user.get('biography', '')[:300],
                'followers': user.get('edge_followed_by', {}).get('count'),
                'follows': user.get('edge_follow', {}).get('count'),
                'posts': user.get('edge_owner_to_timeline_media', {}).get('count'),
                'external_url': user.get('external_url'),
                'is_business': user.get('is_business_account'),
                'is_verified': user.get('is_verified'),
                'id': user.get('id'),
            }
            
            # Estrai contatti dalla bio
            bio = user.get('biography', '')
            emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', bio)
            if emails: result['ig_info']['email_bio'] = emails
            phones = re.findall(r'\+\d{9,15}', bio)
            if phones: result['ig_info']['phone_bio'] = phones
            wa = re.findall(r'wa\.me/(\d+)', bio)
            if wa: result['ig_info']['whatsapp_bio'] = wa
            
    except Exception as e:
        result['ig_status'] = f"ERR: {str(e)[:60]}"
    
    return result


# === STEP 2b: IG DISCOVER (pubblico, senza credenziali) ===
def step2b_ig_discover(nome, citta=''):
    """Cerca profilo IG pubblico senza login"""
    sys.path.insert(0, os.path.join(BASE_DIR, 'tools', 'instagram-discover'))
    try:
        from ig_discover import discover
        r = discover(nome, citta)
        return {
            "found": len(r.get('found_profiles', [])) > 0,
            "profiles": [{
                "username": p['username'],
                "url": p['url'],
                "source": p.get('source', ''),
                "title": p.get('title', '')[:80],
            } for p in r.get('found_profiles', [])],
            "attempts": r.get('username_attempts', []),
            "best_username": r.get('best_username', ''),
            "best_url": r.get('best_url', ''),
        }
    except Exception as e:
        return {"found": False, "error": str(e)[:80]}


# === STEP 3: WEB FINDER ===
def step3_web_finder(nome, citta='', domain_hint=''):
    """Trova sito web usando farmacia-web-finder"""
    import importlib.util
    sys.path.insert(0, WEBFINDER_DIR)
    spec = importlib.util.spec_from_file_location("fwf", os.path.join(WEBFINDER_DIR, "farmacia_web_finder.py"))
    fwf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fwf)
    
    result = fwf.find_website(nome, citta, domain_hint, check=True)
    return result


# === STEP 4 (FALLBACK): HEXSTRIKE ===
def step4_hexstrike(nome, citta='', known_sito=''):
    """Ultima risorsa: cerca via Google/DuckDuckGo quando web finder fallisce"""
    sys.path.insert(0, os.path.join(BASE_DIR, 'pipeline'))
    try:
        from hexstrike_fallback import hexstrike_find_website
        result = hexstrike_find_website(nome, citta, known_sito)
        return result
    except Exception as e:
        return {"found": False, "best_url": "", "error": str(e)[:60], "skipped": True}


# === STEP 5: GENERA REPORT ===
def generate_report(all_results, farmacie_originali):
    """Genera report MD unificato"""
    lines = []
    
    # Intestazione
    now = datetime.now()
    lines.append(f"# Report Farmacie OSINT — Multi-Piattaforma")
    lines.append(f"**Data:** {now.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Farmacie:** {len(all_results)}")
    lines.append(f"")
    
    # Statistiche
    fb_ok = sum(1 for r in all_results if r.get('step1', {}).get('fb_working'))
    ig_ok = sum(1 for r in all_results if r.get('step2', {}).get('ig_working'))
    web_ok = sum(1 for r in all_results if r.get('step3', {}).get('found'))
    
    lines.append(f"## 📊 Riepilogo")
    lines.append(f"| Piattaforma | ✅ OK | ❌ NO |")
    lines.append(f"|------------|-------|------|")
    lines.append(f"| Facebook | {fb_ok} | {len(all_results)-fb_ok} |")
    lines.append(f"| Instagram | {ig_ok} | {len(all_results)-ig_ok} |")
    lines.append(f"| Sito Web | {web_ok} | {len(all_results)-web_ok} |")
    lines.append(f"")
    
    # Dettaglio per farmacia
    lines.append(f"## 📋 Dettaglio Farmacie")
    lines.append(f"")
    
    for idx, r in enumerate(all_results, 1):
        farmacia = r.get('farmacia', '?')
        comune = r.get('citta', r.get('comune', '?'))
        email = r.get('email', '')
        
        s1 = r.get('step1', {})
        s2 = r.get('step2', {})
        s3 = r.get('step3', {})
        
        # Intestazione farmacia
        fb_icon = "✅" if s1.get('fb_working') else ("❌" if s1.get('fb_status') else "⬜")
        ig_icon = "✅" if s2.get('ig_working') else ("❌" if s2.get('ig_working') == False else "⬜")
        web_icon = "✅" if s3.get('found') else "❌"
        
        lines.append(f"### {idx}. {farmacia} ({comune})")
        lines.append(f"**Email:** {email or 'N/D'}")
        lines.append(f"")
        lines.append(f"| | Link | Info |")
        lines.append(f"|---|------|------|")
        
        # FB
        if s1.get('fb_known'):
            status = "✅" if s1.get('fb_working') else "❌"
            code = s1.get('fb_status', '')
            info = s1.get('fb_info', {}).get('title', '')[:60]
            lines.append(f"| {status} FB | {s1['fb_known'][:60]} | {info} |")
        else:
            lines.append(f"| ⬜ FB | N/D | — |")
        
        if s1.get('fb_variants'):
            lines.append(f"| | *Varianti:* | |")
            for v in s1['fb_variants'][:5]:
                lines.append(f"| | {v} | |")
        
        # IG
        if s2.get('ig_username'):
            status = "✅" if s2.get('ig_working') else "❌"
            info = s2.get('ig_info', {})
            foll = info.get('followers', '?')
            lines.append(f"| {status} IG | @{s2['ig_username']} | {foll} followers |")
            if info.get('full_name'):
                lines.append(f"| | Nome: {info['full_name']} | |")
            if info.get('external_url'):
                lines.append(f"| | Sito: {info['external_url']} | |")
            if info.get('email_bio'):
                lines.append(f"| | 📧 {info['email_bio']} | |")
            if info.get('phone_bio'):
                lines.append(f"| | 📞 {info['phone_bio']} | |")
        else:
            lines.append(f"| ⬜ IG | N/D | — |")
        
        # Web
        if s3.get('found'):
            lines.append(f"| ✅ WEB | {s3['best_url']} | |")
            for w in s3.get('working_urls', [])[:3]:
                title = w.get('title', '')[:60]
                src = w.get('source', '')
                if w['url'] == s3['best_url']:
                    lines.append(f"| | *{w['url']}* | {title} |")
                else:
                    lines.append(f"| | {w['url']} | {title} |")
                if w.get('emails'):
                    lines.append(f"| | 📧 {', '.join(w['emails'][:3])} | |")
                if w.get('phones'):
                    lines.append(f"| | 📞 {', '.join(w['phones'][:2])} | |")
        else:
            lines.append(f"| ❌ WEB | Non trovato | |")
        
        lines.append(f"")
    
    return '\n'.join(lines)


# === MAIN ===
def main():
    parser = argparse.ArgumentParser(description="Pipeline Multi-Piattaforma Farmacie OSINT")
    parser.add_argument("--single", help="Singola farmacia")
    parser.add_argument("--citta", help="Città")
    parser.add_argument("--batch", help="File JSON farmacie")
    parser.add_argument("--all", action="store_true", help="Usa farmacie_data.json")
    parser.add_argument("--output", "-o", default="./output_pipeline", help="Directory output")
    parser.add_argument("--skip-fb", action="store_true", help="Salta step FB")
    parser.add_argument("--skip-ig", action="store_true", help="Salta step IG")
    args = parser.parse_args()
    
    # Carica lista farmacie
    farmacie = []
    if args.all:
        json_path = os.path.join(BASE_DIR, 'pipeline', 'farmacie_complete.json')
        if os.path.exists(json_path):
            with open(json_path) as f:
                farmacie = json.load(f)
        else:
            print("[!] farmacie_data.json non trovato. Usa --batch o --single")
            return
    elif args.batch:
        with open(args.batch) as f:
            farmacie = json.load(f)
    elif args.single:
        farmacie = [{"nome": args.single, "citta": args.citta or '', "fb": '', "ig": '', "sito": ''}]
    else:
        print("[!] Specifica --single NOME, --batch file.json, o --all")
        return
    
    os.makedirs(args.output, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"\n{'='*60}")
    print(f"  🏥 FARMASCOPRI v1.0 — Multi-Platform Pharmacy OSINT")
    print(f"  Farmacie: {len(farmacie)}")
    print(f"  FB: {'⏭' if args.skip_fb else '✅'} | IG: {'⏭' if args.skip_ig else '✅'} | Web: ✅")
    print(f"{'='*60}")
    
    all_results = []
    
    for idx, f in enumerate(farmacie, 1):
        nome = f.get('nome', f.get('farmacia', ''))
        citta = f.get('citta', f.get('comune', ''))
        email = f.get('email', '')
        fb_known = f.get('fb', '')
        ig_username = f.get('ig', '').replace('https://www.instagram.com/', '').rstrip('/')
        sito_known = f.get('sito', '')
        
        print(f"\n[{idx}/{len(farmacie)}] {nome} ({citta})")
        
        result = {
            "farmacia": nome,
            "citta": citta,
            "email": email,
        }
        
        # Step 1: FB
        if not args.skip_fb:
            print(f"  🔵 FB...", end=' ', flush=True)
            s1 = step1_facebook(nome, citta, fb_known)
            result['step1'] = s1
            if s1['fb_working']: print("✅", end='')
            elif s1['fb_status']: print(f"❌ ({s1['fb_status']})", end='')
            else: print("⬜", end='')
            print()
        
        # Step 2a: IG Discover (pubblico, senza credenziali)
        print(f"  🟣 IG...", end=' ', flush=True)
        s2a = step2b_ig_discover(nome, citta)
        result['step2a'] = s2a
        if s2a['found']:
            profili = s2a['profiles']
            best = s2a.get('best_username', profili[0]['username'] if profili else '')
            ig_username = ig_username or best
            print(f"✅ @{best}", end='')
            if len(profili) > 1:
                print(f" +{len(profili)-1}", end='')
            print()
        else:
            print("⬜")
        
        # Step 2b: Osintgram (con credenziali, se username noto)
        if not args.skip_ig and ig_username:
            time.sleep(0.3)
            s2b = step2_instagram(nome, ig_username)
            result['step2b'] = s2b
            if s2b.get('ig_working'):
                print(f"  🟣📊 {s2b['ig_info'].get('followers', '?')} foll | bio: {s2b['ig_info'].get('biography','')[:60]}")
            elif s2b.get('ig_status') == 429:
                print(f"  🟣⏳ Rate limit")
            elif s2b.get('ig_status'):
                print(f"  🟣❌ ({s2b['ig_status']})")
        else:
            result['step2b'] = {"ig_username": ig_username, "ig_status": "SKIPPED", "ig_working": False}
        
        # Step 3: Web Finder
        print(f"  🌐 Web...", end=' ', flush=True)
        s3 = step3_web_finder(nome, citta, sito_known)
        result['step3'] = s3
        if s3['found']:
            print(f"✅ {s3['best_url']}")
        else:
            print("❌", end='')
            # Step 4 (Fallback): HexStrike — solo se web finder fallisce
            print(f" ⚡FX...", end=' ', flush=True)
            s4 = step4_hexstrike(nome, citta, sito_known)
            result['step4'] = s4
            if s4['found']:
                print(f"✅ {s4['best_url']}")
                # Copia in step3 per report unificato
                s3['found'] = True
                s3['best_url'] = s4['best_url']
                s3['hexstrike_fallback'] = True
            else:
                print("❌")
        
        all_results.append(result)
        
        # Salva parziale
        with open(os.path.join(args.output, 'pipeline_partial.json'), 'w') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # Report finale
    report_md = generate_report(all_results, farmacie)
    with open(os.path.join(args.output, 'report.md'), 'w', encoding='utf-8') as f:
        f.write(report_md)
    
    with open(os.path.join(args.output, 'report.json'), 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # Riepilogo
    fb_ok = sum(1 for r in all_results if r.get('step1', {}).get('fb_working'))
    ig_pub = sum(1 for r in all_results if r.get('step2a', {}).get('found'))
    ig_priv = sum(1 for r in all_results if r.get('step2b', {}).get('ig_working'))
    web_ok = sum(1 for r in all_results if r.get('step3', {}).get('found'))
    
    print(f"\n{'='*60}")
    print(f"  🏥 FARMASCOPRI — COMPLETATO")
    print(f"  Report: {args.output}/report.md")
    print(f"  JSON: {args.output}/report.json")
    print(f"  FB: {fb_ok}/{len(farmacie)} | IG pub: {ig_pub} priv: {ig_priv} | Web: {web_ok}/{len(farmacie)}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
