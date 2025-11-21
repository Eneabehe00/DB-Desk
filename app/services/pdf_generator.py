"""
Servizio per la generazione di PDF dai fogli tecnici
Utilizza WeasyPrint per convertire HTML in PDF
"""

from flask import render_template, current_app
import os
import base64
from datetime import datetime
from app import db
from app.models.foglio_tecnico import FoglioTecnico


def get_signature_base64(signature_path):
    """
    Carica una firma da file e la converte in base64 per l'embedding nel PDF
    
    Args:
        signature_path (str): Path del file della firma
        
    Returns:
        str: Stringa base64 della firma o stringa vuota se errore
    """
    try:
        if not signature_path or not os.path.exists(signature_path):
            return ""
        
        with open(signature_path, 'rb') as f:
            signature_bytes = f.read()
            return base64.b64encode(signature_bytes).decode('utf-8')
    except Exception as e:
        current_app.logger.error(f"Errore nel caricamento firma {signature_path}: {str(e)}")
        return ""


def genera_pdf_con_reportlab(foglio_id):
    """
    Genera un PDF usando ReportLab con design moderno (versione semplificata)

    Args:
        foglio_id (int): ID del foglio tecnico

    Returns:
        str: Path del file PDF generato
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        raise ImportError("ReportLab non installato. Installare con: pip install reportlab")

    # Carica foglio dal database
    foglio = FoglioTecnico.query.get(foglio_id)
    if not foglio:
        raise ValueError(f"Foglio tecnico {foglio_id} non trovato")

    try:
        # Crea cartella PDF se non esiste
        pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fogli_tecnici_pdf')
        os.makedirs(pdf_dir, exist_ok=True)

        # Nome file PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{foglio.numero_foglio}_{timestamp}.pdf"
        pdf_path = os.path.join(pdf_dir, filename)

        # Crea documento PDF con margini moderni
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=1.5*cm, bottomMargin=2*cm,
                              leftMargin=2*cm, rightMargin=2*cm)

        # Stili moderni
        styles = getSampleStyleSheet()

        # Header principale - DB-DESK con stile premium
        header_style = ParagraphStyle(
            'CompanyHeader',
            parent=styles['Heading1'],
            fontSize=28,
            fontName='Helvetica-Bold',
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=colors.white
        )

        # Sottotitolo documento
        subtitle_style = ParagraphStyle(
            'DocumentType',
            parent=styles['Heading2'],
            fontSize=16,
            fontName='Helvetica-Bold',
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#f1f5f9')
        )

        # Numero documento
        doc_number_style = ParagraphStyle(
            'DocNumber',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            textColor=colors.white,
            backColor=colors.HexColor('#ffffff'),
            borderColor=colors.HexColor('#ffffff'),
            borderWidth=2,
            borderPadding=8,
            borderRadius=15,
            spaceAfter=30
        )

        # Titoli sezione moderni
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            fontName='Helvetica-Bold',
            spaceAfter=15,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=20
        )

        # Stile normale per contenuti
        normal_style = ParagraphStyle(
            'ModernNormal',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            spaceAfter=8,
            textColor=colors.HexColor('#374151')
        )

        # Contenuto del PDF moderno
        story = []

        # === HEADER PREMIUM ===
        header_data = [
            [Paragraph("DB-Desk", header_style)],
            [Paragraph("FOGLIO TECNICO DI INTERVENTO", subtitle_style)],
            [Paragraph(f"N° {foglio.numero_foglio}", doc_number_style)]
        ]

        header_table = Table(header_data, colWidths=[16*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(header_table)
        story.append(Spacer(1, 20))

        # Barra di stato documento
        status_data = [
            [f"Stato: {foglio.stato} • Priorità: {foglio.priorita} • Data: {foglio.data_intervento.strftime('%d/%m/%Y')}"]
        ]
        status_table = Table(status_data, colWidths=[16*cm])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(status_table)
        story.append(Spacer(1, 30))

        # === INFORMAZIONI GENERALI ===
        story.append(Paragraph("Informazioni Generali", section_title_style))

        # Tabella informazioni base
        info_data = [
            ['Cliente:', foglio.cliente.ragione_sociale if foglio.cliente else 'N/A'],
            ['Titolo:', foglio.titolo],
            ['Data Intervento:', foglio.data_intervento.strftime('%d/%m/%Y %H:%M')],
            ['Tecnico:', f"{foglio.tecnico.first_name} {foglio.tecnico.last_name}"],
            ['Categoria:', foglio.categoria or 'N/A'],
            ['Priorità:', foglio.priorita or 'N/A'],
            ['Stato:', foglio.stato],
        ]

        if foglio.durata_intervento:
            info_data.append(['Durata:', f"{foglio.durata_intervento} minuti"])
        if foglio.km_percorsi:
            info_data.append(['Km Percorsi:', f"{foglio.km_percorsi} km"])
        if foglio.indirizzo_intervento:
            info_data.append(['Indirizzo:', foglio.indirizzo_intervento])

        info_table = Table(info_data, colWidths=[4*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (1, 0), (-1, -1), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        story.append(info_table)
        story.append(Spacer(1, 20))

        # Descrizione
        if foglio.descrizione:
            story.append(Paragraph("Descrizione Intervento", section_title_style))
            story.append(Paragraph(foglio.descrizione.replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 15))

        # Macchine coinvolte
        if foglio.macchine_collegate.count() > 0:
            story.append(Paragraph("Macchine Coinvolte", section_title_style))
            for macchina in foglio.macchine_collegate:
                machine_text = f"• {macchina.codice} - {macchina.marca} {macchina.modello}"
                if macchina.numero_serie:
                    machine_text += f"\n   Numero di Serie: {macchina.numero_serie}"
                story.append(Paragraph(machine_text, normal_style))
            story.append(Spacer(1, 15))

        # Ricambi utilizzati
        if foglio.ricambi_utilizzati.count() > 0:
            story.append(Paragraph("Ricambi Utilizzati", section_title_style))
            for ricambio in foglio.ricambi_utilizzati:
                ricambio_text = f"• {ricambio.codice} - {ricambio.descrizione}"
                if ricambio.fornitore:
                    ricambio_text += f"\n   Fornitore: {ricambio.fornitore}"
                story.append(Paragraph(ricambio_text, normal_style))
            story.append(Spacer(1, 15))

        # Informazioni commerciali
        if foglio.modalita_pagamento or foglio.importo_intervento:
            story.append(Paragraph("Informazioni Commerciali", section_title_style))
            if foglio.modalita_pagamento:
                story.append(Paragraph(f"Modalità di pagamento: {foglio.modalita_pagamento}", normal_style))
            if foglio.importo_intervento:
                story.append(Paragraph(f"Importo: € {foglio.importo_intervento:.2f}", normal_style))
            story.append(Spacer(1, 15))

        # Note aggiuntive
        if foglio.note_aggiuntive:
            story.append(Paragraph("Note Aggiuntive", section_title_style))
            story.append(Paragraph(foglio.note_aggiuntive.replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 20))

        # Firme - Versione semplificata per evitare problemi di compatibilità
        story.append(Paragraph("Firme di Accettazione", section_title_style))

        # Firma tecnico
        story.append(Paragraph(f"Firma del Tecnico: {foglio.tecnico.first_name} {foglio.tecnico.last_name}", normal_style))
        story.append(Paragraph("___________________________", normal_style))
        story.append(Spacer(1, 10))

        # Firma cliente
        cliente_nome = foglio.nome_firmatario_cliente or "Nome del cliente"
        story.append(Paragraph(f"Firma del Cliente: {cliente_nome}", normal_style))
        story.append(Paragraph("___________________________", normal_style))
        story.append(Spacer(1, 15))

        # Nota sulle firme digitali
        if foglio.firma_tecnico_path or foglio.firma_cliente_path:
            story.append(Paragraph("Nota: Sono presenti firme digitali allegate al documento elettronico.", normal_style))
            story.append(Spacer(1, 10))

        # Dichiarazione di accettazione se presente nome firmatario
        if foglio.nome_firmatario_cliente:
            story.append(Spacer(1, 15))
            dichiarazione_style = ParagraphStyle(
                'Dichiarazione',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#374151'),
                borderWidth=2,
                borderColor=colors.HexColor('#f59e0b'),
                borderPadding=15,
                backColor=colors.HexColor('#fef3c7'),
                spaceAfter=20
            )
            dichiarazione_text = f"Il sottoscritto {foglio.nome_firmatario_cliente} dichiara di aver ricevuto l'intervento tecnico sopra descritto e di essere soddisfatto del lavoro svolto dal personale tecnico di DB-Desk."
            story.append(Paragraph(dichiarazione_text, dichiarazione_style))

        # Footer moderno
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'ModernFooter',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=5
        )
        story.append(Paragraph("DB-Desk - Sistema Gestionale Aziendale", footer_style))
        story.append(Paragraph(f"Documento generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", footer_style))

        # Genera PDF
        doc.build(story)

        # Aggiorna record nel database
        foglio.pdf_generato = True
        foglio.pdf_path = pdf_path
        foglio.updated_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(f"PDF moderno semplificato generato con ReportLab per foglio {foglio.numero_foglio}: {pdf_path}")
        return pdf_path

    except Exception as e:
        current_app.logger.error(f"Errore generazione PDF moderno semplificato ReportLab per foglio {foglio.numero_foglio}: {str(e)}")
        raise Exception(f"Errore nella generazione del PDF moderno semplificato: {str(e)}")


def genera_pdf_con_reportlab_con_firme(foglio):
    """
    Genera PDF con ReportLab includendo le firme in modo sicuro - VERSIONE MODERNA

    Args:
        foglio: Oggetto FoglioTecnico

    Returns:
        str: Path del file PDF generato
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        # Crea cartella PDF se non esiste
        pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fogli_tecnici_pdf')
        os.makedirs(pdf_dir, exist_ok=True)

        # Nome file PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{foglio.numero_foglio}_{timestamp}_con_firme.pdf"
        pdf_path = os.path.join(pdf_dir, filename)

        # Crea documento PDF con margini ottimizzati per design moderno
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=1*cm, bottomMargin=1.5*cm,
                              leftMargin=1.5*cm, rightMargin=1.5*cm)

        # === SISTEMA DI STILI ULTRA-MODERNO ===
        styles = getSampleStyleSheet()

        # STILI HEADER - Design premium
        company_name_style = ParagraphStyle(
            'CompanyName',
            parent=styles['Heading1'],
            fontSize=32,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            textColor=colors.white,
            spaceAfter=2
        )

        company_subtitle_style = ParagraphStyle(
            'CompanySubtitle',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            alignment=TA_CENTER,
            textColor=colors.HexColor('#e2e8f0'),
            spaceAfter=8
        )

        document_title_style = ParagraphStyle(
            'DocumentTitle',
            parent=styles['Heading2'],
            fontSize=18,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            textColor=colors.white,
            spaceAfter=5
        )

        # STILI SEZIONI - Gerarchia visiva perfetta
        section_header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            textColor=colors.white,
            borderPadding=10,
            spaceAfter=18,
            spaceBefore=25
        )

        subsection_title_style = ParagraphStyle(
            'SubsectionTitle',
            parent=styles['Heading3'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=8,
            spaceBefore=15
        )

        # STILI CONTENUTO - Tipografia ottimizzata
        label_style = ParagraphStyle(
            'ModernLabel',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#64748b'),
            spaceAfter=2
        )

        value_style = ParagraphStyle(
            'ModernValue',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=6
        )

        important_value_style = ParagraphStyle(
            'ImportantValue',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=8
        )

        description_style = ParagraphStyle(
            'ModernDescription',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.HexColor('#475569'),
            spaceAfter=10,
            leading=14
        )

        # STILI SPECIALI
        highlight_style = ParagraphStyle(
            'HighlightText',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#059669'),
            spaceAfter=5
        )

        footer_style = ParagraphStyle(
            'ModernFooter',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica',
            alignment=TA_CENTER,
            textColor=colors.HexColor('#94a3b8'),
            spaceAfter=5
        )

        # === CONTENUTO PDF ULTRA-MODERNO ===
        story = []

        # === HEADER PREMIUM CON GRADIENTE VISIVO ===
        header_data = [
            [Paragraph("DB-Desk", company_name_style)],
            [Paragraph("Sistema Gestionale Aziendale", company_subtitle_style)],
            [Spacer(1, 8)],
            [Paragraph(f"FOGLIO TECNICO N° {foglio.numero_foglio}", document_title_style)],
            [Paragraph(f"Data: {foglio.data_intervento.strftime('%d/%m/%Y')}", company_subtitle_style)]
        ]

        header_table = Table(header_data, colWidths=[18*cm])
        header_table.setStyle(TableStyle([
            # Gradiente simulato con colore blu scuro
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 20),
            # Bordo elegante
            ('LINEBELOW', (0, -1), (-1, -1), 3, colors.HexColor('#3b82f6')),
        ]))

        story.append(header_table)
        story.append(Spacer(1, 30))

        # === SEZIONE INFORMAZIONI GENERALI ===
        # Header sezione con design moderno
        info_header = Paragraph("INFORMAZIONI GENERALI", section_header_style)
        info_header_table = Table([[info_header]], colWidths=[18*cm])
        info_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#6366f1')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(info_header_table)
        story.append(Spacer(1, 20))

        # === LAYOUT A CARD MODERNE ===
        # Card Azienda
        company_card_data = [
            [Paragraph("🏢 DATI AZIENDA", subsection_title_style)],
            [Paragraph("Nome Azienda", label_style)],
            [Paragraph("[INSERIRE NOME AZIENDA]", important_value_style)],
            [Paragraph("Indirizzo", label_style)],
            [Paragraph("[INSERIRE INDIRIZZO AZIENDA]", value_style)],
            [Paragraph("Contatti", label_style)],
            [Paragraph("Tel: [INSERIRE TELEFONO] | Email: [INSERIRE EMAIL]", value_style)],
            [Paragraph("P.IVA", label_style)],
            [Paragraph("[INSERIRE P.IVA]", value_style)]
        ]

        company_card = Table(company_card_data, colWidths=[8.5*cm])
        company_card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#6366f1')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))

        # Card Cliente
        if foglio.cliente:
            client_card_data = [
                [Paragraph("👤 DATI CLIENTE", subsection_title_style)],
                [Paragraph("Ragione Sociale", label_style)],
                [Paragraph(foglio.cliente.ragione_sociale, important_value_style)],
                [Paragraph("Codice Fiscale/P.IVA", label_style)],
                [Paragraph(foglio.cliente.codice_fiscale or 'Non specificato', value_style)],
                [Paragraph("Indirizzo", label_style)],
                [Paragraph(foglio.cliente.indirizzo or 'Non specificato', value_style)],
                [Paragraph("Contatti", label_style)],
                [Paragraph(f"Tel: {foglio.cliente.telefono or 'N/A'} | Email: {foglio.cliente.email or 'N/A'}", value_style)]
            ]
        else:
            client_card_data = [
                [Paragraph("👤 DATI CLIENTE", subsection_title_style)],
                [Paragraph("Cliente non trovato nel sistema", value_style)]
            ]

        client_card = Table(client_card_data, colWidths=[8.5*cm])
        client_card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#10b981')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))

        # Layout a due colonne per le card
        cards_data = [[company_card, client_card]]
        cards_table = Table(cards_data, colWidths=[9*cm, 9*cm])
        cards_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(cards_table)
        story.append(Spacer(1, 30))

        # === SEZIONE DETTAGLI INTERVENTO ===
        # Header sezione
        intervento_header = Paragraph("DETTAGLI DELL'INTERVENTO", section_header_style)
        intervento_header_table = Table([[intervento_header]], colWidths=[18*cm])
        intervento_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#059669')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(intervento_header_table)
        story.append(Spacer(1, 20))

        # === INFORMAZIONI OPERATIVE ===
        # Griglia informazioni principali
        info_grid = [
            [Paragraph("📅 Data e Ora", label_style), 
             Paragraph(foglio.data_intervento.strftime('%d/%m/%Y alle %H:%M'), important_value_style),
             Paragraph("👨‍🔧 Tecnico", label_style), 
             Paragraph(f"{foglio.tecnico.first_name} {foglio.tecnico.last_name}", important_value_style)],
            [Paragraph("📋 Categoria", label_style), 
             Paragraph(foglio.categoria or 'Non specificata', value_style),
             Paragraph("⚡ Priorità", label_style), 
             Paragraph(foglio.priorita, value_style)]
        ]

        # Aggiungi informazioni aggiuntive se presenti
        if foglio.durata_intervento or foglio.km_percorsi:
            additional_row = []
            if foglio.durata_intervento:
                additional_row.extend([
                    Paragraph("⏱️ Durata", label_style),
                    Paragraph(f"{foglio.durata_intervento} minuti", value_style)
                ])
            else:
                additional_row.extend([Paragraph("", label_style), Paragraph("", value_style)])
            
            if foglio.km_percorsi:
                additional_row.extend([
                    Paragraph("🚗 Chilometri", label_style),
                    Paragraph(f"{foglio.km_percorsi} km", value_style)
                ])
            else:
                additional_row.extend([Paragraph("", label_style), Paragraph("", value_style)])
            
            info_grid.append(additional_row)

        info_table = Table(info_grid, colWidths=[2.5*cm, 6*cm, 2.5*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#10b981')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))

        story.append(info_table)
        story.append(Spacer(1, 20))

        # Luogo intervento se presente
        if foglio.indirizzo_intervento:
            location_data = [[
                Paragraph("📍 LUOGO INTERVENTO", highlight_style),
                Paragraph(foglio.indirizzo_intervento, important_value_style)
            ]]
            location_table = Table(location_data, colWidths=[4*cm, 14*cm])
            location_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef3c7')),
                ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor('#f59e0b')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(location_table)
            story.append(Spacer(1, 15))

        # === TITOLO E DESCRIZIONE ===
        if foglio.titolo:
            title_data = [[
                Paragraph("🎯 TITOLO INTERVENTO", highlight_style),
                Paragraph(foglio.titolo, important_value_style)
            ]]
            title_table = Table(title_data, colWidths=[4*cm, 14*cm])
            title_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
                ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor('#3b82f6')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(title_table)
            story.append(Spacer(1, 15))

        if foglio.descrizione:
            story.append(Paragraph("📝 DESCRIZIONE DETTAGLIATA", highlight_style))
            
            desc_box = Table([[Paragraph(foglio.descrizione, description_style)]], colWidths=[18*cm])
            desc_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor('#64748b')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 15),
            ]))
            story.append(desc_box)

        story.append(Spacer(1, 25))

        # === MACCHINE E ATTREZZATURE ===
        if foglio.macchine_collegate.count() > 0:
            # Header sezione
            machines_header = Paragraph("MACCHINE E ATTREZZATURE", section_header_style)
            machines_header_table = Table([[machines_header]], colWidths=[18*cm])
            machines_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#7c3aed')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(machines_header_table)
            story.append(Spacer(1, 18))

            # Lista macchine con design moderno
            for i, macchina in enumerate(foglio.macchine_collegate):
                machine_info = [
                    [Paragraph(f"⚙️ MACCHINA #{i+1}", highlight_style)],
                    [Paragraph("Codice", label_style)],
                    [Paragraph(macchina.codice, important_value_style)],
                    [Paragraph("Marca e Modello", label_style)],
                    [Paragraph(f"{macchina.marca} {macchina.modello}", value_style)]
                ]

                if macchina.numero_serie:
                    machine_info.extend([
                        [Paragraph("Numero di Serie", label_style)],
                        [Paragraph(macchina.numero_serie, value_style)]
                    ])

                machine_card = Table(machine_info, colWidths=[18*cm])
                machine_card.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#faf5ff')),
                    ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#7c3aed')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('PADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(machine_card)
                story.append(Spacer(1, 12))

            story.append(Spacer(1, 20))

        # === RICAMBI E MATERIALI ===
        if foglio.ricambi_utilizzati.count() > 0:
            # Header sezione
            parts_header = Paragraph("RICAMBI E MATERIALI", section_header_style)
            parts_header_table = Table([[parts_header]], colWidths=[18*cm])
            parts_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ea580c')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(parts_header_table)
            story.append(Spacer(1, 18))

            # Lista ricambi con design moderno
            for i, ricambio in enumerate(foglio.ricambi_utilizzati):
                part_info = [
                    [Paragraph(f"🔧 RICAMBIO #{i+1}", highlight_style)],
                    [Paragraph("Codice", label_style)],
                    [Paragraph(ricambio.codice, important_value_style)],
                    [Paragraph("Descrizione", label_style)],
                    [Paragraph(ricambio.descrizione, value_style)]
                ]

                if ricambio.fornitore:
                    part_info.extend([
                        [Paragraph("Fornitore", label_style)],
                        [Paragraph(ricambio.fornitore, value_style)]
                    ])

                part_card = Table(part_info, colWidths=[18*cm])
                part_card.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff7ed')),
                    ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#ea580c')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('PADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(part_card)
                story.append(Spacer(1, 12))

            story.append(Spacer(1, 20))

        # === NOTE AGGIUNTIVE ===
        if foglio.note_aggiuntive:
            # Header sezione
            notes_header = Paragraph("NOTE E OSSERVAZIONI", section_header_style)
            notes_header_table = Table([[notes_header]], colWidths=[18*cm])
            notes_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#64748b')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(notes_header_table)
            story.append(Spacer(1, 18))

            # Box note con design elegante
            story.append(Paragraph("📋 NOTE AGGIUNTIVE", highlight_style))
            
            notes_box = Table([[Paragraph(foglio.note_aggiuntive, description_style)]], colWidths=[18*cm])
            notes_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
                ('LINEABOVE', (0, 0), (-1, -1), 3, colors.HexColor('#64748b')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 15),
            ]))
            story.append(notes_box)
            story.append(Spacer(1, 25))

        # === INFORMAZIONI COMMERCIALI ===
        if foglio.modalita_pagamento or foglio.importo_intervento:
            # Header sezione
            commercial_header = Paragraph("INFORMAZIONI COMMERCIALI", section_header_style)
            commercial_header_table = Table([[commercial_header]], colWidths=[18*cm])
            commercial_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#dc2626')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(commercial_header_table)
            story.append(Spacer(1, 18))

            # Card informazioni commerciali
            commercial_info = []
            if foglio.modalita_pagamento:
                commercial_info.extend([
                    [Paragraph("💳 Modalità di Pagamento", label_style)],
                    [Paragraph(foglio.modalita_pagamento, important_value_style)]
                ])
            
            if foglio.importo_intervento:
                commercial_info.extend([
                    [Paragraph("💰 Importo dell'Intervento", label_style)],
                    [Paragraph(f"€ {foglio.importo_intervento:.2f}", ParagraphStyle('PriceStyle', 
                        parent=styles['Normal'], fontSize=16, fontName='Helvetica-Bold', 
                        textColor=colors.HexColor('#dc2626'), spaceAfter=8))]
                ])

            if commercial_info:
                commercial_card = Table(commercial_info, colWidths=[18*cm])
                commercial_card.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef2f2')),
                    ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#dc2626')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('PADDING', (0, 0), (-1, -1), 15),
                ]))
                story.append(commercial_card)
                story.append(Spacer(1, 30))

        # === SEZIONE FIRME E ACCETTAZIONE ===
        # Header sezione firme
        signatures_header = Paragraph("FIRME DI ACCETTAZIONE", section_header_style)
        signatures_header_table = Table([[signatures_header]], colWidths=[18*cm])
        signatures_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#991b1b')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(signatures_header_table)
        story.append(Spacer(1, 20))

        # === DICHIARAZIONE DI ACCETTAZIONE ===
        acceptance_text = "Con la presente si dichiara che l'intervento è stato eseguito secondo le specifiche concordate e che il cliente accetta il lavoro svolto."
        acceptance_box = Table([[Paragraph(f"✅ {acceptance_text}", ParagraphStyle('AcceptanceStyle', 
            parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', 
            textColor=colors.HexColor('#059669'), alignment=TA_CENTER))]], colWidths=[18*cm])
        acceptance_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
            ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor('#059669')),
            ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor('#059669')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 15),
        ]))
        story.append(acceptance_box)
        story.append(Spacer(1, 25))

        # === CARD FIRME MODERNE ===
        # Card Firma Azienda
        company_signature_info = [
            [Paragraph("🏢 FIRMA AZIENDA", subsection_title_style)],
            [Paragraph("Rappresentante", label_style)],
            [Paragraph("[NOME RAPPRESENTANTE AZIENDA]", important_value_style)],
            [Paragraph("Ruolo", label_style)],
            [Paragraph("[RUOLO RAPPRESENTANTE]", value_style)],
            [Paragraph("Data", label_style)],
            [Paragraph("_______________", value_style)],
            [Paragraph("Firma", label_style)]
        ]

        # Card Firma Cliente
        client_signature_info = [
            [Paragraph("👤 FIRMA CLIENTE", subsection_title_style)],
            [Paragraph("Nome", label_style)],
            [Paragraph(foglio.nome_firmatario_cliente or "[NOME CLIENTE]", important_value_style)],
            [Paragraph("Azienda", label_style)],
            [Paragraph(foglio.cliente.ragione_sociale if foglio.cliente else "[AZIENDA CLIENTE]", value_style)],
            [Paragraph("Data", label_style)],
            [Paragraph("_______________", value_style)],
            [Paragraph("Firma", label_style)]
        ]

        # Gestione firme digitali
        signature_added_company = False
        signature_added_client = False

        if foglio.firma_tecnico_path and os.path.exists(foglio.firma_tecnico_path):
            try:
                from reportlab.platypus import Image
                from io import BytesIO
                import base64
                
                signature_data = get_signature_base64(foglio.firma_tecnico_path)
                if signature_data:
                    img_data = base64.b64decode(signature_data)
                    img_buffer = BytesIO(img_data)
                    firma_img = Image(img_buffer, width=5*cm, height=2.5*cm)
                    company_signature_info.append([firma_img])
                    signature_added_company = True
            except Exception as e:
                company_signature_info.append([Paragraph("✅ Firma digitale presente", highlight_style)])
                signature_added_company = True

        if foglio.firma_cliente_path and os.path.exists(foglio.firma_cliente_path):
            try:
                from reportlab.platypus import Image
                from io import BytesIO
                import base64
                
                signature_data = get_signature_base64(foglio.firma_cliente_path)
                if signature_data:
                    img_data = base64.b64decode(signature_data)
                    img_buffer = BytesIO(img_data)
                    firma_img = Image(img_buffer, width=5*cm, height=2.5*cm)
                    client_signature_info.append([firma_img])
                    signature_added_client = True
            except Exception as e:
                client_signature_info.append([Paragraph("✅ Firma digitale presente", highlight_style)])
                signature_added_client = True

        # Se non ci sono firme digitali, aggiungi spazio per firma manuale
        if not signature_added_company:
            company_signature_info.append([Paragraph("_______________________", value_style)])
        if not signature_added_client:
            client_signature_info.append([Paragraph("_______________________", value_style)])

        # Crea le card per le firme
        company_signature_card = Table(company_signature_info, colWidths=[8.5*cm])
        company_signature_card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef2f2')),
            ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#991b1b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))

        client_signature_card = Table(client_signature_info, colWidths=[8.5*cm])
        client_signature_card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fef2f2')),
            ('LINEABOVE', (0, 0), (-1, 0), 3, colors.HexColor('#991b1b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))

        # Layout a due colonne per le firme
        signatures_layout = Table([[company_signature_card, client_signature_card]], colWidths=[9*cm, 9*cm])
        signatures_layout.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(signatures_layout)
        story.append(Spacer(1, 30))

        # === FOOTER PROFESSIONALE ===
        # Informazioni documento e timestamp
        timestamp = datetime.now().strftime('%d/%m/%Y alle %H:%M')
        
        footer_info = [
            [Paragraph("📄 INFORMAZIONI DOCUMENTO", highlight_style)],
            [Paragraph(f"Documento generato il {timestamp}", footer_style)],
            [Paragraph(f"Foglio Tecnico: {foglio.numero_foglio} | Sistema DB-Desk v2.0", footer_style)],
            [Paragraph("Questo documento è stato generato automaticamente dal sistema gestionale.", footer_style)]
        ]

        footer_table = Table(footer_info, colWidths=[18*cm])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor('#64748b')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))

        story.append(footer_table)

        footer_text = f"Foglio Tecnico n° {foglio.numero_foglio} • Generato il {timestamp}"
        story.append(Paragraph(footer_text, footer_style))

        # Genera PDF
        doc.build(story)

        # Aggiorna record nel database
        foglio.pdf_generato = True
        foglio.pdf_path = pdf_path
        foglio.updated_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(f"PDF moderno generato con ReportLab (con firme): {pdf_path}")
        return pdf_path

    except Exception as e:
        current_app.logger.error(f"Errore generazione PDF moderno ReportLab con firme per foglio {foglio.numero_foglio}: {str(e)}")
        raise Exception(f"Errore nella generazione del PDF moderno con firme: {str(e)}")


