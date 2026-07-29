#!/bin/bash
# Farmacia RG — Verifica multi-piattaforma
# Verifica FB, IG, siti web per tutte 103 farmacie provincia Ragusa
# Estrae: indirizzo, email, telefono, WhatsApp
# Esegui: bash farmacia_scan.sh

cd "$(dirname "$0")"
source venv/bin/activate

cat << 'PYTHON_SCRIPT' | python3
import requests, json, re, time, sys

# === CONFIG ===
IG_SESSIONID = "76528954570%3ADE5FLgC9WBKStr%3A18%3AAYiKPHBzdF04L4hCTNx_gca6wnvW8sPlaekJSdgl5w"

# === DATI FARMACIE: nome, email, comune, fb_url, ig_username, sito_url ===
FARMACIE = [
    # --- ACATE (3) ---
    ("Guarino", "farmacia.guarino71@gmail.com", "Acate", "", "", ""),
    ("Puglisi Acate SRL", "farmaciapuglisiacate@gmail.com", "Acate",
     "https://www.facebook.com/farmaciaPuglisi/", "", "https://farmaciapuglisiacate.carrd.co/"),
    ("Puglisi SRL", "farmaciapuglisisrl@hotmail.com", "Acate",
     "https://www.facebook.com/p/Farmacia-Puglisi-Comiso-61574748877696/", "", ""),

    # --- CHIARAMONTE GULFI (2) ---
    ("Azzara e Garretto", "farmazzaragarretto@tiscali.it", "Chiaramonte Gulfi",
     "https://www.facebook.com/FarmAzzaraGarretto/", "", ""),
    ("Tavormina", "farmaciatavormina@gmail.com", "Chiaramonte Gulfi",
     "https://www.facebook.com/Tavorminafarmacia/", "", ""),

    # --- COMISO (8) ---
    ("Adamo", "info@farmaciadamonline.it", "Comiso",
     "https://www.facebook.com/Farmacia-Adamo-del-Dott-Antonio-Ferdinando-Salvo-1296811927051323/",
     "", "https://www.farmaciadamonline.it/"),
    ("Amato", "farmaciaamatocomiso@gmail.com", "Comiso",
     "https://www.facebook.com/Farmacia.Amato/", "", ""),
    ("Bocchetti", "ebocchetti@farmaciabocchetti.it", "Comiso",
     "https://www.facebook.com/BocchettiFarmacia", "", ""),
    ("Noto 2", "giunoto@gmail.com", "Comiso",
     "https://www.facebook.com/farmacianotocomiso/", "", ""),
    ("Spataro SRL", "farmaciaspatarocomiso@gmail.com", "Comiso",
     "https://www.facebook.com/p/Farmacia-Spataro-100094471054274/", "", ""),
    ("Albani", "nuccioxxx@yahoo.it", "Comiso",
     "https://www.facebook.com/farmacia-Albani-Pedalino-105368476168259/", "", ""),
    ("Lauro di Incardona", "incardona.farma@tiscali.it", "Comiso",
     "", "farmaciaincardona", ""),
    ("Noto di Marilisa Cannizzo SRL", "marilisaca@gmail.com", "Comiso", "", "", ""),

    # --- GIARRATANA (1) ---
    ("Lauretta", "farmacialauretta@gmail.com", "Giarratana",
     "https://www.facebook.com/farmacia.lauretta/", "", ""),

    # --- ISPICA (4) ---
    ("Gerratana", "fcia.gerratana@tiscalinet.it", "Ispica",
     "", "farmacia_gerratana", ""),
    ("Aquiletta", "farmaciaaquiletta@gmail.com", "Ispica",
     "", "farmacia_aquiletta_denaro_srl", ""),
    ("Ispicenia SRL", "farmaciaispiceniasrl@gmail.com", "Ispica",
     "", "farmacia_ispicenia", ""),
    ("Cassar Scalia", "scaliaco@tiscali.it", "Ispica",
     "https://www.facebook.com/farmaciacassarscalia.ispica/", "", ""),

    # --- MODICA (19) ---
    ("Amore", "amorefarmacia@tin.it", "Modica",
     "", "farmacia_amore", ""),
    ("Del Mulino", "farmaciadelmulino2013@gmail.com", "Modica",
     "", "farmaciadelmulino", ""),
    ("Floridia", "farm.floridia@gmail.com", "Modica",
     "", "farmacia_floridia", ""),
    ("Mediterraneo SRL", "farmaciamediterraneosrl@gmail.com", "Modica",
     "https://www.facebook.com/p/Farmacia-Mediterraneo-100063712831866/", "", ""),
    ("Michelica SRL", "farmaciamichelica@gmail.com", "Modica",
     "", "farmaciamichelica", ""),
    ("San Giorgio SRL", "farmaciasangiorgiosrl@gmail.com", "Modica",
     "", "farmaciasangiorgiomodica", ""),
    ("Traina", "farmaciatrainamodica@gmail.com", "Modica",
     "", "farmaciatrainamodica", ""),
    ("Vindigni", "farmaciavindigni@tim.it", "Modica",
     "https://www.facebook.com/FarmaciaVindigni/", "", ""),
    ("G.E. Guccione", "farmguccione@gmail.com", "Modica",
     "https://www.facebook.com/farmacia.guccione/", "", ""),
    ("Iaconinoto", "a.iaconinoto@gmail.com", "Modica",
     "https://www.facebook.com/farmaciaiaconinoto/", "", ""),
    ("Igea SNC", "farmaciaigeamodica@gmail.com", "Modica",
     "https://www.facebook.com/farmaciaigeamodica/", "", ""),
    ("Mantegna", "p.mantegna@tiscali.it", "Modica",
     "https://www.facebook.com/p/Farmacia-Mantegna-100090440809866/", "", ""),
    ("Roccasalva", "sabinaroccasalva@virgilio.it", "Modica",
     "https://www.facebook.com/FarmaciaRoccasalva/", "", ""),
    ("Montalbano Sgarlata SRL", "montalbanosgarlata@farmapos.it", "Modica", "", "", ""),
    ("Schiavo Lena", "farmaciaschiavolena@gmail.com", "Modica", "", "", ""),
    ("Rizzone", "farmaciarizzone@yahoo.it", "Modica", "", "", ""),
    ("Veninata", "luisa.veninata@gmail.com", "Modica", "", "", ""),
    ("Sacro Cuore Biopexor Group SRL", "bioexorgroupsrl@gmail.com", "Modica", "", "", ""),
    ("Roccasalva 2", "sabinaroccasalva63@gmail.com", "Modica", "", "", ""),

    # --- MONTEROSSO ALMO (1) ---
    ("Gulle", "farmaciagulle@gmail.com", "Monterosso Almo",
     "", "farmacia_gulle", ""),

    # --- POZZALLO (6) ---
    ("Costa", "farmcosta@tiscali.it", "Pozzallo",
     "", "farmacia_costa_pozzallo", ""),
    ("Scalia", "scalia.carmela@tiscali.it", "Pozzallo",
     "", "farmacia_scalia", ""),
    ("Eredi Losi", "farmacialosi1@gmail.com", "Pozzallo",
     "https://www.facebook.com/farmacialosi.it/about/", "", ""),
    ("Quinta", "quintafarmacia@virgilio.it", "Pozzallo",
     "https://www.facebook.com/p/Quinta-Farmacia-SRL-Pozzallo-100064187220992/", "", ""),
    ("Maria Regina SRL", "info@farmaciamariaregina.it", "Pozzallo",
     "https://www.facebook.com/FarmaciaMariaReginaSrl/", "", ""),
    ("Papa Giovanni SRL", "farmaciapapagiovannipozzallo@gmail.com", "Pozzallo",
     "https://www.facebook.com/farmaciapapagiovanni/", "", ""),

    # --- RAGUSA (26) ---
    ("Antoci", "farmacia.antoci@gmail.com", "Ragusa", "", "", ""),
    ("Basile", "info@farmaciabasileragusa.it", "Ragusa",
     "", "farmaciabasileragusa", ""),
    ("Croce Verde", "farmaciaparisirg@gmail.com", "Ragusa",
     "", "farmaciaparisiragusa", ""),
    ("Giampiccolo SRL", "farmacia.giampiccololicitra@gmail.com", "Ragusa",
     "", "farmaciagiampiccolo", ""),
    ("Matarazzo", "farmacia.matarazzo@gmail.com", "Ragusa",
     "", "farmacia_matarazzo_ragusa", ""),
    ("Nicosia", "farmanicosia95@gmail.com", "Ragusa",
     "https://www.facebook.com/farmacianicosia.ragusa", "", ""),
    ("Pianetti", "farmaciapianetti@gmail.com", "Ragusa",
     "", "farmacia_pianetti", ""),
    ("Ragusa 22", "farmaciaragusa22srl@libero.it", "Ragusa",
     "", "farmacia_ragusa22", ""),
    ("Schembari Lucio & C.", "lucio.schembari@tiscali.it", "Ragusa",
     "", "farmaciaschembarimrg", ""),
    ("Via Falcone", "farmaciaviafalconesnc@gmail.com", "Ragusa",
     "", "farmacia_via_falcone", ""),
    ("Ecce Homo", "farmaeccehomo@gmail.com", "Ragusa",
     "https://www.facebook.com/farmaeccehom0/", "", ""),
    ("Er. Meli", "farmaciaeredimeli@virgilio.it", "Ragusa",
     "https://www.facebook.com/farmaciaeredimeli/", "", ""),
    ("Gagini SNC", "farmaciagagini@gmail.com", "Ragusa",
     "https://www.facebook.com/farmaciagagini/", "", ""),
    ("Occhipinti", "farmaciaocchipinti@hotmail.it", "Ragusa",
     "https://www.facebook.com/farmaciaocchipinti/", "", ""),
    ("Guccione RG", "farmaciaguccione@gmail.com", "Ragusa",
     "https://www.facebook.com/farmaciaguccioneragusa/", "", ""),
    ("Di Natale", "farmaciadinatale@gmail.com", "Ragusa",
     "", "farmaciadinatale", ""),
    ("Sciveres", "m.sciveres@alice.it", "Ragusa",
     "", "farmacia_sciveres", ""),
    ("C. Ottaviano", "concettaottaviano@alice.it", "Ragusa", "", "", ""),
    ("Ottaviano E.", "emanueleottaviano.farmacia@gmail.com", "Ragusa", "", "", ""),
    ("Farma Salus SNC", "farmaciasalusrg@gmail.com", "Ragusa", "", "", ""),
    ("Pianetti 1", "", "Ragusa", "", "", ""),
    ("Poidomani", "farmaciapoidomani@gmail.com", "Ragusa", "", "", ""),
    ("Pianetti (2)", "giorgioaparo@hotmail.it", "Ragusa", "", "", ""),
    ("Ottaviano G.", "ottaviano@tin.it", "Ragusa", "", "", ""),
    ("Ottaviano E. (2)", "giova.trov@virgilio.it", "Ragusa", "", "", ""),
    ("Ragusa 22 (2)", "filippo.scarfalloto@alice.it", "Ragusa", "", "", ""),

    # --- S. CROCE CAMERINA (2) ---
    ("Carnazzo", "farmaciacarnazzo@gmail.com", "S. Croce Camerina",
     "", "farmaciacarnazzo", ""),
    ("Schembari Giorgio & C.", "farmaciaschembarigiorgio@gmail.com", "S. Croce Camerina",
     "", "farmaciaschembari", ""),

    # --- SCICLI (10) ---
    ("Cartia", "farmaciacartia@gmail.com", "Scicli", "", "", ""),
    ("Comunale", "farmacia.comunale@comune.scicli.rg.it", "Scicli", "", "", ""),
    ("Criscione Donnalucata", "chiara@farmaciadidonnalucata.com", "Scicli",
     "", "farmacia.donnalucata", ""),
    ("del Mare Sampieri", "fdmsampieri@gmail.com", "Scicli", "", "", ""),
    ("del Popolo di Ferro", "paoloferro78@gmail.com", "Scicli",
     "https://www.facebook.com/p/Farmacia-del-Popolo-di-Ferro-100063573415731/", "", ""),
    ("Antica", "anticaf@tin.it", "Scicli",
     "https://www.facebook.com/anticafarmaciascicli/", "", ""),
    ("Papaleo SAS", "farmaciapapaleosnc@gmail.com", "Scicli",
     "https://www.facebook.com/FarmaciaPapaleo/", "", ""),
    ("Pacetto", "farmaciapacetto.amministrazione@gmail.com", "Scicli",
     "", "farmaciapacetto", ""),
    ("Papaleo Emanuele", "mizard87@yahoo.it", "Scicli", "", "", ""),

    # --- SCOGLITTI (2) ---
    ("Del Mare", "farmaciadelmarerg@gmail.com", "Scoglitti", "", "", ""),
    ("I. Iacono", "ivana.iacono@alice.it", "Scoglitti", "", "", ""),

    # --- VITTORIA (19) ---
    ("Amica SRL", "farmaciamicasrl@gmail.com", "Vittoria",
     "https://www.facebook.com/p/Farmacia-Amica-100057152632043/", "", ""),
    ("Bianculli", "biancullifarmacia@gmail.com", "Vittoria",
     "https://www.facebook.com/farmacia.bianculli/", "", ""),
    ("Calí-Mancuso", "farmacista.farmacali@outlook.com", "Vittoria",
     "https://www.facebook.com/farmacia.cali.3/", "", ""),
    ("Cannizzo", "farmaciacannizzoelsamaria@virgilio.it", "Vittoria",
     "https://www.facebook.com/p/Farmacia-Cannizzo-100048470153425/", "", ""),
    ("De Pasquale", "farmadep@gmail.com", "Vittoria",
     "https://www.facebook.com/farmadepasquale/", "", ""),
    ("Emaia", "farmacia.emaia@virgilio.it", "Vittoria",
     "https://www.facebook.com/p/Farmacia-Emaia-100063644186184/", "", ""),
    ("Guastella SNC", "info@farmaciaguastella.com", "Vittoria",
     "https://www.facebook.com/p/Farmacia-Guastella-100063568809250/", "", ""),
    ("Iacono G.A.", "info@farmaciajacono.it", "Vittoria",
     "https://www.facebook.com/farmacia.jacono/", "", ""),
    ("Incardona Luigi", "incardona.farma@tiscali.it", "Vittoria",
     "https://www.facebook.com/farmacia.incardona/", "", ""),
    ("Mangione", "farmaciamangionerg@gmail.com", "Vittoria",
     "https://www.facebook.com/FarmaciaMangione/", "", ""),
    ("Michele Arcangelo SRL", "farmacia.michelearcangelo90@gmail.com", "Vittoria",
     "https://www.facebook.com/farmaciamichelearcangelovittoria/", "", ""),
    ("Roma", "farmaciaromavittoria@gmail.com", "Vittoria",
     "https://www.facebook.com/farmaciaromavittoria/", "", ""),
    ("Vittoria 15", "farmaciavittoria15@gmail.com", "Vittoria",
     "https://www.facebook.com/farmaciavittoria15/", "", ""),
    ("Mangione (senza FB)", "gl85@msn.com", "Vittoria", "", "", ""),
    ("Pelligra", "farmainca@libero.it", "Vittoria", "", "", ""),
    ("Roma 2", "circolarifarmaroma@gmail.com", "Vittoria", "", "", ""),
    ("Spiteri", "consolataspiteri@gmail.com", "Vittoria", "", "", ""),
]

