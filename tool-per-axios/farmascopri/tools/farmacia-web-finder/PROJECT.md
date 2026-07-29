# Farmacia Web Finder

## Descrizione
Tool per scoprire siti web di farmacie italiane partendo dal nome. Usa pattern dominio, directory farmacia, ricerca web.

## Struttura
```
farmacia-web-finder/
├── farmacia_web_finder.py    # Tool principale
├── venv/                     # Python env
└── output/                   # Report generati
```

## Utilizzo
```bash
# Singola farmacia
python3 farmacia_web_finder.py "Farmacia De Pasquale" --citta Vittoria

# Da file JSON batch
python3 farmacia_web_finder.py --batch farmacie.json

# Salta verifica HTTP (solo DNS)
python3 farmacia_web_finder.py "Farmacia Test" --no-check

# Output formati
python3 farmacia_web_finder.py "Farmacia Test" --format md
python3 farmacia_web_finder.py "Farmacia Test" --format json
```

## Come funziona
1. **Domain patterns** — 20+ pattern tipo `farmacia{NOME}.it`, `{NOME}.apotecanatura.it`
2. **DNS check** — verifica se il dominio esiste
3. **HTTP check** — controlla se il sito è online, estrae titolo, email, telefono
4. **Directory farmacia** — cerca su farmaciadinamica.net, farmaciemedici.it, etc.
5. **Ricerca web** — DuckDuckGo fallback

## Stato
✅ Completato v1.0.0
