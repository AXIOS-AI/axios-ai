# FB OSINT Terminal 2036 (ofacebook)

## Descrizione
Webapp client-side per Facebook OSINT workflow. Genera URL variants su prefix universe thumpersecure. Assistente AI integrato, command palette, tema chiaro/scuro.

## Struttura
```
ofacebook/
├── index.html              # UI shell
├── app.js                  # Bootstrap ESM
├── styles.css              # Tema UI
├── package.json
├── security.txt
├── og-image.png
├── LICENSE
├── README.md
├── docs/
│   ├── SECURITY.md
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   └── assistant-usage.md
└── src/
    ├── index.js
    ├── prefix-library.js
    ├── data.js
    ├── osint-assistant.js
    ├── app/
    │   ├── init.js
    │   ├── presets.js
    │   └── settings.js
    ├── assistant/
    │   └── assistant.js
    ├── ui/
    │   ├── modal.js
    │   ├── theme.js
    │   ├── toast.js
    │   └── command-palette.js
    └── utils/
        ├── lang.js
        ├── dom.js
        └── security.js
```

## Features
- Puramente client-side (nessun backend)
- Prefix library thumpersecure
- Assistente AI multi-turn (OpenAI/Anthropic opzionali)
- Command palette (Ctrl+K)
- Esportazione risultati
- Temi light/dark
- CSP strict

## Avvio locale
```bash
python3 -m http.server 5173
```

## Stato
✅ Creato
