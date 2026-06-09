#!/usr/bin/env python
"""
Crea fogli tecnici di test con il massimo di campi compilati.

Scenari:
  prestito  (default) — Riparazione in sede con prestito: macchina cliente in riparazione
                        + macchina sostitutiva in prestito + movimenti
  base      — Riparazione presso cliente (scenario precedente, valori diversi)
  max       — Come prestito + stato Inviato, email, più ricambi/macchine

Uso (dalla root del progetto):
    python scripts/create_test_foglio_completo.py
    python scripts/create_test_foglio_completo.py --scenario max
    python scripts/create_test_foglio_completo.py --scenario prestito --apply-stati
    python scripts/create_test_foglio_completo.py --cliente-id 398 --no-pdf
"""
import argparse
import os
import sys
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


SCENARIOS = {
    'prestito': {
        'tag': 'PRESTITO',
        'tipo_operazione_macchine': 'riparazione_sede_con_prestito',
        'titolo': '[TEST PRESTITO] Riparazione sega con macchina sostitutiva',
        'descrizione': (
            'Scenario test: riparazione in sede con prestito macchina sostitutiva.\n'
            'La sega del cliente (difetto motore) viene ritirata in laboratorio.\n'
            'Al cliente viene consegnata in prestito una bilancia/affettatrice sostitutiva '
            'per continuare l\'attività durante la riparazione.'
        ),
        'categoria': 'Riparazione',
        'priorita': 'Alta',
        'stato': 'Completato',
        'modalita_pagamento': 'Carta di credito/debito',
        'importo': Decimal('542.80'),
        'pagamento_immediato': True,
        'intervento_in_garanzia': False,
        'durata': 185,
        'km': 58,
        'macchina_manuale': 'Affettatrice Berkel 250 (scheda non in anagrafica — verificare S/N)',
        'ricambio_manuale': 'Kit cuscinetti universale KCU-45 + grasso alimentare (manuale)',
        'note': (
            'TEST COMPLETO — Prestito sostitutivo attivo fino a rientro sega riparata. '
            'Cliente formato su uso macchina in prestito. Prossima verifica tra 30 giorni.'
        ),
        'inviato_online': False,
    },
    'base': {
        'tag': 'BASE',
        'tipo_operazione_macchine': 'riparazione_cliente',
        'titolo': '[TEST BASE] Manutenzione bilancia e sega presso cliente',
        'descrizione': (
            'Intervento di test con riparazione presso cliente.\n'
            'Taratura bilancia, verifica sega, pulizia generale.'
        ),
        'categoria': 'Manutenzione',
        'priorita': 'Media',
        'stato': 'Completato',
        'modalita_pagamento': 'Bonifico bancario',
        'importo': Decimal('385.50'),
        'pagamento_immediato': False,
        'intervento_in_garanzia': True,
        'durata': 135,
        'km': 42,
        'macchina_manuale': 'Cs1200 29072845 (inserita manualmente)',
        'ricambio_manuale': 'Filtro aria universale FA-200 (inserito manualmente)',
        'note': (
            'Note di test: cliente informato su prossima manutenzione. '
            'Consigliata sostituzione filtro entro 6 mesi.'
        ),
        'inviato_online': False,
    },
    'max': {
        'tag': 'MAX',
        'tipo_operazione_macchine': 'riparazione_sede_con_prestito',
        'titolo': '[TEST MAX] Intervento full-field — prestito + fatturazione + invio',
        'descrizione': (
            'Foglio di test con TUTTI i campi valorizzati.\n'
            'Riparazione in sede, macchina sostitutiva, ricambi multipli, '
            'pagamento immediato, note estese, PDF e flag invio email.'
        ),
        'categoria': 'Installazione',
        'priorita': 'Alta',
        'stato': 'Inviato',
        'modalita_pagamento': 'Fatturazione differita',
        'importo': Decimal('1299.99'),
        'pagamento_immediato': False,
        'intervento_in_garanzia': False,
        'durata': 240,
        'km': 95,
        'macchina_manuale': 'Cella frigo display 350L — codice interno CEL-350-TMP',
        'ricambio_manuale': 'Termostato digitale TD-88 + guarnizione porta (inserimento manuale)',
        'note': (
            'TEST MASSIMO: verificare allineamento PDF, tab movimenti, firme, '
            'card pagamento (non pagato + fuori garanzia), liste macchine/ricambi.'
        ),
        'inviato_online': True,
    },
}


