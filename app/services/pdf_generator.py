"""
Servizio per la generazione di PDF dai fogli tecnici usando ReportLab
Design minimal e pulito
"""

from flask import current_app
import os
from datetime import datetime
from app import db
from app.models.foglio_tecnico import FoglioTecnico

# Importazioni ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def genera_pdf_foglio_tecnico(foglio_id):
    """
    Genera un PDF per il foglio tecnico usando SOLO ReportLab
    Design minimal e pulito
    
    Args:
        foglio_id (int): ID del foglio tecnico
        
    Returns:
        str: Path del file PDF generato
    """
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

        # Crea documento PDF - MINIMAL
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            topMargin=2*cm,
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm
        )

        # === STILI MINIMAL E PROFESSIONALI ===
        styles = getSampleStyleSheet()
        
        # Colori minimal
        COLOR_PRIMARY = colors.HexColor('#2c3e50')  # Grigio scuro
        COLOR_SECONDARY = colors.HexColor('#7f8c8d')  # Grigio medio
        COLOR_ACCENT = colors.HexColor('#3498db')  # Blu accent
        COLOR_BG_LIGHT = colors.HexColor('#f8f9fa')  # Grigio molto chiaro
        COLOR_BORDER = colors.HexColor('#dee2e6')  # Grigio bordi
        
        # Stile nome azienda (header)
        company_name_style = ParagraphStyle(
            'CompanyName',
            parent=styles['Heading1'],
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=COLOR_PRIMARY,
            spaceAfter=3,
            alignment=TA_LEFT
        )
        
        # Stile dettagli azienda
        company_detail_style = ParagraphStyle(
            'CompanyDetail',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            textColor=COLOR_SECONDARY,
            spaceAfter=2,
            alignment=TA_LEFT
        )
        
        # Titolo foglio tecnico
        doc_title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=COLOR_PRIMARY,
            spaceAfter=8,
            spaceBefore=15,
            alignment=TA_CENTER
        )
        
        # Numero foglio
        doc_number_style = ParagraphStyle(
            'DocNumber',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=COLOR_ACCENT,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Titoli sezione con box colorato
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            spaceBefore=15,
            spaceAfter=0,
            leftIndent=8,
            rightIndent=8
        )
        
        # Label campo
        field_label_style = ParagraphStyle(
            'FieldLabel',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=COLOR_SECONDARY,
            spaceAfter=2,
            textTransform='uppercase'
        )
        
        # Valore campo
        field_value_style = ParagraphStyle(
            'FieldValue',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            textColor=COLOR_PRIMARY,
            spaceAfter=0
        )
        
        # Testo in box
        box_text_style = ParagraphStyle(
            'BoxText',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            textColor=COLOR_PRIMARY,
            leading=14
        )
        
        # Stile firma (nome sotto firma)
        signature_name_style = ParagraphStyle(
            'SignatureName',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=COLOR_PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=2
        )
        
        # Stile label firma
        signature_label_style = ParagraphStyle(
            'SignatureLabel',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica',
            textColor=COLOR_SECONDARY,
            alignment=TA_CENTER
        )
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica',
            textColor=COLOR_SECONDARY,
            alignment=TA_CENTER
        )

        # === CONTENUTO ===
        story = []

        # === HEADER: LOGO SINISTRA + DATI AZIENDA DESTRA ===
        # TODO: Inserire logo aziendale (per ora testo placeholder)
        logo_cell = [
            Paragraph("DB-Desk", company_name_style),
            Paragraph("Sistema Gestionale", company_detail_style)
        ]
        
        # Dati azienda a destra
        company_data_cell = [
            Paragraph("Frigo Balance & Food Srl", company_detail_style),
            Paragraph("Via Rosa Luxemburg 12/14", company_detail_style),
            Paragraph("10093 Collegno (TO)", company_detail_style),
            Paragraph("P.IVA: 12621510010", company_detail_style),
            Paragraph("Tel: +39 011 092 2223 - Email: info@frigobalance.it", company_detail_style)
        ]
        
        header_table = Table(
            [[logo_cell, company_data_cell]],
            colWidths=[8.5*cm, 8.5*cm]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
        
        # Linea separatrice sotto header
        story.append(Spacer(1, 10))
        line = Table([['']], colWidths=[17*cm])
        line.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 2, COLOR_ACCENT),
        ]))
        story.append(line)

        # === TITOLO FOGLIO TECNICO ===
        story.append(Paragraph("FOGLIO TECNICO DI INTERVENTO", doc_title_style))
        story.append(Paragraph(f"N° {foglio.numero_foglio}", doc_number_style))

        # === SEZIONE: INFORMAZIONI GENERALI ===
        section_header = Table(
            [[Paragraph("INFORMAZIONI GENERALI", section_title_style)]],
            colWidths=[17*cm]
        )
        section_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_ACCENT),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(section_header)
        
        # Campi informazioni generali in griglia 2 colonne
        info_fields = []
        
        # Riga 1: Cliente | Tecnico
        row1 = []
        if foglio.cliente:
            cliente_cell = [
                Paragraph("CLIENTE", field_label_style),
                Paragraph(foglio.cliente.ragione_sociale, field_value_style)
            ]
        else:
            cliente_cell = [
                Paragraph("CLIENTE", field_label_style),
                Paragraph("N/A", field_value_style)
            ]
        
        tecnico_cell = [
            Paragraph("TECNICO", field_label_style),
            Paragraph(f"{foglio.tecnico.first_name} {foglio.tecnico.last_name}", field_value_style)
        ]
        row1 = [cliente_cell, tecnico_cell]
        info_fields.append(row1)
        
        # Riga 2: Data Intervento | Categoria
        data_cell = [
            Paragraph("DATA E ORA", field_label_style),
            Paragraph(foglio.data_intervento.strftime('%d/%m/%Y alle %H:%M'), field_value_style)
        ]
        
        categoria_cell = [
            Paragraph("CATEGORIA", field_label_style),
            Paragraph(foglio.categoria or 'Non specificata', field_value_style)
        ]
        info_fields.append([data_cell, categoria_cell])
        
        # Riga 3: Priorità | Stato
        priorita_cell = [
            Paragraph("PRIORITÀ", field_label_style),
            Paragraph(foglio.priorita or 'Media', field_value_style)
        ]
        
        stato_cell = [
            Paragraph("STATO", field_label_style),
            Paragraph(foglio.stato, field_value_style)
        ]
        info_fields.append([priorita_cell, stato_cell])
        
        # Riga 4 opzionale: Durata | Km percorsi
        if foglio.durata_intervento or foglio.km_percorsi:
            durata_cell = [
                Paragraph("DURATA", field_label_style),
                Paragraph(f"{foglio.durata_intervento} minuti" if foglio.durata_intervento else "N/A", field_value_style)
            ]
            
            km_cell = [
                Paragraph("KM PERCORSI", field_label_style),
                Paragraph(f"{foglio.km_percorsi} km" if foglio.km_percorsi else "N/A", field_value_style)
            ]
            info_fields.append([durata_cell, km_cell])
        
        info_table = Table(info_fields, colWidths=[8.5*cm, 8.5*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 15))

        # === SEZIONE: DETTAGLI INTERVENTO ===
        if foglio.titolo or foglio.descrizione or foglio.indirizzo_intervento:
            section_header = Table(
                [[Paragraph("DETTAGLI INTERVENTO", section_title_style)]],
                colWidths=[17*cm]
            )
            section_header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_ACCENT),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(section_header)
            
            details_content = []
            
            if foglio.titolo:
                details_content.append([
                    Paragraph("OGGETTO", field_label_style),
                    Paragraph(foglio.titolo, field_value_style)
                ])
            
            if foglio.descrizione:
                details_content.append([
                    Paragraph("DESCRIZIONE", field_label_style),
                    Paragraph(foglio.descrizione.replace('\n', '<br/>'), box_text_style)
                ])
            
            if foglio.indirizzo_intervento:
                details_content.append([
                    Paragraph("LUOGO INTERVENTO", field_label_style),
                    Paragraph(foglio.indirizzo_intervento, field_value_style)
                ])
            
            details_table = Table(details_content, colWidths=[4*cm, 13*cm])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(details_table)
            story.append(Spacer(1, 15))

        # === SEZIONE: MACCHINE ===
        if foglio.macchine_collegate.count() > 0:
            section_header = Table(
                [[Paragraph("MACCHINE E ATTREZZATURE", section_title_style)]],
                colWidths=[17*cm]
            )
            section_header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_ACCENT),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(section_header)
            
            macchine_data = []
            for i, macchina in enumerate(foglio.macchine_collegate, 1):
                macchina_text = f"{i}. {macchina.codice} - {macchina.marca} {macchina.modello}"
                if macchina.numero_serie:
                    macchina_text += f"<br/>S/N: {macchina.numero_serie}"
                macchine_data.append([Paragraph(macchina_text, box_text_style)])
            
            macchine_table = Table(macchine_data, colWidths=[17*cm])
            macchine_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(macchine_table)
            story.append(Spacer(1, 15))

        # === SEZIONE: RICAMBI ===
        if foglio.ricambi_utilizzati.count() > 0:
            section_header = Table(
                [[Paragraph("RICAMBI E MATERIALI", section_title_style)]],
                colWidths=[17*cm]
            )
            section_header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_ACCENT),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(section_header)
            
            ricambi_data = []
            for i, ricambio in enumerate(foglio.ricambi_utilizzati, 1):
                ricambio_text = f"{i}. {ricambio.codice} - {ricambio.descrizione}"
                if ricambio.fornitore:
                    ricambio_text += f"<br/>Fornitore: {ricambio.fornitore}"
                ricambi_data.append([Paragraph(ricambio_text, box_text_style)])
            
            ricambi_table = Table(ricambi_data, colWidths=[17*cm])
            ricambi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(ricambi_table)
            story.append(Spacer(1, 15))

        # === SEZIONE: NOTE ===
        if foglio.note_aggiuntive:
            section_header = Table(
                [[Paragraph("NOTE E OSSERVAZIONI", section_title_style)]],
                colWidths=[17*cm]
            )
            section_header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_ACCENT),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(section_header)
            
            notes_table = Table(
                [[Paragraph(foglio.note_aggiuntive.replace('\n', '<br/>'), box_text_style)]],
                colWidths=[17*cm]
            )
            notes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_BG_LIGHT),
                ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(notes_table)
            story.append(Spacer(1, 15))

        # === SEZIONE: INFORMAZIONI COMMERCIALI ===
        if foglio.modalita_pagamento or foglio.importo_intervento:
            section_header = Table(
                [[Paragraph("INFORMAZIONI COMMERCIALI", section_title_style)]],
                colWidths=[17*cm]
            )
            section_header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), COLOR_ACCENT),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(section_header)
            
            comm_fields = []
            
            # Riga 1: Modalità pagamento | Importo
            row1 = []
            if foglio.modalita_pagamento:
                pagamento_cell = [
                    Paragraph("MODALITÀ DI PAGAMENTO", field_label_style),
                    Paragraph(foglio.modalita_pagamento, field_value_style)
                ]
            else:
                pagamento_cell = [
                    Paragraph("MODALITÀ DI PAGAMENTO", field_label_style),
                    Paragraph("N/A", field_value_style)
                ]
            
            if foglio.importo_intervento:
                importo_cell = [
                    Paragraph("IMPORTO", field_label_style),
                    Paragraph(f"€ {foglio.importo_intervento:.2f}", ParagraphStyle(
                        'ImportoStyle',
                        parent=field_value_style,
                        fontSize=12,
                        fontName='Helvetica-Bold',
                        textColor=COLOR_ACCENT
                    ))
                ]
            else:
                importo_cell = [
                    Paragraph("IMPORTO", field_label_style),
                    Paragraph("N/A", field_value_style)
                ]
            
            comm_fields.append([pagamento_cell, importo_cell])
            
            # Riga 2: Già pagato | In garanzia
            pagato_cell = [
                Paragraph("GIÀ PAGATO", field_label_style),
                Paragraph('Sì' if foglio.pagamento_immediato else 'No', field_value_style)
            ]
            
            garanzia_cell = [
                Paragraph("IN GARANZIA", field_label_style),
                Paragraph('Sì' if hasattr(foglio, 'intervento_in_garanzia') and foglio.intervento_in_garanzia else 'No', field_value_style)
            ]
            comm_fields.append([pagato_cell, garanzia_cell])
            
            comm_table = Table(comm_fields, colWidths=[8.5*cm, 8.5*cm])
            comm_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(comm_table)
            story.append(Spacer(1, 15))

        # === SEZIONE: FIRME ===
        section_header = Table(
            [[Paragraph("FIRME DI ACCETTAZIONE", section_title_style)]],
            colWidths=[17*cm]
        )
        section_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_ACCENT),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(section_header)
        
        # Box firme affiancate
        firma_tecnico_content = []
        firma_cliente_content = []
        
        # Firma tecnico
        if foglio.firma_tecnico_path and os.path.exists(foglio.firma_tecnico_path):
            try:
                firma_img = RLImage(foglio.firma_tecnico_path, width=6*cm, height=3*cm)
                firma_tecnico_content.append(firma_img)
            except:
                firma_tecnico_content.append(Paragraph("_________________________", signature_name_style))
        else:
            firma_tecnico_content.append(Paragraph("_________________________", signature_name_style))
        
        firma_tecnico_content.append(Spacer(1, 5))
        firma_tecnico_content.append(Paragraph(f"{foglio.tecnico.first_name} {foglio.tecnico.last_name}", signature_name_style))
        firma_tecnico_content.append(Paragraph("TECNICO", signature_label_style))
        
        # Firma cliente
        if foglio.firma_cliente_path and os.path.exists(foglio.firma_cliente_path):
            try:
                firma_img = RLImage(foglio.firma_cliente_path, width=6*cm, height=3*cm)
                firma_cliente_content.append(firma_img)
            except:
                firma_cliente_content.append(Paragraph("_________________________", signature_name_style))
        else:
            firma_cliente_content.append(Paragraph("_________________________", signature_name_style))
        
        firma_cliente_content.append(Spacer(1, 5))
        if foglio.nome_firmatario_cliente:
            firma_cliente_content.append(Paragraph(foglio.nome_firmatario_cliente, signature_name_style))
        else:
            firma_cliente_content.append(Paragraph("_________________________", signature_name_style))
        firma_cliente_content.append(Paragraph("CLIENTE", signature_label_style))
        
        firme_table = Table(
            [[firma_tecnico_content, firma_cliente_content]],
            colWidths=[8.5*cm, 8.5*cm]
        )
        firme_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(firme_table)

        # === FOOTER ===
        story.append(Spacer(1, 20))
        footer_line = Table([['']], colWidths=[17*cm])
        footer_line.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, COLOR_BORDER),
        ]))
        story.append(footer_line)
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"Documento generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", footer_style))
        story.append(Paragraph(f"DB-Desk - Foglio Tecnico N° {foglio.numero_foglio}", footer_style))

        # Genera PDF
        doc.build(story)

        # Aggiorna database
        foglio.pdf_generato = True
        foglio.pdf_path = pdf_path
        foglio.updated_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(f"PDF generato con ReportLab per foglio {foglio.numero_foglio}: {pdf_path}")
        return pdf_path

    except Exception as e:
        current_app.logger.error(f"Errore generazione PDF per foglio {foglio.numero_foglio}: {str(e)}")
        raise Exception(f"Errore nella generazione del PDF: {str(e)}")


# Funzioni di utilità
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