# === FUNZIONI ===
def check_url(url, timeout=10):
    if not url: return {"status": "NO_URL", "contatti": {}}
    try:
        r = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }, timeout=timeout, allow_redirects=True)
        result = {"status": r.status_code, "final_url": r.url}
        if r.status_code == 200:
            html = r.text
            contatti = {}
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
            emails = [e for e in set(emails) if not any(x in e.lower() for x in
                      ['example', 'jquery', 'noreply', '.png', '.jpg', '.css', '.js', '.svg', '.ico'])]
            if emails: contatti['emails'] = emails[:8]
            phones = list(set(re.findall(r'(?:\+39)?[\s.-]?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}', html)))
            phones = [p.strip() for p in phones if len(re.sub(r'[\s.-]', '', p)) >= 7]
            if phones: contatti['phones'] = phones[:5]
            wa = re.findall(r'wa\.me/(\d+)|whatsapp\.com/send/\?phone=(\d+)', html)
            if wa: contatti['whatsapp'] = [w[0] or w[1] for w in wa[:3]]
            addr = re.findall(r'(?:Via|Viale|Piazza|Corso|Contrada|Località)\s+[^<,]{5,120}', html[:8000])
            if addr: contatti['addresses'] = [a.strip()[:100] for a in addr[:3]]
            m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
            if m: contatti['title'] = m.group(1).strip()[:120]
            result['contatti'] = contatti
        return result
    except Exception as e:
        return {"status": "ERR", "error": str(e)[:80]}


