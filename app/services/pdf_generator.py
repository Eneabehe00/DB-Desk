"""
Servizio per la generazione di PDF dai fogli tecnici usando ReportLab
Design moderno e minimale — Header aziendale, card info, footer con firme
Layout compatto su singola pagina A4
"""

from flask import current_app
import os
from datetime import datetime
from xml.sax.saxutils import escape
from app import db
from app.models.foglio_tecnico import FoglioTecnico

# Importazioni ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas as rl_canvas

# ──────────────────────────────────────────────
#  PALETTE COLORI (minimal)
# ──────────────────────────────────────────────
C_PRIMARY    = colors.HexColor('#0f172a')
C_ACCENT     = colors.HexColor('#2563eb')
C_LIGHT_BG   = colors.HexColor('#f8fafc')
C_WHITE      = colors.white
C_BORDER     = colors.HexColor('#e2e8f0')
C_SECONDARY  = colors.HexColor('#64748b')
C_MUTED      = colors.HexColor('#94a3b8')
C_GREEN      = colors.HexColor('#15803d')
C_GREEN_BG   = colors.HexColor('#dcfce7')
C_SLATE_BG   = colors.HexColor('#f1f5f9')
C_HEADER_BG  = colors.HexColor('#0f172a')
C_FOOTER_META_H = 0.55 * cm   # striscia bassa footer (stile header)

VALORE_ASSENTE = "—"

TIPO_OPERAZIONE_LABELS = {
    '': 'Nessuna operazione',
    'riparazione_cliente': 'Riparazione presso cliente',
    'prestito_semplice': 'Prestito d\'uso semplice',
    'riparazione_sede_con_prestito': 'Riparazione in sede con prestito',
    'riparazione_sede': 'Riparazione in sede (solo ritiro)',
    'consegna_riparata': 'Consegna macchina riparata',
    'ritiro_riparazione': 'Ritiro per riparazione',
    'rientro_prestito': 'Rientro da prestito',
    'rientro_riparazione': 'Rientro da riparazione',
    'altro': 'Altro',
}


def _truncate_plain(text, max_len):
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _para_text(text, max_len=None):
    """Testo sicuro per Paragraph ReportLab (escape XML + troncamento opzionale)."""
    plain = (text or "").strip()
    if max_len is not None:
        plain = _truncate_plain(plain, max_len)
    return escape(plain)


PAGE_W, PAGE_H = A4
PAGE_PAD = 1.4 * cm       # margine interno header (logo/testi)
BODY_MARGIN_H = 1.0 * cm  # body e footer (più stretto della pagina piena)
CONTENT_W = PAGE_W - 2 * BODY_MARGIN_H

LOGO_MAX_H = 1.85 * cm
LOGO_MAX_W = 2.1 * cm


