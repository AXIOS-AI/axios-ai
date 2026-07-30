#!/usr/bin/env python3
"""
scopri-farmacie.py — Scopre domini farmacie online via Google Shopping
======================================================================
Cerca centinaia di farmaci OTC/SOP su Google Shopping (SearchAPI.io),
estrae i venditori dai risultati, deduplica per dominio.

Questo bypassa il blocco Gcore/Cloudflare dei siti AIFA e Ministero Salute,
usando direttamente i risultati di Google Shopping come fonte di scoperta.

Usage:
  python3 scopri-farmacie.py                    # Scan completo (~500 farmaci)
  python3 scopri-farmacie.py --rapido            # Scan rapido (~50 farmaci top)
  python3 scopri-farmacie.py --output nuovi_domini.txt

Dipendenze: pip install requests
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("[!] pip install requests")
    sys.exit(1)

VERSION = "1.0.0"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# ─── Lista farmaci OTC/SOP più cercati ──────────────

FARMACI_OTC = [
    # Antidolorifici / Antinfiammatori
    "Tachipirina 1000", "Tachipirina 500", "Oki task", "Moment 400",
    "Moment 200", "Brufen 600", "Brufen 400", "Aspirina C",
    "Aspirina 500", "Ibuprofene 400", "Ibuprofene 600", "Ketodol",
    "Aulin", "Nimis", "Articol", "Voltaren emulgel", "Fastum gel",
    "Lasonil", "Ketoprofene", "Dicloreum", "Muscoril",
    "Buscofen", "Spedifen 400", "Spedifen 600", "Enantyum",
    # Raffreddore / Tosse / Mal di gola
    "Vicks Medinait", "Neoborocillina", "Borocillina", "Bronchenolo",
    "Fluifort", "Fluimucil", "Mucosolvan", "Bisolvon",
    "Actigrip", "Benagol", "Lysopaïne", "Deltariv",
    "Aircort", "Pulmaxan", "Ventolin", "Clenil",
    # Antistaminici / Allergia
    "Zirtec", "Xyzal", "Clarityn", "Neoclarityn", "Aerius",
    "Rupafin", "Bilaxten", "Fexallegra", "Kestin", "Tinset",
    # Antibiotici (uso comune)
    "Augmentin", "Zimox", "Amoxicillina", "Ciprofloxacina",
    "Azitromicina", "Klacid", "Levofloxacina", "Doxiciclina",
    # Stomaco / Intestino
    "Maalox", "Maalox plus", "Gaviscon", "Citrosoda",
    "Milk of Magnesia", "Brioschi", "Enterogermina", "Lactoflorene",
    "Normix", "Dissenten", "Imodium", "Lopemid",
    "Omeprazolo", "Pantoprazolo", "Lansoprazolo", "Esomeprazolo",
    "Riopan", "Levocetirizina", "Plasil", "Peridon",
    # Lassativi
    "Pursennid", "Senna", "Lactulose", "Macrogol", "Movicol",
    "Duphalac", "Dulcolax", "Microlax", "Difesan", "Eucarbon",
    # Integratori / Vitamine
    "Polase", "Polase 60", "Magnesio Supremo", "Magnesio OK", "Cardioaspirina",
    "Acido Folico", "Ferrograd", "Ferroplex", "Sideral", "Trofovit",
    "Supradyn", "Multicentrum", "Becozym", "Cebion", "Redoxon",
    "Vitamina C 1000", "Vitamina D 2000", "Vitamina B12",
    "Omega 3 1000", "Omega 3 2000", "Olio di Krill",
    # Prodotti per la prostata
    "Prostamol 60", "Prostamol 30", "Prostamol 90", "Serenoa Repens",
    "Permixon", "Prostarex", "Difaprost", "Profluss", "Uriprinax",
    "Avodart", "Zoxon", "Omix", "Xatral",
    # Sonno / Ansia / Stress
    "Gotal", "Gotal 30", "Esilgan", "Esilgan 30", "Tavor",
    "Lexotan", "Valium", "Xanax", "En", "Lorazepam",
    "Melatonina 1mg", "Melatonina 5mg", "Cerea", "Tensolan",
    "Biancaneve", "Impromen", "Citalopram", "Sertralina",
    # Problemi di erezione
    "Cialis 5mg", "Cialis 20mg", "Viagra 50mg", "Viagra 100mg",
    "Levitra", "Spedra", "Tadalfil", "Sildenafil", "Vardenafil",
    # Oculari
    "Alfa Intes", "Netildex", "Tobradex", "VisuXL", "Hyabak",
    "Artelac", "Blu-Yal", "Optive", "Systane", "Oftacilox",
    # Dermatologici
    "Micosil", "Canesoral", "Daktarin", "Fungoral", "Lamisl",
    "Clobesol", "Locoidon", "Betacort", "Betanex", "Avena sativa",
    "Aciclovir crema", "Zovirax", "Sali di Schussler", "Epitelin",
    # Omeopatici / Naturali
    "Oscillococcinum", "Boiron", "Traumeel", "Arnica Montana",
    "Echinacea", "Propoli", "Erisimo", "Sambuco", "Zinco 10",
    # Varie
    "Bepanthenol", "Bepanthenol crema", "Aknecolor", "Chlorophyll",
    "Valeriana", "Passiflora", "Biancospino", "Griffonia",
    "Carnitina", "Creatina", "Taurina", "Ginseng", "Guaranà",
    "Ketos", "Xls Medical", "Alli", "Farmaci dimagranti",
    # Benessere sessuale
    "Lubrificante", "Preservativi", "Durex", "Skyn",
    # Prima infanzia
    "Nurofen bambini", "Tachipirina bambini", "Achillea bambini",
    "Bepanthenol bambini", "Babygella", "Pampers",
    # Test diagnostici
    "Test gravidanza", "Test ovulazione", "Clearblue",
    "Glutell", "Accu-Chek", "Contour", "OneTouch",
    # Cura della pelle
    "Bioderma", "Avène", "La Roche-Posay", "Vichy", "Ceramol",
    "Dermovitamina", "Neoviderm", "Dermovitamina", "Topicrem",
]

FARMACI_RAPIDI = [
    "Tachipirina 1000", "Oki task", "Moment 400", "Brufen 600",
    "Aspirina C", "Mucosolvan", "Zirtec", "Maalox", "Normix",
    "Pursennid", "Polase", "Magnesio Supremo", "Prostamol 60",
    "Cardioaspirina", "Ferrograd", "Gotal", "Melatonina 5mg",
    "Augmentin", "Cialis 5mg", "Viagra 50mg", "Tobradex",
    "Micosil", "Voltaren emulgel", "Vicks Medinait",
    "Enterogermina", "Supradyn", "Acido Folico", "Bepanthenol",
    "Oscillococcinum", "Nurofen bambini", "Test gravidanza",
]


# ─── Utility ────────────────────────────────────────

def log(msg, level="+"):
    c = {"+": "\033[92m", "-": "\033[93m", "!": "\033[91m", "*": "\033[94m", "~": "\033[96m"}
    print(f"  {c.get(level, '')}[{level}]\033[0m {msg}")


def load_env():
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def estrai_dominio(url):
    if not url:
        return ""
    parsed = urlparse(url)
    dom = parsed.netloc.lower()
    # Rimuovi www.
    if dom.startswith("www."):
        dom = dom[4:]
    return dom


def carica_domini_esistenti():
    """Carica domini già presenti in siti.md e database."""
    domini = set()
    siti_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "siti.md")
    if os.path.exists(siti_path):
        with open(siti_path) as f:
            for line in f:
                line = line.strip()
                # formato: "- https://www.dominio.it" o "https://dominio.it"
                if "https://" in line:
                    url = line[line.index("https://"):].rstrip("/")
                    dom = estrai_dominio(url)
                    if dom:
                        domini.add(dom)
    log(f"Domini esistenti in siti.md: {len(domini)}", "+")
    return domini


# ─── Google Shopping Discovery ──────────────────────

def cerca_google_shopping(farmaco, api_key):
    """Cerca su Google Shopping via SearchAPI.io, restituisce lista venditori."""
    try:
        r = requests.get("https://www.searchapi.io/api/v1/search", params={
            "engine": "google_shopping",
            "q": farmaco,
            "gl": "it",
            "hl": "it",
            "api_key": api_key,
        }, timeout=15)
        if r.status_code == 200:
            data = r.json()
            venditori = set()
            shopping = data.get("shopping_results", [])
            for s in shopping:
                link = s.get("link", "") or ""
                dom = estrai_dominio(link)
                if dom and dom not in ("", "google.com", "google.it"):
                    venditori.add(dom)
                # seller field può avere anche il nome del venditore senza link
                seller = s.get("seller", "") or ""
                # Se seller sembra un dominio, lo aggiungiamo
                if "." in seller and " " not in seller:
                    seller_dom = seller.lower().strip()
                    # Rimuovi https:// se presente
                    seller_dom = seller_dom.replace("https://", "").replace("http://", "")
                    seller_dom = seller_dom.rstrip("/")
                    if seller_dom and seller_dom not in ("google.com", "google.it"):
                        venditori.add(seller_dom)
            return venditori, len(shopping)
    except Exception as e:
        log(f"Errore SearchAPI: {str(e)[:80]}", "!")
    return set(), 0


# ─── Filtraggio ─────────────────────────────────────

SKIP_DOMINI = {
    "google.com", "google.it", "youtube.com", "facebook.com", "instagram.com",
    "amazon.com", "amazon.it", "ebay.com", "ebay.it", "subito.it",
    "trovaprezzi.it", "prezzifarmaco.it", "doveconviene.it",
    "my-personaltrainer.it", "torrinomedica.it", "farmacoecura.it",
    "medicinali.info", "dica33.it", "farmacovigilanza.eu", "farmacisteria.it",
    "paginemediche.it", "farmasalute.it", "milanofarma.it",
    "humanitas.it", "grupposandonato.it", "clinicacastelli.it",
    # Marketplace / aggregator — non farmacie dirette
    "shop-apotheke.com", "shop-apotheke.it", "disapo.de",
    "sanicare.it", "medpex.de", "eurapon.de", "apotal.de",
    "shopmed.com", "onlinepharmacy.com",
}

TERMINI_FARMACIA = [
    "farmacia", "farma", "pharma", "apoteca", "parafarmacia",
    "farmacie", "wellness", "salute", "sanita", "cura",
    "farmaco", "farmaci", "dottore", "medicina", "medicinali",
    "benessere", "naturale", "erboristeria",
]


def e_dominio_farmacia(dom):
    """Controlla se il dominio sembra una farmacia."""
    if dom in SKIP_DOMINI:
        return False
    # Marketplace grandi vanno sempre presi (hanno sezioni farmacia)
    if dom in ("amazon.it", "ebay.it"):
        return True
    for k in TERMINI_FARMACIA:
        if k in dom:
            return True
    return False


# ─── Main ───────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="scopri-farmacie — Scopre domini farmacie online via Google Shopping"
    )
    parser.add_argument("--rapido", action="store_true", help="Scan rapido (~50 farmaci top)")
    parser.add_argument("--output", "-o", help="File output nuovi domini", default="")
    parser.add_argument("--solo-nuovi", action="store_true", help="Mostra solo nuovi domini (non in siti.md)")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay tra query (default 1.5s)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostra tutti i risultati query")

    args = parser.parse_args()

    load_env()
    api_key = os.environ.get("SEARCHAPI_KEY", "")
    if not api_key:
        log("SEARCHAPI_KEY non trovata in .env!", "!")
        sys.exit(1)

    farmaci = FARMACI_RAPIDI if args.rapido else FARMACI_OTC
    log(f"{'='*60}")
    log(f"SCOPRI-FARMACIE v{VERSION}")
    log(f"Modalità: {'RAPIDO' if args.rapido else 'COMPLETO'}")
    log(f"Farmaci da cercare: {len(farmaci)}")
    log(f"API Key: {api_key[:6]}...{api_key[-4:]}")
    log(f"{'='*60}")

    # Carica domini esistenti
    domini_esistenti = carica_domini_esistenti()

    # Scopri nuovi domini
    tutti_venditori = {}  # dominio -> {farmaci: [], totale_annunci: N}

    for i, farmaco in enumerate(farmaci):
        log(f"\n[{i+1}/{len(farmaci)}] {farmaco}", "*")
        venditori, n_annunci = cerca_google_shopping(farmaco, api_key)

        if not venditori:
            log(f"  Nessun venditore trovato", "-")
        else:
            # Filtra domini interessanti
            nuovi = 0
            for dom in sorted(venditori):
                if dom not in tutti_venditori:
                    tutti_venditori[dom] = {"farmaci": [], "totale_annunci": 0}
                tutti_venditori[dom]["farmaci"].append(farmaco)
                tutti_venditori[dom]["totale_annunci"] += n_annunci
                if dom not in domini_esistenti:
                    nuovi += 1

            if args.verbose or nuovi > 0:
                log(f"  Venditori: {len(venditori)}, nuovi: {nuovi}", "+")
                if args.verbose:
                    for dom in sorted(venditori):
                        gia_presente = "✓" if dom in domini_esistenti else "●"
                        tipo = "🏥" if e_dominio_farmacia(dom) else "🌐"
                        log(f"    {tipo} {gia_presente} {dom}", "~")

        # Delay tra query
        if i < len(farmaci) - 1:
            time.sleep(args.delay)

    # ─── Report finale ──────────────────────────────

    log(f"\n{'='*60}")
    log(f"✅ SCAN COMPLETATO", "+")
    log(f"{'='*60}")

    # Classifica per numero di farmaci trovati
    domini_ordinati = sorted(tutti_venditori.items(),
                              key=lambda x: len(x[1]["farmaci"]), reverse=True)

    # Separa farmacie da altri
    farmacie = [(d, v) for d, v in domini_ordinati if e_dominio_farmacia(d)]
    altri = [(d, v) for d, v in domini_ordinati if not e_dominio_farmacia(d)]
    nuovi_farmacie = [(d, v) for d, v in farmacie if d not in domini_esistenti]
    nuovi_altri = [(d, v) for d, v in altri if d not in domini_esistenti]

    log(f"\n📊 RIEPILOGO:", "*")
    log(f"  Totale domini unici scoperti: {len(tutti_venditori)}", "+")
    log(f"  Di cui farmacie/parafarmacie: {len(farmacie)}", "+")
    log(f"  Di cui altri siti: {len(altri)}", "+")
    log(f"  NUOVI domini farmacia: {len(nuovi_farmacie)}", "~")
    log(f"  NUOVI altri domini: {len(nuovi_altri)}", "~")

    if farmacie:
        log(f"\n{'─'*60}", "*")
        log(f"  🏥 FARMACIE E PARAFARMACIE ({len(farmacie)})", "*")
        log(f"{'─'*60}", "*")
        for dom, info in farmacie:
            nuovo = "🆕" if dom not in domini_esistenti else "  "
            # Mostra primi 3 farmaci come esempio
            esempi = info["farmaci"][:3]
            altri_n = len(info["farmaci"]) - 3
            if altri_n > 0:
                esempi_str = ", ".join(esempi) + f" e altri {altri_n}"
            else:
                esempi_str = ", ".join(esempi)
            log(f"    {nuovo} {dom}", "~")
            log(f"         {len(info['farmaci'])} farmaci: {esempi_str}", "-")
            # Aggiungi a siti.md (solo nuove farmacie)
            if dom not in domini_esistenti:
                domini_esistenti.add(dom)

    if altri:
        log(f"\n{'─'*60}", "*")
        log(f"  🌐 ALTRI SITI ({len(altri)})", "*")
        log(f"{'─'*60}", "*")
        for dom, info in altri[:10]:  # Mostra solo top 10
            nuovo = "🆕" if dom not in domini_esistenti else "  "
            esempi = info["farmaci"][:2]
            log(f"    {nuovo} {dom} — {len(info['farmaci'])} farmaci", "-")
            log(f"         esempio: {', '.join(esempi)}", "-")

    # Salva output
    output_path = args.output
    if not output_path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = "rapido" if args.rapido else "completo"
        output_path = f"domini_scoperti_{mode}_{ts}.json"

    output_data = {
        "timestamp": datetime.now().isoformat(),
        "versione": VERSION,
        "modalita": "rapido" if args.rapido else "completo",
        "farmaci_cercati": len(farmaci),
        "domini_trovati": len(tutti_venditori),
        "farmacie": [
            {
                "dominio": d,
                "nuovo": d not in domini_esistenti,
                "farmaci_trovati": len(v["farmaci"]),
                "esempi_farmaci": v["farmaci"][:5],
            }
            for d, v in farmacie
        ],
        "altri_siti": [
            {
                "dominio": d,
                "farmaci_trovati": len(v["farmaci"]),
            }
            for d, v in altri[:20]
        ],
        "farmaci_non_trovati": [],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    log(f"\n📄 Output salvato: {output_path}", "+")

    # Suggerisci prossimo step
    if nuovi_farmacie:
        log(f"\n{'='*60}", "*")
        log(f"  📋 PROSSIMI STEP CONSIGLIATI:", "*")
        log(f"{'='*60}", "*")
        log(f"  1. Aggiungi nuovi domini a siti.md", "~")
        log(f"     python3 -c \"import sys; sys.path.insert(0, '.'); exec(open('siti.md').read().replace('#',''))\"", "-")
        log(f"  2. Rigenera indice prezzi con nuovi domini:", "~")
        log(f"     python3 crawler-indice.py --workers 3", "~")
        log(f"  3. Test su un farmaco:", "~")
        log(f"     python3 compara-offerte.py \"Prostamol 60\"", "~")
    log()

    return output_data


if __name__ == "__main__":
    main()