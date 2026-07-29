OBIETTIVO: Trovare i profili social ufficiali della farmacia "[NOME/COGNOME]"
(città: [CITTA], se disponibile).

ORDINE DI RICERCA (propedeutico — passa alla piattaforma successiva SOLO se
la precedente non produce match con alta confidenza dopo aver esaurito tutte
le query previste):
1° FACEBOOK
2° INSTAGRAM
3° TIKTOK
4° X (Twitter)

Non saltare piattaforme e non cercarle in parallelo: procedi in sequenza.
Se trovi un match valido su Facebook, prova comunque a cercare se esiste anche
il collegamento agli altri profili nella bio/pagina "Informazioni" prima di
avviare ricerche separate su Instagram/TikTok/X.

═══════════════════════════════════
FASE 1 — FACEBOOK
═══════════════════════════════════
1. site:facebook.com "farmacia [X]"
2. site:facebook.com "farmacia dott [X]"
3. site:facebook.com "farmacia dr [X]" OR "farmacia dottor [X]" OR "farmacia dottoressa [X]"
4. site:facebook.com "farmacia [X]" [CITTA]
5. site:facebook.com "[X]" farmacia [CITTA]
6. site:facebook.com "farmacia [X] snc" OR "farmacia [X] srl"
7. facebook.com "farmacia" "[X]" (query libera)
8. Varianti ortografiche di [X] (apostrofi, accenti, spazi)
9. site:facebook.com "[X]" [CITTA] (senza "farmacia" davanti)

Se trovato → estrai anche eventuali link a Instagram/TikTok/X presenti nella
bio o nella sezione "Informazioni" della pagina, e riportali.
Se NON trovato dopo tutte le query → passa a FASE 2.

═══════════════════════════════════
FASE 2 — INSTAGRAM (solo se Facebook non trovato)
═══════════════════════════════════
1. site:instagram.com "farmacia [X]"
2. site:instagram.com "[X]" farmacia
3. site:instagram.com "farmacia[X]" OR "farmacia_[X]" OR "farmacia.[X]" (spesso gli username uniscono le parole)
4. site:instagram.com "[X]" [CITTA]
5. Ricerca diretta nell'app/tool Instagram (se disponibile): farmacia [X]
6. Varianti ortografiche di [X]

Se trovato → estrai link ad altri social dalla bio.
Se NON trovato → passa a FASE 3.

═══════════════════════════════════
FASE 3 — TIKTOK (solo se Facebook e Instagram non trovati)
═══════════════════════════════════
1. site:tiktok.com "@farmacia[X]" OR "farmacia [X]"
2. site:tiktok.com "[X]" farmacia
3. Ricerca diretta su TikTok (se disponibile): farmacia [X]
4. Varianti ortografiche di [X]

Nota: molte farmacie non hanno TikTok — se dopo queste query non emerge nulla,
è un esito plausibile, non necessariamente un fallimento di ricerca.

Se NON trovato → passa a FASE 4.

═══════════════════════════════════
FASE 4 — X / TWITTER (solo se le precedenti 3 non hanno trovato nulla)
═══════════════════════════════════
1. site:x.com "farmacia [X]"
2. site:twitter.com "farmacia [X]"
3. site:x.com "[X]" farmacia [CITTA]
4. Varianti ortografiche di [X]

Nota: X è raramente usato da farmacie singole — bassa priorità realistica,
ma va comunque provato per completezza se richiesto.

═══════════════════════════════════
CRITERI DI MATCH (validi per tutte le fasi)
═══════════════════════════════════
- Il nome/username del profilo deve contenere il cognome/nome cercato
- Se nota la città, deve comparire in bio/post/indirizzo
- Scartare profili personali non riconducibili a un'attività commerciale
- In caso di ambiguità (più farmacie con nome simile in città diverse),
  segnalarle tutte invece di scegliere arbitrariamente

═══════════════════════════════════
OUTPUT RICHIESTO
═══════════════════════════════════
Per ogni farmacia cercata, tabella riassuntiva:

| Piattaforma | Trovato | URL | Nome profilo | Città (se visibile) | Query vincente |
|---|---|---|---|---|---|
| Facebook | Sì/No | ... | ... | ... | ... |
| Instagram | Sì/No/Non cercato* | ... | ... | ... | ... |
| TikTok | Sì/No/Non cercato* | ... | ... | ... | ... |
| X | Sì/No/Non cercato* | ... | ... | ... | ... |

*"Non cercato" se una fase precedente ha già dato match e non si è proceduto oltre.