def genera_pdf_foglio_tecnico(foglio_id):
    """
    Genera un PDF per il foglio tecnico specificato usando il metodo migliore disponibile

    Strategia:
    1. Prima prova WeasyPrint con template HTML moderno (include firme)
    2. Se fallisce, usa ReportLab con firme incluse in modo sicuro
    3. Come ultimo fallback, genera HTML

    Args:
        foglio_id (int): ID del foglio tecnico

    Returns:
        str: Path del file PDF generato

    Raises:
        Exception: Se il foglio non esiste o errori nella generazione
    """
    # Carica foglio dal database
    from app.models.foglio_tecnico import FoglioTecnico
    foglio = FoglioTecnico.query.get(foglio_id)
    if not foglio:
        raise ValueError(f"Foglio tecnico {foglio_id} non trovato")

    try:
        # Prima opzione: WeasyPrint con template HTML moderno e firme
        current_app.logger.info("Tentativo generazione PDF con WeasyPrint (template HTML con firme)")
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration

        # Crea cartella PDF se non esiste
        pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fogli_tecnici_pdf')
        os.makedirs(pdf_dir, exist_ok=True)

        # Nome file PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{foglio.numero_foglio}_{timestamp}.pdf"
        pdf_path = os.path.join(pdf_dir, filename)

        # Render template HTML con firme
        html_content = render_template(
            'fogli_tecnici/pdf_template.html',
            foglio=foglio,
            timestamp=timestamp,
            get_signature_base64=get_signature_base64
        )

        # Genera PDF con WeasyPrint
        font_config = FontConfiguration()
        html_doc = HTML(string=html_content)
        css_content = """
        @page {
            size: A4;
            margin: 1.5cm;
        }

        body {
            font-family: 'Inter', 'Arial', sans-serif;
            font-size: 11px;
            line-height: 1.6;
            color: #1f2937;
        }
        """
        css_doc = CSS(string=css_content, font_config=font_config)

        html_doc.write_pdf(pdf_path, stylesheets=[css_doc], font_config=font_config)

        # Aggiorna record nel database
        foglio.pdf_generato = True
        foglio.pdf_path = pdf_path
        foglio.updated_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(f"PDF generato con WeasyPrint (con firme): {pdf_path}")
        return pdf_path

    except (ImportError, OSError, Exception) as weasyprint_error:
        current_app.logger.warning(f"WeasyPrint fallito ({str(weasyprint_error)}), usando ReportLab con firme")

        try:
            # Seconda opzione: ReportLab con firme incluse in modo sicuro
            return genera_pdf_con_reportlab_con_firme(foglio)
        except Exception as reportlab_error:
            current_app.logger.error(f"Anche ReportLab fallito ({str(reportlab_error)}), generando HTML")

            # Ultimo fallback: HTML
            return genera_html_foglio_tecnico(foglio_id)


