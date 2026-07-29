# Farmacia OSINT Tool

Tool OSINT automatizzato per farmacie italiane. Scopre dati dominio, presenza web, profili social, email e offerte attive.

## Installazione

```bash
# Dipendenze Python
pip install requests beautifulsoup4 lxml

# Tool esterni (consigliati)
pipx install maigret       # Ricerca username su 3000+ siti
pipx install holehe         # Verifica email su servizi
sudo apt install amass dnsenum fierce httpx whois dnsutils  # già su Kali
```

## Utilizzo

```bash
# Base — specifica solo nome
python3 farmacia-osint.py "Farmacia Calì Mancuso"

# Con dominio e città
python3 farmacia-osint.py "Farmacia Calì Mancuso" --city Vittoria --domain farmaciacalimancuso.it

# Modalità veloce (salta amass/dnsenum)
python3 farmacia-osint.py "Farmacia Test" --fast

# Salta fase social (più veloce, no maigret/holehe)
python3 farmacia-osint.py "Farmacia Test" --skip-social

# Confronto prezzi Google Shopping (richiede API key)
python3 farmacia-osint.py "Farmacia Test" --shopping --shopping-api-key "tua_chiave"

# Oppure via variabile ambiente
export SEARCHAPI_KEY="tua_chiave"
python3 farmacia-osint.py "Farmacia Test" --shopping

# Output in directory specifica
python3 farmacia-osint.py "Farmacia Test" -o ./output
```

### API key Google Shopping

Servizio gratuito: **SearchAPI.io** — 100 richieste/mese gratis, no carta di credito.

1. Vai su https://www.searchapi.io/ e registrati
2. Ottieni la tua API key dalla dashboard
3. Usala con `--shopping-api-key` o imposta `SEARCHAPI_KEY` come variabile d'ambiente

## Fasi

1. **Ricognizione Dominio** — whois, DNS records, subdomini (fierce/amass), tech detection (httpx)
2. **Presenza Web** — scraping pagine, estrazione email, discovery social links, theHarvester
3. **Social & Email OSINT** — maigret (username su 3000+ siti), holehe (email su 100+ servizi)
4. **Offerte & E-commerce** — scraping pagine offerte, rilevamento piattaforme e-commerce
5. **Report HTML** — report completo con grafiche e link

## Output

```
output_<farmacia>_<data>/
├── report.html           # Report HTML leggibile
├── report.txt            # Report testo
├── report_completo.json  # Tutti i dati in JSON
├── phase1_domain.json    # Dati dominio
├── phase2_web.json       # Dati presenza web
├── phase3_social.json    # Dati social
└── phase4_offers.json    # Dati offerte
```

## Tool integrati

| Tool | Funzione | API Key? |
|------|----------|----------|
| whois | Registrazione dominio | ❌ No |
| dig | DNS records | ❌ No |
| fierce/amass | Subdomain enumeration | ❌ No |
| httpx | Tech detection | ❌ No |
| theHarvester | Email/subdomain discovery | ❌ No |
| maigret | Username su 3000+ siti | ❌ No |
| holehe | Email su servizi | ❌ No |
| curl/requests | Web scraping | ❌ No |
