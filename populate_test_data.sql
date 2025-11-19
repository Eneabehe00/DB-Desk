-- Script SQL per popolare il database con dati di test
-- Eseguire dopo aver creato tutte le tabelle del sistema

-- ===== MACCHINE =====
-- Assumendo che esistano già clienti con ID 1, 2, 3, 4, 5 e dipartimenti con ID 1, 2
INSERT IGNORE INTO macchine (codice, modello, marca, numero_serie, tipo_macchina_id, stato, ubicazione, cliente_id, data_assegnazione, anno_produzione, peso, dimensioni, alimentazione, prezzo_acquisto, prezzo_vendita, fornitore, data_acquisto, data_scadenza_garanzia, prossima_manutenzione, intervallo_manutenzione_giorni, note, department_id) VALUES

-- Macchine DISPONIBILI (in magazzino)
('BAL001', 'Precision Scale Pro 150', 'TechScale', 'TS150-2024-001', 1, 'Disponibile', 'Magazzino A1', NULL, NULL, 2024, 15.50, '40x30x15 cm', '220V', 450.00, 650.00, 'TechScale Italia', '2024-01-15', '2026-01-15', '2025-01-15', 365, 'Bilancia di precisione per uso commerciale', 1),
('BAL002', 'Digital Scale DX200', 'WeighMaster', 'WM200-2023-045', 1, 'Disponibile', 'Magazzino A2', NULL, NULL, 2023, 12.30, '35x25x12 cm', '220V', 380.00, 550.00, 'WeighMaster SRL', '2023-06-20', '2025-06-20', '2024-12-20', 365, 'Bilancia digitale con display LCD', 1),
('AFF001', 'SliceMaster 3000', 'CutPro', 'CP3000-2024-012', 11, 'Disponibile', 'Magazzino B1', NULL, NULL, 2024, 45.80, '80x60x50 cm', '220V', 1200.00, 1800.00, 'CutPro Equipment', '2024-02-10', '2026-02-10', '2025-02-10', 180, 'Affettatrice professionale con lama da 30cm', 1),
('SEG001', 'SegaOssa Pro', 'CutTech', 'CT-SO-2024-003', 12, 'Disponibile', 'Magazzino C1', NULL, NULL, 2024, 8.50, '45x35x20 cm', '220V', 850.00, 1200.00, 'CutTech Solutions', '2024-03-05', '2026-03-05', '2025-03-05', 365, 'Sega ossa professionale', 1),
('SUB001', 'SottoVuoto Pro', 'VacTech', 'VT-SV-2023-089', 13, 'Disponibile', 'Magazzino D1', NULL, NULL, 2023, 3.20, '25x20x15 cm', '220V', 280.00, 420.00, 'VacTech Italia', '2023-09-12', '2025-09-12', '2024-12-12', 365, 'Macchina sottovuoto', 1),
('HAM001', 'Hamburgeratrice Manual', 'BurgerTech', 'BT-HM-2024-007', 14, 'Disponibile', 'Magazzino E1', NULL, NULL, 2024, 0.85, '15x8x5 cm', 'Manuale', 150.00, 220.00, 'BurgerTech Europe', '2024-01-25', '2026-01-25', '2025-01-25', 365, 'Hamburgeratrice manuale', 1),

-- Macchine ATTIVE presso clienti (assumendo clienti con ID 1, 2, 3)
('BAL003', 'Precision Scale Pro 200', 'TechScale', 'TS200-2023-078', 1, 'Attiva', 'Cliente: Panificio Rossi', 1, '2023-08-15 09:30:00', 2023, 18.20, '45x35x18 cm', '220V', 520.00, 750.00, 'TechScale Italia', '2023-07-10', '2025-07-10', '2024-12-15', 365, 'Bilancia venduta al Panificio Rossi', 1),
('AFF002', 'SliceMaster 2500', 'CutPro', 'CP2500-2023-156', 11, 'Attiva', 'Cliente: Salumeria Bianchi', 2, '2023-09-20 14:15:00', 2023, 42.50, '75x55x45 cm', '220V', 1100.00, 1650.00, 'CutPro Equipment', '2023-08-30', '2025-08-30', '2024-11-20', 180, 'Affettatrice venduta alla Salumeria Bianchi', 1),
('SEG002', 'SegaOssa Standard', 'CutTech', 'CT-SO-2023-234', 12, 'Attiva', 'Cliente: Alimentari Verdi', 3, '2023-10-05 11:00:00', 2023, 7.80, '40x30x18 cm', '220V', 650.00, 950.00, 'CutTech Solutions', '2023-09-15', '2025-09-15', '2024-12-05', 365, 'Sega ossa venduta agli Alimentari Verdi', 1),