def genera_html_foglio_tecnico(foglio_id):
    """
    Genera un file HTML del foglio tecnico come fallback quando WeasyPrint non è disponibile
    
    Args:
        foglio_id (int): ID del foglio tecnico
        
    Returns:
        str: Path del file HTML generato
    """
    # Carica foglio dal database
    foglio = FoglioTecnico.query.get(foglio_id)
    if not foglio:
        raise ValueError(f"Foglio tecnico {foglio_id} non trovato")
    
    try:
        # Crea cartella HTML se non esiste
        html_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fogli_tecnici_html')
        os.makedirs(html_dir, exist_ok=True)
        
        # Nome file HTML
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{foglio.numero_foglio}_{timestamp}.html"
        html_path = os.path.join(html_dir, filename)
        
        # Render template HTML
        html_content = render_template(
            'fogli_tecnici/pdf_template.html',
            foglio=foglio,
            timestamp=timestamp,
            is_html=True,  # Flag per template per adattare lo stile
            get_signature_base64=get_signature_base64
        )
        
        # Salva HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Aggiorna record nel database
        foglio.pdf_generato = True
        foglio.pdf_path = html_path
        foglio.updated_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"HTML generato per foglio {foglio.numero_foglio}: {html_path}")
        return html_path
        
    except Exception as e:
        current_app.logger.error(f"Errore generazione HTML per foglio {foglio.numero_foglio}: {str(e)}")
        raise Exception(f"Errore nella generazione dell'HTML: {str(e)}")


