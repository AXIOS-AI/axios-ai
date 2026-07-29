# Compara-offerte v2.0

Tool confronto prezzi farmacie. Usa dati Farmascopri + Google Shopping API.

**Input**: file JSON generato da Farmascopri (`farmacie_complete.json`)
**Output**: report HTML comparativo con offerte siti + prezzi Google Shopping

## Utilizzo

```bash
# Default — usa dati Farmascopri, analizza tutte le farmacie
python3 compara-offerte.py

# Test su una farmacia
python3 compara-offerte.py --nome "Farmacia Amato"

# Confronto Google Shopping su termine specifico
python3 compara-offerte.py --shopping-only --search "Tachipirina 1000"

# Con file dati custom
python3 compara-offerte.py --data ./altro-file.json

# Solo scraping siti (salta API)
python3 compara-offerte.py --skip-shopping

# Output in directory custom
python3 compara-offerte.py -o ./report_20260729
```

## API Key

Servizio: **SearchAPI.io** — 100 richieste/mese gratis, no carta.

Chiave in `.env`:
```
SEARCHAPI_KEY="tua_chiave"
```

## Dipendenze

```bash
pip install requests beautifulsoup4 lxml
```

## Struttura

```
Compara-offerte/
├── compara-offerte.py      # Script principale
├── .env                    # API key (SearchAPI.io)
├── PROJECT.md
├── README.md
└── report_comparativo/     # Output generato
    ├── report.html         # Report HTML leggibile
    ├── report.json         # Dati completi JSON
    └── scraping_parziale.json  # Parziale durante esecuzione
```
