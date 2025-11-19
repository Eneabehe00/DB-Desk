from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func, extract
from app import csrf
from app import db
from app.models.ticket import Ticket
from app.models.cliente import Cliente
from app.models.user import User
from app.models.ticket_attachment import TicketAttachment
from app.models.ticket_subtask import TicketSubtask
from app.forms.ticket import TicketForm, TicketFilterForm
from app.utils.permissions import filter_by_department_access, PermissionManager, require_permission
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, date
import os
import uuid
import calendar

tickets_bp = Blueprint('tickets', __name__)


@tickets_bp.route('/')
@login_required
def list_tickets():
    """Lista di tutti i ticket con filtri"""
    form = TicketFilterForm()
    
    # Query base - filtra per reparto accessibile
    query = filter_by_department_access(Ticket.query, Ticket)
    
    # Controlla se ci sono filtri nei parametri URL
    has_filters = any([
        request.args.get('search'),
        request.args.get('stato'),
        request.args.get('priorita'), 
        request.args.get('categoria'),
        request.args.get('cliente')
    ])
    
    # Imposta filtro di default per stato "Aperto" (tutti gli stati attivi) se non ci sono filtri specificati
    default_filter_applied = False
    if not has_filters and not request.args.get('page'):
        # Prima visita della pagina, applica filtro default per stati aperti
        form.stato.data = 'Aperto'
        query = query.filter(Ticket.stato.in_(Ticket.get_stati_aperti()))
        default_filter_applied = True
    
    # Applica filtri da parametri URL
    search_term = request.args.get('search', '').strip()
    if search_term:
        form.search.data = search_term
        search_pattern = f"%{search_term}%"
        query = query.filter(or_(
            Ticket.titolo.like(search_pattern),
            Ticket.descrizione.like(search_pattern),
            Ticket.numero_ticket.like(search_pattern)
        ))
    
    stato_filter = request.args.get('stato', '').strip()
    if stato_filter:
        form.stato.data = stato_filter
        
        if stato_filter == 'Aperto':
            # "Aperto" include tutti gli stati attivi (non chiusi)
            query = query.filter(Ticket.stato.in_(Ticket.get_stati_aperti()))
        elif stato_filter == 'Chiuso':
            # "Chiuso" include solo i ticket definitivamente chiusi
            query = query.filter(Ticket.stato.in_(Ticket.get_stati_chiusi()))
        elif stato_filter == 'Aperto_exact':
            # "Solo Aperti" - solo lo stato specifico "Aperto"
            query = query.filter(Ticket.stato == 'Aperto')
        elif stato_filter != '---':  # Ignora il separatore
            # Stati specifici
            query = query.filter(Ticket.stato == stato_filter)
    
    priorita_filter = request.args.get('priorita', '').strip()
    if priorita_filter:
        form.priorita.data = priorita_filter
        query = query.filter(Ticket.priorita == priorita_filter)
    
    categoria_filter = request.args.get('categoria', '').strip()
    if categoria_filter:
        form.categoria.data = categoria_filter
        query = query.filter(Ticket.categoria == categoria_filter)
    
    cliente_filter = request.args.get('cliente', '').strip()
    if cliente_filter:
        try:
            cliente_id = int(cliente_filter)
            cliente = Cliente.query.get(cliente_id)
            if cliente:
                form.cliente.data = cliente
                query = query.filter(Ticket.cliente_id == cliente_id)
        except (ValueError, TypeError):
            pass
    
    # Ordinamento
    sort_by = request.args.get('sort_by', '').strip()
    sort_order = request.args.get('sort_order', '').strip()
    
    # Mapping dei campi ordinabili
    sortable_fields = {
        'numero': Ticket.numero_ticket,
        'titolo': Ticket.titolo,
        'cliente': Cliente.ragione_sociale,
        'stato': Ticket.stato,
        'priorita': Ticket.priorita,
        'created_at': Ticket.created_at
    }
    
    # Applica ordinamento se specificato
    if sort_by in sortable_fields and sort_order in ['asc', 'desc']:
        sort_field = sortable_fields[sort_by]
        
        # Per i campi che richiedono join
        if sort_by == 'cliente':
            query = query.join(Cliente, Ticket.cliente_id == Cliente.id, isouter=True)
        
        if sort_order == 'asc':
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
    else:
        # Ordinamento di default
        query = query.order_by(Ticket.created_at.desc())
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Numero di ticket per pagina
    
    tickets = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('tickets/list.html', 
                         tickets=tickets, 
                         form=form, 
                         default_filter_applied=default_filter_applied,
                         current_sort_by=sort_by,
                         current_sort_order=sort_order)