def get_foglio_pdf_path(foglio_id):
    """
    Restituisce il path del PDF di un foglio se esiste
    
    Args:
        foglio_id (int): ID del foglio tecnico
        
    Returns:
        str|None: Path del PDF o None se non esiste
    """
    foglio = FoglioTecnico.query.get(foglio_id)
    if not foglio or not foglio.pdf_generato or not foglio.pdf_path:
        return None
    
    # Verifica che il file esista fisicamente
    if os.path.exists(foglio.pdf_path):
        return foglio.pdf_path
    
    # Se il record dice che esiste ma il file no, aggiorna il database
    foglio.pdf_generato = False
    foglio.pdf_path = None
    db.session.commit()
    
    return None


def elimina_pdf_foglio_tecnico(foglio_id):
    """
    Elimina il PDF di un foglio tecnico
    
    Args:
        foglio_id (int): ID del foglio tecnico
        
    Returns:
        bool: True se eliminato con successo
    """
    try:
        foglio = FoglioTecnico.query.get(foglio_id)
        if not foglio:
            return False
        
        # Elimina file fisico se esiste
        if foglio.pdf_path and os.path.exists(foglio.pdf_path):
            os.remove(foglio.pdf_path)
        
        # Aggiorna database
        foglio.pdf_generato = False
        foglio.pdf_path = None
        foglio.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Errore eliminazione PDF foglio {foglio_id}: {str(e)}")
        return False


def rigenera_pdf_foglio_tecnico(foglio_id):
    """
    Rigenera il PDF di un foglio tecnico eliminando quello esistente
    
    Args:
        foglio_id (int): ID del foglio tecnico
        
    Returns:
        str: Path del nuovo PDF generato
    """
    # Elimina PDF esistente
    elimina_pdf_foglio_tecnico(foglio_id)
    
    # Genera nuovo PDF
    return genera_pdf_foglio_tecnico(foglio_id)