-- Macchine IN PRESTITO (nostre macchine presso clienti temporaneamente)
('BAL004', 'Digital Scale Basic', 'WeighMaster', 'WM-BASIC-2024-023', 1, 'In prestito', 'Cliente: Panificio Rossi', 1, '2024-10-15 10:00:00', 2024, 10.50, '30x25x10 cm', '220V', 320.00, 480.00, 'WeighMaster SRL', '2024-09-10', '2026-09-10', '2025-03-15', 365, 'Bilancia in prestito temporaneo', 1),
('AFF003', 'SliceMaster Compact', 'CutPro', 'CP-COMP-2024-067', 11, 'In prestito', 'Cliente: Salumeria Bianchi', 2, '2024-11-01 15:30:00', 2024, 35.20, '60x45x40 cm', '220V', 900.00, 1350.00, 'CutPro Equipment', '2024-10-01', '2026-10-01', '2025-05-01', 180, 'Affettatrice in prestito durante riparazione', 1),

-- Macchine IN RIPARAZIONE (macchine dei clienti presso di noi)
('SUB002', 'SottoVuoto Pro', 'VacTech', 'VT-SV-2022-445', 13, 'In riparazione', 'Officina Riparazioni', NULL, NULL, 2022, 9.20, '42x32x22 cm', '220V', 750.00, 1100.00, 'VacTech Italia', '2022-05-20', '2024-05-20', '2024-11-20', 365, 'SottoVuoto del cliente in riparazione - problema pompa', 1),
('HAM002', 'Hamburgeratrice Advanced', 'BurgerTech', 'BT-HA-2023-156', 14, 'In riparazione', 'Officina Riparazioni', NULL, NULL, 2023, 4.50, '30x25x18 cm', 'Manuale', 380.00, 580.00, 'BurgerTech Europe', '2023-04-15', '2025-04-15', '2024-10-15', 365, 'Hamburgeratrice del cliente - problema meccanismo', 1),

-- Macchine per test department 2
('BAL005', 'Precision Scale Pro 300', 'TechScale', 'TS300-2024-001', 1, 'Disponibile', 'Magazzino F1', NULL, NULL, 2024, 25.50, '50x40x35 cm', '220V', 1500.00, 2200.00, 'TechScale Italia', '2024-01-10', '2026-01-10', '2025-01-10', 180, 'Bilancia di precisione per department 2', 2),
('AFF004', 'SliceMaster Industrial', 'CutPro', 'CP-IND-2023-089', 11, 'Attiva', 'Cliente: Pasticceria Dolci', 4, '2023-07-20 16:00:00', 2023, 85.30, '120x80x100 cm', '380V', 2800.00, 4200.00, 'CutPro Equipment', '2023-06-15', '2025-06-15', '2024-12-20', 90, 'Affettatrice venduta alla Pasticceria Dolci', 2);

-- ===== RICAMBI =====
INSERT IGNORE INTO ricambi (codice, descrizione, quantita_disponibile, quantita_minima, prezzo_unitario, fornitore, note, department_id) VALUES

