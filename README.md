# AXIOS AI — sito statico

Sito a 11 pagine (1 home + 10 sezioni) generato a partire dai contenuti del progetto
AXIOS AI. Solo HTML/CSS/JS puro, nessuna build, nessuna dipendenza da installare:
pronto per essere pubblicato così com'è su GitHub Pages.

## Struttura

```
axios-ai-site/
├── index.html              ← Home (hero fotografico + menu di navigazione a card)
├── filosofia.html
├── compatibilita.html
├── chatbox.html
├── ecosistema.html
├── privacy.html
├── requisiti.html
├── guida-uso.html
├── sicurezza.html
├── progetto-libero.html
├── contatti.html
├── .nojekyll                ← disattiva l'elaborazione Jekyll su GitHub Pages
└── assets/
    ├── css/style.css        ← design system (colori, font, componenti)
    ├── js/main.js           ← menu mobile, pagina attiva, animazioni in scroll
    └── img/
        ├── favicon.svg
        └── hero-cover.jpg   ← foto di copertina usata come sfondo della home
```

Ogni pagina interna ha in fondo una barra "Indietro / Indice / Avanti" per scorrere
tutte le sezioni in ordine, oltre al menu principale sempre visibile in alto.

## Anteprima locale

Sono file statici: puoi aprire `index.html` con doppio click, ma per evitare le
limitazioni dei browser sui file `file://` è meglio avviare un mini server locale
dalla cartella del sito:

```bash
cd axios-ai-site
python3 -m http.server 8000
```

Poi apri `http://localhost:8000` nel browser.

## Pubblicare su GitHub Pages

1. **Crea un repository** su GitHub (es. `axios-ai-site`), pubblico.
2. **Carica questi file nella root del repository** (non in una sottocartella),
   mantenendo la struttura sopra. Via web: "Add file → Upload files" e trascina
   tutto il contenuto di questa cartella (compresa `assets/` e `.nojekyll`).
   Da riga di comando:
   ```bash
   cd axios-ai-site
   git init
   git add .
   git commit -m "Primo deploy sito AXIOS AI"
   git branch -M main
   git remote add origin https://github.com/<tuo-utente>/axios-ai-site.git
   git push -u origin main
   ```
3. Nel repository su GitHub vai su **Settings → Pages**.
4. In **"Build and deployment"** scegli **Source: Deploy from a branch**.
5. In **"Branch"** seleziona `main` e cartella **`/ (root)`**, poi **Save**.
6. Dopo 1-2 minuti il sito sarà online su:
   `https://<tuo-utente>.github.io/axios-ai-site/`
   (GitHub mostra l'URL esatto in cima alla stessa pagina Settings → Pages).

Se vuoi un dominio tuo (es. `axios-ai.it`) invece dell'URL `github.io`, nella stessa
pagina Pages c'è il campo **"Custom domain"**: basta avere un dominio registrato e
puntarlo con un record DNS CNAME al tuo `<utente>.github.io`.

## Aggiornare i contenuti in futuro

Il copy ufficiale di riferimento (con eventuali modifiche) vive anche nella skill
`axios-ai-web` del progetto Claude, in `references/copy-completo.md`: usala come
fonte quando chiedi modifiche al testo, così resta tutto coerente tra sito e brand.

Per modifiche di stile, i colori e i font sono centralizzati come variabili in cima
a `assets/css/style.css` (`:root { --color-... ; --font-... }`): cambiando quei
valori si aggiorna automaticamente tutto il sito.

## Nota sulla grafica

L'hero della home usa `assets/img/hero-cover.jpg`, la foto di copertina fornita
("ΑΞΙΟΣ AI" con caduceo e città sullo sfondo). Lo stile di questa immagine
(estetica AI/neon notturna) è diverso dalla palette verde-bosco/carta/ottone usata
nel resto del sito — una scelta deliberata della prima versione per evitare i
cliché grafici "AI futuristica" tipici del settore. Per integrarla:

- la foto è a piena larghezza nell'hero, con un velo sfumato verde scuro che si
  scurisce verso il basso, dove sono ancorati eyebrow/titolo/CTA in sovraimpressione;
- la parte alta dell'immagine (titolo "ΑΞΙΟΣ AI" e grafica del caduceo già presenti
  nella foto) resta visibile senza testo sovrapposto, per non duplicare il titolo;
- il resto del sito (icone, card, colori) mantiene la linea verde/carta/ottone
  invariata — se in futuro vuoi estendere lo stile "neon/futuristico" anche alle
  pagine interne, va aggiornata la palette in `style.css` di conseguenza.

Per sostituire la foto in futuro, basta rimpiazzare il file
`assets/img/hero-cover.jpg` (stesso nome) oppure cambiare il percorso nella regola
`.hero` dentro `assets/css/style.css`.
