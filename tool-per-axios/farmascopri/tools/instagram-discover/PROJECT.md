# Instagram Discover

Tool come ofacebook per Instagram — username discovery senza credenziali.

## Funzionamento
1. **Username generation** — 15+ varianti da nome farmacia
2. **URL patterns** — `instagram.com/{username}`, imginn, bibliogram
3. **JSON public data** — estrae bio, follower, email, telefono da pagine pubbliche
4. **Web search** — DuckDuckGo fallback per profili non trovati
5. **Terze parti** — imginn, piknu, findinsta

## Utilizzo
```bash
# Singola
python3 ig_discover.py "Farmacia De Pasquale" --citta Vittoria

# Batch
python3 ig_discover.py --batch farmacie.json -o output/

# Solo generazione (no HTTP check)
python3 ig_discover.py "Farmacia Test" --no-check
```
