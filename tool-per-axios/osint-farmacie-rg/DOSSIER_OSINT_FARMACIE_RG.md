# DOSSIER OSINT — Farmacie Provincia di Ragusa

**Data completamento:** 2026-07-07  
**Strumenti:** Holehe v1.61, Mosint v3.0, Blackbird, GHunt 2.3.4, theHarvester v4.11.1, web search  
**Account GHunt:** mianopino@gmail.com  
**Totale farmacie analizzate:** 102  
**Totale email processate:** 103

---

## Indice

1. [Metodologia](#1-metodologia)
2. [Riepilogo Statistico](#2-riepilogo-statistico)
3. [Fonti Online — Ricerca Web](#3-fonti-online--ricerca-web)
4. [Account su Piattaforme Pubbliche — Holehe & Blackbird](#4-account-su-piattaforme-pubbliche--holehe--blackbird)
5. [Google Intelligence — GHunt](#5-google-intelligence--ghunt)
6. [Breach & Password Leak — Mosint](#6-breach--password-leak--mosint)
7. [Tabella Completa — 103 Farmacie](#7-tabella-completa--103-farmacie)
8. [Statistiche per Città](#8-statistiche-per-città)
9. [Dettaglio GHunt — 60 Gmail](#9-dettaglio-ghunt--60-gmail)
10. [Appendice: Note Tecniche](#10-appendice-note-tecniche)

---

## 1. Metodologia

### 1.1 Fonti dati
- **Fonte primaria:** File `REFERENZA_FONTI.md` contenente 104 indirizzi email estratti dal database Federfarma Ragusa
- **Verifica pubblicità:** Ricerca su motori (Google, DuckDuckGo), directory farmacia, siti ufficiali, social media, registro imprese

### 1.2 Tool utilizzati

| Tool | Versione | Funzione | Risultato chiave |
|------|----------|----------|-----------------|
| **Holehe** | 1.61 | Verifica 121 piattaforme per account associati all'email | 17 email con account pubblici |
| **Blackbird** | latest | Verifica 16 piattaforme mirate (con API Adobe) | **46** email con account (Adobe, Spotify, Twitter/X, Duolingo, Xvideos, Chess.com) |
| **Mosint** | 3.0 | Scansione breach, DNS, IP, social, Google search | ~80 email con breach/password leak |
| **theHarvester** | 4.11.1 | Scansione domini farmacia per email pubbliche indicizzate | Email da domini .it |
| **GHunt** | 2.3.4 | Google Intelligence (People API, Maps, Calendar, Play Games) | **59/60 Gmail** con account Google verificato |
| **Web search** | — | Ricerca manuale su Google + DuckDuckGo | **44** fonti online trovate (siti, directory, social) |

### 1.3 Workflow

```
Lista 104 email
    │
    ├─→ Holehe (121 piattaforme) → 17 account pubblici
    ├─→ Blackbird (16 piattaforme) → 46 account pubblici
    ├─→ Mosint (breach + social) → ~80 leak
    ├─→ Web search (fonti online) → 42 fonti
    └─→ GHunt (Gmail) → 59/60 account Google
```

**Tornate di ricerca web:**
- **Prima tornata:** 36 fonti trovate su 103 (34%)
- **Seconda tornata (approfondita):** +6 fonti = 42 su 103 (40.8%)
- **Quarta tornata (Modica - 2026-07-13):** +2 fonti = 44 su 103 (42.7%)
- **Conferma negativa:** 53 farmacie NON pubblicano email sul web (solo telefono)

---

## 2. Riepilogo Statistico

### 2.1 Panoramica

| Indicatore | Valore |
|------------|--------|
| Totale farmacie analizzate | **103** |
| Totale email processate | **104** |
| Con account su piattaforme pubbliche (Holehe) | **17** (16.3%) |
| Con account su piattaforme pubbliche (Blackbird) | **46** (44.2%) |
| Con breach/password leak (Mosint) | **~80** (76.9%) |
| Con fonte web/directory pubblica | **44** (42.7%) |
| Con account Google (GHunt su 60 Gmail) | **59** (98.3%) |
| Senza email pubblica sul web | **53** (51.5%) |

### 2.2 Distribuzione per città

| Città | Totale | Fonte online | % |
|-------|--------|-------------|---|
| Acate | 3 | 3 | **100%** |
| Chiaramonte Gulfi | 2 | 2 | **100%** |
| Comiso | 8 | 7 | 88% |
| Giarratana | 1 | 0 | 0% |
| Ispica | 4 | 3 | 75% |
| Modica | 19 | 14 | 74% |
| Monterosso Almo | 1 | 1 | **100%** |
| Pozzallo | 6 | 6 | **100%** |
| Ragusa | 26 | 21 | 81% |
| S. Croce Camerina | 2 | 2 | 100% |
| Scicli | 10 | 8 | 80% |
| Scoglitti | 2 | 0 | 0% |
| Vittoria | 17 | 17 | 100% |

### 2.3 Risultati GHunt

| Metrica | Valore |
|---------|--------|
| Gmail processate | **60** |
| Account Google trovati | **59** (98.3%) |
| Non trovati | **1** (Farmacia Cartia) |
| Foto profilo custom | **59/59** |
| Con Maps Profile | **37** |
| Con recensioni Maps | **2** |
| YouTube attivo | **13** |
| Photos attivo | **29** |
| Meet attivo | **27** |
| Calendar pubblico | **0** |

### 2.4 Servizi Google attivi (top)

| Servizio | N. farmacie |
|----------|-------------|
| Maps | 34 |
| Meet | 27 |
| Photos | 29 |
| YouTube | 13 |
| Nessun servizio aggiuntivo | 8 |

---

## 3. Fonti Online — Ricerca Web

### 3.1 Nuove fonti trovate (seconda tornata)

| # | Farmacia | Email | Città | Fonte URL | Tipo |
|---|----------|-------|-------|-----------|------|
| 1 | Farmacia Guarino | farmacia.guarino71@gmail.com | Acate | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Acate-Farmacia%2520Guarino%2520Dottssa%2520Giovanna-5059621W.html) | Directory |
| 2 | Farmacia C. Ottaviano | concettaottaviano@alice.it | Ragusa | [ragusawelcome.com](https://www.ragusawelcome.com/it/scopri-ragusa/a-disposizione-dell-ospite/servizi/farmacia-dott-ssa-concetta-ottaviano) | Sito turistico |
| 3 | Farmacia Ottaviano E. | emanueleottaviano.farmacia@gmail.com | Ragusa | [dermatologiainfarmacia.it](https://www.dermatologiainfarmacia.it/farmacia-dr-ottaviano-ragusa) | Sito web |
| 4 | Farmacia Ragusa 22 | farmaciaragusa22srl@libero.it | Ragusa | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Ragusa-Farmacia%2520Ragusa%252022-2191608C.html) | Directory |
| 5 | Farmacia Nicosia | farmanicosia95@gmail.com | Ragusa | [Facebook ufficiale](https://www.facebook.com/farmacianicosia.ragusa) | Social |
| 6 | Farmacia Schembari Giorgio | farmaciaschembarigiorgio@gmail.com | S. Croce Camerina | [puntaseccalive.it](https://www.puntaseccalive.it/listing/farmacia-schembari/) | Directory locale |

### 3.2 Nuove fonti Pozzallo (terza tornata — 2026-07-13)

| # | Farmacia | Email | Città | Fonte URL | Tipo |
|---|----------|-------|-------|-----------|------|
| 1 | Farmacia Eredi Losi | farmalosi@libero.it | Pozzallo | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Pozzallo-Farmacia%2520Losi-1124145I.html) | directory |
| 2 | Farmacia Papa Giovanni SRL | farmaciapapagiovannipozzallo@gmail.com | Pozzallo | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Pozzallo-Farmacia%2520Papa%2520Giovanni-4152415L.html) | directory |
| 3 | Farmacia Quinta | quintafarmacia@virgilio.it | Pozzallo | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Pozzallo-Quinta%2520Farmacia-1381843J.html) | directory |
| 4 | Farmacia Scalia | farmacia.scalia1978@gmail.com | Pozzallo | [farmaciascalia1978.it/contatti](https://www.farmaciascalia1978.it/contatti) | sito ufficiale |

### 3.3 Nuove fonti Modica (quarta tornata — 2026-07-13)

| # | Farmacia | Email | Città | Fonte URL | Tipo |
|---|----------|-------|-------|-----------|------|
| 1 | Farmacia Rizzone | farmaciarizzone@yahoo.it | Modica | [lemalo.it](https://lemalo.it/dove-fare-il-test/) | directory test |
| 2 | Farmacia Roccasalva | sabinaroccasalva@virgilio.it | Modica | [lemalo.it](https://lemalo.it/dove-fare-il-test/) | directory test |

### 3.4 Altre fonti per farmacia

Vedi [Sezione 7 — Tabella Completa](#7-tabella-completa--103-farmacie) per l'elenco completo con URL per ogni farmacia.

---

## 4. Account su Piattaforme Pubbliche — Holehe & Blackbird

### 4.1 Holehe — 17 email con account

| # | Farmacia | Email | Piattaforma(e) | Riferimento |
|---|----------|-------|----------------|-------------|
| 1 | FARMACIA IACONINOTO | a.iaconinoto@gmail.com | Office365 | Piattaforma Microsoft |
| 2 | FARMACIA CALI | amministrazione.farmacali@outlook.com | Amazon | Amazon.com account |
| 3 | FARMACIA ANTICA | anticaf@tin.it | Amazon | Amazon.com account |
| 4 | FARMACIA ADAMO | barbarase@tin.it | Spotify | Spotify.com account |
| 5 | FARMACIA OTTAVIANO E. | emanueleottaviano.farmacia@gmail.com | Office365, Spotify | Microsoft + Spotify |
| 6 | FARMACIA ANTOCI | farmacia.antoci@gmail.com | Office365 | Piattaforma Microsoft |
| 7 | FARMACIA CARNAZZO | farmaciacarnazzo@gmail.com | Firefox | Mozilla Firefox account |
| 8 | FARMACIA DI NATALE | farmaciadinatale@gmail.com | Spotify | Spotify.com account |
| 9 | FARMACIA ER. MELI | farmaciaeredimeli@virgilio.it | Office365 | Piattaforma Microsoft |
| 10 | FARMACIA GUARINO | farmacia.guarino71@gmail.com | Amazon, Office365 | Amazon + Microsoft |
| 11 | FARMACIA RAGUSA 22 | filippo.scarfalloto@alice.it | Office365 | Piattaforma Microsoft |
| 12 | FARMACIA MANGIONE | gl85@msn.com | Spotify, Twitter | Spotify + Twitter/X |
| 13 | FARMACIA LAURO DI INCARDONA | incardona.farma@tiscali.it | Office365 | Piattaforma Microsoft |
| 14 | FARMACIA NOTO 2 | marilisaca@gmail.com | Office365, Spotify | Microsoft + Spotify |
| 15 | FARMACIA ALBANI | nuccioxxx@yahoo.it | Spotify | Spotify.com account |
| 16 | FARMACIA DEL POPOLO DI FERRO | info@farmaciaferro.com | Twitter | Twitter/X account |
| 17 | FARMACIA TAVORMINA | vale.tavormina@gmail.com | Twitter | Twitter/X account |

### 4.2 Blackbird — 46 email con account

| Piattaforma | Email trovate |
|-------------|---------------|
| **Spotify** | 20 |
| **Adobe** (con avatar) | 19 |
| **Xvideos** | 15 |
| **Duolingo** | 7 |
| **Twitter/X** | 4 |
| **Chess.com** | 1 |

Dettaglio delle 46 email:

```
a.iaconinoto@gmail.com                  → Adobe
amatofarmacia@gmail.com                 → Twitter, Adobe
barbarase@tin.it                         → Spotify
concettaottaviano@alice.it              → Duolingo
ebocchetti@farmaciabocchetti.it         → Spotify, Adobe, Duolingo
emanuele.mortillaro91@gmail.com         → Spotify, Twitter, Chess.com
emanueleottaviano.farmacia@gmail.com    → Spotify
farm.floridia@gmail.com                 → Adobe
farmacia.antoci@gmail.com               → Adobe
farmacia.donnalucata@gmail.com          → Adobe
farmacia.guarino71@gmail.com            → Spotify, Duolingo
farmaciaaquiletta@gmail.com             → Adobe
farmaciadinatale@gmail.com              → Adobe, Spotify
farmaciagagini@gmail.com                → Adobe
farmaciamediterraneosrl@gmail.com       → Spotify
farmaciapapagiovannipozzallo@gmail.com  → Adobe
farmaciasalusrg@gmail.com               → Adobe
farmaciasangiorgiosrl@gmail.com         → Spotify, Adobe
farmaciaschembarigiorgio@gmail.com      → Spotify, Adobe
farmaciaschiavolena@gmail.com           → Adobe
farmadep@gmail.com                      → Spotify, Adobe
farmainca@libero.it                     → Spotify, Twitter
farmanicosia95@gmail.com                → Adobe
farmaroma@virgilio.it                   → Twitter, Duolingo
filippo.scarfalloto@alice.it            → Spotify
giunoto@gmail.com                       → Spotify
gl85@msn.com                            → Spotify
incardona.farma@tiscali.it              → Adobe
info@farmaciamariaregina.it             → Spotify
ivana.iacono@alice.it                   → Duolingo
luisa.veninata@gmail.com                → Adobe
m.sciveres@alice.it                     → Xvideos
marilisaca@gmail.com                    → Xvideos, Spotify
mirka04.70@gmail.com                    → Xvideos
mizard87@yahoo.it                       → Xvideos, Spotify, Duolingo
montalbanosgarlata@farmapos.it          → Xvideos
nuccioxxx@yahoo.it                      → Xvideos, Spotify
otaviano@tin.it                         → Xvideos
p.mantegna@tiscali.it                   → Xvideos
info@farmaciaferro.com                  → Xvideos, Duolingo, Spotify
quintafarmacia@virgilio.it              → Xvideos
sabinaroccasalva63@gmail.com            → Xvideos
sabinaroccasalva@virgilio.it            → Xvideos, Adobe
scalia.carmela@tiscali.it               → Xvideos
scaliaco@tiscali.it                     → Xvideos
vale.tavormina@gmail.com                → Xvideos, Spotify
```

> **Nota:** Blackbird non invia notifiche. I risultati Adobe includono URL avatar pubblici.

---

## 5. Google Intelligence — GHunt

### 5.1 Riepilogo GHunt

| Metrica | Valore |
|---------|--------|
| Gmail nella lista | **60** |
| Account Google trovati | **59** (98.3%) |
| Non trovati | **1** ❌ |
| Foto profilo custom | **59/59** |
| Maps Profile URL | **37** |
| Recensioni Maps | **2** (con recensioni) |
| YouTube attivo | **13** |
| Photos attivo | **29** |
| Meet attivo | **27** |
| Calendar pubblico | **0** |

### 5.2 Tabella riassuntiva GHunt

| # | Farmacia | Email | Gaia ID | Maps | Servizi |
|---|----------|-------|---------|------|---------|
| 1 | Farmacia Iaconinoto | a.iaconinoto@gmail.com | 111584546857649149512 | ✅ | Maps |
| 2 | Farmacia Amato | amatofarmacia@gmail.com | 105802774029605956452 | ✅ | — |
| 3 | Farmacia Sacro Cuore Biopexor Group SRL | bioexorgroupsrl@gmail.com | 103640361192111453885 | ✅ | Maps |
| 4 | Farmacia Roma 2 | circolarifarmaroma@gmail.com | 116127194258702740507 | ✅ | — |
| 5 | Farmacia Spiteri | consolataspiteri@gmail.com | 103037094406507979150 | ✅ | — |
| 6 | Farmacia Michele Arcangelo | emanuele.mortillaro91@gmail.com | 102701199818784660667 | ✅ | YT,Photos,Maps,Meet |
| 7 | Farmacia Ottaviano E. | emanueleottaviano.farmacia@gmail.com | 115691230739908247971 | ✅ | Maps |
| 8 | Farmacia Antoci | farmacia.antoci@gmail.com | 117681707313064124740 | — | YT,Photos |
| 9 | Farmacia Aquiletta | farmaciaaquiletta@gmail.com | 118260041939579110341 | ✅ | Photos,Maps,Meet |
| 10 | Farmacia Bianculli | farmaciabianculli@gmail.com | 115789702695350686175 | ✅ | Maps,Meet |
| 11 | Farmacia Carnazzo | farmaciacarnazzo@gmail.com | 111292705819062363718 | ✅ | Maps,Meet |
| 12 | Farmacia Cartia | farmaciacartia@gmail.com | ❌ | ❌ | ❌ |
| 13 | Farmacia Del Mare | farmaciadelmarerg@gmail.com | 113411419602516860428 | — | Photos,Maps,Meet |
| 14 | Farmacia Del Mulino | farmaciadelmulino2013@gmail.com | 101376227976364211867 | ✅ | YT,Maps,Meet,Photos |
| 15 | Farmacia Di Natale | farmaciadinatale@gmail.com | 102438842016339357573 | — | Meet |
| 16 | Farmacia Donnalucata | farmacia.donnalucata@gmail.com | 107196456376803398666 | ✅ | Photos,Maps,Meet |
| 17 | Farmacia Gagini | farmaciagagini@gmail.com | 106029218248247413732 | — | YT,Photos,Meet |
| 18 | Farmacia Giampiccolo | farmacia.giampiccololicitra@gmail.com | 114902737900348470526 | — | Photos |
| 19 | Farmacia Guarino | farmacia.guarino71@gmail.com | 107008111882354000750 | ✅ | Maps |
| 20 | Farmacia Guccione | farmaciaguccione@gmail.com | 106171692256877757546 | — | YT,Photos,Meet |
| 21 | Farmacia Igea Modica | farmaciaigeamodica@gmail.com | 115545551706867012194 | — | YT,Photos,Maps,Meet |
| 22 | Farmacia Incardona | farmacia.incardona@gmail.com | 112493326635349456353 | ✅ | Maps |
| 23 | Farmacia Ispicenia | farmaciaispiceniasrl@gmail.com | 103379094882039667103 | — | — |
| 24 | Farmacia Lauretta | farmacialauretta@gmail.com | 102062250247254566796 | ✅ | Photos,Maps,Meet |
| 25 | Farmacia Losi | farmacialosi1@gmail.com | 114336001528361463236 | — | YT,Photos |
| 26 | Farmacia Mangione | farmacia.mangionerg@gmail.com | 108015532553852876728 | ✅ | Photos,Maps,Meet |
| 27 | Farmacia Matarazzo | farmacia.matarazzo@gmail.com | 111213741243445097389 | — | Meet,Photos |
| 28 | Farmacia Mediterraneo | farmaciamediterraneosrl@gmail.com | 103087664842361453056 | ✅ | Photos,Maps,Meet |
| 29 | Farmacia Amica | farmaciamicasrl@gmail.com | 105499157613839155067 | ✅ | Maps |
| 30 | Farmacia Michele Arcangelo SRL | farmacia.michelearcangelo90@gmail.com | 101554555874522612565 | ✅ | Maps |
| 31 | Farmacia Michelica | farmaciamichelica@gmail.com | 106043503670182248728 | ✅ | YT,Photos,Maps,Meet |
| 32 | Farmacia Pacetto | farmaciapacetto.amministrazione@gmail.com | 114713072785302412265 | ✅ | Maps,Meet |
| 33 | Farmacia Papa Giovanni | farmaciapapagiovannipozzallo@gmail.com | 111939283129526206261 | ✅ | Maps |
| 34 | Farmacia Papaleo | farmaciapapaleosnc@gmail.com | 113199050212147795380 | ✅ | Maps |
| 35 | Farmacia Croce Verde | farmaciaparisirg@gmail.com | 103207570658365668010 | — | — |
| 36 | Farmacia Pianetti | farmaciapianetti@gmail.com | 102644775012946554333 | ✅ | Maps,Meet,Photos |
| 37 | Farmacia Poidomani | farmaciapoidomani@gmail.com | 105720573576083382686 | ✅ | Photos,Maps,Meet |
| 38 | Farmacia Puglisi Acate | farmaciapuglisiacate@gmail.com | 116907376929547016286 | ✅ | Photos,Maps,Meet |
| 39 | Farmacia Salus | farmaciasalusrg@gmail.com | 104012933652656940387 | ✅ | Maps,Meet |
| 40 | Farmacia San Giorgio | farmaciasangiorgiosrl@gmail.com | 115498299010604716445 | — | Meet |
| 41 | Farmacia Schembari Giorgio | farmaciaschembarigiorgio@gmail.com | 114440876272018303119 | ✅ | YT,Photos,Maps,Meet |
| 42 | Farmacia Schiavo Lena | farmaciaschiavolena@gmail.com | 114120579535591407187 | ✅ | Meet,Maps,Photos |
| 43 | Farmacia Spataro | farmaciaspatarocomiso@gmail.com | 111100770369708518684 | ✅ | Photos,Maps,Meet |
| 44 | Farmacia Traina | farmaciatrainamodica@gmail.com | 113312657103769689073 | — | — |
| 45 | Farmacia Via Falcone | farmaciaviafalconesnc@gmail.com | 116728972667249178475 | ✅ | YT,Photos,Maps,Meet |
| 46 | Farmacia Vittoria 15 | farmaciavittoria15@gmail.com | 103096787170060391340 | — | — |
| 47 | Farmacia De Pasquale | farmadep@gmail.com | 112863453968228411968 | ✅ | YT,Photos,Maps,Meet |
| 48 | Farmacia Ecce Homo | farmaeccehomo@gmail.com | 108305924420893637333 | — | — |
| 49 | Farmacia Nicosia | farmanicosia95@gmail.com | 102027433317368535394 | — | Photos,Meet |
| 50 | Farmacia Floridia | farm.floridia@gmail.com | 106236419601368566526 | — | Photos,Meet |
| 51 | Farmacia Guccione RG | farmguccione@gmail.com | 103666066590050697113 | ✅ | Maps,Meet |
| 52 | Farmacia Del Mare Sampieri | fdmsampieri@gmail.com | 111816055758357798799 | ✅ | Photos,Maps,Meet |
| 53 | Federfarma Ragusa | federfarmarg@gmail.com | 111679230766296148653 | ✅ | Maps,Meet |
| 54 | Farmacia Noto 2 | giunoto@gmail.com | 113851726409922234094 | — | — |
| 55 | Farmacia Veninata | luisa.veninata@gmail.com | 113709427135902219480 | — | YT,Photos,Maps,Meet |
| 56 | Farmacia Noto Cannizzo | marilisaca@gmail.com | 105730592817021475795 | ✅ | Meet,Maps |
| 57 | Farmacia Gulle | mirka04.70@gmail.com | 116600712653971738091 | — | YT,Photos,Maps,Meet |
| 58 | Farmacia Del Popolo di Ferro | info@farmaciaferro.com | 113980053832938888739 | ✅ | YT,Photos,Maps,Meet |
| 59 | Farmacia Roccasalva 2 | sabinaroccasalva63@gmail.com | 113471193496438758767 | ✅ | Photos,Maps,Meet |
| 60 | Farmacia Tavormina | vale.tavormina@gmail.com | 112543480155367286096 | ✅ | Photos,Maps,Meet |

Legenda servizi: YT = YouTube, Maps = Google Maps, Meet = Google Meet, Photos = Google Photos

---

## 6. Breach & Password Leak — Mosint

Mosint ha rilevato che circa **80 delle 104 email** (76.9%) sono presenti in breach database pubblici con password leak.

### 6.1 Tipologia breach

| Tipo | Descrizione |
|------|-------------|
| **Breach verificati** | Password esposte in leak pubblici (Collection #1, LinkedIn 2021, Adobe 2013, etc.) |
| **Piattaforme coinvolte** | Spotify, Twitter, Amazon, Office365, Adobe |
| **Rischio** | ALTO — credenziali in circolazione su dark web |

### 6.2 Implicazioni

> **Nota legale:** La presenza di queste email in breach database dimostra che gli indirizzi sono pubblici e circolano al di fuori del canale Federfarma. Alcune password leakate potrebbero essere le stesse usate per l'accesso a sistemi aziendali.

---

## 7. Tabella Completa — 103 Farmacie

| # | Stato | Farmacia | Email | Città | Fonte URL | Tipo Fonte |
|---|-------|----------|-------|-------|-----------|-----------|
| 1 | ✅ OK | Farmacia Guarino | farmacia.guarino71@gmail.com | Acate | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Acate-Farmacia%2520Guarino%2520Dottssa%2520Giovanna-5059621W.html) + [Facebook](https://www.facebook.com/profile.php?id=100069316614657) | directory + social |
| 2 | ✅ OK | Farmacia Puglisi Acate SRL | farmaciapuglisiacate@gmail.com | Acate | [Facebook](https://www.facebook.com/farmaciaPuglisi/) | social |
| 3 | ✅ OK | Farmacia Puglisi SRL | farmaciapuglisisrl@hotmail.com | Acate | [farmaciapuglisicomiso.it](https://farmaciapuglisicomiso.it/contatti) | sito ufficiale |
| 4 | ✅ OK | Farmacia Azzara e Garretto | farmazzaragarretto@tiscali.it | Chiaramonte Gulfi | [Facebook](https://www.facebook.com/) | social |
| 5 | ✅ OK | Farmacia Tavormina | farmaciatavormina@gmail.com | Chiaramonte Gulfi | [Facebook](https://www.facebook.com/Tavorminafarmacia/) | social |
| 6 | ✅ OK | Farmacia Adamo | info@farmaciadamonline.it | Comiso | [Facebook](https://www.facebook.com/Farmacia-Adamo-del-Dott-Antonio-Ferdinando-Salvo-1296811927051323/) | social |
| 7 | ❌ NO | Farmacia Albani | nuccioxxx@yahoo.it | Comiso | [Facebook](https://www.facebook.com/farmacia-Albani-Pedalino-105368476168259/) | social |
| 8 | ✅ OK | Farmacia Amato | farmaciaamatocomiso@gmail.com | Comiso | [farmaciaamato.it](https://farmaciaamato.it/) | sito ufficiale |
| 9 | ✅ OK | Farmacia Bocchetti | ebocchetti@farmaciabocchetti.it | Comiso | [farmaciabocchetti.it](https://www.farmaciabocchetti.it/) | sito ufficiale |
| 10 | ✅ OK | Farmacia Lauro di Incardona | incardona.farma@tiscali.it | Comiso | [farmaciaincardona.com](https://www.farmaciaincardona.com/contatti) | sito ufficiale |
| 11 | ✅ OK | Farmacia Noto 2 | giunoto@gmail.com | Comiso | [Facebook](https://www.facebook.com/) | social |
| 12 | ✅ OK | Farmacia Noto di Marilisa Cannizzo SRL | marilisaca@gmail.com | Comiso | [Facebook](https://www.facebook.com/farmacianotocomiso/) | social |
| 13 | ✅ OK | Farmacia Spataro SRL | farmaciaspatarocomiso@gmail.com | Comiso | [Facebook](https://www.facebook.com/) | social |
| 14 | ❌ NO | Farmacia Lauretta | farmacialauretta@gmail.com | Giarratana | — | non trovata |
| 15 | ✅ OK | Farmacia Aquiletta | farmaciaaquiletta@virgilio.it | Ispica | [Facebook](https://www.facebook.com/Farmacia-Aquiletta-Denaro-ispica) | social |
| 16 | ❌ NO | Farmacia Cassar Scalia | scaliaco@tiscali.it | Ispica | — | non trovata |
| 17 | ✅ OK | Farmacia Gerratana | fcia.gerratana@gmail.com | Ispica | [Facebook](https://www.facebook.com/farmaciagerratana) | social |
| 18 | ✅ OK | Farmacia Ispicenia | farmaciaispiceniasrl@gmail.com | Ispica | [Facebook](https://www.facebook.com/farmaciaispicenia) | social |
| 19 | ✅ OK | Farmacia Amore | amorefarmacia@tin.it | Modica | [detergentenaturale.com](https://www.detergentenaturale.com/punti-vendita-2/) | sito web |
| 20 | ✅ OK | Farmacia Del Mulino | farmaciadelmulino2013@gmail.com | Modica | [farmaciadelmulino.it](https://www.farmaciadelmulino.it/contatti/) | sito ufficiale |
| 21 | ✅ OK | Farmacia Floridia | farm.floridia@gmail.com | Modica | [farmaciafloridia.it](https://www.farmaciafloridia.it/) | sito ufficiale |
| 22 | ❌ NO | Farmacia G.E. Guccione | farmguccione@gmail.com | Modica | — | non trovata |
| 23 | ❌ NO | Farmacia Iaconinoto | a.iaconinoto@gmail.com | Modica | — | non trovata |
| 24 | ❌ NO | Farmacia Igea SNC | farmaciaigeamodica@gmail.com | Modica | — | non trovata |
| 25 | ❌ NO | Farmacia Mantegna | p.mantegna@tiscali.it | Modica | — | non trovata |
| 26 | ❌ NO | Farmacia Mediterraneo SRL | farmaciamediterraneosrl@gmail.com | Modica | — | non trovata |
| 27 | ✅ OK | Farmacia Michelica SRL | farmaciamichelica@gmail.com | Modica | [farmaciamichelica.it](https://www.farmaciamichelica.it/) | sito ufficiale |
| 28 | ✅ OK | Farmacia Montalbano Sgarlata SRL | montalbanosgarlata@farmapos.it | Modica | [farmaciadinamica.net](https://www.farmaciadinamica.net/farmacie/farmacia-dinamica-montalbano-sgarlata-modica/) | directory farmacia |
| 29 | ✅ OK | Farmacia Rizzone | farmaciarizzone@yahoo.it | Modica | [lemalo.it](https://lemalo.it/dove-fare-il-test/) | directory test |
| 30 | ✅ OK | Farmacia Roccasalva | sabinaroccasalva@virgilio.it | Modica | [lemalo.it](https://lemalo.it/dove-fare-il-test/) | directory test |
| 31 | ❌ NO | Farmacia Roccasalva 2 | sabinaroccasalva63@gmail.com | Modica | — | non trovata |
| 32 | ❌ NO | Farmacia Sacro Cuore Biopexor Group SRL | bioexorgroupsrl@gmail.com | Modica | — | non trovata |
| 33 | ✅ OK | Farmacia San Giorgio SRL | farmaciasangiorgiosrl@gmail.com | Modica | [farmaciasangiorgiomodica.it](https://www.farmaciasangiorgiomodica.it/) | sito ufficiale |
| 34 | ✅ OK | Farmacia Schiavo Lena | farmaciaschiavolena@gmail.com | Modica | [farmaciadinamica.net](https://www.farmaciadinamica.net/farmacie/farmacia-schiavo-lena/) | directory farmacia |
| 35 | ✅ OK | Farmacia Traina | farmaciatrainamodica@gmail.com | Modica | [farmaciadinamica.net](https://www.farmaciadinamica.net/farmacie/farmacia-traina/) | directory farmacia |
| 36 | ❌ NO | Farmacia Veninata | luisa.veninata@gmail.com | Modica | — | non trovata |
| 37 | ❌ NO | Farmacia Vindigni | farmaciavindigni@tim.it | Modica | — | non trovata |
| 38 | ✅ OK | Farmacia Gulle | farmaciagulle@gmail.com | Monterosso Almo | [Facebook](https://www.facebook.com/) | social |](https://farmacia-vicino-a-me.it/farmacia-vicino-a/monterosso-almo/farmacia-gulle-del-dr-nasca/) | directory |
| 39 | ✅ OK | Farmacia Costa | amministrazione@farmaciacostapozzallo.it | Pozzallo | [farmaciacostapozzallo.it](https://www.farmaciacostapozzallo.it/contatti.html) | sito ufficiale |
| 40 | ✅ OK | Farmacia Eredi Losi | farmalosi@libero.it | Pozzallo | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Pozzallo-Farmacia%2520Losi-1124145I.html) | directory |
| 41 | ✅ OK | Farmacia Maria Regina SRL | info@farmaciamariaregina.it | Pozzallo | [Facebook](https://www.facebook.com/Farmacia-Maria-Regina-Pozzallo-Dott-A-Addario-494844710555884/) | social |
| 42 | ✅ OK | Farmacia Papa Giovanni SRL | farmaciapapagiovannipozzallo@gmail.com | Pozzallo | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Pozzallo-Farmacia%2520Papa%2520Giovanni-4152415L.html) | directory |
| 43 | ✅ OK | Farmacia Quinta | quintafarmacia@virgilio.it | Pozzallo | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Pozzallo-Quinta%2520Farmacia-1381843J.html) | directory |
| 44 | ✅ OK | Farmacia Scalia | farmacia.scalia@gmail.com | Pozzallo | [Facebook](https://www.facebook.com/Farmacia-Scalia-Pozzallo) | social |
| 45 | ✅ OK | Farmacia Antoci | farmacia.antoci@gmail.com | Ragusa | [farmaciadinamica.net](https://www.farmaciadinamica.net/farmacie/farmacia-dinamica-antoci/) | directory farmacia |
| 46 | ✅ OK | Farmacia Basile | info@farmaciabasileragusa.it | Ragusa | [farmaciabasileragusa.it](https://www.farmaciabasileragusa.it/) | sito ufficiale |
| 47 | ✅ OK | Farmacia C. Ottaviano | concettaottaviano@alice.it | Ragusa | [ragusawelcome.com](https://www.ragusawelcome.com/it/scopri-ragusa/a-disposizione-dell-ospite/servizi/farmacia-dott-ssa-concetta-ottaviano) | sito turistico |
| 48 | ✅ OK | Farmacia Croce Verde | farmaciaparisirg@gmail.com | Ragusa | [farmaciacroceverde.it](https://farmaciacroceverde.it/) | sito ufficiale |
| 49 | ❌ NO | Farmacia Di Natale | farmaciadinatale@gmail.com | Ragusa | — | non trovata |
| 50 | ❌ NO | Farmacia Ecce Homo | farmaeccehomo@gmail.com | Ragusa | — | non trovata |
| 51 | ❌ NO | Farmacia Er. Meli | farmaciaeredimeli@virgilio.it | Ragusa | — | non trovata |
| 52 | ✅ OK | Farmacia Farma Salus SNC | farmaciasalusrg@gmail.com | Ragusa | [farmaciacasconerizza.it](https://www.farmaciacasconerizza.it/servizi/galenica/) | sito ufficiale |
| 53 | ❌ NO | Farmacia Gagini SNC | farmaciagagini@gmail.com | Ragusa | — | non trovata |
| 54 | ✅ OK | Farmacia Giampiccolo SRL | farmacia.giampiccololicitra@gmail.com | Ragusa | [alphega-farmacia.it](https://www.alphega-farmacia.it/farmacie/farmacia-giampiccolo-ragusa/) | sito ufficiale |
| 55 | ❌ NO | Farmacia Guccione RG | farmaciaguccione@gmail.com | Ragusa | — | non trovata |
| 56 | ✅ OK | Farmacia Matarazzo | farmacia.matarazzo@gmail.com | Ragusa | [farmaciamatarazzo.it](https://www.farmaciamatarazzo.it/) | sito ufficiale |
| 57 | ✅ OK | Farmacia Nicosia | farmanicosia95@gmail.com | Ragusa | [Facebook ufficiale](https://www.facebook.com/farmacianicosia.ragusa) | social |
| 58 | ❌ NO | Farmacia Occhipinti | farmaciaocchipinti@hotmail.it | Ragusa | — | non trovata |
| 59 | ✅ OK | Farmacia Ottaviano E. | emanueleottaviano.farmacia@gmail.com | Ragusa | [dermatologiainfarmacia.it](https://www.dermatologiainfarmacia.it/farmacia-dr-ottaviano-ragusa) | sito web |
| 60 | ❌ NO | Farmacia Ottaviano E. (2) | giova.trov@virgilio.it | Ragusa | — | non trovata |
| 61 | ❌ NO | Farmacia Ottaviano G. | ottaviano@tin.it | Ragusa | — | non trovata |
| 62 | ❌ NO | Farmacia Pianetti | giorgioaparo@hotmail.it | Ragusa | — | non trovata |
| 63 | ✅ OK | Farmacia Pianetti 1 | farmaciapianetti@gmail.com | Ragusa | [farmaciapianetti.it](https://farmaciapianetti.it/) | sito ufficiale |
| 64 | ❌ NO | Farmacia Poidomani | farmaciapoidomani@gmail.com | Ragusa | — | non trovata |
| 65 | ✅ OK | Farmacia Ragusa 22 | farmaciaragusa22srl@libero.it | Ragusa | [oraridiapertura24.it](https://www.oraridiapertura24.it/filiale/Ragusa-Farmacia%2520Ragusa%252022-2191608C.html) | directory farmacia |
| 66 | ❌ NO | Farmacia Ragusa 22 (2) | filippo.scarfalloto@alice.it | Ragusa | — | non trovata |
| 67 | ✅ OK | Farmacia Schembari Lucio & C. | lucio.schembari@tiscali.it | Ragusa | [farmaciaschembarilucio.it](https://farmaciaschembarilucio.it/) | sito ufficiale |
| 68 | ✅ OK | Farmacia Sciveres | m.sciveres@alice.it | Ragusa | [etic.travelnostop.com](https://etic.travelnostop.com/scheda_azienda.php?azienda=141181) | directory aziende |
| 69 | ✅ OK | Farmacia Via Falcone | farmaciaviafalconesnc@gmail.com | Ragusa | [farmaciaviafalconeragusa.it](https://farmaciaviafalconeragusa.it/contatti) | sito ufficiale |
| 70 | ❌ NO | Farmacia Via Falcone PEC | farmaciaviafalconesnc@pec.it | Ragusa | — | non trovata |
| 71 | ✅ OK | Farmacia Carnazzo | farmaciacarnazzo@gmail.com | S. Croce Camerina | [puntaseccalive.it](https://www.puntaseccalive.it/listing/farmacia-carnazzo/) | sito web |
| 72 | ✅ OK | Farmacia Schembari Giorgio & C. | farmaciaschembarigiorgio@gmail.com | S. Croce Camerina | [puntaseccalive.it](https://www.puntaseccalive.it/listing/farmacia-schembari/) | directory locale |
| 73 | ✅ OK | Farmacia Antica | anticaf@tin.it | Scicli | [facebook.com/anticafarmaciascicli](https://www.facebook.com/anticafarmaciascicli/) | social network |
| 74 | ✅ OK | Farmacia Cartia | farmaciacartia@gmail.com | Scicli | [farmaciadinamica.net](https://www.farmaciadinamica.net/farmacie/farmacia-cartia/) | directory farmacia |
| 75 | ✅ OK | Farmacia Comunale | farmacia.comunale@comune.scicli.rg.it | Scicli | [comune.scicli.rg.it](https://www.comune.scicli.rg.it/) | sito istituzionale |
| 76 | ✅ OK | Farmacia Criscione Donnalucata | chiara@farmaciadidonnalucata.com | Scicli | [farmaciadidonnalucata.com](https://www.farmaciadidonnalucata.com/) | sito ufficiale |
| 77 | ✅ OK | Farmacia Criscione Donnalucata | farmacia.donnalucata@gmail.com | Scicli | [farmaciadinamica.net](https://www.farmaciadinamica.net/farmacie/farmacia-criscione/) | directory farmacia |
| 78 | ❌ NO | Farmacia Pacetto | farmaciapacetto.amministrazione@gmail.com | Scicli | — | non trovata |
| 79 | ✅ OK | Farmacia Papaleo SAS | farmaciapapaleosnc@gmail.com | Scicli | [facebook.com/FarmaciaPapaleo](https://www.facebook.com/FarmaciaPapaleo/) | social network |
| 80 | ✅ OK | Farmacia del Mare Sampieri | fdmsampieri@gmail.com | Scicli | [farmaciadinamica.net](https://www.farmaciadinamica.net/farmacie/farmacia-del-mare/) | directory farmacia |
| 81 | ✅ OK | Farmacia del Popolo di Ferro | info@farmaciaferro.com | Scicli | [farmaciaferro.com](https://www.farmaciaferro.com/) | sito ufficiale |
| 82 | ❌ NO | Farmacia Del Mare | farmaciadelmarerg@gmail.com | Scoglitti | — | non trovata |
| 83 | ❌ NO | Farmacia I. Iacono | ivana.iacono@alice.it | Scoglitti | — | non trovata |
| 84 | ✅ OK | Farmacia Amica SRL | farmaciamicasrl@gmail.com | Vittoria | [valoresalute.it](https://ordinionline.valoresalute.it/farmacie/amica-srl/290328) | sito web |
| 85 | ✅ OK | Farmacia Bianculli | biancullifarmacia@gmail.com | Vittoria | [farmaciadinamica.net](https://www.farmaciadinamica.net/farmacie/farmacia-bianculli-dr-luigi/) | directory farmacia |
| 86 | ✅ OK | Farmacia Cali | farmacista.farmacali@outlook.com | Vittoria | [Facebook](https://www.facebook.com/) | social |
| 87 | ✅ OK | Farmacia Cannizzo | farmaciacannizzoelsamaria@virgilio.it | Vittoria | [Facebook](https://www.facebook.com/) | social |
| 89 | ✅ OK | Farmacia De Pasquale | farmadep@gmail.com | Vittoria | [farmaciadepasquale.com](https://farmaciadepasquale.com/contatti) | sito ufficiale |
| 90 | ❌ NO | Farmacia Emaia | farmacia.emaia@virgilio.it | Vittoria | — | non trovata |
| 91 | ✅ OK | Farmacia Guastella SNC | info@farmaciaguastella.com | Vittoria | [Facebook](https://www.facebook.com/) | social |
| 92 | ✅ OK | Farmacia Iacono G.A. | info@farmaciajacono.it | Vittoria | [Facebook](https://www.facebook.com/) | social |
| 93 | ✅ OK | Farmacia Incardona Luigi | incardona.farma@tiscali.it | Vittoria | [Facebook](https://www.facebook.com/) | social |
| 94 | ❌ NO | Farmacia Mangione | gl85@msn.com | Vittoria | — | non trovata |
| 95 | ✅ OK | Farmacia Mangione 2 | farmaciamangionerg@gmail.com | Vittoria | [Facebook](https://www.facebook.com/) | social |
| 97 | ✅ OK | Farmacia Michele Arcangelo SRL | farmacia.michelearcangelo90@gmail.com | Vittoria | [farmaciamichelearcangelo.it](https://farmaciamichelearcangelo.it/policies/contact-information) | sito ufficiale |
| 98 | ❌ NO | Farmacia Pelligra | farmainca@libero.it | Vittoria | — | non trovata |
| 99 | ✅ OK | Farmacia Roma | farmaciaromavittoria@gmail.com | Vittoria | [Facebook](https://www.facebook.com/) | social |
| 100 | ✅ OK | Farmacia Roma 2 | circolarifarmaroma@gmail.com | Vittoria | [farmaciadinamica.net](https://www.farmaciadinamica.net/farmacie/farmacia-roma-2/) | directory farmacia |
| 101 | ❌ NO | Farmacia Spiteri | consolataspiteri@gmail.com | Vittoria | — | non trovata |
| 102 | ✅ OK | Farmacia Vittoria 15 | farmaciavittoria15@gmail.com | Vittoria | [Facebook](https://www.facebook.com/) | social |

---

## 8. Statistiche per Città

| Città | Totale | Fonte Online | % | GHunt OK |
|-------|--------|-------------|---|---------|
| Acate | 3 | 3 | **100%** | 2/2 |
| Chiaramonte Gulfi | 2 | 2 | **100%** | 1/1 |
| Comiso | 8 | 7 | 88% | 3/4 |
| Giarratana | 1 | 0 | 0% | 1/1 |
| Ispica | 4 | 3 | 75% | 1/2 |
| Modica | 19 | 14 | 74% | 13/13 |
| Monterosso Almo | 1 | 1 | **100%** | 1/1 |
| Pozzallo | 6 | 6 | **100%** | 0/2 |
| Ragusa | 26 | 14 | 54% | 16/16 |
| S. Croce Camerina | 2 | 2 | 100% | 2/2 |
| Scicli | 10 | 8 | 80% | 6/5 |
| Scoglitti | 2 | 0 | 0% | 0/0 |
| Vittoria | 17 | 17 | 100% | 12/12 |

**Aggiornamento 2026-07-13 (FB utente):** +11 fonti verificate dall'utente su Facebook (Vittoria +8, Comiso +2, Chiaramonte Gulfi +1).
**Aggiornamento 2026-07-13 (sesta tornata):** +1 fonte (Farmacia Sciveres su ETIC travelnostop). Totale fonti online: **56 su 103 (54.4%)**.

---

## 9. Dettaglio GHunt — 60 Gmail

Per ogni Gmail, GHunt ha estratto:
- **Gaia ID** — Identificativo univoco Google
- **Foto profilo** — URL pubblico della foto (93×93 px)
- **Maps Profile** — Link alle recensioni Google Maps
- **Servizi attivi** — YouTube, Photos, Maps, Meet, etc.
- **Calendar pubblico** — Se presente
- **Recensioni Maps** — Numero di recensioni pubblicate

Vedi report completo in `RAPPORTO_GHUNT_FARMACIE_RG.md` per i dettagli completi di ogni Gmail.

---

## 10. Appendice: Note Tecniche

### 10.1 Strumenti

- **Holehe v1.61:** Verifica asincrona su 121 piattaforme senza notifiche all'utente
- **Blackbird:** Verifica su 16 piattaforme con API Adobe per avatar pubblici
- **Mosint v3.0:** Scansione breach via HaveIBeenPwned API + Google dorking
- **GHunt 2.3.4:** People API + Maps API + Calendar API + Play Games API
- **theHarvester v4.11.1:** Scansione motori di ricerca per email aziendali

### 10.2 Limitazioni

- **55 farmacie senza fonte web** — La mancanza di email pubblica sul web NON significa che l'email non sia pubblica, ma solo che non è indicizzata sui canali verificati
- **Blackbird** — Include piattaforme come Xvideos e Duolingo che sono siti pubblici (l'account esiste)
- **Mosint breach** — I leak includono dati reali; ~80 email risultano esposte
- **GHunt** — Richiede cookies Google validi; funziona solo su Gmail (60 su 104)

### 10.3 File sorgente

- **Lista originale:** `REFERENZA_FONTI.md` (da backup farmacia)
- **CSF completo:** `farmacie_con_fonti_online.csv`
- **Report Holehe/Mosint:** `RAPPORTO_OSINT_FARMACIE_RG.md`
- **Report GHunt:** `RAPPORTO_GHUNT_FARMACIE_RG.md`

### 10.4 Evidenze chiave

1. **Tutte le 104 email** sono documentate da Federfarma Ragusa — fonte primaria
2. **42 farmacie** hanno la propria email pubblicata su siti web/directory
3. **59 su 60 Gmail** hanno un account Google attivo — verificato con GHunt
4. **46 email** hanno account su piattaforme pubbliche (Adobe, Spotify, Twitter, Xvideos)
5. **~80 email** risultano in breach database con password leak

---

*Fine dossier. Generato il 2026-07-07 da OSINT workflow: Holehe + Mosint + Blackbird + GHunt + theHarvester + web search.*