def check_ig(username):
    if not username: return {"status": "NO_USERNAME"}
    session = requests.Session()
    session.cookies.set('sessionid', IG_SESSIONID, domain='.instagram.com')
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
            phones = re.findall(r'\+?\d{9,15}', bio)
            if phones: contatti['phones'] = phones
            wa = re.findall(r'wa\.me/(\d+)', bio)
            if wa: contatti['whatsapp'] = wa
            return {
                "status": 200, "username": username,
                "full_name": user.get('full_name', ''),
                "bio": bio[:300],
                "followers": user.get('edge_followed_by', {}).get('count'),
                "posts": user.get('edge_owner_to_timeline_media', {}).get('count'),
                "external_url": user.get('external_url', ''),
                "is_business": user.get('is_business_account'),
                "contatti": contatti
            }
        return {"status": r.status_code}
    except Exception as e:
        return {"status": "ERR", "error": str(e)[:80]}


# === MAIN ===
report_lines = []
total = len(FARMACIE)
stats = {"ok": 0, "fb_ok": 0, "fb_ko": 0, "ig_ok": 0, "ig_ko": 0, "web_ok": 0, "web_ko": 0, "con_email": 0, "con_tel": 0}

print("\n" + "=" * 70)
print("  SCAN MULTI-PIATTAFORMA — FARMACIE PROVINCIA RAGUSA")
print(f"  Totale: {total} farmacie | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 70)

import datetime
start = datetime.datetime.now()

for idx, (nome, email, comune, fb, ig, sito) in enumerate(FARMACIE, 1):
    print(f"\n[{idx}/{total}] {nome} — {comune}")
    report_lines.append(f"\n--- {nome} ({comune}) ---")
    report_lines.append(f"Email: {email}")
    
    # FB CHECK
    if fb:
        r = check_url(fb)
        if r['status'] == 200:
            stats['fb_ok'] += 1
            print(f"  🔵 FB: ✅ {fb[:50]}")
            report_lines.append(f"FB: ✅ {fb}")
            if r.get('contatti'):
                for k, v in r['contatti'].items():
                    if k != 'title':
                        print(f"     {k}: {v}")
                        report_lines.append(f"  {k}: {v}")
        else:
            stats['fb_ko'] += 1
            print(f"  🔵 FB: ❌ ({r['status']}) {fb[:50]}")
            report_lines.append(f"FB: ❌ ({r['status']}) {fb}")
    else:
        print(f"  🔵 FB: N/D")
    
    # IG CHECK
    if ig:
        time.sleep(0.5)
        ig_data = check_ig(ig)
        if ig_data.get('status') == 200:
            stats['ig_ok'] += 1
            foll = ig_data.get('followers', '?')
            print(f"  🟣 IG: ✅ @{ig} ({foll} followers)")
            report_lines.append(f"IG: ✅ @{ig} ({foll} followers)")
            if ig_data.get('full_name'):
                print(f"     Nome: {ig_data['full_name']}")
            if ig_data.get('external_url'):
                print(f"     URL: {ig_data['external_url']}")
                report_lines.append(f"  URL sito: {ig_data['external_url']}")
            if ig_data.get('contatti'):
                for k, v in ig_data['contatti'].items():
                    print(f"     {k}: {v}")
                    report_lines.append(f"  IG {k}: {v}")
            if ig_data.get('bio'):
                print(f"     Bio: {ig_data['bio'][:100]}")
        elif ig_data.get('status') == 429:
            print(f"  🟣 IG: ⏳ RATE LIMIT — fermo")
            report_lines.append(f"IG: RATE LIMIT")
            break
        else:
            stats['ig_ko'] += 1
            print(f"  🟣 IG: ❌ ({ig_data.get('status')})")
            report_lines.append(f"IG: ❌")
    else:
        print(f"  🟣 IG: N/D")
    
    # WEB CHECK
    if sito:
        time.sleep(0.3)
        r = check_url(sito)
        if r['status'] == 200:
            stats['web_ok'] += 1
            print(f"  🌐 WEB: ✅ {sito[:50]}")
            report_lines.append(f"WEB: ✅ {sito[:50]}")
            if r.get('contatti'):
                for k, v in r['contatti'].items():
                    if k not in ('title',):
                        print(f"     {k}: {v}")
                        report_lines.append(f"  {k}: {v}")
        else:
            stats['web_ko'] += 1
            print(f"  🌐 WEB: ❌ ({r['status']}) {sito[:50]}")
    else:
        print(f"  🌐 WEB: N/D")
    
    stats['ok'] += 1
    sys.stdout.flush()

elapsed = datetime.datetime.now() - start
print(f"\n{'='*70}")
print(f"  SCAN COMPLETATO in {elapsed.total_seconds():.0f}s")
print(f"  Processate: {stats['ok']}/{total}")
print(f"  FB: {stats['fb_ok']}✅ {stats['fb_ko']}❌")
print(f"  IG: {stats['ig_ok']}✅ {stats['ig_ko']}❌")
print(f"  Web: {stats['web_ok']}✅ {stats['web_ko']}❌")
print(f"{'='*70}")

# Salva report
report_path = "report_farmacie_scan.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("SCAN MULTI-PIATTAFORMA — FARMACIE PROVINCIA RAGUSA\n")
    import datetime
    f.write(f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"Trovate: {stats['ok']}/{total}\n\n")
    f.write('\n'.join(report_lines))
print(f"\n📄 Report salvato: {report_path}")
PYTHON_SCRIPT
