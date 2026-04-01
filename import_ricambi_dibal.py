#!/usr/bin/env python
"""
Script to import Dibal spare parts from PDF into the database.
Extracts data from 'listino ricambi cs 1200 (1).pdf' and populates the ricambi table.
"""

import re
from app import create_app, db
from app.models.ricambio import Ricambio

# Parsed data from PDF
RICAMBI_DATA = [
    # Page 1 - CS-1200W-2200 STMP 2" Gruppo stampante
    {"codice": "BI1054C", "descrizione": "Kit Stampante completa", "prezzo": 396.00, "modello": "CS-1200W-2200"},
    {"codice": "BH-KF2002GR", "descrizione": "Testina Termica 2\"", "prezzo": 144.00, "modello": "CS-1200W-2200"},
    {"codice": "BL-PM35S", "descrizione": "Motore carta", "prezzo": 36.00, "modello": "CS-1200W-2200"},
    {"codice": "49-1673", "descrizione": "Motore Riavvolgitore con pignone", "prezzo": 21.60, "modello": "CS-1200W-2200"},
    {"codice": "49-2495", "descrizione": "Kit Boccole", "prezzo": 8.40, "modello": "CS-1200W-2200"},
    {"codice": "49-2493", "descrizione": "Kit Molle stampante", "prezzo": 8.40, "modello": "CS-1200W-2200"},
    {"codice": "BCES0052", "descrizione": "Kit puleggie Stampante", "prezzo": 9.60, "modello": "CS-1200W-2200"},
    {"codice": "4505014053", "descrizione": "Sensore carta digital", "prezzo": 27.60, "modello": "CS-1200W-2200"},
    {"codice": "BK-M1109", "descrizione": "Rullo gommato", "prezzo": 19.20, "modello": "CS-1200W-2200"},
    {"codice": "BL-C1589", "descrizione": "Tagliacarta", "prezzo": 5.40, "modello": "CS-1200W-2200"},
    
    # CS-2200 W FLAT 12+7 3" Gruppo Stampante
    {"codice": "495943E", "descrizione": "Kit Stampante completa", "prezzo": 396.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BEV91", "descrizione": "Testina termica 3\"", "prezzo": 192.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "WI297AAA", "descrizione": "Sensore carta completo", "prezzo": 33.60, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BE-P5399", "descrizione": "Maniglia di apertura", "prezzo": 7.20, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "495649A", "descrizione": "Gruppo motore pignone avvolgicarta", "prezzo": 54.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "WI300AAA", "descrizione": "Motore passo passo stampante termica", "prezzo": 132.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BE-M1512", "descrizione": "Rullo gommato", "prezzo": 36.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BE-P5400", "descrizione": "Regolatore larghezza rotolo", "prezzo": 7.20, "modello": "CS-2200 W FLAT 12+7 3\""},
    
    # Elettronica
    {"codice": "BCZ95B", "descrizione": "CPU INTEL CELERON N3060 MS-98F1 EMC", "prezzo": 504.00, "modello": "CS 1200 W"},
    {"codice": "BI1054C", "descrizione": "CPU MS-98I0 HDMI 2XLAN N3161", "prezzo": 372.00, "modello": "CS-2200"},
    {"codice": "496838B", "descrizione": "KIT DISCO SSD 128GB ALTEC CON SUPPORTO", "prezzo": 204.00, "modello": "CS1200 W"},
    {"codice": "BI0921", "descrizione": "Msata / 128GB / 3D TLC", "prezzo": 130.80, "modello": "CS-2200"},
    {"codice": "BEV45", "descrizione": "RAM 4 Gb", "prezzo": 66.00, "modello": "CS-1200W-2200"},
    {"codice": "4517004092", "descrizione": "Scheda Raccordo 12V 5 Ah CS1200", "prezzo": 118.80, "modello": "CS 1200 W"},
    {"codice": "4517004101", "descrizione": "Scheda Raccordo 12V 5 Ah CS2200", "prezzo": 118.80, "modello": "CS-2200"},
    {"codice": "4511020001", "descrizione": "Alimentatore WS/CL3", "prezzo": 294.00, "modello": "CS-1200W-2200"},
    {"codice": "4511016027T", "descrizione": "Convertitore Peso JavaPos", "prezzo": 264.00, "modello": "CS-1200W-2200"},
    {"codice": "45110170B13", "descrizione": "Controllo Stampante 2\"", "prezzo": 189.60, "modello": "CS-1200W-2200"},
    {"codice": "BC-F243", "descrizione": "Cella di carico pw2cc3 6/15kg 3000 div", "prezzo": 90.00, "modello": "CS-1200W-2200"},
    {"codice": "BC-F284", "descrizione": "Cella di carico pw2cc6 12 kg o 30 kg 6000 div", "prezzo": 111.60, "modello": "CS-1200W-2200"},
    {"codice": "493715A", "descrizione": "Filtro rete 2 Ah", "prezzo": 43.20, "modello": "CS-1200W-2200"},
    {"codice": "BL-P5637V", "descrizione": "Protezione Alimentatore", "prezzo": 21.60, "modello": "CS-1200W-2200"},
    {"codice": "BI1196", "descrizione": "Scheda Controllo TOUCH-CPU", "prezzo": 56.40, "modello": "CS-1200W-2200"},
    {"codice": "BI1007A", "descrizione": "LVDS converter HDMI", "prezzo": 42.00, "modello": "CS-2200"},
    
    # Monitor Operatore CS-1200W -2200 15+15
    {"codice": "BI1195", "descrizione": "Monitor Touch TFT 15 completo", "prezzo": 360.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BI0684", "descrizione": "Monitor TFT 15\"", "prezzo": 276.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P5106VMG4", "descrizione": "Cover monitor 15\"", "prezzo": 69.60, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P5478BVMG6", "descrizione": "Cover monitor 15\" (Cliente)", "prezzo": 90.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P5227", "descrizione": "Protezione monitor 15\"", "prezzo": 33.60, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P5202VNP", "descrizione": "Cornice monitor TFT 15\"", "prezzo": 36.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-C2445C", "descrizione": "Staffa di supporto monitor colonna", "prezzo": 10.80, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-C2444E", "descrizione": "Supporto monitor 15\" OPE", "prezzo": 56.40, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P5107VG6", "descrizione": "Tappo monitor self service", "prezzo": 18.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P3273", "descrizione": "Adesivo monitor self service", "prezzo": 3.60, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-C2463EG4", "descrizione": "Supporto carcassa monitor 15\" CLI", "prezzo": 42.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-C2462BG4", "descrizione": "Aggancio per supporto monitor 15\" CLI", "prezzo": 30.00, "modello": "CS-1200W -2200 15+15"},
    
    # Monitor CS-2200 W FLAT 12+7 3"
    {"codice": "BI0940", "descrizione": "Monitor touch completo 12\"", "prezzo": 336.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-P5644G", "descrizione": "Cover TFT 12\"", "prezzo": 30.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-C2781", "descrizione": "Supporto TFT", "prezzo": 90.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-P5606", "descrizione": "Protezione monitor 12\"", "prezzo": 38.40, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-P5645N", "descrizione": "Telaio TFT 12\"", "prezzo": 24.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-P5646N", "descrizione": "Supporto interno TFT", "prezzo": 14.40, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-P5695", "descrizione": "Vetro TFT 7\"", "prezzo": 18.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-P5692VNP", "descrizione": "Cornice TFT 7\"", "prezzo": 22.80, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-P5693VG6", "descrizione": "Coperchio posteriore TFT 7\"", "prezzo": 27.60, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BI0798A", "descrizione": "Monitor TFT 7\"", "prezzo": 198.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    
    # Monitor P.I 15+15
    {"codice": "BL-C2478C", "descrizione": "Cover TFT 15\" lato OP", "prezzo": 132.00, "modello": "CS-1200W-2200 P.I 15+15"},
    {"codice": "BL-C2479", "descrizione": "Cover TFT 15\"", "prezzo": 144.00, "modello": "CS-1200W-2200 P.I 15+15"},
    {"codice": "BL-C2485B", "descrizione": "Supporto TFT 15\" (Operatore)", "prezzo": 36.00, "modello": "CS-1200W-2200 P.I 15+15"},
    {"codice": "BL-C2919", "descrizione": "Supporto TFT 15\" (Cliente)", "prezzo": 46.80, "modello": "CS-1200W-2200 P.I 15+15"},
    
    # Carrozzeria CS-1200W -2200 15+15
    {"codice": "BU-C1229", "descrizione": "Piatto Piano inox con astina", "prezzo": 54.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "49-1321", "descrizione": "Crociera piatto completa di rondelle in gomma", "prezzo": 45.60, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BU-P1011", "descrizione": "Rondella in gomma per crociera piatto", "prezzo": 2.40, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P3141N", "descrizione": "Tappo copertura viti carcassa sottopiatto", "prezzo": 2.40, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P4260VG4", "descrizione": "Tappo Frontale grigio stampante", "prezzo": 60.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P4258VFG4", "descrizione": "Carcassa sottopiatto", "prezzo": 90.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-F1232", "descrizione": "Colonna Alluminio", "prezzo": 58.80, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BCES0003VEG6", "descrizione": "Pulsante sgancio cassetto con leva", "prezzo": 36.00, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-F1121C", "descrizione": "Sgancio cassetto stampante", "prezzo": 9.60, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BCES0086", "descrizione": "Piedino con controdado", "prezzo": 7.20, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-C1642", "descrizione": "Molla di Sgancio cassetto", "prezzo": 3.60, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BCES0005", "descrizione": "Coperchio Scheda Raccordo Stampante", "prezzo": 10.80, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BL-P5798", "descrizione": "Protezione Stampante", "prezzo": 8.40, "modello": "CS-1200W -2200 15+15"},
    {"codice": "BCES0054B", "descrizione": "Meccanica con guida su cuscinetti cassetto", "prezzo": 174.00, "modello": "CS-1200W -2200 15+15"},
    
    # Carrozzeria P.I 15+15
    {"codice": "BC-C2571", "descrizione": "Braccio porta piatto", "prezzo": 103.20, "modello": "CS-1200W-2200 P.I 15+15"},
    {"codice": "BH-P4759VG6", "descrizione": "Cerniera sportello stampante", "prezzo": 15.60, "modello": "CS-1200W-2200 P.I 15+15"},
    {"codice": "BH-C2302", "descrizione": "Perno cerniera sportello stampante", "prezzo": 3.60, "modello": "CS-1200W-2200 P.I 15+15"},
    {"codice": "BL-M1379", "descrizione": "Adattatore cella mod PC", "prezzo": 24.00, "modello": "CS-1200W-2200 P.I 15+15"},
    {"codice": "BL-P5104D", "descrizione": "Supporto convertitore peso", "prezzo": 24.00, "modello": "CS-1200W-2200 P.I 15+15"},
    {"codice": "BL-C2702", "descrizione": "Coperchio convertitore peso", "prezzo": 16.80, "modello": "CS-1200W-2200 P.I 15+15"},
    {"codice": "49-2986", "descrizione": "Gancio piatto completo", "prezzo": 42.00, "modello": "CS-1200W-2200 P.I 15+15"},
    
    # Carrozzeria CS-2200 W FLAT 12+7 3"
    {"codice": "48-MSOPORTAP", "descrizione": "Crociera piatto completa di rondelle in gomma", "prezzo": 45.60, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-C2778", "descrizione": "Coperchio di tenuta", "prezzo": 22.80, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-C2785", "descrizione": "Telaio posteriore", "prezzo": 132.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BE-C2584", "descrizione": "Supporto convertitore", "prezzo": 43.20, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-C2787", "descrizione": "Protezione cavi stampante", "prezzo": 22.80, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-C2783", "descrizione": "Telaio frontale", "prezzo": 156.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-C2777", "descrizione": "Portello stampante", "prezzo": 34.80, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-C2784", "descrizione": "Cerniera portello stampante", "prezzo": 18.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-C2782", "descrizione": "Carcassa", "prezzo": 156.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BE-P5495", "descrizione": "Ponte superiore", "prezzo": 18.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BE-P5497", "descrizione": "Cerniera destra", "prezzo": 4.80, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BE-P5499", "descrizione": "Cerniera sinistra", "prezzo": 4.80, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BH-C2246", "descrizione": "Perno sportello stampante", "prezzo": 8.40, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BVV11", "descrizione": "Piedino", "prezzo": 7.20, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BK-P4149", "descrizione": "Morsetto anti-trazione cavi", "prezzo": 6.00, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BE-C525", "descrizione": "Cerniera inox", "prezzo": 8.40, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-P5214N", "descrizione": "Snodo A", "prezzo": 8.40, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-P5217N", "descrizione": "Snodo D", "prezzo": 10.80, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BL-6080", "descrizione": "Indicatore LED con cavo", "prezzo": 19.20, "modello": "CS-2200 W FLAT 12+7 3\""},
    {"codice": "BLI99", "descrizione": "Pulsante doppio contatto", "prezzo": 10.80, "modello": "CS-2200 W FLAT 12+7 3\""},
]


def main():
    """Main function to import spare parts."""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("Importazione Ricambi Dibal - CS 1200/2200")
        print("=" * 80)
        print()
        
        # Constants
        FORNITORE = "Dibal"
        DEPARTMENT_ID = 1  # Assistenza IT (informatica)
        
        # Statistics
        total_items = len(RICAMBI_DATA)
        added = 0
        skipped = 0
        errors = []
        
        print(f"Trovati {total_items} ricambi da importare")
        print(f"Fornitore: {FORNITORE}")
        print(f"Reparto: Assistenza IT (ID: {DEPARTMENT_ID})")
        print()
        print("-" * 80)
        
        for idx, item in enumerate(RICAMBI_DATA, 1):
            codice = item['codice']
            descrizione_base = item['descrizione']
            prezzo = item['prezzo']
            modello = item['modello']
            
            # Append model to description
            descrizione_completa = f"{descrizione_base} - {modello}"
            
            try:
                # Check if spare part already exists
                existing = Ricambio.query.filter_by(codice=codice).first()
                
                if existing:
                    print(f"[{idx}/{total_items}] SKIP - {codice}: Già esistente nel database")
                    skipped += 1
                    continue
                
                # Create new spare part
                nuovo_ricambio = Ricambio(
                    codice=codice,
                    descrizione=descrizione_completa,
                    prezzo_unitario=prezzo,
                    fornitore=FORNITORE,
                    department_id=DEPARTMENT_ID,
                    quantita_disponibile=0,  # Start with 0 quantity
                    quantita_prenotata=0,
                    quantita_minima=0
                )
                
                db.session.add(nuovo_ricambio)
                print(f"[{idx}/{total_items}] OK - {codice}: {descrizione_base[:50]}... (€{prezzo:.2f})")
                added += 1
                
            except Exception as e:
                error_msg = f"[{idx}/{total_items}] ERROR - {codice}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                db.session.rollback()
                continue
        
        # Commit all changes
        if added > 0:
            try:
                db.session.commit()
                print()
                print("-" * 80)
                print("[OK] Database aggiornato con successo!")
            except Exception as e:
                print()
                print("-" * 80)
                print(f"[ERRORE] durante il commit: {str(e)}")
                db.session.rollback()
                return
        
        # Print summary
        print()
        print("=" * 80)
        print("RIEPILOGO IMPORTAZIONE")
        print("=" * 80)
        print(f"Totale ricambi processati: {total_items}")
        print(f"[+] Aggiunti:               {added}")
        print(f"[-] Saltati (gia' esistenti): {skipped}")
        print(f"[!] Errori:                 {len(errors)}")
        print()
        
        if errors:
            print("ERRORI RILEVATI:")
            for error in errors:
                print(f"  - {error}")
            print()
        
        print("=" * 80)
        print(f"Importazione completata!")
        print("=" * 80)


if __name__ == '__main__':
    main()
