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
    Genera un PDF usando ReportLab (più compatibile con Windows)
    
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
        
        # Crea documento PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
        
        # Stili
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#007bff')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#2c3e50')
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        normal_style.spaceAfter = 6
        
        # Contenuto del PDF
        story = []
        
        # Header
        story.append(Paragraph("DB-DESK", title_style))
        story.append(Paragraph("FOGLIO TECNICO DI INTERVENTO", heading_style))
        story.append(Paragraph(f"N. {foglio.numero_foglio}", normal_style))
        story.append(Spacer(1, 20))
        
        # Informazioni base
        story.append(Paragraph("INFORMAZIONI GENERALI", heading_style))
        
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
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Descrizione
        if foglio.descrizione:
            story.append(Paragraph("DESCRIZIONE INTERVENTO", heading_style))
            story.append(Paragraph(foglio.descrizione.replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 15))
        
        # Macchine coinvolte
        if foglio.macchine_collegate.count() > 0:
            story.append(Paragraph("MACCHINE COINVOLTE", heading_style))
            for macchina in foglio.macchine_collegate:
                story.append(Paragraph(f"• {macchina.codice} - {macchina.marca} {macchina.modello}", normal_style))
            story.append(Spacer(1, 15))
        
        # Ricambi utilizzati
        if foglio.ricambi_utilizzati.count() > 0:
            story.append(Paragraph("RICAMBI UTILIZZATI", heading_style))
            for ricambio in foglio.ricambi_utilizzati:
                story.append(Paragraph(f"• {ricambio.codice} - {ricambio.descrizione}", normal_style))
            story.append(Spacer(1, 15))
        
        # Informazioni commerciali
        if foglio.modalita_pagamento or foglio.importo_intervento:
            story.append(Paragraph("INFORMAZIONI COMMERCIALI", heading_style))
            if foglio.modalita_pagamento:
                story.append(Paragraph(f"Modalità di pagamento: {foglio.modalita_pagamento}", normal_style))
            if foglio.importo_intervento:
                story.append(Paragraph(f"Importo: € {foglio.importo_intervento:.2f}", normal_style))
            story.append(Spacer(1, 15))
        
        # Note aggiuntive
        if foglio.note_aggiuntive:
            story.append(Paragraph("NOTE AGGIUNTIVE", heading_style))
            story.append(Paragraph(foglio.note_aggiuntive.replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 20))
        
        # Firme - Versione semplificata per evitare problemi di compatibilità
        story.append(Paragraph("FIRME DI ACCETTAZIONE", heading_style))

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
                borderWidth=1,
                borderColor=colors.HexColor('#f59e0b'),
                borderPadding=10,
                backColor=colors.HexColor('#fef3c7')
            )
            dichiarazione_text = f"Il sottoscritto {foglio.nome_firmatario_cliente} dichiara di aver ricevuto l'intervento tecnico sopra descritto e di essere soddisfatto del lavoro svolto dal personale tecnico di DB-Desk."
            story.append(Paragraph(dichiarazione_text, dichiarazione_style))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph(f"Documento generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", footer_style))
        
        # Genera PDF
        doc.build(story)
        
        # Aggiorna record nel database
        foglio.pdf_generato = True
        foglio.pdf_path = pdf_path
        foglio.updated_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(f"PDF generato con ReportLab per foglio {foglio.numero_foglio}: {pdf_path}")
        return pdf_path

    except Exception as e:
        current_app.logger.error(f"Errore generazione PDF ReportLab per foglio {foglio.numero_foglio}: {str(e)}")
        raise Exception(f"Errore nella generazione del PDF: {str(e)}")


