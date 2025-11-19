from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc, asc
from werkzeug.utils import secure_filename
from app import db
from app.models.ricambio import Ricambio, MovimentoMagazzino, PrenotazioneRicambio
from app.models.ticket import Ticket
from app.forms.magazzino import (
    RicambioForm, MovimentoMagazzinoForm, PrenotazioneRicambioForm, 
    ScaricoRicambioForm, RicercaRicambiForm, GestionePrenotazioneForm,
    CalendarioPrenotazioniForm
)
from app.utils.permissions import filter_by_department_access
from datetime import datetime, timedelta
import os
import uuid

magazzino_bp = Blueprint('magazzino', __name__)


@magazzino_bp.route('/')
@login_required
def index():
    """Pagina principale del magazzino con elenco ricambi"""
    
    # Form di ricerca
    search_form = RicercaRicambiForm()
    
    # Query base - filtra per reparto accessibile
    query = filter_by_department_access(Ricambio.query, Ricambio)
    
    # Applica filtri se presenti
    if request.args.get('search'):
        search_term = request.args.get('search')
        query = query.filter(or_(
            Ricambio.codice.ilike(f'%{search_term}%'),
            Ricambio.descrizione.ilike(f'%{search_term}%')
        ))
        search_form.search.data = search_term
    
    if request.args.get('filtro_stato'):
        filtro = request.args.get('filtro_stato')
        search_form.filtro_stato.data = filtro
        
        if filtro == 'disponibili':
            query = query.filter(Ricambio.quantita_disponibile > Ricambio.quantita_prenotata)
        elif filtro == 'prenotati':
            query = query.filter(Ricambio.quantita_prenotata > 0)
        elif filtro == 'sotto_scorta':
            query = query.filter(
                Ricambio.quantita_minima > 0,
                Ricambio.quantita_disponibile <= Ricambio.quantita_minima
            )
        elif filtro == 'esauriti':
            query = query.filter(Ricambio.quantita_disponibile <= Ricambio.quantita_prenotata)
    
    if request.args.get('ubicazione'):
        ubicazione = request.args.get('ubicazione')
        query = query.filter(Ricambio.ubicazione.ilike(f'%{ubicazione}%'))
        search_form.ubicazione.data = ubicazione
    
    if request.args.get('fornitore'):
        fornitore = request.args.get('fornitore')
        query = query.filter(Ricambio.fornitore.ilike(f'%{fornitore}%'))
        search_form.fornitore.data = fornitore
    
    # Ordinamento
    sort_by = request.args.get('sort', 'codice')
    sort_dir = request.args.get('dir', 'asc')
    
    if sort_by == 'codice':
        query = query.order_by(asc(Ricambio.codice) if sort_dir == 'asc' else desc(Ricambio.codice))
    elif sort_by == 'descrizione':
        query = query.order_by(asc(Ricambio.descrizione) if sort_dir == 'asc' else desc(Ricambio.descrizione))
    elif sort_by == 'quantita':
        query = query.order_by(asc(Ricambio.quantita_disponibile) if sort_dir == 'asc' else desc(Ricambio.quantita_disponibile))
    elif sort_by == 'ubicazione':
        query = query.order_by(asc(Ricambio.ubicazione) if sort_dir == 'asc' else desc(Ricambio.ubicazione))
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 20
    ricambi = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Statistiche rapide - filtra per reparto accessibile
    ricambi_query = filter_by_department_access(Ricambio.query, Ricambio)
    stats = {
        'totale_ricambi': ricambi_query.count(),
        'sotto_scorta': ricambi_query.filter(
            Ricambio.quantita_minima > 0,
            Ricambio.quantita_disponibile <= Ricambio.quantita_minima
        ).count(),
        'con_prenotazioni': ricambi_query.filter(Ricambio.quantita_prenotata > 0).count(),
        'esauriti': ricambi_query.filter(Ricambio.quantita_disponibile <= Ricambio.quantita_prenotata).count()
    }
    
    return render_template('magazzino/index.html', 
                         ricambi=ricambi, 
                         search_form=search_form,
                         stats=stats,
                         sort_by=sort_by,
                         sort_dir=sort_dir,
                         active_tab='index')


@magazzino_bp.route('/ricambio/<int:id>')
@login_required
def dettaglio_ricambio(id):
    """Dettaglio singolo ricambio con storico movimenti"""
    
    ricambio = Ricambio.query.get_or_404(id)
    
    # Verifica accesso al ricambio
    from app.utils.permissions import can_access_resource
    if not can_access_resource(ricambio):
        abort(403)
    
    # Ultimi movimenti
    movimenti = MovimentoMagazzino.query.filter_by(ricambio_id=id)\
                                       .order_by(desc(MovimentoMagazzino.created_at))\
                                       .limit(20).all()
    
    # Prenotazioni attive
    prenotazioni = PrenotazioneRicambio.query.filter_by(ricambio_id=id, stato='Attiva')\
                                            .order_by(desc(PrenotazioneRicambio.data_prenotazione))\
                                            .all()
    
    # Form per azioni rapide
    prenotazione_form = PrenotazioneRicambioForm()
    prenotazione_form.ricambio_id.data = id
    
    scarico_form = ScaricoRicambioForm()
    scarico_form.ricambio_id.data = id
    
    return render_template('magazzino/dettaglio_ricambio.html',
                         ricambio=ricambio,
                         movimenti=movimenti,
                         prenotazioni=prenotazioni,
                         prenotazione_form=prenotazione_form,
                         scarico_form=scarico_form,
                         active_tab='index')