-- Ricambi per Bilance
('RIC-BAL-001', 'Piatto pesatura acciaio inox 30x25cm', 15, 3, 45.50, 'TechScale Italia', 'Piatto di ricambio per bilance serie Pro', 1),
('RIC-BAL-002', 'Display LCD retroilluminato', 8, 2, 85.00, 'WeighMaster SRL', 'Display compatibile con serie Digital Scale', 1),
('RIC-BAL-003', 'Cella di carico 150kg', 5, 1, 120.00, 'TechScale Italia', 'Cella di carico di precisione', 1),
('RIC-BAL-004', 'Alimentatore 12V 2A', 12, 3, 25.00, 'Componenti Elettronici SRL', 'Alimentatore universale per bilance', 1),
('RIC-BAL-005', 'Tastiera membrana 16 tasti', 6, 2, 35.00, 'TechScale Italia', 'Tastiera di ricambio per modelli Pro', 1),

-- Ricambi per Affettatrici
('RIC-AFF-001', 'Lama circolare diametro 30cm', 4, 1, 180.00, 'CutPro Equipment', 'Lama in acciaio temperato per SliceMaster', 1),
('RIC-AFF-002', 'Motore elettrico 0.5HP', 2, 1, 350.00, 'Motori Industriali SpA', 'Motore di ricambio per affettatrici professionali', 1),
('RIC-AFF-003', 'Carrello portafetta regolabile', 6, 2, 95.00, 'CutPro Equipment', 'Carrello con regolazione spessore 0-15mm', 1),
('RIC-AFF-004', 'Protezione lama trasparente', 10, 2, 45.00, 'CutPro Equipment', 'Protezione di sicurezza in policarbonato', 1),
('RIC-AFF-005', 'Affilatoio automatico', 3, 1, 220.00, 'CutPro Equipment', 'Sistema di affilatura automatica lama', 1),

-- Ricambi per Registratori di Cassa
('RIC-REG-001', 'Rotolo carta termica 80mm', 50, 10, 2.50, 'Forniture Ufficio SRL', 'Rotoli termici per scontrini', 1),
('RIC-REG-002', 'Tastiera numerica USB', 8, 2, 65.00, 'RegTech Solutions', 'Tastiera di ricambio per CashPoint', 1),
('RIC-REG-003', 'Cassetto portamonete 5 scomparti', 4, 1, 120.00, 'RegTech Solutions', 'Cassetto con serratura elettronica', 1),
('RIC-REG-004', 'Display cliente LCD 20x2', 6, 2, 75.00, 'Display Solutions', 'Display per visualizzazione prezzi cliente', 1),
('RIC-REG-005', 'Stampante termica 80mm', 3, 1, 180.00, 'RegTech Solutions', 'Stampante per scontrini fiscali', 1),

-- Ricambi per Stampanti
('RIC-STA-001', 'Testina di stampa termica', 5, 1, 150.00, 'PrintTech Italia', 'Testina per stampanti serie LabelPrint', 1),
('RIC-STA-002', 'Rullo di trascinamento', 12, 3, 25.00, 'PrintTech Italia', 'Rullo in gomma per alimentazione etichette', 1),
('RIC-STA-003', 'Sensore carta ottico', 8, 2, 45.00, 'Sensori Industriali SRL', 'Sensore per rilevamento fine rotolo', 1),
('RIC-STA-004', 'Ribbon cera-resina 110mm', 25, 5, 18.00, 'Materiali Stampa SpA', 'Ribbon per stampa etichette durevoli', 1),
('RIC-STA-005', 'Scheda madre USB/Ethernet', 3, 1, 280.00, 'PrintTech Italia', 'Scheda di controllo con connettività', 1),

-- Ricambi per Scanner
('RIC-SCA-001', 'Modulo laser scanner', 4, 1, 95.00, 'ScanTech Europe', 'Modulo di scansione laser per codici 1D/2D', 1),
('RIC-SCA-002', 'Cavo USB spiralato 2m', 15, 3, 12.00, 'Cavi e Connettori SRL', 'Cavo di collegamento rinforzato', 1),
('RIC-SCA-003', 'Base di ricarica wireless', 6, 2, 85.00, 'ScanTech Europe', 'Base per scanner wireless con LED status', 1),
('RIC-SCA-004', 'Batteria Li-ion 2200mAh', 10, 2, 35.00, 'Batterie Professionali SpA', 'Batteria ricaricabile per scanner cordless', 1),
('RIC-SCA-005', 'Trigger di scansione', 8, 2, 15.00, 'ScanTech Europe', 'Pulsante di attivazione scansione', 1),

