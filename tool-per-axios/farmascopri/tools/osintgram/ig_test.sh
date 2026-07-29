#!/bin/bash
# Test Instagram API - esegui dopo rate limit
cd "$(dirname "$0")"
source venv/bin/activate

python3 << 'PY'
import requests, json

sessionid = "76528954570%3ADE5FLgC9WBKStr%3A18%3AAYiKPHBzdF04L4hCTNx_gca6wnvW8sPlaekJSdgl5w"
session = requests.Session()
session.cookies.set('sessionid', sessionid, domain='.instagram.com')
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Brave/1.92 Safari/537.36',
    'X-IG-App-ID': '936619743392459',
})

# Test con un profilo farmacia noto
targets = [
    "farmaciabasileragusa",
    "farmacia_amore",
    "farmaciadelmulino",
]

for target in targets:
    r = session.get(f'https://i.instagram.com/api/v1/users/web_profile_info/?username={target}')
    if r.status_code == 200:
        user = r.json().get('data', {}).get('user', {})
        print(f"\n✅ @{target}")
        print(f"  Nome: {user.get('full_name', '?')}")
        print(f"  Bio: {user.get('biography', '')[:150]}")
        print(f"  Followers: {user.get('edge_followed_by', {}).get('count', '?')}")
        print(f"  Posts: {user.get('edge_owner_to_timeline_media', {}).get('count', '?')}")
        print(f"  URL: {user.get('external_url', 'N/D')}")
        print(f"  Business: {user.get('is_business_account', '?')}")
        print(f"  Verified: {user.get('is_verified', '?')}")
        # Email/phone dalla bio
        bio = user.get('biography', '')
        import re
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', bio)
        phones = re.findall(r'\+?\d{2,3}[\s.-]?\d{2,3}[\s.-]?\d{3,4}[\s.-]?\d{3,4}', bio)
        if emails: print(f"  📧 Email in bio: {emails}")
        if phones: print(f"  📞 Telefono in bio: {phones}")
    elif r.status_code == 429:
        print(f"⏳ Rate limit - riprova più tardi")
        break
    else:
        print(f"❌ @{target}: HTTP {r.status_code}")

print("\n✅ Fatto")
PY