def _firme_esistenti():
    from app.models.foglio_tecnico import FoglioTecnico

    esempio = FoglioTecnico.query.filter(
        FoglioTecnico.firma_tecnico_path.isnot(None),
        FoglioTecnico.firma_cliente_path.isnot(None),
    ).first()
    if not esempio:
        return None, None
    t, c = esempio.firma_tecnico_path, esempio.firma_cliente_path
    if t and os.path.exists(t) and c and os.path.exists(c):
        return t, c
    return None, None


def _crea_firma_placeholder(app, numero_foglio, tipo):
    from PIL import Image, ImageDraw

    upload = app.config.get('UPLOAD_FOLDER', 'uploads')
    cartella = os.path.join(upload, 'signatures')
    os.makedirs(cartella, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(cartella, f'{numero_foglio}_{tipo}_{ts}.png')
    img = Image.new('RGB', (400, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.line([(30, 80), (120, 40), (200, 70), (320, 35)], fill=(30, 60, 120), width=3)
    draw.text((30, 15), f'Firma {tipo} (test)', fill=(100, 100, 100))
    img.save(path)
    return os.path.abspath(path)


def _trova_risorse(cliente_id=None):
    from app.models.cliente import Cliente
    from app.models.user import User
    from app.models.macchina import Macchina
    from app.models.ricambio import Ricambio

    if cliente_id:
        cliente = Cliente.query.filter_by(id=cliente_id, is_active=True).first()
    else:
        cliente = Cliente.query.filter_by(is_active=True, id=398).first()
    if not cliente:
        cliente = Cliente.query.filter_by(is_active=True).first()
    if not cliente:
        raise RuntimeError('Nessun cliente attivo trovato.')

    tecnico = User.query.filter_by(is_active=True, department_id=1).first()
    if not tecnico:
        tecnico = User.query.filter_by(is_active=True).first()
    if not tecnico:
        raise RuntimeError('Nessun tecnico attivo trovato.')

    macchine_cliente = (
        Macchina.query.filter_by(cliente_id=cliente.id)
        .order_by(Macchina.codice)
        .limit(3)
        .all()
    )
    if len(macchine_cliente) < 1:
        macchine_cliente = Macchina.query.filter(
            Macchina.cliente_id.isnot(None),
        ).order_by(Macchina.codice).limit(2).all()

    # Macchine da prestare: preferenza Disponibile in magazzino, altrimenti Attiva altro cliente
    macchine_sostitutive = (
        Macchina.query.filter(Macchina.stato.in_(['Disponibile', 'Attiva']))
        .filter(
            (Macchina.cliente_id.is_(None)) | (Macchina.cliente_id != cliente.id)
        )
        .order_by(Macchina.stato, Macchina.codice)
        .limit(2)
        .all()
    )
    if len(macchine_sostitutive) < 1:
        macchine_sostitutive = (
            Macchina.query.filter(Macchina.stato.in_(['Disponibile', 'Attiva', 'In prestito']))
            .filter(Macchina.cliente_id != cliente.id)
            .order_by(Macchina.codice)
            .limit(2)
            .all()
        )

    ricambi = Ricambio.query.order_by(Ricambio.codice).limit(4).all()
    if not ricambi:
        raise RuntimeError('Nessun ricambio trovato nel database.')

    return {
        'cliente': cliente,
        'tecnico': tecnico,
        'macchine_cliente': macchine_cliente,
        'macchine_sostitutive': macchine_sostitutive,
        'ricambi': ricambi,
    }


def _registra_movimento(db, macchina, foglio, tecnico, tipo_movimento,
                        stato_nuovo, note, apply_stati):
    """Registra movimento; opzionalmente aggiorna stato macchina come in step2."""
    from app.models.macchina import MovimentoMacchina

    stato_prec = macchina.stato
    if apply_stati and stato_nuovo and stato_nuovo != stato_prec:
        macchina.stato = stato_nuovo
        if stato_nuovo == 'In prestito':
            macchina.cliente_id = foglio.cliente_id
            macchina.ubicazione = f'Cliente: {foglio.cliente.ragione_sociale}'
        elif stato_nuovo == 'In riparazione':
            macchina.ubicazione = 'Riparazione in sede'

    mov = MovimentoMacchina(
        macchina_id=macchina.id,
        tipo_movimento=tipo_movimento,
        stato_precedente=stato_prec,
        stato_nuovo=macchina.stato,
        cliente_id=foglio.cliente_id,
        foglio_id=foglio.id,
        user_id=tecnico.id,
        note=note,
    )
    db.session.add(mov)
    return mov


def _applica_operazioni_macchine(db, foglio, cfg, risorse, apply_stati):
    """Simula step2: macchine collegate + movimenti (+ sostitutive se prestito)."""
    from app.models.foglio_tecnico import foglio_macchine

    tipo = cfg['tipo_operazione_macchine']
    tecnico = risorse['tecnico']
    cliente = risorse['cliente']
    numero = foglio.numero_foglio

    macchine_cliente = risorse['macchine_cliente']
    macchine_sost = risorse['macchine_sostitutive']

    for macchina in macchine_cliente:
        foglio.macchine_collegate.append(macchina)

    if tipo == 'riparazione_cliente':
        for macchina in macchine_cliente:
            _registra_movimento(
                db, macchina, foglio, tecnico,
                'Riparazione presso cliente', macchina.stato,
                f'Riparazione presso cliente — foglio test {numero}',
                apply_stati,
            )

    elif tipo == 'riparazione_sede_con_prestito':
        for macchina in macchine_cliente:
            _registra_movimento(
                db, macchina, foglio, tecnico,
                'Riparazione', 'In riparazione',
                f'Riparazione in sede con prestito — foglio test {numero}',
                apply_stati,
            )

        for macchina in macchine_sost:
            foglio.macchine_collegate.append(macchina)
            _registra_movimento(
                db, macchina, foglio, tecnico,
                'Assegnazione', 'In prestito',
                f'Prestito sostitutivo durante riparazione — foglio test {numero}',
                apply_stati,
            )

    elif tipo == 'prestito_semplice' and macchine_sost:
        macchina = macchine_sost[0]
        foglio.macchine_collegate.append(macchina)
        _registra_movimento(
            db, macchina, foglio, tecnico,
            'Assegnazione', 'In prestito',
            f'Prestito d\'uso semplice — foglio test {numero}',
            apply_stati,
        )


def _collega_ricambi(db, foglio, ricambi):
    from app.models.foglio_tecnico import foglio_ricambi

    quantita = [2, 1, 3, 1]
    for i, ricambio in enumerate(ricambi[:4]):
        qty = quantita[i] if i < len(quantita) else 1
        db.session.execute(
            foglio_ricambi.insert().values(
                foglio_id=foglio.id,
                ricambio_id=ricambio.id,
                quantita_utilizzata=qty,
            )
        )


def run(scenario='prestito', cliente_id=None, apply_stati=False, genera_pdf=True):
    from app import create_app, db
    from app.models.foglio_tecnico import FoglioTecnico
    from app.services.pdf_generator import genera_pdf_foglio_tecnico

    if scenario not in SCENARIOS:
        raise ValueError(f'Scenario sconosciuto: {scenario}. Usa: {", ".join(SCENARIOS)}')

    cfg = SCENARIOS[scenario]
    app = create_app()

    with app.app_context():
        risorse = _trova_risorse(cliente_id)
        cliente = risorse['cliente']
        tecnico = risorse['tecnico']

        if cfg['tipo_operazione_macchine'] == 'riparazione_sede_con_prestito':
            if not risorse['macchine_cliente']:
                raise RuntimeError(
                    'Servono macchine del cliente per scenario prestito. '
                    'Specifica --cliente-id con macchine in anagrafica.'
                )
            if not risorse['macchine_sostitutive']:
                print(
                    'ATTENZIONE: nessuna macchina idonea per prestito sostitutivo; '
                    'verranno registrati solo movimenti sulle macchine cliente.'
                )

        firma_tecnico, firma_cliente = _firme_esistenti()
        indirizzo = cliente.indirizzo_completo or (
            'Via Rosa Luxemburg 12/14, 10093 Collegno (TO)'
        )

        data_intervento = datetime(2026, 6, 3, 9, 15)
        email_invio = cliente.email or 'test.foglio@frigobalance.it'

        foglio = FoglioTecnico(
            titolo=cfg['titolo'],
            descrizione=cfg['descrizione'],
            categoria=cfg['categoria'],
            priorita=cfg['priorita'],
            stato=cfg['stato'],
            cliente_id=cliente.id,
            tecnico_id=tecnico.id,
            department_id=tecnico.department_id,
            indirizzo_intervento=indirizzo[:200],
            data_intervento=data_intervento,
            modalita_pagamento=cfg['modalita_pagamento'],
            importo_intervento=cfg['importo'],
            pagamento_immediato=cfg['pagamento_immediato'],
            intervento_in_garanzia=cfg['intervento_in_garanzia'],
            durata_intervento=cfg['durata'],
            km_percorsi=cfg['km'],
            note_aggiuntive=cfg['note'],
            tipo_operazione_macchine=cfg['tipo_operazione_macchine'],
            macchina_manuale=cfg['macchina_manuale'],
            ricambio_manuale=cfg['ricambio_manuale'],
            firma_tecnico_path=firma_tecnico,
            firma_cliente_path=firma_cliente,
            nome_firmatario_cliente='Dr. Paolo Testa — Responsabile qualità',
            step_corrente=5,
            step_completati=[1, 2, 3, 4, 5],
            completed_at=datetime.now(),
            email_invio=email_invio,
            inviato_online=cfg['inviato_online'],
            data_invio=datetime.now() if cfg['inviato_online'] else None,
        )

        db.session.add(foglio)
        db.session.flush()

        if not firma_tecnico or not firma_cliente:
            firma_tecnico = firma_tecnico or _crea_firma_placeholder(
                app, foglio.numero_foglio, 'tecnico'
            )
            firma_cliente = firma_cliente or _crea_firma_placeholder(
                app, foglio.numero_foglio, 'cliente'
            )
            foglio.firma_tecnico_path = firma_tecnico
            foglio.firma_cliente_path = firma_cliente

        _applica_operazioni_macchine(db, foglio, cfg, risorse, apply_stati)
        _collega_ricambi(db, foglio, risorse['ricambi'])

        db.session.commit()

        pdf_path = None
        if genera_pdf:
            pdf_path = genera_pdf_foglio_tecnico(foglio.id)
            db.session.refresh(foglio)

        n_mov = foglio.id  # will count movimenti below
        from app.models.macchina import MovimentoMacchina
        n_mov = MovimentoMacchina.query.filter_by(foglio_id=foglio.id).count()

        _stampa_riepilogo(foglio, cliente, tecnico, risorse, cfg, pdf_path, n_mov, apply_stati)


def _stampa_riepilogo(foglio, cliente, tecnico, risorse, cfg, pdf_path, n_mov, apply_stati):
    tipo_labels = {
        'riparazione_sede_con_prestito': 'Riparazione in sede con prestito',
        'riparazione_cliente': 'Riparazione presso cliente',
        'prestito_semplice': 'Prestito d\'uso semplice',
    }
    tipo_label = tipo_labels.get(
        cfg['tipo_operazione_macchine'], cfg['tipo_operazione_macchine']
    )

    print('=' * 68)
    print(f"FOGLIO TECNICO DI TEST — scenario {cfg['tag']}")
    print('=' * 68)
    print(f'ID:                 {foglio.id}')
    print(f'Numero:             {foglio.numero_foglio}')
    print(f'Cliente:            {cliente.ragione_sociale} (id={cliente.id})')
    print(f'Tecnico:            {tecnico.first_name} {tecnico.last_name}')
    print(f'Stato / Priorità:   {foglio.stato} / {foglio.priorita}')
    print(f'Categoria:          {foglio.categoria}')
    print(f'Tipo operazione:    {tipo_label}')
    print('-' * 68)
    print(f'Macchine cliente:   {len(risorse["macchine_cliente"])} collegate')
    for m in risorse['macchine_cliente']:
        print(f'  · {m.codice} — {m.marca} {m.modello} ({m.stato})')
    if cfg['tipo_operazione_macchine'] == 'riparazione_sede_con_prestito':
        print(f'Macchine sostitutive:{len(risorse["macchine_sostitutive"])} (prestito)')
        for m in risorse['macchine_sostitutive']:
            print(f'  · {m.codice} — {m.marca} {m.modello} ({m.stato})')
    print(f'Macchina manuale:   {foglio.macchina_manuale}')
    print(f'Ricambi DB:         {min(4, len(risorse["ricambi"]))} (quantità 2/1/3/1)')
    print(f'Ricambio manuale:   {foglio.ricambio_manuale}')
    print(f'Movimenti creati:   {n_mov}')
    print(f'Stati macchine DB:  {"AGGIORNATI" if apply_stati else "non modificati (solo movimenti)"}')
    print('-' * 68)
    print(f'Importo:            EUR {foglio.importo_intervento}')
    print(f'Pagamento:          {foglio.modalita_pagamento}')
    print(f'Pagato subito:      {foglio.pagamento_immediato}')
    print(f'In garanzia:        {foglio.intervento_in_garanzia}')
    print(f'Durata / Km:        {foglio.durata_intervento} min / {foglio.km_percorsi} km')
    print(f'Firmatario:         {foglio.nome_firmatario_cliente}')
    print(f'Inviato online:     {foglio.inviato_online} ({foglio.email_invio})')
    print(f'Firme:              tecnico={bool(foglio.firma_tecnico_path)} '
          f'cliente={bool(foglio.firma_cliente_path)}')
    print('-' * 68)
    if pdf_path:
        print(f'PDF:                {pdf_path}')
    else:
        print('PDF:                (non generato, usa senza --no-pdf)')
    print(f'Pagina web:         /fogli-tecnici/view/{foglio.id}')
    print('=' * 68)


def main():
    parser = argparse.ArgumentParser(description='Crea foglio tecnico di test completo')
    parser.add_argument(
        '--scenario',
        choices=list(SCENARIOS.keys()),
        default='prestito',
        help='prestito=riparazione+sostitutiva (default), base=pressoché cliente, max=tutto+inviato',
    )
    parser.add_argument('--cliente-id', type=int, default=None, help='ID cliente specifico')
    parser.add_argument(
        '--apply-stati',
        action='store_true',
        help='Aggiorna anche stato/ubicazione macchine nel DB (attenzione in produzione)',
    )
    parser.add_argument('--no-pdf', action='store_true', help='Non generare il PDF')
    args = parser.parse_args()

    run(
        scenario=args.scenario,
        cliente_id=args.cliente_id,
        apply_stati=args.apply_stati,
        genera_pdf=not args.no_pdf,
    )


if __name__ == '__main__':
    main()
