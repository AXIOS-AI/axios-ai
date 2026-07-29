# OSINT Farmacie Provincia Ragusa

**Alias:** `email farmacia`
**Directory dati:** `/media/k10/PASSWORDLIST/backup-farmacia/`
**Progetto creato:** 2026-07-11
**Wiki:** `~/wiki/` — sorgenti in `sources/obs-*farmacie*`

---

## Obiettivo

Verificare la pubblicità su web di tutti gli indirizzi email delle 102 farmacie della provincia di Ragusa. Per ogni farmacia: trovare almeno una fonte pubblica (social, sito web, directory) che confermi l'email, o certificare che non esiste fonte pubblica.

---

## Stato Attuale (2026-07-23)

| Metrica | Valore |
|---------|--------|
| **Totale farmacie** | 100 |
| **✅ OK (fonte pubblica)** | 65 |
| **❌ NO (nessuna fonte)** | 36 |
| **Copertura** | 64% |

### Per Comune

| Città | Totale | ✅ OK | ❌ NO | % |
|-------|--------|-------|-------|---|
| Acate | 3 | 3 | 0 | 100% |
| Chiaramonte Gulfi | 2 | 2 | 0 | 100% |
| Comiso | 8 | 7 | 1 | 88% |
| Giarratana | 1 | 1 | 0 | 100% |
| Ispica | 4 | 4 | 0 | **100%** |
| Modica | 19 | 16 | 3 | 84% |
| Monterosso Almo | 1 | 1 | 0 | 100% |
| Pozzallo | 6 | 6 | 0 | **100%** |
| Ragusa | 26 | 24 | 2 | 92% |
| S. Croce Camerina | 2 | 2 | 0 | 100% |
| Scicli | 10 | 8 | 2 | 80% |
| Scoglitti | 2 | 0 | 2 | 0% |
| Vittoria | 19 | 18 | 1 | 95% |

---

## File Principali

| File | Descrizione |
|------|-------------|
| `DOSSIER_OSINT_FARMACIE_RG.md` | Dossier completo con tutte le 102 farmacie, fonti, statistiche |
| `email.txt` | Lista email (39 già verificate con fonte pubblica + note) |
| `REFERENZA_FONTI.md` | Lista originale 104 email da Federfarma Ragusa |
| `RAPPORTO_OSINT_FARMACIE_RG.md` | Report dettagliato Holehe + Mosint |
| `RAPPORTO_GHUNT_FARMACIE_RG.md` | Report GHunt per 60 Gmail |
| `farmacie_con_fonti_online.csv` | CSV con tutte le farmacie e relative fonti |

---

## Metodologia

### Fonti Verificate
1. **Facebook** (primario) — user logged in via Thorium browser, CDP su porta 9222 per estrarre testo
2. **Instagram** — account farmacia
3. **Siti ufficiali** farmacia
4. **Directory farmacia:** farmaciadinamica.net, dica33.it, farmaciediturno.org, pharmaround.it, paginegialle.it
5. **puntaseccalive.it** (directory S. Croce Camerina)
6. **Siti istituzionali:** comune.scicli.rg.it, asp.rg.it

### Tool OSINT Usati
- **Holehe** 1.61 — verifica 121 piattaforme
- **Blackbird** — verifica 16 piattaforme (Adobe, Spotify, Twitter, Duolingo, Xvideos, Chess.com)
- **Mosint** 3.0 — breach + DNS + IP + social
- **GHunt** 2.3.4 — Google Intelligence per 60 Gmail (59/60 attivi)
- **theHarvester** 4.11.1 — email da domini .it

### Regole di Verifica
- ✅ OK = email trovata su sito ufficiale, directory, social (FB/IG), o fonte istituzionale
- ❌ NO = nessuna email pubblica trovata su web (anche se l'email esiste in Federfarma)
- **Email alternative da FB sostituiscono quelle Federfarma** (es: Iaconinoto, Igea SNC)
- **Duplicati vanno rimossi** (es: Papaleo Emanuele → Papaleo SAS, rimosso)

---

## Lavoro Residuale

### Da Fare
1. **Scoglitti** (2): Del Mare, Iacono
2. **Ragusa** (5): Ecce Homo, Er. Meli, Gagini, Occhipinti, Sciveres
3. **Comiso** (1): Albani
4. **Modica** (9): G.E. Guccione, Iaconinoto, Igea SNC, Mantegna, Roccasalva 2, Sacro Cuore, Veninata, Vindigni, Mediterraneo SRL
5. **Vittoria** (4): Cannizzo 2, Pelligra, Spiteri, Vittoria 15
6. **Scicli** (1): Papaleo Emanuele (duplicato?)
7. **Ispica** (1): Cassar Scalia (scaliaco@tiscali.it — non trovata)

### Bloccanti
- Google search bloccato (ProcessSingleton conflitto con Thorium apertura profilo sf/web/default)
- Solo DuckDuckGo funzionante (copertura limitata)

---

## Note Tecniche

### Accesso Thorium (CDP)
```bash
# Thorium path
/opt/chromium.org/thorium/thorium <url>
# CDP endpoint
ws://localhost:9222/devtools/page/...
# Estrarre testo pagina via WS
Runtime.evaluate → document.body.innerText
```

### Wiki
- Tutte le osservazioni salvate in `~/wiki/` con tag `osint farmacie`
- Usare `wiki_recall` con query "farmacie" o "email farmacia" per ritrovare contesto

### Email Notevoli Verificate
- Iaconinoto: `a.iaconinoto@gmail.com` → `farmaciaiaconinoto@virgilio.it` (da FB)
- Igea SNC: `farmaciaigeamodica@gmail.com` → `farmaciaigeasnc@libero.it` (da FB)
- Ferro: `paoloferro78@gmail.com` → `info@farmaciaferro.com` (da sito)

---

## Comandi Veloci

```bash
# Leggere dossier
less /media/k10/PASSWORDLIST/backup-farmacia/DOSSIER_OSINT_FARMACIE_RG.md
# Leggere email list
cat /media/k10/PASSWORDLIST/backup-farmacia/email.txt
# Elenco wiki observations
grep -r "farmacie" ~/.llm-wiki/wiki/sources/ --include="*.md" -l
```