@magazzino_bp.route('/ricambio/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_ricambio():
    """Crea nuovo ricambio"""
    
    form = RicambioForm()
    
    if form.validate_on_submit():
        try:
            ricambio = Ricambio(
                codice=form.codice.data.upper().strip(),
                descrizione=form.descrizione.data.strip(),
                quantita_disponibile=form.quantita_disponibile.data,
                quantita_minima=form.quantita_minima.data if form.quantita_minima.data else 0,
                ubicazione=form.ubicazione.data.strip() if form.ubicazione.data else None,
                note=form.note.data.strip() if form.note.data else None,
                prezzo_unitario=form.prezzo_unitario.data,
                fornitore=form.fornitore.data.strip() if form.fornitore.data else None,
                department_id=form.department_id.data
            )
            
            # Gestione upload foto
            if form.foto.data:
                foto_file = form.foto.data
                if foto_file.filename:
                    # Genera nome file unico
                    filename = secure_filename(foto_file.filename)
                    name, ext = os.path.splitext(filename)
                    # Applica secure_filename anche al codice ricambio per evitare caratteri non validi
                    safe_codice = secure_filename(ricambio.codice)
                    unique_filename = f"{safe_codice}_{uuid.uuid4().hex[:8]}{ext}"
                    
                    # Salva il file
                    foto_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ricambi', unique_filename)
                    os.makedirs(os.path.dirname(foto_path), exist_ok=True)
                    foto_file.save(foto_path)
                    
                    ricambio.foto_filename = unique_filename
            
            db.session.add(ricambio)
            db.session.flush()  # Forza l'assegnazione dell'ID senza fare commit
            
            # Se c'è una quantità iniziale, registra il movimento di carico
            if ricambio.quantita_disponibile > 0:
                movimento = MovimentoMagazzino(
                    ricambio_id=ricambio.id,
                    tipo_movimento='Carico',
                    quantita=ricambio.quantita_disponibile,
                    motivo='Carico iniziale',
                    user_id=current_user.id
                )
                db.session.add(movimento)
            
            db.session.commit()
            
            flash(f'Ricambio {ricambio.codice} creato con successo!', 'success')
            return redirect(url_for('magazzino.dettaglio_ricambio', id=ricambio.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione: {str(e)}', 'error')
    
    return render_template('magazzino/form_ricambio.html', form=form, title='Nuovo Ricambio', active_tab='index')


@magazzino_bp.route('/ricambio/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_ricambio(id):
    """Modifica ricambio esistente"""
    
    ricambio = Ricambio.query.get_or_404(id)
    
    # Verifica accesso al ricambio
    from app.utils.permissions import can_access_resource
    if not can_access_resource(ricambio):
        abort(403)
    form = RicambioForm(obj=ricambio)
    form._ricambio_id = id  # Per la validazione del codice univoco
    
    if form.validate_on_submit():
        try:
            # Salva la quantità precedente per il movimento
            quantita_precedente = ricambio.quantita_disponibile
            
            # Aggiorna i campi
            ricambio.codice = form.codice.data.upper().strip()
            ricambio.descrizione = form.descrizione.data.strip()
            ricambio.quantita_disponibile = form.quantita_disponibile.data
            ricambio.quantita_minima = form.quantita_minima.data if form.quantita_minima.data else 0
            ricambio.ubicazione = form.ubicazione.data.strip() if form.ubicazione.data else None
            ricambio.note = form.note.data.strip() if form.note.data else None
            ricambio.prezzo_unitario = form.prezzo_unitario.data
            ricambio.fornitore = form.fornitore.data.strip() if form.fornitore.data else None
            ricambio.department_id = form.department_id.data
            
            # Gestione upload foto
            if form.foto.data and form.foto.data.filename:
                # Elimina la foto precedente se esiste
                if ricambio.foto_filename:
                    old_foto_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ricambi', ricambio.foto_filename)
                    if os.path.exists(old_foto_path):
                        os.remove(old_foto_path)
                
                # Salva la nuova foto
                foto_file = form.foto.data
                filename = secure_filename(foto_file.filename)
                name, ext = os.path.splitext(filename)
                # Applica secure_filename anche al codice ricambio per evitare caratteri non validi
                safe_codice = secure_filename(ricambio.codice)
                unique_filename = f"{safe_codice}_{uuid.uuid4().hex[:8]}{ext}"
                
                foto_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ricambi', unique_filename)
                os.makedirs(os.path.dirname(foto_path), exist_ok=True)
                foto_file.save(foto_path)
                
                ricambio.foto_filename = unique_filename
            
            # Se la quantità è cambiata, registra il movimento
            if quantita_precedente != ricambio.quantita_disponibile:
                differenza = ricambio.quantita_disponibile - quantita_precedente
                movimento = MovimentoMagazzino(
                    ricambio_id=ricambio.id,
                    tipo_movimento='Rettifica',
                    quantita=differenza,
                    motivo=f'Rettifica da modifica ricambio (da {quantita_precedente} a {ricambio.quantita_disponibile})',
                    user_id=current_user.id
                )
                db.session.add(movimento)
            
            db.session.commit()
            
            flash(f'Ricambio {ricambio.codice} aggiornato con successo!', 'success')
            return redirect(url_for('magazzino.dettaglio_ricambio', id=ricambio.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return render_template('magazzino/form_ricambio.html', 
                         form=form, 
                         ricambio=ricambio,
                         title=f'Modifica {ricambio.codice}',
                         active_tab='index')


@magazzino_bp.route('/ricambio/<int:id>/elimina', methods=['POST'])
@login_required
def elimina_ricambio(id):
    """Elimina ricambio esistente"""
    
    ricambio = Ricambio.query.get_or_404(id)
    
    # Verifica accesso al ricambio
    from app.utils.permissions import can_access_resource
    if not can_access_resource(ricambio):
        abort(403)
    
    try:
        # Elimina la foto se esiste
        if ricambio.foto_filename:
            foto_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ricambi', ricambio.foto_filename)
            if os.path.exists(foto_path):
                os.remove(foto_path)
        
        # Il database eliminerà automaticamente i movimenti e prenotazioni collegati
        # grazie al cascade='all, delete-orphan' definito nel modello
        codice_ricambio = ricambio.codice
        db.session.delete(ricambio)
        db.session.commit()
        
        flash(f'Ricambio {codice_ricambio} eliminato con successo!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
        return redirect(url_for('magazzino.dettaglio_ricambio', id=id))
    
    return redirect(url_for('magazzino.index'))


@magazzino_bp.route('/ricambio/<int:id>/prenota', methods=['POST'])
@login_required
def prenota_ricambio(id):
    """Prenota ricambio per ticket"""
    
    ricambio = Ricambio.query.get_or_404(id)
    
    # Verifica accesso al ricambio
    from app.utils.permissions import can_access_resource
    if not can_access_resource(ricambio):
        abort(403)
    form = PrenotazioneRicambioForm()
    
    if form.validate_on_submit():
        try:
            prenotazione = ricambio.prenota_quantita(
                quantita=form.quantita.data,
                ticket_id=form.ticket_id.data if form.ticket_id.data != 0 else None,
                data_prenotazione=datetime.utcnow()
            )
            
            if form.data_scadenza.data:
                prenotazione.data_scadenza = form.data_scadenza.data
            
            if form.note.data:
                prenotazione.note = form.note.data.strip()
            
            prenotazione.user_id = current_user.id
            
            db.session.commit()
            
            flash(f'Prenotati {form.quantita.data} pezzi di {ricambio.codice}!', 'success')
            
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la prenotazione: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('magazzino.dettaglio_ricambio', id=id))


@magazzino_bp.route('/ricambio/<int:id>/scarica', methods=['POST'])
@login_required
def scarica_ricambio(id):
    """Scarica ricambio dal magazzino"""
    
    ricambio = Ricambio.query.get_or_404(id)
    
    # Verifica accesso al ricambio
    from app.utils.permissions import can_access_resource
    if not can_access_resource(ricambio):
        abort(403)
    form = ScaricoRicambioForm()
    
    if form.validate_on_submit():
        try:
            ricambio.scarica_quantita(
                quantita=form.quantita.data,
                motivo=form.motivo.data,
                ticket_id=form.ticket_id.data if form.ticket_id.data != 0 else None,
                user_id=current_user.id
            )
            
            db.session.commit()
            
            flash(f'Scaricati {form.quantita.data} pezzi di {ricambio.codice}!', 'success')
            
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante lo scarico: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('magazzino.index'))


@magazzino_bp.route('/ricambio/<int:id>/carica', methods=['POST'])
@login_required
def carica_ricambio(id):
    """Carica ricambio nel magazzino"""
    
    ricambio = Ricambio.query.get_or_404(id)
    
    # Verifica accesso al ricambio
    from app.utils.permissions import can_access_resource
    if not can_access_resource(ricambio):
        abort(403)
    
    # Usa il form di scarico ma per il carico (stessi campi)
    from app.forms.magazzino import ScaricoRicambioForm
    form = ScaricoRicambioForm()
    
    if form.validate_on_submit():
        try:
            ricambio.carica_quantita(
                quantita=form.quantita.data,
                motivo=form.motivo.data,
                user_id=current_user.id
            )
            
            db.session.commit()
            
            flash(f'Caricati {form.quantita.data} pezzi di {ricambio.codice}!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante il carico: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('magazzino.index'))


@magazzino_bp.route('/movimenti')
@login_required
def movimenti():
    """Elenco movimenti magazzino"""
    
    # Query base
    query = MovimentoMagazzino.query.join(Ricambio)
    
    # Filtri
    if request.args.get('ricambio_id'):
        query = query.filter(MovimentoMagazzino.ricambio_id == request.args.get('ricambio_id'))
    
    if request.args.get('tipo'):
        query = query.filter(MovimentoMagazzino.tipo_movimento == request.args.get('tipo'))
    
    if request.args.get('data_da'):
        try:
            data_da = datetime.strptime(request.args.get('data_da'), '%Y-%m-%d')
            query = query.filter(MovimentoMagazzino.created_at >= data_da)
        except ValueError:
            pass
    
    if request.args.get('data_a'):
        try:
            data_a = datetime.strptime(request.args.get('data_a'), '%Y-%m-%d')
            query = query.filter(MovimentoMagazzino.created_at <= data_a + timedelta(days=1))
        except ValueError:
            pass
    
    # Ordinamento
    query = query.order_by(desc(MovimentoMagazzino.created_at))
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    movimenti = query.paginate(page=page, per_page=50, error_out=False)
    
    return render_template('magazzino/movimenti.html', movimenti=movimenti, active_tab='movimenti')


@magazzino_bp.route('/prenotazioni')
@login_required
def prenotazioni():
    """Elenco prenotazioni"""
    
    # Query base
    query = PrenotazioneRicambio.query.join(Ricambio)
    
    # Filtri
    stato_filtro = request.args.get('stato', 'attive')
    if stato_filtro == 'attive':
        query = query.filter(PrenotazioneRicambio.stato == 'Attiva')
    elif stato_filtro == 'scadute':
        query = query.filter(
            PrenotazioneRicambio.stato == 'Attiva',
            PrenotazioneRicambio.data_scadenza < datetime.utcnow()
        )
    elif stato_filtro != 'tutte':
        query = query.filter(PrenotazioneRicambio.stato == stato_filtro.title())
    
    if request.args.get('ricambio_id'):
        query = query.filter(PrenotazioneRicambio.ricambio_id == request.args.get('ricambio_id'))
    
    if request.args.get('ticket_id'):
        query = query.filter(PrenotazioneRicambio.ticket_id == request.args.get('ticket_id'))
    
    # Ordinamento
    query = query.order_by(desc(PrenotazioneRicambio.data_prenotazione))
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    prenotazioni = query.paginate(page=page, per_page=30, error_out=False)
    
    return render_template('magazzino/prenotazioni.html', 
                         prenotazioni=prenotazioni,
                         stato_filtro=stato_filtro,
                         active_tab='prenotazioni')


@magazzino_bp.route('/calendario')
@login_required
def calendario():
    """Vista calendario prenotazioni"""
    
    form = CalendarioPrenotazioniForm()
    
    # Parametri dal form o default
    mese = request.args.get('mese', datetime.now().month, type=int)
    anno = request.args.get('anno', datetime.now().year, type=int)
    ricambio_id = request.args.get('filtro_ricambio', 0, type=int)
    
    # Calcola primo e ultimo giorno del mese
    primo_giorno = datetime(anno, mese, 1)
    if mese == 12:
        ultimo_giorno = datetime(anno + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_giorno = datetime(anno, mese + 1, 1) - timedelta(days=1)
    
    # Calcola giorni per il calendario (inclusi giorni del mese precedente e successivo)
    primo_giorno_settimana = primo_giorno.weekday()  # 0 = Lunedì
    giorni_mese = (ultimo_giorno - primo_giorno).days + 1
    
    # Giorni del mese precedente
    giorni_precedenti = []
    for i in range(primo_giorno_settimana):
        giorno_precedente = primo_giorno - timedelta(days=(primo_giorno_settimana - i))
        giorni_precedenti.append(giorno_precedente)
    
    # Giorni del mese corrente
    giorni_correnti = []
    for giorno in range(1, giorni_mese + 1):
        data_corrente = primo_giorno.replace(day=giorno)
        giorni_correnti.append(data_corrente)
    
    # Giorni del mese successivo per completare la griglia (42 celle totali = 6 settimane)
    celle_totali = 42
    celle_usate = len(giorni_precedenti) + len(giorni_correnti)
    giorni_successivi = []
    for i in range(celle_totali - celle_usate):
        giorno_successivo = ultimo_giorno + timedelta(days=(i + 1))
        giorni_successivi.append(giorno_successivo)
    
    # Query prenotazioni del mese - filtra per reparto accessibile
    # Prima filtriamo i ricambi per reparto, poi le prenotazioni
    ricambi_accessibili_query = filter_by_department_access(Ricambio.query, Ricambio)
    ricambi_ids = [r.id for r in ricambi_accessibili_query.all()]
    
    query = PrenotazioneRicambio.query.filter(
        PrenotazioneRicambio.stato == 'Attiva',
        PrenotazioneRicambio.data_prenotazione >= primo_giorno,
        PrenotazioneRicambio.data_prenotazione <= ultimo_giorno,
        PrenotazioneRicambio.ricambio_id.in_(ricambi_ids)  # Filtra solo ricambi del reparto
    ).join(Ricambio)
    
    if ricambio_id > 0:
        query = query.filter(PrenotazioneRicambio.ricambio_id == ricambio_id)
    
    prenotazioni = query.all()
    
    # Organizza prenotazioni per giorno
    prenotazioni_per_giorno = {}
    for prenotazione in prenotazioni:
        giorno = prenotazione.data_prenotazione.day
        if giorno not in prenotazioni_per_giorno:
            prenotazioni_per_giorno[giorno] = []
        prenotazioni_per_giorno[giorno].append(prenotazione)
    
    return render_template('magazzino/calendario.html',
                         form=form,
                         mese=mese,
                         anno=anno,
                         ricambio_id=ricambio_id,
                         prenotazioni_per_giorno=prenotazioni_per_giorno,
                         primo_giorno=primo_giorno,
                         ultimo_giorno=ultimo_giorno,
                         giorni_precedenti=giorni_precedenti,
                         giorni_correnti=giorni_correnti,
                         giorni_successivi=giorni_successivi,
                         oggi=datetime.now().date(),
                         active_tab='calendario')


@magazzino_bp.route('/api/ricambi/search')
@login_required
def api_ricambi_search():
    """API per ricerca ricambi (per autocomplete)"""
    
    term = request.args.get('term', '')
    if len(term) < 2:
        return jsonify([])
    
    ricambi = Ricambio.query.filter(or_(
        Ricambio.codice.ilike(f'%{term}%'),
        Ricambio.descrizione.ilike(f'%{term}%')
    )).limit(10).all()
    
    results = []
    for ricambio in ricambi:
        results.append({
            'id': ricambio.id,
            'codice': ricambio.codice,
            'descrizione': ricambio.descrizione,
            'quantita_effettiva': ricambio.quantita_effettiva,
            'ubicazione': ricambio.ubicazione,
            'label': f"{ricambio.codice} - {ricambio.descrizione}",
            'value': ricambio.codice
        })
    
    return jsonify(results)


@magazzino_bp.route('/api/ricambi/filter')
@login_required
def api_ricambi_filter():
    """API per filtri in tempo reale"""
    
    # Query base
    query = Ricambio.query
    
    # Applica filtri
    search_term = request.args.get('search', '').strip()
    if search_term:
        query = query.filter(or_(
            Ricambio.codice.ilike(f'%{search_term}%'),
            Ricambio.descrizione.ilike(f'%{search_term}%')
        ))
    
    filtro_stato = request.args.get('filtro_stato', '')
    if filtro_stato == 'disponibili':
        query = query.filter(Ricambio.quantita_disponibile > Ricambio.quantita_prenotata)
    elif filtro_stato == 'prenotati':
        query = query.filter(Ricambio.quantita_prenotata > 0)
    elif filtro_stato == 'sotto_scorta':
        query = query.filter(
            Ricambio.quantita_minima > 0,
            Ricambio.quantita_disponibile <= Ricambio.quantita_minima
        )
    elif filtro_stato == 'esauriti':
        query = query.filter(Ricambio.quantita_disponibile <= Ricambio.quantita_prenotata)
    
    ubicazione = request.args.get('ubicazione', '').strip()
    if ubicazione:
        query = query.filter(Ricambio.ubicazione.ilike(f'%{ubicazione}%'))
    
    fornitore = request.args.get('fornitore', '').strip()
    if fornitore:
        query = query.filter(Ricambio.fornitore.ilike(f'%{fornitore}%'))
    
    # Ordinamento
    sort_by = request.args.get('sort', 'codice')
    sort_dir = request.args.get('dir', 'asc')
    
    if sort_by == 'codice':
        query = query.order_by(asc(Ricambio.codice) if sort_dir == 'asc' else desc(Ricambio.codice))
    elif sort_by == 'descrizione':
        query = query.order_by(asc(Ricambio.descrizione) if sort_dir == 'asc' else desc(Ricambio.descrizione))
    elif sort_by == 'quantita':
        query = query.order_by(asc(Ricambio.quantita_disponibile) if sort_dir == 'asc' else desc(Ricambio.quantita_disponibile))
    elif sort_by == 'ubicazione':
        query = query.order_by(asc(Ricambio.ubicazione) if sort_dir == 'asc' else desc(Ricambio.ubicazione))
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 20
    ricambi = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Prepara i dati per JSON
    results = []
    for ricambio in ricambi.items:
        results.append({
            'id': ricambio.id,
            'codice': ricambio.codice,
            'descrizione': ricambio.descrizione,
            'quantita_disponibile': ricambio.quantita_disponibile,
            'quantita_prenotata': ricambio.quantita_prenotata,
            'quantita_effettiva': ricambio.quantita_effettiva,
            'quantita_minima': ricambio.quantita_minima,
            'ubicazione': ricambio.ubicazione,
            'fornitore': ricambio.fornitore,
            'prezzo_unitario': float(ricambio.prezzo_unitario) if ricambio.prezzo_unitario else None,
            'foto_filename': ricambio.foto_filename,
            'is_sotto_scorta': ricambio.is_sotto_scorta,
            'stato_disponibilita': ricambio.stato_disponibilita,
            'created_at': ricambio.created_at.isoformat() if ricambio.created_at else None
        })
    
    return jsonify({
        'ricambi': results,
        'pagination': {
            'page': ricambi.page,
            'pages': ricambi.pages,
            'per_page': ricambi.per_page,
            'total': ricambi.total,
            'has_prev': ricambi.has_prev,
            'has_next': ricambi.has_next,
            'prev_num': ricambi.prev_num,
            'next_num': ricambi.next_num
        }
    })


@magazzino_bp.route('/api/ricambio/<int:id>/info')
@login_required
def api_ricambio_info(id):
    """API per informazioni ricambio"""
    
    ricambio = Ricambio.query.get_or_404(id)
    
    # Verifica accesso al ricambio
    from app.utils.permissions import can_access_resource
    if not can_access_resource(ricambio):
        abort(403)
    return jsonify(ricambio.to_dict())


@magazzino_bp.route('/api/stats')
@login_required
def api_stats():
    """API per statistiche magazzino"""
    
    stats = {
        'totale_ricambi': Ricambio.query.count(),
        'sotto_scorta': Ricambio.query.filter(
            Ricambio.quantita_minima > 0,
            Ricambio.quantita_disponibile <= Ricambio.quantita_minima
        ).count(),
        'con_prenotazioni': Ricambio.query.filter(Ricambio.quantita_prenotata > 0).count(),
        'esauriti': Ricambio.query.filter(Ricambio.quantita_disponibile <= Ricambio.quantita_prenotata).count(),
        'prenotazioni_attive': PrenotazioneRicambio.query.filter_by(stato='Attiva').count(),
        'prenotazioni_scadute': PrenotazioneRicambio.query.filter(
            PrenotazioneRicambio.stato == 'Attiva',
            PrenotazioneRicambio.data_scadenza < datetime.utcnow()
        ).count()
    }
    
    return jsonify(stats)


@magazzino_bp.route('/api/soglie-scorta')
@login_required
def api_soglie_scorta():
    """API per monitoraggio soglie di scorta"""
    
    # Ricambi sotto scorta
    sotto_scorta = Ricambio.query.filter(
        Ricambio.quantita_disponibile <= Ricambio.quantita_minima,
        Ricambio.quantita_minima > 0
    ).order_by(asc(Ricambio.quantita_disponibile)).all()
    
    # Ricambi in via di esaurimento (quantità <= soglia + 2)
    in_esaurimento = Ricambio.query.filter(
        Ricambio.quantita_disponibile <= (Ricambio.quantita_minima + 2),
        Ricambio.quantita_disponibile > Ricambio.quantita_minima,
        Ricambio.quantita_minima > 0
    ).order_by(asc(Ricambio.quantita_disponibile)).all()
    
    result = {
        'sotto_scorta': [{
            'id': r.id,
            'codice': r.codice,
            'descrizione': r.descrizione,
            'quantita_disponibile': r.quantita_disponibile,
            'quantita_minima': r.quantita_minima,
            'quantita_effettiva': r.quantita_effettiva,
            'ubicazione': r.ubicazione,
            'fornitore': r.fornitore,
            'giorni_sotto_scorta': (datetime.utcnow() - r.updated_at).days if r.quantita_disponibile <= r.quantita_minima else 0
        } for r in sotto_scorta],
        
        'in_esaurimento': [{
            'id': r.id,
            'codice': r.codice,
            'descrizione': r.descrizione,
            'quantita_disponibile': r.quantita_disponibile,
            'quantita_minima': r.quantita_minima,
            'quantita_effettiva': r.quantita_effettiva,
            'ubicazione': r.ubicazione,
            'fornitore': r.fornitore
        } for r in in_esaurimento],
        
        'statistiche': {
            'totale_sotto_scorta': len(sotto_scorta),
            'totale_in_esaurimento': len(in_esaurimento),
            'valore_sotto_scorta': sum(r.quantita_effettiva * (r.prezzo_unitario or 0) for r in sotto_scorta),
            'ultimo_aggiornamento': datetime.utcnow().isoformat()
        }
    }
    
    return jsonify(result)


@magazzino_bp.route('/prenotazione/<int:id>/gestisci', methods=['POST'])
@login_required
def gestisci_prenotazione(id):
    """Gestisce prenotazione (utilizza, annulla, modifica)"""
    
    prenotazione = PrenotazioneRicambio.query.get_or_404(id)
    form = GestionePrenotazioneForm()
    
    if form.validate_on_submit():
        try:
            azione = form.azione.data
            
            if azione == 'utilizza_totale':
                prenotazione.utilizza_prenotazione()
                flash(f'Prenotazione utilizzata completamente!', 'success')
                
            elif azione == 'utilizza_parziale':
                quantita = form.quantita_utilizzo.data
                prenotazione.utilizza_prenotazione(quantita)
                flash(f'Utilizzati {quantita} pezzi dalla prenotazione!', 'success')
                
            elif azione == 'annulla':
                prenotazione.annulla_prenotazione()
                flash(f'Prenotazione annullata!', 'warning')
                
            elif azione == 'modifica_scadenza':
                prenotazione.data_scadenza = form.nuova_scadenza.data
                flash(f'Data scadenza aggiornata!', 'info')
            
            if form.note.data:
                prenotazione.note = form.note.data.strip()
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'operazione: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('magazzino.prenotazioni'))


@magazzino_bp.route('/reports')
@login_required
def reports():
    """Report e statistiche magazzino"""

    # Ricambi sotto scorta
    sotto_scorta = Ricambio.query.filter(
        Ricambio.quantita_minima > 0,
        Ricambio.quantita_disponibile <= Ricambio.quantita_minima
    ).order_by(asc(Ricambio.quantita_disponibile)).all()

    # Top 10 ricambi più utilizzati (ultimi 30 giorni)
    data_limite = datetime.utcnow() - timedelta(days=30)
    top_utilizzati = db.session.query(
        Ricambio.codice,
        Ricambio.descrizione,
        db.func.sum(db.func.abs(MovimentoMagazzino.quantita)).label('totale_utilizzato')
    ).join(MovimentoMagazzino)\
     .filter(MovimentoMagazzino.created_at >= data_limite)\
     .filter(MovimentoMagazzino.quantita < 0)\
     .group_by(Ricambio.id, Ricambio.codice, Ricambio.descrizione)\
     .order_by(desc('totale_utilizzato'))\
     .limit(10).all()

    # Prenotazioni in scadenza (prossimi 7 giorni)
    data_scadenza = datetime.utcnow() + timedelta(days=7)
    prenotazioni_scadenza = PrenotazioneRicambio.query.filter(
        PrenotazioneRicambio.stato == 'Attiva',
        PrenotazioneRicambio.data_scadenza.between(datetime.utcnow(), data_scadenza)
    ).join(Ricambio).order_by(asc(PrenotazioneRicambio.data_scadenza)).all()

    # Valore totale magazzino (solo ricambi effettivamente disponibili)
    valore_totale = db.session.query(
        db.func.sum((Ricambio.quantita_disponibile - Ricambio.quantita_prenotata) * Ricambio.prezzo_unitario)
    ).filter(
        Ricambio.prezzo_unitario.isnot(None),
        (Ricambio.quantita_disponibile - Ricambio.quantita_prenotata) > 0
    ).scalar() or 0

    # Statistiche generali
    stats = {
        'totale_ricambi': Ricambio.query.count(),
        'con_prenotazioni': Ricambio.query.filter(Ricambio.quantita_prenotata > 0).count(),
        'esauriti': Ricambio.query.filter(Ricambio.quantita_disponibile <= Ricambio.quantita_prenotata).count()
    }

    return render_template('magazzino/reports.html',
                         sotto_scorta=sotto_scorta,
                         top_utilizzati=top_utilizzati,
                         prenotazioni_scadenza=prenotazioni_scadenza,
                         valore_totale=valore_totale,
                         stats=stats,
                         active_tab='reports')


@magazzino_bp.route('/reports/export')
@login_required
def export_reports():
    """Pagina di stampa report magazzino (non download CSV)"""
    from flask import render_template_string

    # Ricambi con prezzo definito
    ricambi = Ricambio.query.filter(Ricambio.prezzo_unitario.isnot(None)).all()

    # Calcola valore totale
    valore_totale = sum(
        (r.quantita_disponibile - r.quantita_prenotata) * r.prezzo_unitario
        for r in ricambi
        if (r.quantita_disponibile - r.quantita_prenotata) > 0
    )

    # Template HTML per la stampa
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Report Magazzino - DB-Desk</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                margin: 20px;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #333;
                padding-bottom: 10px;
            }
            .header h1 {
                margin: 0;
                font-size: 24px;
                color: #333;
            }
            .header .subtitle {
                margin: 5px 0 0 0;
                font-size: 14px;
                color: #666;
            }
            .summary {
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #333;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .text-right {
                text-align: right;
            }
            .text-center {
                text-align: center;
            }
            .footer {
                margin-top: 30px;
                text-align: center;
                font-size: 10px;
                color: #666;
                border-top: 1px solid #ccc;
                padding-top: 10px;
            }
            @media print {
                body { margin: 0; }
                .no-print { display: none; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Report Magazzino</h1>
            <div class="subtitle">DB-Desk - Sistema Gestione Ricambi</div>
            <div class="subtitle">Generato il: {{ data_oggi }}</div>
        </div>

        <div class="summary">
            <strong>Riepilogo:</strong><br>
            Totale Ricambi: {{ ricambi|length }}<br>
            Valore Totale Magazzino: €{{ "%.2f"|format(valore_totale) }}
        </div>

        <table>
            <thead>
                <tr>
                    <th>Codice</th>
                    <th>Descrizione</th>
                    <th class="text-center">Disp.</th>
                    <th class="text-center">Pren.</th>
                    <th class="text-center">Eff.</th>
                    <th class="text-center">Min.</th>
                    <th class="text-right">Prezzo</th>
                    <th class="text-right">Valore</th>
                    <th>Fornitore</th>
                    <th>Ubicazione</th>
                    <th>Stato</th>
                </tr>
            </thead>
            <tbody>
                {% for ricambio in ricambi %}
                <tr>
                    <td>{{ ricambio.codice }}</td>
                    <td>{{ ricambio.descrizione }}</td>
                    <td class="text-center">{{ ricambio.quantita_disponibile }}</td>
                    <td class="text-center">{{ ricambio.quantita_prenotata }}</td>
                    <td class="text-center">{{ ricambio.quantita_disponibile - ricambio.quantita_prenotata }}</td>
                    <td class="text-center">{{ ricambio.quantita_minima }}</td>
                    <td class="text-right">€{{ "%.2f"|format(ricambio.prezzo_unitario) }}</td>
                    <td class="text-right">€{{ "%.2f"|format((ricambio.quantita_disponibile - ricambio.quantita_prenotata) * ricambio.prezzo_unitario) }}</td>
                    <td>{{ ricambio.fornitore or '-' }}</td>
                    <td>{{ ricambio.ubicazione or '-' }}</td>
                    <td>{{ ricambio.stato_disponibilita }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="footer">
            Report generato automaticamente da DB-Desk - {{ data_oggi }}
        </div>

        <script>
            // Avvia automaticamente la stampa quando la pagina si carica
            window.onload = function() {
                window.print();
            };
        </script>
    </body>
    </html>
    """

    return render_template_string(html_template,
                                ricambi=ricambi,
                                valore_totale=valore_totale,
                                data_oggi=datetime.now().strftime('%d/%m/%Y %H:%M'))


@magazzino_bp.route('/ricambi/foto/<filename>')
@login_required
def foto_ricambio(filename):
    """Serve le immagini dei ricambi dalla cartella uploads/ricambi"""
    ricambi_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ricambi')
    return send_from_directory(ricambi_folder, filename)


@magazzino_bp.route('/api/suggerisci-soglia/<int:ricambio_id>')
@login_required
def suggerisci_soglia_scorta(ricambio_id):
    """API per suggerire soglia di scorta basata sull'utilizzo storico"""
    
    ricambio = Ricambio.query.get_or_404(ricambio_id)
    
    # Analizza gli ultimi 90 giorni di movimenti
    data_limite = datetime.utcnow() - timedelta(days=90)
    
    movimenti_scarico = MovimentoMagazzino.query.filter(
        MovimentoMagazzino.ricambio_id == ricambio_id,
        MovimentoMagazzino.created_at >= data_limite,
        MovimentoMagazzino.quantita < 0  # Solo scarichi
    ).all()
    
    if not movimenti_scarico:
        return jsonify({
            'suggerimento': ricambio.quantita_minima or 1,
            'motivo': 'Nessun movimento di scarico negli ultimi 90 giorni',
            'dettagli': {
                'utilizzo_medio_mensile': 0,
                'utilizzo_massimo_mensile': 0,
                'giorni_copertura_attuale': 'N/A',
                'raccomandazione': 'Mantieni soglia attuale o imposta 1 come minimo'
            }
        })
    
    # Calcola statistiche utilizzo
    utilizzo_totale = sum(abs(m.quantita) for m in movimenti_scarico)
    utilizzo_medio_mensile = utilizzo_totale / 3  # 90 giorni = 3 mesi
    
    # Calcola utilizzo per mese
    utilizzi_mensili = {}
    for movimento in movimenti_scarico:
        mese_key = movimento.created_at.strftime('%Y-%m')
        if mese_key not in utilizzi_mensili:
            utilizzi_mensili[mese_key] = 0
        utilizzi_mensili[mese_key] += abs(movimento.quantita)
    
    utilizzo_massimo_mensile = max(utilizzi_mensili.values()) if utilizzi_mensili else 0
    
    # Suggerimento basato su utilizzo massimo + buffer del 20%
    suggerimento_base = int(utilizzo_massimo_mensile * 1.2)
    
    # Considera anche il lead time (assumiamo 15 giorni se non specificato)
    lead_time_giorni = 15
    utilizzo_giornaliero = utilizzo_medio_mensile / 30 if utilizzo_medio_mensile > 0 else 0
    scorta_lead_time = int(utilizzo_giornaliero * lead_time_giorni)
    
    # Il suggerimento finale è il maggiore tra i due calcoli
    suggerimento_finale = max(suggerimento_base, scorta_lead_time, 1)
    
    # Calcola giorni di copertura con scorta attuale
    giorni_copertura = int(ricambio.quantita_disponibile / utilizzo_giornaliero) if utilizzo_giornaliero > 0 else 999
    
    # Determina il motivo del suggerimento
    if utilizzo_medio_mensile == 0:
        motivo = "Ricambio non utilizzato negli ultimi 90 giorni"
        raccomandazione = "Considera di ridurre la scorta o verificare se il ricambio è ancora necessario"
    elif suggerimento_finale > ricambio.quantita_minima:
        motivo = f"Utilizzo elevato rilevato (media {utilizzo_medio_mensile:.1f}/mese)"
        raccomandazione = "Aumenta la soglia per evitare rotture di stock"
    elif suggerimento_finale < ricambio.quantita_minima:
        motivo = f"Utilizzo basso rilevato (media {utilizzo_medio_mensile:.1f}/mese)"
        raccomandazione = "Puoi ridurre la soglia per ottimizzare il capitale immobilizzato"
    else:
        motivo = "Soglia attuale appropriata per l'utilizzo corrente"
        raccomandazione = "Mantieni la soglia attuale"
    
    return jsonify({
        'suggerimento': suggerimento_finale,
        'motivo': motivo,
        'dettagli': {
            'utilizzo_medio_mensile': round(utilizzo_medio_mensile, 1),
            'utilizzo_massimo_mensile': utilizzo_massimo_mensile,
            'utilizzo_giornaliero': round(utilizzo_giornaliero, 2),
            'giorni_copertura_attuale': giorni_copertura if giorni_copertura < 999 else 'Illimitata',
            'scorta_lead_time': scorta_lead_time,
            'raccomandazione': raccomandazione,
            'periodo_analisi': '90 giorni',
            'movimenti_analizzati': len(movimenti_scarico)
        }
    })