@tickets_bp.route('/api/macchine_disponibili')
@login_required
def get_macchine_disponibili():
    """API endpoint per ottenere le macchine disponibili per il prestito"""
    try:
        from app.models.macchina import Macchina
        from app.utils.permissions import filter_by_department_access

        # Ottieni il cliente_id dai parametri della richiesta (se fornito)
        cliente_id = request.args.get('cliente_id', type=int)

        # Ottieni le macchine disponibili e attive del reparto dell'utente (per prestiti d'uso)
        query = filter_by_department_access(Macchina.query, Macchina)
        macchine = query.filter(Macchina.stato.in_(['Disponibile', 'Attiva'])).order_by(Macchina.codice).all()

        # Escludi le macchine del cliente selezionato (se specificato)
        if cliente_id:
            macchine = [m for m in macchine if m.cliente_id != cliente_id]
        
        macchine_data = []
        for macchina in macchine:
            if PermissionManager.can_view_machine(current_user, macchina):
                macchine_data.append({
                    'id': macchina.id,
                    'codice': macchina.codice,
                    'modello': macchina.modello,
                    'marca': macchina.marca,
                    'stato': macchina.stato,
                    'text': f"{macchina.codice} - {macchina.marca} {macchina.modello}",
                    'stato_badge': macchina.stato
                })

        return jsonify({
            'success': True,
            'macchine': macchine_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tickets_bp.route('/api/search_clients')
@login_required
def search_clients():
    """API endpoint per la ricerca dei clienti"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    # Ricerca nei campi ragione_sociale, codice_fiscale e email
    clienti = Cliente.query.filter(
        and_(
            Cliente.is_active == True,
            or_(
                Cliente.ragione_sociale.ilike(f'%{query}%'),
                Cliente.codice_fiscale.ilike(f'%{query}%'),
                Cliente.email.ilike(f'%{query}%')
            )
        )
    ).limit(10).all()

    return jsonify([{
        'id': cliente.id,
        'text': cliente.ragione_sociale,
        'subtitle': f'{cliente.codice_fiscale or "N/A"} - {cliente.email}' if cliente.email else (cliente.codice_fiscale or "N/A")
    } for cliente in clienti])


@tickets_bp.route('/api/client_machines/<int:cliente_id>')
@login_required
def get_client_machines(cliente_id):
    """API endpoint per ottenere le macchine associate a un cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)

        # Verifica che l'utente possa vedere il cliente (i clienti sono condivisi)
        # Ma controlliamo che l'utente possa vedere le macchine del cliente

        from app.models.macchina import Macchina
        macchine = Macchina.query.filter_by(cliente_id=cliente_id).order_by(Macchina.codice).all()

        # Filtro basato sui permessi dell'utente per vedere macchine
        macchine_filtrate = []
        for macchina in macchine:
            if PermissionManager.can_view_machine(current_user, macchina):
                macchine_filtrate.append({
                    'id': macchina.id,
                    'codice': macchina.codice,
                    'modello': macchina.modello,
                    'marca': macchina.marca,
                    'stato': macchina.stato,
                    'text': f"{macchina.codice} - {macchina.marca} {macchina.modello}",
                    'stato_badge': macchina.stato
                })

        return jsonify({
            'success': True,
            'macchine': macchine_filtrate
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@tickets_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    """Crea nuovo ticket"""
    form = TicketForm()
    
    # Se è un POST, popola le scelte delle macchine basate sul cliente selezionato
    if request.method == 'POST':
        cliente_id = request.form.get('cliente')
        if cliente_id and cliente_id != '0':
            try:
                cliente_id = int(cliente_id)
                from app.models.macchina import Macchina
                
                # Ottieni le macchine del cliente che l'utente può vedere
                macchine = Macchina.query.filter_by(cliente_id=cliente_id).order_by(Macchina.codice).all()
                macchine_filtrate = []
                
                for macchina in macchine:
                    if PermissionManager.can_view_machine(current_user, macchina):
                        macchine_filtrate.append((macchina.id, f"{macchina.codice} - {macchina.marca} {macchina.modello}"))
                
                # Aggiorna le scelte del campo macchine
                form.macchine.choices = macchine_filtrate
                
                # Aggiorna anche le scelte del cliente per la validazione
                from app.models.cliente import Cliente
                cliente = Cliente.query.get(cliente_id)
                if cliente:
                    form.cliente.choices = [(0, 'Seleziona cliente...'), (cliente.id, cliente.ragione_sociale)]
                
            except (ValueError, TypeError):
                pass
        
        # Popola sempre le scelte per le macchine sostitutive se è una riparazione con prestito
        tipo_operazione = request.form.get('tipo_operazione_macchine')
        if tipo_operazione == 'riparazione_sede_con_prestito':
            from app.models.macchina import Macchina
            from app.utils.permissions import filter_by_department_access
            
            # Ottieni le macchine disponibili del reparto dell'utente
            query = filter_by_department_access(Macchina.query, Macchina)
            macchine_disponibili = query.filter_by(stato='Disponibile').order_by(Macchina.codice).all()
            
            macchine_sostitutive_choices = []
            for macchina in macchine_disponibili:
                if PermissionManager.can_view_machine(current_user, macchina):
                    macchine_sostitutive_choices.append((macchina.id, f"{macchina.codice} - {macchina.marca} {macchina.modello}"))
            
            form.macchine_sostitutive.choices = macchine_sostitutive_choices
    
    if form.validate_on_submit():
        # Determina il reparto per il ticket - usa sempre il reparto dell'utente
        # I clienti sono condivisi, ma i ticket appartengono al reparto di chi li crea
        department_id = current_user.department_id
        
        ticket = Ticket(
            titolo=form.titolo.data,
            descrizione=form.descrizione.data,
            cliente_id=form.cliente.data if form.cliente.data else None,
            created_by_id=current_user.id,
            department_id=department_id,
            categoria=form.categoria.data,
            priorita=form.priorita.data,
            stato=form.stato.data,
            assigned_to_id=form.assigned_to.data if form.assigned_to.data and form.assigned_to.data != 0 else current_user.id,
            due_date=form.due_date.data,
            tempo_stimato=form.tempo_stimato.data,
            note_interne=form.note_interne.data
        )

        # Gestisci le macchine collegate se specificate
        if form.macchine.data:
            from app.models.macchina import Macchina
            for macchina_id in form.macchine.data:
                macchina = Macchina.query.get(macchina_id)
                if macchina:
                    ticket.macchine_collegate.append(macchina)
        
        # Gestisci i tag
        if form.tags.data:
            ticket.set_tags([tag.strip() for tag in form.tags.data.split(',')])
        
        db.session.add(ticket)
        db.session.flush()  # Per ottenere l'ID del ticket
        
        # Gestisci operazioni sulle macchine (dopo aver ottenuto l'ID del ticket)
        if form.macchine.data and form.tipo_operazione_macchine.data:
            from app.models.macchina import Macchina
            tipo_operazione = form.tipo_operazione_macchine.data
            
            for macchina_id in form.macchine.data:
                macchina = Macchina.query.get(macchina_id)
                if macchina:
                    try:
                        if tipo_operazione == 'prestito_semplice':
                            # Presta macchina al cliente (anche se attiva presso altro cliente)
                            if macchina.is_disponibile or macchina.is_attiva:
                                if macchina.is_disponibile:
                                    # Macchina disponibile - usa metodo standard
                                    movimento = macchina.assegna_a_cliente(
                                        form.cliente.data, 
                                        'In prestito', 
                                        f'Prestito semplice per ticket {ticket.numero_ticket}'
                                    )
                                else:
                                    # Macchina attiva - usa prestito temporaneo
                                    movimento = macchina.presta_temporaneamente(
                                        form.cliente.data,
                                        f'Prestito semplice per ticket {ticket.numero_ticket}'
                                    )
                                movimento.ticket_id = ticket.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'riparazione_sede':
                            # Porta macchina in riparazione in sede (solo ritiro)
                            if not macchina.is_in_riparazione:
                                movimento = macchina.invia_in_riparazione(
                                    f'Riparazione in sede per ticket {ticket.numero_ticket}'
                                )
                                movimento.ticket_id = ticket.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'riparazione_sede_con_prestito':
                            # Porta macchina del cliente in riparazione
                            if not macchina.is_in_riparazione:
                                movimento = macchina.invia_in_riparazione(
                                    f'Riparazione in sede con prestito per ticket {ticket.numero_ticket}'
                                )
                                movimento.ticket_id = ticket.id
                                movimento.user_id = current_user.id
                        # Per 'riparazione_cliente' non cambiamo stato, è solo documentazione
                    except Exception as e:
                        # Log dell'errore ma non bloccare la creazione del ticket
                        flash(f'Attenzione: errore nell\'operazione sulla macchina {macchina.codice}: {str(e)}', 'warning')
            
            # Gestisci macchine sostitutive per riparazione con prestito
            if tipo_operazione == 'riparazione_sede_con_prestito' and form.macchine_sostitutive.data:
                for macchina_sostitutiva_id in form.macchine_sostitutive.data:
                    macchina_sostitutiva = Macchina.query.get(macchina_sostitutiva_id)
                    if macchina_sostitutiva and macchina_sostitutiva.is_disponibile:
                        try:
                            movimento = macchina_sostitutiva.assegna_a_cliente(
                                form.cliente.data,
                                'In prestito',
                                f'Prestito sostitutivo durante riparazione per ticket {ticket.numero_ticket}'
                            )
                            movimento.ticket_id = ticket.id
                            movimento.user_id = current_user.id
                        except Exception as e:
                            flash(f'Attenzione: errore nell\'assegnazione della macchina sostitutiva {macchina_sostitutiva.codice}: {str(e)}', 'warning')
        
        # Gestisci i ricambi necessari con quantità
        if form.ricambi_necessari.data:
            from app.models.ticket import ticket_ricambi
            for ricambio_id in form.ricambi_necessari.data:
                # Ottieni la quantità dal form (se specificata)
                quantity_field_name = f'ricambio_quantity_{ricambio_id}'
                quantity_str = request.form.get(quantity_field_name, '1').strip()
                quantita_necessaria = int(quantity_str) if quantity_str else 1
                
                # Inserisci nella tabella di associazione
                db.session.execute(
                    ticket_ricambi.insert().values(
                        ticket_id=ticket.id,
                        ricambio_id=ricambio_id,
                        quantita_necessaria=quantita_necessaria,
                        quantita_utilizzata=0
                    )
                )
        
        db.session.commit()
        
        # Gestione allegato in creazione (opzionale: "file")
        if 'file' in request.files and request.files['file'] and request.files['file'].filename:
            file = request.files['file']
            if _allowed_extension(file.filename, current_app.config['ALLOWED_ATTACHMENT_EXTENSIONS']):
                original_name = secure_filename(file.filename)
                unique_name = f"{ticket.id}_{uuid.uuid4().hex}_{original_name}"
                save_path = os.path.join(current_app.config['ATTACHMENTS_FOLDER'], unique_name)
                file.save(save_path)
                attachment = TicketAttachment(
                    ticket_id=ticket.id,
                    filename=original_name,
                    stored_filename=unique_name,
                    content_type=file.mimetype,
                    size_bytes=os.path.getsize(save_path),
                    uploaded_by_id=current_user.id
                )
                db.session.add(attachment)
                db.session.commit()

        flash(f'Ticket {ticket.numero_ticket} creato con successo!', 'success')
        return redirect(url_for('tickets.view_ticket', id=ticket.id))
    else:
        # Se ci sono errori di validazione, mostra i dettagli per debug
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Errore nel campo {field}: {error}', 'error')
    
    return render_template(
        'tickets/form.html',
        form=form,
        title='Nuovo Ticket',
        allowed_attach_exts=sorted(list(current_app.config['ALLOWED_ATTACHMENT_EXTENSIONS']))
    )


@tickets_bp.route('/<int:id>')
@login_required
def view_ticket(id):
    """Visualizza dettagli ticket"""
    ticket = Ticket.query.get_or_404(id)
    
    # Verifica accesso al ticket
    if not PermissionManager.check_ticket_access(ticket):
        abort(403)
    
    subtasks = ticket.subtasks.all()
    attachments = ticket.attachments.order_by(TicketAttachment.uploaded_at.desc()).all()
    
    # Ottieni i ricambi associati con le quantità
    from app.models.ticket import ticket_ricambi
    from app.models.ricambio import Ricambio
    
    ricambi_query = db.session.query(
        Ricambio,
        ticket_ricambi.c.quantita_necessaria,
        ticket_ricambi.c.quantita_utilizzata
    ).join(
        ticket_ricambi, Ricambio.id == ticket_ricambi.c.ricambio_id
    ).filter(
        ticket_ricambi.c.ticket_id == ticket.id
    ).all()
    
    ricambi_associati = []
    for ricambio, qta_necessaria, qta_utilizzata in ricambi_query:
        ricambi_associati.append({
            'ricambio': ricambio,
            'quantita_necessaria': qta_necessaria,
            'quantita_utilizzata': qta_utilizzata,
            'quantita_rimanente': qta_necessaria - qta_utilizzata
        })
    
    return render_template('tickets/detail.html', 
                         ticket=ticket, 
                         subtasks=subtasks, 
                         attachments=attachments,
                         ricambi_associati=ricambi_associati)


@tickets_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(id):
    """Modifica ticket"""
    ticket = Ticket.query.get_or_404(id)
    
    # Verifica accesso al ticket
    if not PermissionManager.check_ticket_access(ticket):
        abort(403)
    
    form = TicketForm(obj=ticket)
    
    # Se è un POST, popola le scelte delle macchine basate sul cliente selezionato
    if request.method == 'POST':
        cliente_id = request.form.get('cliente')
        if cliente_id and cliente_id != '0':
            try:
                cliente_id = int(cliente_id)
                from app.models.macchina import Macchina
                
                # Ottieni le macchine del cliente che l'utente può vedere
                macchine = Macchina.query.filter_by(cliente_id=cliente_id).order_by(Macchina.codice).all()
                macchine_filtrate = []
                
                for macchina in macchine:
                    if PermissionManager.can_view_machine(current_user, macchina):
                        macchine_filtrate.append((macchina.id, f"{macchina.codice} - {macchina.marca} {macchina.modello}"))
                
                # Aggiorna le scelte del campo macchine
                form.macchine.choices = macchine_filtrate
                
                # Aggiorna anche le scelte del cliente per la validazione
                from app.models.cliente import Cliente
                cliente = Cliente.query.get(cliente_id)
                if cliente:
                    form.cliente.choices = [(0, 'Seleziona cliente...'), (cliente.id, cliente.ragione_sociale)]
                
            except (ValueError, TypeError):
                pass
        
        # Popola sempre le scelte per le macchine sostitutive se è una riparazione con prestito
        tipo_operazione = request.form.get('tipo_operazione_macchine')
        if tipo_operazione == 'riparazione_sede_con_prestito':
            from app.models.macchina import Macchina
            from app.utils.permissions import filter_by_department_access
            
            # Ottieni le macchine disponibili del reparto dell'utente
            query = filter_by_department_access(Macchina.query, Macchina)
            macchine_disponibili = query.filter_by(stato='Disponibile').order_by(Macchina.codice).all()
            
            macchine_sostitutive_choices = []
            for macchina in macchine_disponibili:
                if PermissionManager.can_view_machine(current_user, macchina):
                    macchine_sostitutive_choices.append((macchina.id, f"{macchina.codice} - {macchina.marca} {macchina.modello}"))
            
            form.macchine_sostitutive.choices = macchine_sostitutive_choices
    
    # Pre-popola i campi del form
    if request.method == 'GET':
        form.cliente.data = ticket.cliente
        form.assigned_to.data = ticket.assigned_to
        form.tags.data = ', '.join(ticket.tag_list)

        # Pre-popola le macchine del cliente se esiste
        if ticket.cliente_id:
            from app.models.macchina import Macchina
            macchine = Macchina.query.filter_by(cliente_id=ticket.cliente_id).order_by(Macchina.codice).all()
            macchine_filtrate = []
            
            for macchina in macchine:
                if PermissionManager.can_view_machine(current_user, macchina):
                    macchine_filtrate.append((macchina.id, f"{macchina.codice} - {macchina.marca} {macchina.modello}"))
            
            form.macchine.choices = macchine_filtrate
        
        # Pre-popola le macchine collegate
        if ticket.macchine_collegate:
            form.macchine.data = [m.id for m in ticket.macchine_collegate]
        
        # Pre-popola i ricambi necessari con quantità
        from app.models.ticket import ticket_ricambi
        ricambi_query = db.session.query(
            ticket_ricambi.c.ricambio_id,
            ticket_ricambi.c.quantita_necessaria
        ).filter(
            ticket_ricambi.c.ticket_id == ticket.id
        ).all()
        
        form.ricambi_necessari.data = [r[0] for r in ricambi_query]
        
        # Aggiungi le quantità esistenti al form per il JavaScript
        form.ricambi_quantities = {r[0]: r[1] for r in ricambi_query}
    
    if form.validate_on_submit():
        ticket.titolo = form.titolo.data
        ticket.descrizione = form.descrizione.data
        ticket.cliente_id = form.cliente.data if form.cliente.data else None
        ticket.categoria = form.categoria.data
        ticket.priorita = form.priorita.data
        ticket.stato = form.stato.data
        ticket.assigned_to_id = form.assigned_to.data if form.assigned_to.data and form.assigned_to.data != 0 else None
        ticket.due_date = form.due_date.data
        ticket.tempo_stimato = form.tempo_stimato.data
        ticket.note_interne = form.note_interne.data
        
        # Gestisci i tag
        if form.tags.data:
            ticket.set_tags([tag.strip() for tag in form.tags.data.split(',')])
        else:
            ticket.tags = None
        
        # Gestisci i ricambi necessari
        from app.models.ticket import ticket_ricambi
        
        # Rimuovi i ricambi esistenti
        db.session.execute(
            ticket_ricambi.delete().where(ticket_ricambi.c.ticket_id == ticket.id)
        )
        
        # Aggiungi i nuovi ricambi con quantità
        if form.ricambi_necessari.data:
            for ricambio_id in form.ricambi_necessari.data:
                # Ottieni la quantità dal form (se specificata)
                quantity_field_name = f'ricambio_quantity_{ricambio_id}'
                quantity_str = request.form.get(quantity_field_name, '1').strip()
                quantita_necessaria = int(quantity_str) if quantity_str else 1
                
                db.session.execute(
                    ticket_ricambi.insert().values(
                        ticket_id=ticket.id,
                        ricambio_id=ricambio_id,
                        quantita_necessaria=quantita_necessaria,
                        quantita_utilizzata=0
                    )
                )

        # Gestisci le macchine collegate
        # Rimuovi tutte le associazioni esistenti dalla tabella di associazione
        from app.models.macchina import ticket_macchine
        db.session.execute(
            ticket_macchine.delete().where(ticket_macchine.c.ticket_id == ticket.id)
        )
        if form.macchine.data:
            from app.models.macchina import Macchina
            for macchina_id in form.macchine.data:
                macchina = Macchina.query.get(macchina_id)
                if macchina:
                    ticket.macchine_collegate.append(macchina)

        # Gestisci operazioni sulle macchine (solo se specificato tipo operazione)
        if form.macchine.data and form.tipo_operazione_macchine.data:
            from app.models.macchina import Macchina
            tipo_operazione = form.tipo_operazione_macchine.data
            
            for macchina_id in form.macchine.data:
                macchina = Macchina.query.get(macchina_id)
                if macchina:
                    try:
                        if tipo_operazione == 'prestito_semplice':
                            # Presta macchina al cliente (anche se attiva presso altro cliente)
                            if macchina.is_disponibile or macchina.is_attiva:
                                if macchina.is_disponibile:
                                    # Macchina disponibile - usa metodo standard
                                    movimento = macchina.assegna_a_cliente(
                                        form.cliente.data, 
                                        'In prestito', 
                                        f'Prestito semplice per ticket {ticket.numero_ticket} (aggiornamento)'
                                    )
                                else:
                                    # Macchina attiva - usa prestito temporaneo
                                    movimento = macchina.presta_temporaneamente(
                                        form.cliente.data,
                                        f'Prestito semplice per ticket {ticket.numero_ticket} (aggiornamento)'
                                    )
                                movimento.ticket_id = ticket.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'riparazione_sede':
                            # Porta macchina in riparazione in sede (solo se non già in riparazione)
                            if not macchina.is_in_riparazione:
                                movimento = macchina.invia_in_riparazione(
                                    f'Riparazione in sede per ticket {ticket.numero_ticket} (aggiornamento)'
                                )
                                movimento.ticket_id = ticket.id
                                movimento.user_id = current_user.id
                        elif tipo_operazione == 'riparazione_sede_con_prestito':
                            # Porta macchina del cliente in riparazione (solo se non già in riparazione)
                            if not macchina.is_in_riparazione:
                                movimento = macchina.invia_in_riparazione(
                                    f'Riparazione in sede con prestito per ticket {ticket.numero_ticket} (aggiornamento)'
                                )
                                movimento.ticket_id = ticket.id
                                movimento.user_id = current_user.id
                        # Per 'riparazione_cliente' non cambiamo stato, è solo documentazione
                    except Exception as e:
                        # Log dell'errore ma non bloccare l'aggiornamento del ticket
                        flash(f'Attenzione: errore nell\'operazione sulla macchina {macchina.codice}: {str(e)}', 'warning')
            
            # Gestisci macchine sostitutive per riparazione con prestito (in modifica)
            if tipo_operazione == 'riparazione_sede_con_prestito' and form.macchine_sostitutive.data:
                for macchina_sostitutiva_id in form.macchine_sostitutive.data:
                    macchina_sostitutiva = Macchina.query.get(macchina_sostitutiva_id)
                    if macchina_sostitutiva and macchina_sostitutiva.is_disponibile:
                        try:
                            movimento = macchina_sostitutiva.assegna_a_cliente(
                                form.cliente.data,
                                'In prestito',
                                f'Prestito sostitutivo durante riparazione per ticket {ticket.numero_ticket} (aggiornamento)'
                            )
                            movimento.ticket_id = ticket.id
                            movimento.user_id = current_user.id
                        except Exception as e:
                            flash(f'Attenzione: errore nell\'assegnazione della macchina sostitutiva {macchina_sostitutiva.codice}: {str(e)}', 'warning')

        # Aggiorna timestamp risoluzione/chiusura
        if form.stato.data == 'Risolto' and ticket.stato != 'Risolto':
            ticket.risolvi_ticket()
        elif form.stato.data == 'Chiuso' and ticket.stato != 'Chiuso':
            ticket.chiudi_ticket()
            # Ripristina stati macchine quando il ticket viene chiuso
            _ripristina_stati_macchine_ticket(ticket)
        elif form.stato.data in ['Aperto', 'In Lavorazione'] and ticket.stato in ['Risolto', 'Chiuso']:
            ticket.riapri_ticket()
        
        db.session.commit()
        flash(f'Ticket {ticket.numero_ticket} aggiornato con successo!', 'success')
        return redirect(url_for('tickets.view_ticket', id=ticket.id))
    
    return render_template(
        'tickets/form.html',
        form=form,
        ticket=ticket,
        title='Modifica Ticket',
        allowed_attach_exts=sorted(list(current_app.config['ALLOWED_ATTACHMENT_EXTENSIONS']))
    )


@tickets_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_ticket(id):
    """Elimina ticket (solo admin o creatore)"""
    ticket = Ticket.query.get_or_404(id)
    
    # Verifica permessi
    if not current_user.is_admin and ticket.created_by_id != current_user.id:
        flash('Non hai i permessi per eliminare questo ticket.', 'error')
        return redirect(url_for('tickets.view_ticket', id=id))
    
    numero_ticket = ticket.numero_ticket
    
    # Ripristina i ricambi utilizzati prima di eliminare il ticket
    from app.models.ticket import ticket_ricambi
    from app.models.ricambio import Ricambio
    from app.models.ricambio import MovimentoMagazzino
    
    # Ottieni tutti i ricambi associati al ticket con quantità utilizzate
    ricambi_query = db.session.query(
        ticket_ricambi.c.ricambio_id,
        ticket_ricambi.c.quantita_utilizzata
    ).filter(
        ticket_ricambi.c.ticket_id == ticket.id,
        ticket_ricambi.c.quantita_utilizzata > 0  # Solo quelli effettivamente utilizzati
    ).all()
    
    # Ripristina ogni ricambio utilizzato
    ricambi_ripristinati = []
    for ricambio_id, quantita_utilizzata in ricambi_query:
        ricambio = Ricambio.query.get(ricambio_id)
        if ricambio and quantita_utilizzata > 0:
            # Ripristina la quantità nel magazzino
            ricambio.quantita_disponibile += quantita_utilizzata
            ricambi_ripristinati.append(f"{ricambio.codice} (+{quantita_utilizzata})")
            
            # Registra il movimento di ripristino
            movimento = MovimentoMagazzino(
                ricambio_id=ricambio.id,
                tipo_movimento='Carico',
                quantita=quantita_utilizzata,
                motivo=f'Ripristino per eliminazione ticket {numero_ticket}',
                ticket_id=ticket.id,
                user_id=current_user.id
            )
            db.session.add(movimento)
    
    db.session.delete(ticket)
    db.session.commit()
    
    # Messaggio di conferma con dettagli sui ricambi ripristinati
    message = f'Ticket {numero_ticket} eliminato con successo.'
    if ricambi_ripristinati:
        message += f' Ricambi ripristinati: {", ".join(ricambi_ripristinati)}'
    
    flash(message, 'success')
    return redirect(url_for('tickets.list_tickets'))


@tickets_bp.route('/<int:id>/change_status', methods=['POST'])
@login_required
@csrf.exempt
def change_status(id):
    """Cambia rapidamente lo stato di un ticket (AJAX)"""
    try:
        ticket = Ticket.query.get_or_404(id)

        # Debug: verifica che il JSON sia valido
        if not request.json:
            return jsonify({'success': False, 'message': 'Dati JSON mancanti'}), 400

        # Verifica manuale del token CSRF per richieste JSON
        csrf_token = request.json.get('csrf_token')
        if not csrf_token:
            return jsonify({'success': False, 'message': 'Token CSRF mancante'}), 400

        # Valida il token CSRF manualmente
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(csrf_token)
        except Exception:
            return jsonify({'success': False, 'message': 'Token CSRF non valido'}), 400

        new_status = request.json.get('status')

        if not new_status:
            return jsonify({'success': False, 'message': 'Stato non specificato'}), 400

        if new_status not in ['Aperto', 'In Lavorazione', 'In Attesa Cliente', 'Risolto', 'Chiuso']:
            return jsonify({'success': False, 'message': f'Stato non valido: {new_status}'}), 400

        old_status = ticket.stato
        ticket.stato = new_status

        # Aggiorna timestamp appropriati
        if new_status == 'Risolto' and old_status != 'Risolto':
            ticket.risolvi_ticket()
        elif new_status == 'Chiuso' and old_status != 'Chiuso':
            ticket.chiudi_ticket()
            # Ripristina stati macchine quando il ticket viene chiuso
            _ripristina_stati_macchine_ticket(ticket)
        elif new_status in ['Aperto', 'In Lavorazione'] and old_status in ['Risolto', 'Chiuso']:
            ticket.riapri_ticket()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Stato del ticket cambiato da "{old_status}" a "{new_status}"',
            'new_status': new_status
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Errore interno: {str(e)}'}), 500


@tickets_bp.route('/<int:id>/assign', methods=['POST'])
@login_required
@csrf.exempt
def assign_ticket(id):
    """Assegna ticket a un utente (AJAX)"""
    try:
        ticket = Ticket.query.get_or_404(id)

        # Verifica che il JSON sia valido
        if not request.json:
            return jsonify({'success': False, 'message': 'Dati JSON mancanti'}), 400

        # Verifica manuale del token CSRF per richieste JSON
        csrf_token = request.json.get('csrf_token')
        if not csrf_token:
            return jsonify({'success': False, 'message': 'Token CSRF mancante'}), 400

        # Valida il token CSRF manualmente
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(csrf_token)
        except Exception:
            return jsonify({'success': False, 'message': 'Token CSRF non valido'}), 400

        user_id = request.json.get('user_id')

        if user_id:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'success': False, 'message': 'Utente non trovato'}), 404

            ticket.assigned_to_id = user_id
            message = f'Ticket assegnato a {user.full_name}'
        else:
            ticket.assigned_to_id = None
            message = 'Ticket non assegnato'

        db.session.commit()

        return jsonify({
            'success': True,
            'message': message,
            'assigned_to_name': ticket.assigned_to.full_name if ticket.assigned_to else None
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Errore interno: {str(e)}'}), 500


def _allowed_extension(filename, allowed_set):
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in {e.strip().lower() for e in allowed_set}


@tickets_bp.route('/<int:id>/attachments/upload', methods=['POST'])
@login_required
def upload_attachment(id):
    ticket = Ticket.query.get_or_404(id)
    if 'file' not in request.files:
        flash('Nessun file selezionato.', 'error')
        return redirect(url_for('tickets.view_ticket', id=id))

    file = request.files['file']
    if file.filename == '':
        flash('Nessun file selezionato.', 'error')
        return redirect(url_for('tickets.view_ticket', id=id))

    if not _allowed_extension(file.filename, current_app.config['ALLOWED_ATTACHMENT_EXTENSIONS']):
        flash('Estensione file non permessa.', 'error')
        return redirect(url_for('tickets.view_ticket', id=id))

    original_name = secure_filename(file.filename)
    unique_name = f"{ticket.id}_{uuid.uuid4().hex}_{original_name}"
    save_path = os.path.join(current_app.config['ATTACHMENTS_FOLDER'], unique_name)
    file.save(save_path)

    attachment = TicketAttachment(
        ticket_id=ticket.id,
        filename=original_name,
        stored_filename=unique_name,
        content_type=file.mimetype,
        size_bytes=os.path.getsize(save_path),
        uploaded_by_id=current_user.id
    )
    db.session.add(attachment)
    db.session.commit()

    flash('Allegato caricato con successo.', 'success')
    return redirect(url_for('tickets.view_ticket', id=id))


@tickets_bp.route('/attachments/<path:stored_filename>')
@login_required
def download_attachment(stored_filename):
    # autorizzazione: consenti download solo se l'utente ha accesso al ticket
    attachment = TicketAttachment.query.filter_by(stored_filename=stored_filename).first_or_404()
    ticket = Ticket.query.get(attachment.ticket_id)
    if not ticket:
        abort(404)
    # opzionale: ulteriori controlli su permessi
    return send_from_directory(current_app.config['ATTACHMENTS_FOLDER'], stored_filename, as_attachment=True, download_name=attachment.filename)


@tickets_bp.route('/<int:id>/attachments/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(id, attachment_id):
    ticket = Ticket.query.get_or_404(id)
    attachment = TicketAttachment.query.get_or_404(attachment_id)
    if attachment.ticket_id != ticket.id:
        abort(400)
    # permessi: admin o creatore o assegnato
    if not (current_user.is_admin or ticket.created_by_id == current_user.id or ticket.assigned_to_id == current_user.id):
        flash('Non hai i permessi per eliminare questo allegato.', 'error')
        return redirect(url_for('tickets.view_ticket', id=id))
    # elimina file su disco
    file_path = os.path.join(current_app.config['ATTACHMENTS_FOLDER'], attachment.stored_filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass
    db.session.delete(attachment)
    db.session.commit()
    flash('Allegato eliminato.', 'success')
    return redirect(url_for('tickets.view_ticket', id=id))


@tickets_bp.route('/<int:id>/subtasks', methods=['POST'])
@login_required
def add_subtask(id):
    ticket = Ticket.query.get_or_404(id)
    title = request.form.get('title', '').strip()
    if not title:
        flash('Il titolo della sotto-attività è obbligatorio.', 'error')
        return redirect(url_for('tickets.view_ticket', id=id))
    position = (ticket.subtasks.count() or 0) + 1
    subtask = TicketSubtask(ticket_id=ticket.id, title=title, position=position)
    db.session.add(subtask)
    db.session.commit()
    flash('Sotto-attività aggiunta.', 'success')
    return redirect(url_for('tickets.view_ticket', id=id))


@tickets_bp.route('/<int:id>/subtasks/<int:subtask_id>/toggle', methods=['POST'])
@login_required
def toggle_subtask(id, subtask_id):
    ticket = Ticket.query.get_or_404(id)
    subtask = TicketSubtask.query.get_or_404(subtask_id)
    if subtask.ticket_id != ticket.id:
        abort(400)
    if subtask.is_done:
        subtask.mark_undone()
    else:
        subtask.mark_done()
    db.session.commit()
    return redirect(url_for('tickets.view_ticket', id=id))


@tickets_bp.route('/<int:id>/subtasks/<int:subtask_id>/delete', methods=['POST'])
@login_required
def delete_subtask(id, subtask_id):
    ticket = Ticket.query.get_or_404(id)
    subtask = TicketSubtask.query.get_or_404(subtask_id)
    if subtask.ticket_id != ticket.id:
        abort(400)
    db.session.delete(subtask)
    db.session.commit()
    flash('Sotto-attività eliminata.', 'success')
    return redirect(url_for('tickets.view_ticket', id=id))


@tickets_bp.route('/my')
@login_required
def my_tickets():
    """I miei ticket assegnati (tutti gli stati attivi)"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = Ticket.query.filter_by(assigned_to_id=current_user.id).filter(
        Ticket.stato.in_(Ticket.get_stati_aperti())
    ).order_by(Ticket.created_at.desc())

    tickets = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('tickets/my_tickets.html', tickets=tickets)


@tickets_bp.route('/api/active')
@login_required
def api_active_tickets():
    """API endpoint per ottenere i ticket attivi per le select"""
    tickets = Ticket.query.filter(
        Ticket.stato.in_(Ticket.get_stati_aperti())
    ).order_by(Ticket.created_at.desc()).limit(50).all()
    
    return jsonify([{
        'id': ticket.id,
        'numero': ticket.numero_ticket,
        'titolo': ticket.titolo[:50] + ('...' if len(ticket.titolo) > 50 else '')
    } for ticket in tickets])


@tickets_bp.route('/export')
@login_required
def export_tickets():
    """Esporta ticket in formato CSV"""
    import csv
    from flask import make_response
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Numero Ticket', 'Titolo', 'Cliente', 'Stato', 'Priorità', 'Categoria',
        'Creato da', 'Assegnato a', 'Data Creazione', 'Data Scadenza'
    ])
    
    # Dati
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    for ticket in tickets:
        writer.writerow([
            ticket.numero_ticket,
            ticket.titolo,
            ticket.cliente.ragione_sociale,
            ticket.stato,
            ticket.priorita,
            ticket.categoria,
            ticket.created_by_user.full_name,
            ticket.assigned_to.full_name if ticket.assigned_to else '',
            ticket.created_at.strftime('%Y-%m-%d %H:%M'),
            ticket.due_date.strftime('%Y-%m-%d %H:%M') if ticket.due_date else ''
        ])
    
    # Crea response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=tickets.csv'
    
    return response


@tickets_bp.route('/calendar')
@login_required
def calendar_view():
    """Pagina calendario per la gestione dei ticket"""
    # Get current date parameters
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    # Calculate month range
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Get tickets for the month - filtra per reparto accessibile
    tickets_with_dates_query = filter_by_department_access(Ticket.query, Ticket)
    tickets_with_dates = tickets_with_dates_query.filter(
        Ticket.due_date.between(start_date, end_date + timedelta(days=1))
    ).order_by(Ticket.due_date).all()
    
    # Get open tickets without dates for drag and drop (tutti gli stati attivi) - filtra per reparto accessibile
    open_tickets_query = filter_by_department_access(Ticket.query, Ticket)
    open_tickets = open_tickets_query.filter(
        Ticket.stato.in_(Ticket.get_stati_aperti()),
        Ticket.due_date.is_(None)
    ).order_by(Ticket.created_at.desc()).all()
    
    # Create calendar data structure
    cal = calendar.monthcalendar(year, month)
    calendar_data = {}
    
    for ticket in tickets_with_dates:
        day = ticket.due_date.day
        if day not in calendar_data:
            calendar_data[day] = []
        calendar_data[day].append(ticket)
    
    # Navigation dates
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    return render_template('tickets/calendar.html', 
                         calendar_data=cal,
                         tickets_data=calendar_data,
                         open_tickets=open_tickets,
                         current_year=year,
                         current_month=month,
                         month_name=calendar.month_name[month],
                         prev_year=prev_year,
                         prev_month=prev_month,
                         next_year=next_year,
                         next_month=next_month)


@tickets_bp.route('/api/update-ticket-date', methods=['POST'])
@login_required
@csrf.exempt
def update_ticket_date():
    """API endpoint per aggiornare la data di un ticket via drag and drop"""
    try:
        # Verifica se la richiesta ha Content-Type JSON
        if not request.is_json:
            print(f"Content-Type non JSON: {request.content_type}")
            return jsonify({'success': False, 'message': 'Content-Type deve essere application/json'}), 400

        data = request.get_json()
        if not data:
            print("Nessun dato JSON ricevuto")
            return jsonify({'success': False, 'message': 'Dati JSON mancanti'}), 400

        print(f"Dati ricevuti: {data}")
        ticket_id = data.get('ticket_id')
        new_date = data.get('date')

        # Validazione parametri
        if not ticket_id:
            print(f"ticket_id mancante: {ticket_id}")
            return jsonify({'success': False, 'message': 'ID ticket mancante'}), 400

        print(f"ticket_id type: {type(ticket_id)}, value: {ticket_id}")
        if not isinstance(ticket_id, int):
            # Prova a convertire da stringa a int
            try:
                ticket_id = int(ticket_id)
                print(f"Convertito ticket_id da {type(ticket_id)} a int: {ticket_id}")
            except (ValueError, TypeError):
                print(f"ticket_id non è un int: {ticket_id} (type: {type(ticket_id)})")
                return jsonify({'success': False, 'message': 'ID ticket deve essere un numero'}), 400

        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return jsonify({'success': False, 'message': 'Ticket non trovato'}), 404

        # Verifica accesso al ticket
        if not PermissionManager.check_ticket_access(ticket):
            return jsonify({'success': False, 'message': 'Accesso negato al ticket'}), 403

        # Parse the date
        if new_date:
            if not isinstance(new_date, str):
                return jsonify({'success': False, 'message': 'Data deve essere una stringa'}), 400

            try:
                # Prova diversi formati di data
                if 'T' in new_date:
                    # Formato ISO completo (YYYY-MM-DDTHH:MM:SS)
                    parsed_date = datetime.fromisoformat(new_date.replace('Z', '+00:00'))
                else:
                    # Formato solo data (YYYY-MM-DD) - aggiungi orario
                    parsed_date = datetime.strptime(new_date, '%Y-%m-%d')

                ticket.due_date = parsed_date

                # Change status to "In Lavorazione" when scheduled
                if ticket.stato == 'Aperto':
                    ticket.stato = 'In Lavorazione'

            except ValueError as e:
                return jsonify({'success': False, 'message': f'Formato data non valido: {str(e)}. Formati accettati: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS'}), 400
        else:
            # Remove date
            ticket.due_date = None
            if ticket.stato == 'In Lavorazione':
                ticket.stato = 'Aperto'

        db.session.commit()

        # Determina il messaggio appropriato
        if new_date:
            message = 'Data ticket aggiornata con successo'
        else:
            message = 'Ticket rimosso dal calendario'

        return jsonify({
            'success': True,
            'message': message,
            'ticket': {
                'id': ticket.id,
                'numero_ticket': ticket.numero_ticket,
                'titolo': ticket.titolo,
                'stato': ticket.stato,
                'priorita': ticket.priorita,
                'due_date': ticket.due_date.isoformat() if ticket.due_date else None
            }
        })

    except Exception as e:
        db.session.rollback()
        # Log dell'errore per debug
        print(f"Errore nell'aggiornamento ticket date: {str(e)}")
        return jsonify({'success': False, 'message': f'Errore interno del server: {str(e)}'}), 500


@tickets_bp.route('/api/calendar-tickets')
@login_required
def calendar_tickets():
    """API endpoint per ottenere i ticket per una data specifica"""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'tickets': []})
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get tickets for this date - filtra per reparto accessibile
        tickets_query = filter_by_department_access(Ticket.query, Ticket)
        tickets = tickets_query.filter(
            func.date(Ticket.due_date) == target_date
        ).order_by(Ticket.priorita.desc(), Ticket.created_at).all()
        
        tickets_data = []
        for ticket in tickets:
            tickets_data.append({
                'id': ticket.id,
                'numero_ticket': ticket.numero_ticket,
                'titolo': ticket.titolo,
                'stato': ticket.stato,
                'priorita': ticket.priorita,
                'cliente': ticket.cliente.ragione_sociale,
                'assigned_to': ticket.assigned_to.full_name if ticket.assigned_to else None
            })
        
        return jsonify({'tickets': tickets_data})
        
    except ValueError:
        return jsonify({'error': 'Formato data non valido'}), 400


def _ripristina_stati_macchine_ticket(ticket):
    """
    Ripristina gli stati originali delle macchine quando un ticket viene chiuso.
    Gestisce sia le macchine in riparazione che quelle in prestito sostitutivo.
    """
    from app.models.macchina import Macchina, MovimentoMacchina
    from flask_login import current_user
    
    # Trova tutti i movimenti collegati a questo ticket
    movimenti_ticket = MovimentoMacchina.query.filter_by(ticket_id=ticket.id).order_by(MovimentoMacchina.created_at).all()
    
    if not movimenti_ticket:
        return
    
    # Debug: mostra i movimenti trovati
    flash(f'Debug: Trovati {len(movimenti_ticket)} movimenti per il ticket {ticket.numero_ticket}', 'info')
    
    for movimento in movimenti_ticket:
        macchina = movimento.macchina
        if not macchina:
            continue
            
        try:
            # Debug: mostra stato attuale della macchina
            flash(f'Debug: Macchina {macchina.codice} - Stato attuale: {macchina.stato}, Movimento: {movimento.tipo_movimento}, Note: {movimento.note}', 'info')
            
            # Identifica se è una macchina sostitutiva dalle note
            is_macchina_sostitutiva = ('sostitutiv' in (movimento.note or '').lower() or 
                                     'prestito sostitutivo' in (movimento.note or '').lower())
            
            if macchina.is_in_riparazione and movimento.tipo_movimento == 'Riparazione':
                # Macchina che era in riparazione - RIPRISTINA STATO ORIGINALE COMPLETO
                stato_originale = movimento.stato_precedente
                cliente_originale_id = movimento.cliente_originale_id
                ubicazione_originale = movimento.ubicazione_originale
                data_assegnazione_originale = movimento.data_assegnazione_originale
                data_vendita_originale = movimento.data_vendita_originale
                prezzo_vendita_originale = movimento.prezzo_vendita_originale
                prossima_manutenzione_originale = movimento.prossima_manutenzione_originale
                
                # RIPRISTINA STATO COMPLETO ESATTAMENTE COME ERA (TUTTI I CAMPI)
                macchina.stato = stato_originale
                macchina.cliente_id = cliente_originale_id
                macchina.ubicazione = ubicazione_originale  # Ripristina esatto, anche se None
                macchina.data_assegnazione = data_assegnazione_originale
                macchina.data_vendita = data_vendita_originale
                macchina.prezzo_vendita = prezzo_vendita_originale
                macchina.prossima_manutenzione = prossima_manutenzione_originale
                
                # Registra il movimento di ripristino
                movimento_ripristino = MovimentoMacchina(
                    macchina_id=macchina.id,
                    tipo_movimento='Ripristino',
                    stato_precedente='In riparazione',
                    stato_nuovo=stato_originale,
                    cliente_id=cliente_originale_id,
                    note=f'Ripristino stato {stato_originale} dopo riparazione - chiusura ticket {ticket.numero_ticket}',
                    ticket_id=ticket.id,
                    user_id=current_user.id
                )
                db.session.add(movimento_ripristino)
                
                flash(f'Macchina {macchina.codice} ripristinata da In riparazione a {stato_originale}', 'success')
                
            elif macchina.is_in_prestito and movimento.tipo_movimento == 'Assegnazione' and is_macchina_sostitutiva:
                # Macchina sostitutiva - DEVE tornare disponibile (non ha stato originale da ripristinare)
                macchina.stato = 'Disponibile'
                macchina.cliente_id = None
                macchina.ubicazione = 'Magazzino'
                macchina.data_assegnazione = None
                
                # Registra il movimento di ripristino
                movimento_ripristino = MovimentoMacchina(
                    macchina_id=macchina.id,
                    tipo_movimento='Rientro',
                    stato_precedente='In prestito',
                    stato_nuovo='Disponibile',
                    note=f'Ripristino macchina sostitutiva a Disponibile - chiusura ticket {ticket.numero_ticket}',
                    ticket_id=ticket.id,
                    user_id=current_user.id
                )
                db.session.add(movimento_ripristino)
                
                flash(f'Macchina sostitutiva {macchina.codice} ripristinata da In prestito a Disponibile', 'success')
                
            elif macchina.is_in_prestito and movimento.tipo_movimento == 'Assegnazione' and not is_macchina_sostitutiva:
                # Prestito semplice - RIPRISTINA STATO ORIGINALE COMPLETO
                stato_originale = movimento.stato_precedente
                cliente_originale_id = movimento.cliente_originale_id
                ubicazione_originale = movimento.ubicazione_originale
                data_assegnazione_originale = movimento.data_assegnazione_originale
                data_vendita_originale = movimento.data_vendita_originale
                prezzo_vendita_originale = movimento.prezzo_vendita_originale
                prossima_manutenzione_originale = movimento.prossima_manutenzione_originale
                
                # RIPRISTINA STATO COMPLETO ESATTAMENTE COME ERA (TUTTI I CAMPI)
                macchina.stato = stato_originale
                macchina.cliente_id = cliente_originale_id
                macchina.ubicazione = ubicazione_originale  # Ripristina esatto, anche se None
                macchina.data_assegnazione = data_assegnazione_originale
                macchina.data_vendita = data_vendita_originale
                macchina.prezzo_vendita = prezzo_vendita_originale
                macchina.prossima_manutenzione = prossima_manutenzione_originale
                
                # Registra il movimento di ripristino
                movimento_ripristino = MovimentoMacchina(
                    macchina_id=macchina.id,
                    tipo_movimento='Ripristino',
                    stato_precedente='In prestito',
                    stato_nuovo=stato_originale,
                    cliente_id=cliente_originale_id,
                    note=f'Ripristino stato {stato_originale} dopo prestito semplice - chiusura ticket {ticket.numero_ticket}',
                    ticket_id=ticket.id,
                    user_id=current_user.id
                )
                db.session.add(movimento_ripristino)
                
                flash(f'Macchina {macchina.codice} ripristinata da In prestito a {stato_originale}', 'success')
                    
        except Exception as e:
            # Log dell'errore ma continua con le altre macchine
            flash(f'Errore nel ripristino della macchina {macchina.codice}: {str(e)}', 'danger')