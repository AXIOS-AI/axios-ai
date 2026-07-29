# Farmacia OSINT Tool

## Descrizione
Tool OSINT automatizzato per farmacie italiane. Scopre dati dominio, presenza web, profili social, email e offerte attive.

## Struttura
```
farmacia-osint/
├── farmacia-osint.py      # Script principale
├── .env                   # API key (SEARCHAPI_KEY)
├── .gitignore
├── README.md
└── __pycache__/
```

## Dipendenze
- Python 3 + requests, beautifulsoup4, lxml
- Opzionali: maigret, holehe, amass, dnsenum, fierce, httpx, whois

## Utilizzo
```bash
python3 farmacia-osint.py "Farmacia Nome" --city Vittoria --domain dominio.it
```

## Fasi
1. Ricognizione dominio (whois, DNS, subdomini, tech detection)
2. Presenza web (scraping, estrazione email, social links)
3. Social & Email OSINT (maigret, holehe)
4. Offerte & E-commerce
5. Report HTML/JSON/TXT

## Stato
✅ Creato
