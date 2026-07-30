# MEMORIA — sito AXIOS AI

## Info progetto

- **Path locale**: `/home/k10/progetto axios/axios-ai-main`
- **Repository**: `AXIOS-AI/axios-ai.git` (GitHub)
- **Tipo**: sito statico HTML/CSS/JS — nessuna build, nessuna dipendenza
- **Pagine**: 10 (index.html + 9 sezioni)
- **Design**: palette verde-bosco/carta/ottone, font Fraunces (display) + Archivo (corpo) + Space Mono (mono)

## Struttura

```
/ (root)
├── index.html              ← Home (hero fotografico + menu a card)
├── filosofia.html          ← 01
├── compatibilita.html      ← 02
├── chatbox.html             ← 03
├── privacy.html             ← 04
├── requisiti.html           ← 05
├── guida-uso.html           ← 06
├── sicurezza.html           ← 07
├── progetto-libero.html     ← 08
├── contatti.html            ← 09
├── README.md
├── MEMORIA.md               ← QUESTO FILE
├── logo.jpg                 ← logo AXIOS AI
├── .nojekyll
└── assets/
    ├── css/style.css        ← design system completo
    ├── js/main.js           ← menu mobile, pagina attiva, scroll reveal
    └── img/
        ├── favicon.svg/png/ico
        ├── hero-cover.jpg   ← sfondo hero index
        └── logo.jpg         ← stessa immagine (link simbolico? no, copia)
```

## Regole operative

1. **Prima di ogni modifica**: leggere MEMORIA.md + verificare stato git
2. **Modificare solo i file necessari** — nessun refactoring non richiesto
3. **Dopo ogni modifica**: testare visivamente, fare commit + push
4. **Commit**: messaggi chiari in italiano, prefisso tipo (fix, feat, style, etc.)
5. **Stili**: variabili CSS in `:root` in cima a style.css — cambiarle lì per aggiornare tutto
6. **Design responsive**: testare sempre su mobile (viewport < 600px)

## Storico modifiche

| Data | Commit | Descrizione |
|------|--------|-------------|
| 2026-07-26 | 56eab46 | fix: logo stamp ridotto su mobile per evitare sovrapposizione testo |
| 2026-07-26 | 0619d73 | fix: hero contatti piu alto, testo esteso |
| 2026-07-26 | a6a1d39 | add: logo stamp animato in hero tutte le pagine, fix filosofia text |
| 2026-07-26 | fc095c9 | fix: page-hero__index allineato a numerazione 01-09 |
| 2026-07-26 | 6517153 | fix: riordinata numerazione sezioni (01-09), rimosso /10 residuo |
| 2026-07-26 | 63a3d66 | footer: logo circolare in footer e header, favicon aggiornata |
| 2026-07-20 | 9486aa2 | sicurezza: riscritta versione completa senza card |
| 2026-07-20 | 8756f57 | guida-uso: riscritta versione completa senza card |

## Elementi speciali

- **hero__brand-stamp**: logo circolare che pulsa (animazione `stamp-pulse`) in alto a destra in hero di TUTTE le pagine. Su mobile ridotto a 90px per non sovrapporsi al testo.
- **brand__logo**: logo nell'header (navbar), 60x60px circolare
- **footer-logo**: logo nel footer, 80x80px
- **page-hero__index**: numero sezione in basso a destra nell'hero delle pagine interne
- **reveal**: elementi animati all'ingresso nella viewport (IntersectionObserver)

## Pagine ancora da aggiornare (stile "vecchio")

Rispetto alle pagine riscritte (guida-uso, sicurezza) che usano `<div class="prose">` pulito, le pagine seguenti hanno ancora layout "feature-grid", "duo-card", "step-list" o stili inline:
- filosofia.html
- compatibilita.html
- chatbox.html
- privacy.html (duo-card)
- requisiti.html (step-list)
- progetto-libero.html (feature-grid)
- contatti.html (feature-grid + callout)
