#!/bin/bash
# Farmacia RG — Verifica multi-piattaforma
# FB (ofacebook prefix), IG (API), web scraping
# Esegui: bash farmacia_scan.sh

cd "$(dirname "$0")"
source venv/bin/activate

cat << 'PYTHON_SCRIPT' | python3
import requests, json, re, time, sys
from urllib.parse import urlparse

# === CONFIG ===
IG_SESSIONID = "76528954570%3ADE5FLgC9WBKStr%3A18%3AAYiKPHBzdF04L4hCTNx_gca6wnvW8sPlaekJSdgl5w"
RATE_LIMIT_WAIT = 5  # secondi tra richieste

# === LISTA FARMACIE DA DOSSIER ===
# (nome, email, comune, fb_url, ig_url, sito_url)
FARMACIE = [
    # Vittoria
    ("Amica SRL", "farmaciamicasrl@gmail.com", "Vittoria",
     "https://www.facebook.com/p/Farmacia-Amica-100057152632043/", "", "https://ordinionline.valoresalute.it/farmacie/amica-srl/290328"),
    ("Bianculli", "biancullifarmacia@gmail.com", "Vittoria",
     "https://www.facebook.com/farmacia.bianculli/", "", "https://www.farmaciadinamica.net/farmacie/farmacia-bianculli-dr-luigi/"),
    ("Calí-Mancuso", "farmacista.farmacali@outlook.com", "Vittoria",
     "https://www.facebook.com/farmacia.cali.3/", "", "https://www.farmaciacalimancuso.it/"),
    # ... aggiungi tutte qui
]

# === FUNZIONI ===
def check_url(url, name="?", timeout=10):
    """Verifica URL e cerca contatti nella pagina"""
    if not url:
        return {"status": "NO_URL", "contatti": {}}
    
    try:
        r = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        }, timeout=timeout, allow_redirects=True)
        
        result = {"status": r.status_code, "final_url": r.url}
        
        if r.status_code == 200:
            html = r.text
            contatti = {}
            
            # Email
            emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', html)
            # Filtra false email
            emails = [e for e in emails if not any(x in e.lower() for x in 
                      ['example', 'domain.com', 'jquery', 'noreply', 'nobody', 'localhost', '.png', '.jpg', '.css', '.js'])]
            if emails: contatti['emails'] = list(set(emails))[:10]
            
            # Telefono (pattern IT +39, 3xx, numeri fissi)
            phones = list(set(re.findall(r'(?:\+39)?[\s.-]?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}', html)))
            phones = [p.strip() for p in phones if len(re.sub(r'[\s.-]', '', p)) >= 6]
            if phones: contatti['phones'] = phones[:5]
            
            # WhatsApp
            wa = re.findall(r'wa\.me/(\d+)|whatsapp\.com/(?:send/)?\?phone=(\d+)', html)
            if wa: contatti['whatsapp'] = wa[:3]
            
            # Indirizzo
            addr = re.findall(r'(?:via|viale|piazza|corso|contrada)\s+[^<,]{5,100}(?:,?\s*\d{1,5})?', html[:5000], re.IGNORECASE)
            if addr: contatti['addresses'] = addr[:3]
            
            # Title
            m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
            if m: contatti['title'] = m.group(1).strip()[:100]
            
            result['contatti'] = contatti
        
        return result
    except Exception as e:
        return {"status": "ERR", "error": str(e)[:100]}


def check_ig(username):
    """Verifica profilo Instagram via API"""
    if not username: return {"status": "NO_USERNAME"}
    
    session = requests.Session()
    session.cookies.set('sessionid', IG_SESSIONID, domain='.instagram.com')
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'X-IG-App-ID': '936619743392459',
    })
    
    try:
        r = session.get(f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}')
        if r.status_code == 200:
            user = r.json().get('data', {}).get('user', {})
            bio = user.get('biography', '')
            contatti = {}
            emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', bio)
            if emails: contatti['emails'] = emails
            phones = re.findall(r'\+\d{10,15}', bio)
            if phones: contatti['phones'] = phones
            
            return {
                "status": 200,
                "username": username,
                "full_name": user.get('full_name', ''),
                "bio": bio[:200],
                "followers": user.get('edge_followed_by', {}).get('count'),
                "posts": user.get('edge_owner_to_timeline_media', {}).get('count'),
                "external_url": user.get('external_url', ''),
                "is_business": user.get('is_business_account'),
                "contatti": contatti
            }
        else:
            return {"status": r.status_code}
    except Exception as e:
        return {"status": "ERR", "error": str(e)[:100]}


# === MAIN ===
print("\n" + "="*70)
print("  SCAN MULTI-PIATTAFORMA — FARMACIE PROVINCIA RAGUSA")
print("="*70)
print(f"  Farmacie da processare: {len(FARMACIE)}")
print("="*70)

results = {"ok": 0, "fb": 0, "ig": 0, "web": 0}
for nome, email, comune, fb, ig, sito in FARMACIE:
    print(f"\n{'─'*60}")
    print(f"  🏥 {nome} — {comune}")
    print(f"  📧 {email}")
    
    # === FB CHECK ===
    print(f"  🔵 FB: ", end="")
    fb_username = fb.rstrip('/').split('/')[-1] if fb and 'p/' not in fb else fb.split('/')[-1] if fb else ""
    # Non fare richiesta HTTP se non c'è URL valido
    if fb:
        r = check_url(fb, nome)
        if r['status'] == 200:
            print("✅")
            results['fb'] += 1
            if r['contatti']:
                for k, v in r['contatti'].items():
                    print(f"     {k}: {v}")
        else:
            print(f"❌ ({r['status']})")
    else:
        print("N/D")
    
    # === IG CHECK ===
    print(f"  🟣 IG: ", end="")
    ig_username = ig.replace('https://www.instagram.com/', '').rstrip('/') if ig else ""
    if ig_username:
        time.sleep(1)  # rate limiting
        ig_data = check_ig(ig_username)
        if ig_data['status'] == 200:
            print(f"✅ {ig_data.get('followers', '?')} followers")
            if ig_data.get('external_url'):
                print(f"     URL: {ig_data['external_url']}")
            if ig_data.get('contatti'):
                for k, v in ig_data['contatti'].items():
                    print(f"     {k}: {v}")
            results['ig'] += 1
        elif ig_data['status'] == 429:
            print(f"⏳ RATE LIMIT")
            break
        else:
            print(f"❌ ({ig_data['status']})")
    else:
        print("N/D")
    
    # === WEB CHECK ===
    if sito:
        print(f"  🌐 WEB: ", end="")
        r = check_url(sito, nome)
        if r['status'] == 200:
            print("✅")
            results['web'] += 1
            if r['contatti']:
                for k, v in r['contatti'].items():
                    print(f"     {k}: {v}")
        else:
            print(f"❌ ({r['status']})")
    
    results['ok'] += 1
    sys.stdout.flush()

print(f"\n{'='*70}")
print(f"  RIEPILOGO")
print(f"  Farmacie processate: {results['ok']}")
print(f"  FB funzionanti: {results['fb']}")
print(f"  IG trovati: {results['ig']}")
print(f"  Siti web: {results['web']}")
print(f"{'='*70}")
PYTHON_SCRIPT
