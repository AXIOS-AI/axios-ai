# 🏥 Farmascopri — Multi-Platform Pharmacy OSINT

Farmascopri = Farmacia + Scopri. Pipeline multi-piattaforma per scoprire e verificare presenza digitale di farmacie: nome → Facebook, Instagram, sito web.

**Input:** Nome farmacia (+ città opzionale)  
**Output:** Report unificato con FB, IG, sito web, email, telefono

## Struttura
```
osint-projects/
├── tools/                          # Tool OSINT indipendenti
│   ├── ofacebook/                  # Facebook discovery (prefix library)
│   ├── osintgram/                  # Instagram extraction (con credenziali)
│   ├── farmacia-web-finder/        # Sito web discovery da nome farmacia
│   ├── instagram-discover/         # Instagram discovery pubblico (no login)
│   └── hexstrike-ai/               # Pentesting framework (fallback)
├── pipeline/                       # Pipeline Farmascopri
│   ├── pipeline.py                 # Orchestratore 6 step
│   ├── hexstrike_fallback.py       # Fallback search module
│   └── farmacie_complete.json      # Dataset farmacie
└── PROJECT.md
```

## Pipeline 6 Step
| Step | Tool | Cosa fa |
|------|------|---------|
| 1 🔵 | **ofacebook** | Verifica FB link noti + genera URL variants |
| 2 🟣 | **IG Discover** | Cerca profilo IG pubblico senza login (DDG) |
| 3 🟣 | **Osintgram** | Estrae dati IG con credenziali |
| 4 🌐 | **Web Finder** | Scopre sito web da nome + parked detection |
| 5 ⚡ | **HexStrike** | DuckDuckGo fallback ultima risorsa |
| 6 📊 | **Report** | Output MD + JSON unificato |

## Utilizzo
```bash
cd ~/progetti/osint-projects
source tools/farmacia-web-finder/venv/bin/activate

# Singola farmacia
python3 pipeline/pipeline.py --single "Farmacia Nome" --citta Citta

# Batch da file JSON
python3 pipeline/pipeline.py --batch pipeline/farmacie_complete.json -o report/
```

## Tool autonomi
Ogni tool nella cartella `tools/` funziona anche standalone:
```bash
python3 tools/instagram-discover/ig_discover.py "Farmacia Amore" --citta Modica
python3 tools/farmacia-web-finder/farmacia_web_finder.py "Farmacia Amore" --citta Modica
```
