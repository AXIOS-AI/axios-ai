# Compara-offerte v3.1.1

## Descrizione
Confronto prezzi farmacie con 3 motori di ricerca in cascata:
1. Indice FTS5 locale (0s)
2. Pattern URL + scraping parallelo (1.5s)
3. Google Shopping API SearchAPI.io (3s)

## Stato
✅ 192 domini in siti.md (170 → 192, +22 via Google Shopping + directory scraping)
✅ 1,091,724 URL indicizzati (da 791K, +300K)
✅ 50 domini con sitemap crawlati su 192 totali
✅ Scopri-farmacie.py: discovery domini via SearchAPI.io
✅ v3.2.0: --usa-indice ottimizzato — salta Farmascopri + DuckDuckGo se indice ha match

## Scoperta nuovi domini
`scopri-farmacie.py` usa Google Shopping API per trovare farmacie non in siti.md:
- Cerca N farmaci OTC/SOP su Google Shopping
- Estrae venditori dai risultati
- Deduplica nuovi domini

```bash
python3 scopri-farmacie.py --rapido    # ~50 farmaci, ~3 min
python3 scopri-farmacie.py             # ~226 farmaci, ~10 min
```