def _get_logo_path():
    """Percorso Logo.png (root progetto o cartella instance Flask)."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    candidates = [
        os.path.join(base, 'Logo.png'),
        os.path.join(base, 'logo.png'),
    ]
    try:
        root = current_app.root_path
        candidates.extend([
            os.path.join(root, 'Logo.png'),
            os.path.join(root, '..', 'Logo.png'),
        ])
    except RuntimeError:
        pass
    for path in candidates:
        path = os.path.abspath(path)
        if os.path.isfile(path):
            return path
    return None


def _logo_display_size(logo_path, max_w, max_h):
    """Calcola dimensioni logo in punti PDF mantenendo le proporzioni."""
    from reportlab.lib.utils import ImageReader

    iw, ih = ImageReader(logo_path).getSize()
    if iw <= 0 or ih <= 0:
        return 0, 0
    aspect = iw / ih
    logo_h = max_h
    logo_w = logo_h * aspect
    if logo_w > max_w:
        logo_w = max_w
        logo_h = logo_w / aspect
    return logo_w, logo_h


def _draw_header_logo(cv, logo_path, x, y, width, height):
    """Disegna Logo.png con canale alpha (PNG RGBA, sfondo trasparente)."""
    from reportlab.lib.utils import ImageReader

    cv.drawImage(
        ImageReader(logo_path),
        x,
        y,
        width=width,
        height=height,
        preserveAspectRatio=True,
        mask='auto',
    )


def genera_pdf_foglio_tecnico(foglio_id):
    """
    Genera un PDF per il foglio tecnico usando SOLO ReportLab.
    Design moderno: header aziendale a banda piena, card sezioni, footer firme.

    Args:
        foglio_id (int): ID del foglio tecnico

    Returns:
        str: Path del file PDF generato
    """
    foglio = FoglioTecnico.query.get(foglio_id)
    if not foglio:
        raise ValueError(f"Foglio tecnico {foglio_id} non trovato")

    try:
        # ── Percorso file ──────────────────────────────────────────────────
        pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fogli_tecnici_pdf')
        os.makedirs(pdf_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename  = f"{foglio.numero_foglio}_{timestamp}.pdf"
        pdf_path  = os.path.join(pdf_dir, filename)

        # ── Costanti layout ────────────────────────────────────────────────
        HEADER_H   = 2.45 * cm
        FOOTER_H   = 4.35 * cm
        SIGN_H     = 2.85 * cm
        PAY_GAP    = 0.18 * cm
        TOP_MARGIN = HEADER_H + 0.45 * cm

        # ── Stili tipografici ──────────────────────────────────────────────
        def style(name, **kw):
            base = kw.pop('parent', 'Normal')
            s = getSampleStyleSheet()
            return ParagraphStyle(name, parent=s[base], **kw)

        S_SECTION_TITLE = style('SectionTitle',
            fontSize=6, fontName='Helvetica-Bold',
            textColor=C_SECONDARY, spaceAfter=0, spaceBefore=0,
            leading=7, alignment=TA_LEFT)

        S_LABEL = style('FieldLabel',
            fontSize=5.8, fontName='Helvetica-Bold',
            textColor=C_MUTED, spaceAfter=1, leading=7)

        S_VALUE = style('FieldValue',
            fontSize=7.8, fontName='Helvetica',
            textColor=C_PRIMARY, spaceAfter=0, leading=9.5)

        S_BODY = style('BodyText',
            fontSize=7.2, fontName='Helvetica',
            textColor=C_PRIMARY, leading=9.5)

        # ── Helpers ────────────────────────────────────────────────────────
        def lv_cell(label: str, value: str):
            """Cella label + valore impilati verticalmente."""
            return [
                Paragraph(label.upper(), S_LABEL),
                Paragraph(value or VALORE_ASSENTE, S_VALUE),
            ]

        def card_table(rows, col_widths):
            """Tabella stile card (sfondo trasparente, solo bordo)."""
            t = Table(rows, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('BOX',           (0, 0), (-1, -1), 0.4, C_BORDER),
                ('INNERGRID',     (0, 0), (-1, -1), 0.25, C_BORDER),
                ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING',    (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
                ('ROUNDEDCORNERS', [4]),
            ]))
            return t

        def plain_card(content_flowable):
            """Card a larghezza piena (sfondo trasparente)."""
            t = Table([[content_flowable]], colWidths=[CONTENT_W])
            t.setStyle(TableStyle([
                ('BOX',           (0, 0), (-1, -1), 0.4, C_BORDER),
                ('TOPPADDING',    (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING',   (0, 0), (-1, -1), 10),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
                ('ROUNDEDCORNERS', [4]),
            ]))
            return t

        def section_label(text: str):
            """Titolo sezione senza linea sotto."""
            t = Table([[Paragraph(text.upper(), S_SECTION_TITLE)]],
                      colWidths=[CONTENT_W])
            t.setStyle(TableStyle([
                ('LEFTPADDING',   (0, 0), (-1, -1), 1),
                ('TOPPADDING',    (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            return t

        def stato_chip(label: str, active: bool):
            """Badge compatto per stati booleani."""
            chip_style = style(
                'Chip',
                fontSize=6.5,
                fontName='Helvetica-Bold',
                textColor=C_GREEN if active else C_SECONDARY,
                alignment=TA_LEFT,
                leading=8,
            )
            bg = C_GREEN_BG if active else C_SLATE_BG
            t = Table([[Paragraph(label, chip_style)]], colWidths=[2.1 * cm])
            t.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (0, 0), bg),
                ('TOPPADDING',    (0, 0), (0, 0), 3),
                ('BOTTOMPADDING', (0, 0), (0, 0), 3),
                ('LEFTPADDING',   (0, 0), (0, 0), 6),
                ('RIGHTPADDING',  (0, 0), (0, 0), 6),
                ('ROUNDEDCORNERS', [3]),
            ]))
            return t

        importo_str = (
            f"€ {foglio.importo_intervento:,.2f}"
            if foglio.importo_intervento else VALORE_ASSENTE
        )
        pagamento_str = _truncate_plain(
            foglio.modalita_pagamento or "Non specificato", 36
        )
        pagato_label = "Pagato" if foglio.pagamento_immediato else "Non pagato"
        garanzia_val = (
            hasattr(foglio, 'intervento_in_garanzia') and foglio.intervento_in_garanzia
        )
        garanzia_lbl = "In garanzia" if garanzia_val else "Fuori garanzia"

        pay_col_w = CONTENT_W / 4
        pay_table = card_table([[
            lv_cell("Modalità pagamento", pagamento_str),
            lv_cell("Importo intervento", importo_str),
            [Paragraph("SALDO", S_LABEL), stato_chip(pagato_label, foglio.pagamento_immediato)],
            [Paragraph("GARANZIA", S_LABEL), stato_chip(garanzia_lbl, garanzia_val)],
        ]], [pay_col_w] * 4)
        _, pay_table_h = pay_table.wrap(CONTENT_W, PAGE_H)
        BOTTOM_MARGIN = FOOTER_H + PAY_GAP + pay_table_h + 0.4 * cm

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            leftMargin=BODY_MARGIN_H,
            rightMargin=BODY_MARGIN_H,
        )

        # ── Header / Footer disegnati sul canvas ──────────────────────────
        def draw_header_footer(cv, doc_obj):
            cv.saveState()
            w, h = A4

            # ── HEADER ─────────────────────────────────────────────────────
            cv.setFillColor(C_HEADER_BG)
            cv.rect(0, h - HEADER_H, w, HEADER_H, fill=1, stroke=0)

            text_left = PAGE_PAD
            logo_path = _get_logo_path()
            if logo_path:
                try:
                    logo_w, logo_h = _logo_display_size(
                        logo_path, LOGO_MAX_W, LOGO_MAX_H,
                    )
                    if logo_w > 0:
                        logo_x = PAGE_PAD
                        logo_y = h - HEADER_H + (HEADER_H - logo_h) / 2
                        _draw_header_logo(cv, logo_path, logo_x, logo_y, logo_w, logo_h)
                        text_left = logo_x + logo_w + 0.35 * cm
                except Exception as e:
                    current_app.logger.warning(
                        f'Logo header PDF non caricato: {e}'
                    )

            cv.setFont('Helvetica-Bold', 13)
            cv.setFillColor(C_WHITE)
            cv.drawString(text_left, h - 0.95 * cm, "Frigo Balance & Food Srl")

            cv.setFont('Helvetica', 6.8)
            cv.setFillColor(colors.HexColor('#cbd5e1'))
            cv.drawString(text_left, h - 1.55 * cm,
                          "Assistenza tecnica refrigerazione")

            right_x = w - PAGE_PAD
            cv.setFont('Helvetica', 6.5)
            cv.drawRightString(right_x, h - 0.9 * cm,
                               "Via Rosa Luxemburg 12/14 · 10093 Collegno (TO)")
            cv.drawRightString(right_x, h - 1.35 * cm,
                               "P.IVA 12621510010  ·  011 092 2223  ·  info@frigobalance.it")

            # ── FOOTER (bianco + striscia meta scura in basso) ─────────────
            footer_top = FOOTER_H

            # Card pagamento (sopra la zona firme)
            pay_y = footer_top + PAY_GAP
            pay_table.drawOn(cv, BODY_MARGIN_H, pay_y)

            # Striscia inferiore come l'header (numero doc / pagina)
            cv.setFillColor(C_HEADER_BG)
            cv.rect(0, 0, w, C_FOOTER_META_H, fill=1, stroke=0)

            cv.setFont('Helvetica', 6)
            cv.setFillColor(colors.HexColor('#94a3b8'))
            meta_y = C_FOOTER_META_H * 0.32
            cv.drawString(
                PAGE_PAD, meta_y,
                f"{foglio.numero_foglio}  ·  "
                f"Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            )
            cv.drawRightString(w - PAGE_PAD, meta_y, "Pag. 1 / 1")

            sign_y = C_FOOTER_META_H + 0.38 * cm
            sign_gap = 0.4 * cm
            sign_inner_w = w - 2 * BODY_MARGIN_H
            sign_box_w = (sign_inner_w - sign_gap) / 2
            sign_left_x = BODY_MARGIN_H
            sign_right_x = BODY_MARGIN_H + sign_box_w + sign_gap

            def draw_sign_box(x, y, bw, bh, title, img_path, name_str):
                cv.setFillColor(colors.HexColor('#fafbfc'))
                cv.setStrokeColor(C_BORDER)
                cv.setLineWidth(0.45)
                cv.roundRect(x, y, bw, bh, 4, fill=1, stroke=1)

                cv.setFont('Helvetica-Bold', 6)
                cv.setFillColor(C_MUTED)
                cv.drawString(x + 8, y + bh - 12, title.upper())

                name_zone = 0.5 * cm
                nome_y = y + 10
                cv.setFont('Helvetica-Bold', 7.2)
                cv.setFillColor(C_PRIMARY)
                nome = _truncate_plain(name_str or "", 42)
                cv.drawCentredString(x + bw / 2, nome_y, nome)

                line_y = y + name_zone + 8
                cv.setStrokeColor(C_BORDER)
                cv.setLineWidth(0.35)
                cv.line(x + 12, line_y, x + bw - 12, line_y)

                firma_top = y + bh - 0.4 * cm
                if img_path and os.path.exists(img_path):
                    try:
                        zone_h = firma_top - line_y - 4
                        img_h_val = min(zone_h * 0.78, 1.25 * cm)
                        img_w_val = bw * 0.55
                        img_x_val = x + (bw - img_w_val) / 2
                        img_y_val = line_y + zone_h - img_h_val - 2
                        cv.drawImage(
                            img_path, img_x_val, img_y_val,
                            width=img_w_val, height=img_h_val,
                            preserveAspectRatio=True, mask='auto',
                        )
                    except Exception:
                        pass

            tecnico_nome = f"{foglio.tecnico.first_name} {foglio.tecnico.last_name}"
            cliente_nome = foglio.nome_firmatario_cliente or "_______________"

            draw_sign_box(
                sign_left_x, sign_y, sign_box_w, SIGN_H,
                "Firma tecnico", foglio.firma_tecnico_path, tecnico_nome,
            )
            draw_sign_box(
                sign_right_x, sign_y, sign_box_w, SIGN_H,
                "Firma cliente", foglio.firma_cliente_path, cliente_nome,
            )

            cv.restoreState()

        # ── Mesi italiani ──────────────────────────────────────────────────
        MESI_IT = {
            1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
            5: "maggio",  6: "giugno",   7: "luglio", 8: "agosto",
            9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
        }

        def data_it(dt):
            if not dt:
                return VALORE_ASSENTE
            return f"{dt.day} {MESI_IT[dt.month]} {dt.year} — {dt.strftime('%H:%M')}"

        # ── Costruzione storia (body content) ─────────────────────────────
        story = []

        # ── 1. Titolo documento + data (stessa riga) ────────────────────────
        title_row = [[
            Paragraph(
                f"Foglio d'intervento  "
                f"<font color='#{C_ACCENT.hexval()[2:]}'><b>N° {foglio.numero_foglio}</b></font>",
                style('DocTitle',
                      fontSize=13, fontName='Helvetica-Bold',
                      textColor=C_PRIMARY, alignment=TA_LEFT, leading=16),
            ),
            Paragraph(
                data_it(foglio.data_intervento),
                style('DocDate',
                      fontSize=9, fontName='Helvetica',
                      textColor=C_MUTED, alignment=TA_RIGHT, leading=16),
            ),
        ]]
        t_title = Table(title_row, colWidths=[CONTENT_W * 0.58, CONTENT_W * 0.42])
        t_title.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING',   (0, 0), (-1, -1), 0),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
            ('TOPPADDING',    (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_title)
        story.append(Spacer(1, 10))

        # ── 2. Card: Dati intervento (3 colonne × 2 righe) ───────────────
        story.append(section_label("Dati intervento"))
        story.append(Spacer(1, 3))

        indirizzo = foglio.indirizzo_intervento or VALORE_ASSENTE
        durata_km = (
            f"{foglio.durata_intervento or '—'} min  /  "
            f"{foglio.km_percorsi or '—'} km"
        )
        col3 = CONTENT_W / 3

        row1 = [
            lv_cell("Cliente",  foglio.cliente.ragione_sociale[:40] if foglio.cliente else VALORE_ASSENTE),
            lv_cell("Tecnico",  f"{foglio.tecnico.first_name} {foglio.tecnico.last_name}"),
            lv_cell("Categoria", foglio.categoria or "Intervento"),
        ]
        row2 = [
            lv_cell("Indirizzo intervento", indirizzo[:50]),
            lv_cell("Durata / Km percorsi", durata_km),
        ]
        t_intervento = card_table([row1, row2], [col3, col3, col3])
        t_intervento.setStyle(TableStyle([('SPAN', (0, 1), (1, 1))]))
        story.append(t_intervento)
        story.append(Spacer(1, 8))

        # ── 3. Descrizione / Titolo intervento ────────────────────────────
        desc_text = ""
        if foglio.titolo:
            desc_text = foglio.titolo
        if foglio.descrizione and foglio.descrizione != foglio.titolo:
            desc_text = (desc_text + ": " + foglio.descrizione) if desc_text else foglio.descrizione

        if desc_text:
            story.append(section_label("Descrizione intervento"))
            story.append(Spacer(1, 3))
            story.append(plain_card(Paragraph(desc_text[:300], S_BODY)))
            story.append(Spacer(1, 8))

        # ── 4. Card: Macchine | Ricambi (2 colonne) ──────────────────────
        story.append(section_label("Apparecchiature e ricambi"))
        story.append(Spacer(1, 3))

        half = CONTENT_W / 2 - 0.2 * cm

        # — Macchine —
        mac_rows = []
        idx = 1
        if foglio.macchina_manuale and str(foglio.macchina_manuale).strip():
            mac_rows.append([Paragraph(
                f"<b>{idx}.</b>  {_para_text(foglio.macchina_manuale, 70)}", S_BODY)])
            idx += 1
        for m in foglio.macchine_collegate:
            desc = _para_text(f"{m.codice} — {m.marca} {m.modello}", 55)
            txt = f"<b>{idx}.</b>  {desc}"
            if m.numero_serie:
                sn = _para_text(m.numero_serie)
                txt += f"  <font color='#{C_SECONDARY.hexval()[2:]}' size='7'>(S/N: {sn})</font>"
            mac_rows.append([Paragraph(txt, S_BODY)])
            idx += 1
        if not mac_rows:
            mac_rows = [[Paragraph("Nessuna apparecchiatura registrata", S_BODY)]]

        # — Ricambi —
        ric_rows = []
        idx = 1
        if foglio.ricambio_manuale and str(foglio.ricambio_manuale).strip():
            ric_rows.append([Paragraph(
                f"<b>{idx}.</b>  {_para_text(foglio.ricambio_manuale, 70)}", S_BODY)])
            idx += 1
        for r in foglio.ricambi_utilizzati:
            txt = f"<b>{idx}.</b>  {_para_text(f'{r.codice} — {r.descrizione}', 80)}"
            ric_rows.append([Paragraph(txt, S_BODY)])
            idx += 1
        if not ric_rows:
            ric_rows = [[Paragraph("Nessun ricambio utilizzato", S_BODY)]]

        def mini_list_table(rows, col_w):
            t = Table(rows, colWidths=[col_w])
            t.setStyle(TableStyle([
                ('BOX',           (0, 0), (-1, -1), 0.4, C_BORDER),
                ('LINEBELOW',     (0, 0), (-1, -2), 0.25, C_BORDER),
                ('TOPPADDING',    (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
                ('ROUNDEDCORNERS', [4]),
            ]))
            return t

        mac_header = Paragraph(
            "Apparecchiature",
            style('MiniH', fontSize=6.5, fontName='Helvetica-Bold',
                  textColor=C_SECONDARY, leading=8),
        )
        ric_header = Paragraph(
            "Ricambi utilizzati",
            style('MiniH2', fontSize=6.5, fontName='Helvetica-Bold',
                  textColor=C_SECONDARY, leading=8),
        )

        left_col  = [mac_header, Spacer(1, 2), mini_list_table(mac_rows, half)]
        right_col = [ric_header, Spacer(1, 2), mini_list_table(ric_rows, half)]

        two_col = Table([[left_col, right_col]],
                        colWidths=[half + 0.2 * cm, half + 0.2 * cm])
        two_col.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING',   (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
        ]))
        story.append(two_col)
        story.append(Spacer(1, 8))

        # ── 5. Operazioni / movimenti macchine ────────────────────────────
        from app.models.macchina import MovimentoMacchina

        movimenti = (
            MovimentoMacchina.query.filter_by(foglio_id=foglio.id)
            .order_by(MovimentoMacchina.created_at.asc())
            .all()
        )
        tipo_op = foglio.tipo_operazione_macchine or ''
        tipo_op_label = TIPO_OPERAZIONE_LABELS.get(
            tipo_op, tipo_op or 'Non specificata'
        )

        if tipo_op or movimenti:
            story.append(section_label("Operazioni sulle macchine"))
            story.append(Spacer(1, 3))
            story.append(card_table(
                [[lv_cell("Tipo operazione", tipo_op_label)]],
                [CONTENT_W],
            ))
            story.append(Spacer(1, 4))

            S_TH = style(
                'MovTh',
                fontSize=6,
                fontName='Helvetica-Bold',
                textColor=C_SECONDARY,
                leading=7.5,
            )
            S_TD = style(
                'MovTd',
                fontSize=6.5,
                fontName='Helvetica',
                textColor=C_PRIMARY,
                leading=8,
            )
            S_TD_NOTE = style(
                'MovTdNote',
                fontSize=6.5,
                fontName='Helvetica',
                textColor=C_PRIMARY,
                leading=9,
            )

            if movimenti:
                mov_header = [
                    Paragraph('MACCHINA', S_TH),
                    Paragraph('MOVIMENTO', S_TH),
                    Paragraph('NOTE', S_TH),
                ]
                mov_rows = [mov_header]
                for mov in movimenti[:12]:
                    mac = mov.macchina
                    if mac:
                        mac_txt = _para_text(
                            f'{mac.codice} — {mac.marca} {mac.modello}', 42
                        )
                    else:
                        mac_txt = VALORE_ASSENTE
                    note_plain = (mov.note or '').strip() or VALORE_ASSENTE
                    note_html = escape(note_plain).replace('\n', '<br/>')
                    mov_rows.append([
                        Paragraph(mac_txt, S_TD),
                        Paragraph(_para_text(mov.tipo_movimento), S_TD),
                        Paragraph(note_html, S_TD_NOTE),
                    ])

                col_mov = [
                    CONTENT_W * 0.26,
                    CONTENT_W * 0.22,
                    CONTENT_W * 0.52,
                ]
                t_mov = Table(mov_rows, colWidths=col_mov, repeatRows=1)
                t_mov.setStyle(TableStyle([
                    ('BOX',           (0, 0), (-1, -1), 0.4, C_BORDER),
                    ('INNERGRID',     (0, 0), (-1, -1), 0.25, C_BORDER),
                    ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING',    (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
                    ('ROUNDEDCORNERS', [4]),
                ]))
                story.append(t_mov)
                if len(movimenti) > 12:
                    story.append(Spacer(1, 2))
                    story.append(Paragraph(
                        f'<font color="#{C_MUTED.hexval()[2:]}">'
                        f'… e altri {len(movimenti) - 12} movimenti</font>',
                        S_TD,
                    ))
            else:
                story.append(plain_card(Paragraph(
                    'Nessun movimento macchine registrato per questo foglio.',
                    S_BODY,
                )))

            story.append(Spacer(1, 8))

        # ── 6. Note aggiuntive ────────────────────────────────────────────
        if foglio.note_aggiuntive:
            story.append(section_label("Note aggiuntive"))
            story.append(Spacer(1, 3))
            note_testo = foglio.note_aggiuntive[:350]
            if len(foglio.note_aggiuntive) > 350:
                note_testo += "…"
            story.append(plain_card(Paragraph(note_testo, S_BODY)))
            story.append(Spacer(1, 8))

        # ── Build ──────────────────────────────────────────────────────────
        doc.build(
            story,
            onFirstPage=draw_header_footer,
            onLaterPages=draw_header_footer,
        )

        # ── Aggiorna DB ───────────────────────────────────────────────────
        foglio.pdf_generato = True
        foglio.pdf_path     = pdf_path
        foglio.updated_at   = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(
            f"PDF generato con ReportLab per foglio {foglio.numero_foglio}: {pdf_path}"
        )
        return pdf_path

    except Exception as e:
        current_app.logger.error(
            f"Errore generazione PDF per foglio {foglio.numero_foglio}: {str(e)}"
        )
        raise Exception(f"Errore nella generazione del PDF: {str(e)}")


# ──────────────────────────────────────────────────────────────────────────────
#  FUNZIONI DI UTILITÀ (invariate)
# ──────────────────────────────────────────────────────────────────────────────

def get_foglio_pdf_path(foglio_id):
    """
    Restituisce il path del PDF di un foglio se esiste.

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

    foglio.pdf_generato = False
    foglio.pdf_path     = None
    db.session.commit()
    return None


def elimina_pdf_foglio_tecnico(foglio_id):
    """
    Elimina il PDF di un foglio tecnico.

    Args:
        foglio_id (int): ID del foglio tecnico

    Returns:
        bool: True se eliminato con successo
    """
    try:
        foglio = FoglioTecnico.query.get(foglio_id)
        if not foglio:
            return False

        if foglio.pdf_path and os.path.exists(foglio.pdf_path):
            os.remove(foglio.pdf_path)

        foglio.pdf_generato = False
        foglio.pdf_path     = None
        foglio.updated_at   = datetime.utcnow()
        db.session.commit()
        return True

    except Exception as e:
        current_app.logger.error(
            f"Errore eliminazione PDF foglio {foglio_id}: {str(e)}"
        )
        return False


def rigenera_pdf_foglio_tecnico(foglio_id):
    """
    Rigenera il PDF di un foglio tecnico eliminando quello esistente.

    Args:
        foglio_id (int): ID del foglio tecnico

    Returns:
        str: Path del nuovo PDF generato
    """
    elimina_pdf_foglio_tecnico(foglio_id)
    return genera_pdf_foglio_tecnico(foglio_id)