-- Ricambi per department 2 (Macchine Caffè e Impastatrici)
('RIC-CAF-001', 'Gruppo erogazione completo', 2, 1, 450.00, 'CoffeeTech Italia', 'Gruppo per macchine EspressoMaster', 2),
('RIC-CAF-002', 'Caldaia inox 2L', 1, 1, 380.00, 'CoffeeTech Italia', 'Caldaia di ricambio per vapore', 2),
('RIC-CAF-003', 'Macinacaffè ceramico', 3, 1, 220.00, 'CoffeeTech Italia', 'Macinino con macine ceramiche', 2),
('RIC-IMP-001', 'Gancio impastatore a spirale', 4, 1, 180.00, 'BakeTech Professional', 'Gancio per impasti pesanti', 2),
('RIC-IMP-002', 'Motore trifase 3HP', 1, 1, 850.00, 'Motori Industriali SpA', 'Motore per impastatrici 50L', 2),
('RIC-IMP-003', 'Vasca inox 50L', 2, 1, 650.00, 'BakeTech Professional', 'Vasca di impastamento acciaio inox', 2);

-- ===== MOVIMENTI MACCHINE PER RIPARAZIONI =====
-- Creiamo movimenti per le macchine in riparazione per salvare stato originale
INSERT IGNORE INTO movimenti_macchine (macchina_id, tipo_movimento, stato_precedente, stato_nuovo, cliente_id, cliente_originale_id, ubicazione_originale, data_assegnazione_originale, data_vendita_originale, prezzo_vendita_originale, prossima_manutenzione_originale, note, created_at) VALUES

-- SUB002: era Attiva presso cliente 1, ora in riparazione
((SELECT id FROM macchine WHERE codice = 'SUB002'), 'Riparazione', 'Attiva', 'In riparazione', NULL, 1, 'Cliente: Alimentari Verdi', '2023-10-05 11:00:00', '2023-10-05', 1100.00, '2024-11-20', 'Macchina del cliente in riparazione - problema pompa', NOW()),

-- HAM002: era Attiva presso cliente 2, ora in riparazione
((SELECT id FROM macchine WHERE codice = 'HAM002'), 'Riparazione', 'Attiva', 'In riparazione', NULL, 2, 'Cliente: Salumeria Bianchi', '2023-09-20 14:15:00', '2023-09-20', 580.00, '2024-10-15', 'Macchina del cliente in riparazione - problema meccanismo', NOW());

-- ===== AGGIORNA CONTATORI AUTO-INCREMENT =====
-- Questo assicura che i prossimi inserimenti non vadano in conflitto
ALTER TABLE tipi_macchine AUTO_INCREMENT = 100;
ALTER TABLE macchine AUTO_INCREMENT = 100;
ALTER TABLE ricambi AUTO_INCREMENT = 100;

-- ===== RIEPILOGO DATI INSERITI =====
SELECT 'RIEPILOGO DATI INSERITI' as info;
SELECT COUNT(*) as 'Macchine Inserite' FROM macchine;
SELECT COUNT(*) as 'Ricambi Inseriti' FROM ricambi;

SELECT 'DISTRIBUZIONE MACCHINE PER STATO' as info;
SELECT stato, COUNT(*) as quantita FROM macchine GROUP BY stato;

SELECT 'RICAMBI PER FORNITORE' as info;
SELECT fornitore, COUNT(*) as quantita FROM ricambi GROUP BY fornitore;

SELECT 'MACCHINE PER DIPARTIMENTO' as info;
SELECT department_id, COUNT(*) as quantita FROM macchine GROUP BY department_id;

SELECT 'RICAMBI PER DIPARTIMENTO' as info;
SELECT department_id, COUNT(*) as quantita FROM ricambi GROUP BY department_id;