def genera_pdf_con_reportlab_con_firme(foglio):
    """
    Genera PDF con ReportLab includendo le firme in modo sicuro

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

        # Crea documento PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)

        # Stili
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#007bff')
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#2c3e50')
        )

        normal_style = styles['Normal']
        normal_style.fontSize = 10
        normal_style.spaceAfter = 6

        # Contenuto del PDF
        story = []

        # Header con design moderno
        story.append(Paragraph("DB-Desk", title_style))
        story.append(Paragraph("FOGLIO TECNICO DI INTERVENTO", heading_style))
        story.append(Paragraph(f"N. {foglio.numero_foglio}", normal_style))
        story.append(Spacer(1, 20))

        # Informazioni base
        story.append(Paragraph("INFORMAZIONI GENERALI", heading_style))

        info_data = [
            [f"Cliente: {foglio.cliente.ragione_sociale if foglio.cliente else 'N/A'}", f"Tecnico: {foglio.tecnico.first_name} {foglio.tecnico.last_name}"],
            [f"Data Intervento: {foglio.data_intervento.strftime('%d/%m/%Y %H:%M')}", f"Categoria: {foglio.categoria}"],
            [f"Priorità: {foglio.priorita}", f"Stato: {foglio.stato}"]
        ]

        info_table = Table(info_data, colWidths=[8*cm, 8*cm], rowHeights=[0.8*cm, 0.8*cm, 0.8*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(info_table)
        story.append(Spacer(1, 15))

        # Dettagli intervento
        if foglio.titolo:
            story.append(Paragraph("DETTAGLI INTERVENTO", heading_style))
            story.append(Paragraph(f"Titolo: {foglio.titolo}", normal_style))
            story.append(Spacer(1, 5))

        if foglio.descrizione:
            story.append(Paragraph("Descrizione:", normal_style))
            story.append(Paragraph(foglio.descrizione, normal_style))
            story.append(Spacer(1, 10))

        # Macchine coinvolte
        if foglio.macchine_collegate.count() > 0:
            story.append(Paragraph("MACCHINE COINVOLTE", heading_style))
            for macchina in foglio.macchine_collegate:
                story.append(Paragraph(f"• {macchina.codice} - {macchina.marca} {macchina.modello}", normal_style))
            story.append(Spacer(1, 15))

        # Ricambi utilizzati
        if foglio.ricambi_utilizzati.count() > 0:
            story.append(Paragraph("RICAMBI UTILIZZATI", heading_style))
            for ricambio in foglio.ricambi_utilizzati:
                story.append(Paragraph(f"• {ricambio.codice} - {ricambio.descrizione}", normal_style))
            story.append(Spacer(1, 15))

        # Informazioni commerciali
        if foglio.modalita_pagamento or foglio.importo_intervento:
            story.append(Paragraph("INFORMAZIONI COMMERCIALI", heading_style))
            if foglio.modalita_pagamento:
                story.append(Paragraph(f"Modalità di pagamento: {foglio.modalita_pagamento}", normal_style))
            if foglio.importo_intervento:
                story.append(Paragraph(f"Importo: € {foglio.importo_intervento:.2f}", normal_style))
            story.append(Spacer(1, 15))

        # Note aggiuntive
        if foglio.note_aggiuntive:
            story.append(Paragraph("NOTE AGGIUNTIVE", heading_style))
            story.append(Paragraph(foglio.note_aggiuntive.replace('\n', '<br/>'), normal_style))
            story.append(Spacer(1, 20))

        # Sezione firme migliorata
        story.append(Paragraph("FIRME DI ACCETTAZIONE", heading_style))

        # Firma tecnico
        story.append(Paragraph(f"Firma del Tecnico: {foglio.tecnico.first_name} {foglio.tecnico.last_name}", normal_style))
        story.append(Paragraph("___________________________", normal_style))
        if foglio.firma_tecnico_path and os.path.exists(foglio.firma_tecnico_path):
            story.append(Paragraph("✓ Firma digitale presente", styles['Italic']))
        story.append(Spacer(1, 10))

        # Firma cliente
        cliente_nome = foglio.nome_firmatario_cliente or "Nome del cliente"
        story.append(Paragraph(f"Firma del Cliente: {cliente_nome}", normal_style))
        story.append(Paragraph("___________________________", normal_style))
        if foglio.firma_cliente_path and os.path.exists(foglio.firma_cliente_path):
            story.append(Paragraph("✓ Firma digitale presente", styles['Italic']))
        story.append(Spacer(1, 15))

        # Dichiarazione di accettazione
        if foglio.nome_firmatario_cliente:
            dichiarazione_style = ParagraphStyle(
                'Dichiarazione',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#374151'),
                borderWidth=1,
                borderColor=colors.HexColor('#f59e0b'),
                borderPadding=10,
                backColor=colors.HexColor('#fef3c7')
            )
            dichiarazione_text = f"Il sottoscritto {foglio.nome_firmatario_cliente} dichiara di aver ricevuto l'intervento tecnico sopra descritto e di essere soddisfatto del lavoro svolto dal personale tecnico di DB-Desk."
            story.append(Paragraph(dichiarazione_text, dichiarazione_style))
            story.append(Spacer(1, 15))

        # Nota sulle firme digitali
        if foglio.firma_tecnico_path or foglio.firma_cliente_path:
            story.append(Paragraph("NOTA: Le firme digitali originali sono conservate nel sistema e disponibili per verifica.", styles['Italic']))
            story.append(Spacer(1, 10))

        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph(f"Documento generato automaticamente da DB-Desk il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", footer_style))

        # Genera PDF
        doc.build(story)

        # Aggiorna record nel database
        foglio.pdf_generato = True
        foglio.pdf_path = pdf_path
        foglio.updated_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(f"PDF generato con ReportLab (con firme): {pdf_path}")
        return pdf_path

    except Exception as e:
        current_app.logger.error(f"Errore generazione PDF ReportLab con firme per foglio {foglio.numero_foglio}: {str(e)}")
        raise Exception(f"Errore nella generazione del PDF con firme: {str(e)}")


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
