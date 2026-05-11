from datetime import datetime, time
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _fmt_date_it(value):
    if not value:
        return ''
    return value.strftime('%d/%m/%Y')


def _fmt_time_it(value):
    if not value:
        return ''
    return value.strftime('%H:%M')


def _label_tipo_operazione(value):
    labels = {
        'riparazione_cliente': 'Riparazione presso cliente',
        'prestito_semplice': 'Prestito d uso semplice',
        'riparazione_sede_con_prestito': 'Riparazione in sede con prestito',
        'riparazione_sede': 'Riparazione in sede'
    }
    return labels.get(value, value or '')


def _to_day_range(dt_value, is_end=False):
    if not dt_value:
        return None
    day = dt_value.date()
    return datetime.combine(day, time.max if is_end else time.min)


def build_ticket_daily_report_pdf(pdf_path, tickets, created_by_name, date_from, date_to, criticita_note='', tempi_stimati_note=''):
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        'TicketReportNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12
    )
    bold = ParagraphStyle(
        'TicketReportBold',
        parent=normal,
        fontName='Helvetica-Bold'
    )
    title = ParagraphStyle(
        'TicketReportTitle',
        parent=bold,
        fontSize=14,
        leading=16,
        alignment=1
    )
    subtitle = ParagraphStyle(
        'TicketReportSubtitle',
        parent=normal,
        fontSize=11,
        leading=13,
        alignment=1
    )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        topMargin=1.4 * cm,
        bottomMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm
    )

    story = []
    story.append(Paragraph('MAREL S.R.L.', ParagraphStyle('Company', parent=bold, fontSize=13, alignment=1)))
    story.append(Paragraph('ALLEGATO A', ParagraphStyle('Attach', parent=bold, fontSize=12, alignment=1)))
    story.append(Spacer(1, 4))
    story.append(Paragraph('MODELLO DI REPORTISTICA GIORNALIERA DELLE ATTIVITA', title))
    story.append(Paragraph('Reparto tecnico-informatico - MAREL S.R.L.', subtitle))
    story.append(Spacer(1, 8))

    range_label = f"{_fmt_date_it(date_from)} - {_fmt_date_it(date_to)}"
    story.append(Paragraph(f"<b>Intervallo:</b> {range_label}", normal))
    story.append(Paragraph(f"<b>Dipendente:</b> {created_by_name}", normal))
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>A) Chiamate da/verso la clientela</b>', bold))
    story.append(Paragraph('Riporta ogni chiamata ricevuta o effettuata con identificativo cliente, durata e oggetto.', normal))
    story.append(Spacer(1, 6))

    headers = ['N.', 'Ora inizio', 'Ora fine', 'Cliente', 'Tipo attivita', 'Oggetto / descrizione', 'Esito', 'Note']
    rows = [headers]
    for ticket in tickets:
        rows.append([
            ticket.numero_ticket or '',
            _fmt_time_it(ticket.ora_inizio_lavoro),
            _fmt_time_it(ticket.ora_fine_lavoro),
            ticket.cliente.ragione_sociale if ticket.cliente else '',
            _label_tipo_operazione(ticket.tipo_operazione or ticket.categoria),
            (ticket.descrizione or '')[:95],
            ticket.stato or '',
            (ticket.note_interne or '')[:65]
        ])

    min_rows = 14
    while len(rows) - 1 < min_rows:
        rows.append([''] * len(headers))

    table = Table(
        rows,
        colWidths=[1.4 * cm, 1.8 * cm, 1.8 * cm, 3.1 * cm, 2.3 * cm, 4.8 * cm, 1.7 * cm, 2.3 * cm]
    )
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f2')),
        ('LEADING', (0, 1), (-1, -1), 9),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>B) Criticita rilevate e attivita non concluse</b>', bold))
    criticita_text = criticita_note.strip() if criticita_note else '\n\n\n'
    criticita_box = Table([[Paragraph(criticita_text.replace('\n', '<br/>'), normal)]], colWidths=[18.2 * cm], rowHeights=[2.8 * cm])
    criticita_box.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.6, colors.black), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(Spacer(1, 4))
    story.append(criticita_box)
    story.append(Spacer(1, 8))

    story.append(Paragraph('<b>C) Tempi stimati di completamento delle attivita in corso</b>', bold))
    tempi_text = tempi_stimati_note.strip() if tempi_stimati_note else '\n\n\n'
    tempi_box = Table([[Paragraph(tempi_text.replace('\n', '<br/>'), normal)]], colWidths=[18.2 * cm], rowHeights=[2.8 * cm])
    tempi_box.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.6, colors.black), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(Spacer(1, 4))
    story.append(tempi_box)
    story.append(Spacer(1, 12))

    story.append(Paragraph('Trasmissione: il presente report deve essere compilato in ogni sua parte e trasmesso entro la fine della giornata lavorativa.', normal))
    story.append(Spacer(1, 16))
    signature_table = Table(
        [['Data: ____________________', f'Firma del dipendente: {created_by_name} ____________________']],
        colWidths=[8.8 * cm, 9.4 * cm]
    )
    signature_table.setStyle(TableStyle([('FONTSIZE', (0, 0), (-1, -1), 9)]))
    story.append(signature_table)

    doc.build(story)


def build_ticket_report_file_name(date_from, date_to, username):
    safe_username = ''.join(ch for ch in (username or 'utente') if ch.isalnum() or ch in ('-', '_')).strip('_') or 'utente'
    return f"report_ticket_DAL_{date_from.strftime('%Y-%m-%d')}_AL_{date_to.strftime('%Y-%m-%d')}-{safe_username}.pdf"


def get_filter_range(start_raw, end_raw):
    date_from = datetime.strptime(start_raw, '%Y-%m-%d')
    date_to = datetime.strptime(end_raw, '%Y-%m-%d')
    return _to_day_range(date_from), _to_day_range(date_to, is_end=True), date_from, date_to
