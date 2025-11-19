from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models.cliente import Cliente
from app.models.ticket import Ticket
from app.models.macchina import Macchina
from app.forms.cliente import ClienteForm, ClienteFilterForm
from app.utils.permissions import PermissionManager

clients_bp = Blueprint('clients', __name__)


@clients_bp.route('/')
@login_required
def list_clients():
    """Lista di tutti i clienti con filtri"""
    form = ClienteFilterForm()
    
    # Query base - clienti condivisi tra tutti i reparti
    query = Cliente.query
    
    # Applica filtri da parametri URL
    search_term = request.args.get('search', '').strip()
    if search_term:
        form.search.data = search_term
        search_pattern = f"%{search_term}%"
        query = query.filter(or_(
            Cliente.ragione_sociale.like(search_pattern),
            Cliente.email.like(search_pattern),
            Cliente.citta.like(search_pattern)
        ))
    
    settore_filter = request.args.get('settore', '').strip()
    if settore_filter:
        form.settore.data = settore_filter
        query = query.filter(Cliente.settore.like(f"%{settore_filter}%"))
    
    provincia_filter = request.args.get('provincia', '').strip()
    if provincia_filter:
        form.provincia.data = provincia_filter
        query = query.filter(Cliente.provincia == provincia_filter)
    
    is_active_filter = request.args.get('is_active', '').strip()
    if is_active_filter:
        form.is_active.data = is_active_filter
        is_active = is_active_filter == 'True'
        query = query.filter(Cliente.is_active == is_active)
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Numero di clienti per pagina
    
    clienti = query.order_by(Cliente.ragione_sociale.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('clients/list.html', clienti=clienti, form=form)


@clients_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_client():
    """Crea nuovo cliente"""
    form = ClienteForm()
    
    if form.validate_on_submit():
        cliente = Cliente(
            ragione_sociale=form.ragione_sociale.data,
            email=form.email.data,
            department_id=1,  # Assegna sempre al reparto "Generale" per condivisione
            codice_fiscale=form.codice_fiscale.data.upper() if form.codice_fiscale.data else None,
            partita_iva=form.partita_iva.data if form.partita_iva.data else None,
            telefono=form.telefono.data,
            cellulare=form.cellulare.data,
            indirizzo=form.indirizzo.data,
            cap=form.cap.data,
            citta=form.citta.data,
            provincia=form.provincia.data if form.provincia.data else None,
            paese=form.paese.data or 'Italia',
            settore=form.settore.data,
            note=form.note.data,
            is_active=form.is_active.data
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        flash(f'Cliente "{cliente.ragione_sociale}" creato con successo!', 'success')
        return redirect(url_for('clients.view_client', id=cliente.id))
    
    return render_template('clients/form.html', form=form, title='Nuovo Cliente')


@clients_bp.route('/<int:id>')
@login_required
def view_client(id):
    """Visualizza dettagli cliente"""
    cliente = Cliente.query.get_or_404(id)
    
    # I clienti sono condivisi tra tutti i reparti - nessun controllo di accesso necessario
    
    # Statistiche sui ticket del cliente
    tickets_stats = {
        'totali': cliente.tickets.count(),
        'aperti': cliente.tickets.filter_by(stato='Aperto').count(),
        'in_lavorazione': cliente.tickets.filter_by(stato='In Lavorazione').count(),
        'risolti': cliente.tickets.filter_by(stato='Risolto').count(),
        'chiusi': cliente.tickets.filter_by(stato='Chiuso').count()
    }
    
    # Ultimi ticket del cliente
    ultimi_tickets = cliente.tickets.order_by(Ticket.created_at.desc()).limit(10).all()

    # Macchine assegnate al cliente
    macchine_assegnate = Macchina.query.filter_by(cliente_id=cliente.id).order_by(Macchina.codice).all()

    return render_template('clients/detail.html',
                         cliente=cliente,
                         tickets_stats=tickets_stats,
                         ultimi_tickets=ultimi_tickets,
                         macchine_assegnate=macchine_assegnate)


@clients_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    """Modifica cliente"""
    cliente = Cliente.query.get_or_404(id)
    form = ClienteForm(cliente=cliente, obj=cliente)
    
    if form.validate_on_submit():
        cliente.ragione_sociale = form.ragione_sociale.data
        cliente.email = form.email.data
        cliente.codice_fiscale = form.codice_fiscale.data.upper() if form.codice_fiscale.data else None
        cliente.partita_iva = form.partita_iva.data if form.partita_iva.data else None
        cliente.telefono = form.telefono.data
        cliente.cellulare = form.cellulare.data
        cliente.indirizzo = form.indirizzo.data
        cliente.cap = form.cap.data
        cliente.citta = form.citta.data
        cliente.provincia = form.provincia.data if form.provincia.data else None
        cliente.paese = form.paese.data or 'Italia'
        cliente.settore = form.settore.data
        cliente.note = form.note.data
        cliente.is_active = form.is_active.data
        
        db.session.commit()
        flash(f'Cliente "{cliente.ragione_sociale}" aggiornato con successo!', 'success')
        return redirect(url_for('clients.view_client', id=cliente.id))
    
    return render_template('clients/form.html', form=form, cliente=cliente, title='Modifica Cliente')


@clients_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_client(id):
    """Elimina cliente (solo se non ha ticket associati)"""
    if not current_user.is_admin:
        flash('Solo gli amministratori possono eliminare i clienti.', 'error')
        return redirect(url_for('clients.view_client', id=id))
    
    cliente = Cliente.query.get_or_404(id)
    
    # Verifica se ha ticket associati
    if cliente.tickets.count() > 0:
        flash(f'Impossibile eliminare il cliente "{cliente.ragione_sociale}" perché ha {cliente.tickets.count()} ticket associati.', 'error')
        return redirect(url_for('clients.view_client', id=id))
    
    ragione_sociale = cliente.ragione_sociale
    db.session.delete(cliente)
    db.session.commit()
    
    flash(f'Cliente "{ragione_sociale}" eliminato con successo.', 'success')
    return redirect(url_for('clients.list_clients'))


@clients_bp.route('/<int:id>/toggle_status', methods=['POST'])
@login_required
def toggle_status(id):
    """Attiva/disattiva cliente (AJAX)"""
    cliente = Cliente.query.get_or_404(id)
    cliente.is_active = not cliente.is_active
    db.session.commit()
    
    status_text = 'attivato' if cliente.is_active else 'disattivato'
    
    return jsonify({
        'success': True,
        'message': f'Cliente "{cliente.ragione_sociale}" {status_text}',
        'is_active': cliente.is_active
    })


@clients_bp.route('/<int:id>/tickets')
@login_required
def client_tickets(id):
    """Lista ticket di un cliente specifico"""
    cliente = Cliente.query.get_or_404(id)
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    tickets = cliente.tickets.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('clients/tickets.html', cliente=cliente, tickets=tickets)


@clients_bp.route('/export')
@login_required
def export_clients():
    """Esporta clienti in formato CSV"""
    import csv
    from flask import make_response
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Ragione Sociale', 'Codice Fiscale', 'Partita IVA', 'Email', 'Telefono',
        'Cellulare', 'Indirizzo', 'CAP', 'Città', 'Provincia', 'Paese',
        'Settore', 'Attivo', 'Ticket Totali', 'Ticket Aperti', 'Data Creazione'
    ])
    
    # Dati
    clienti = Cliente.query.order_by(Cliente.ragione_sociale.asc()).all()
    for cliente in clienti:
        writer.writerow([
            cliente.ragione_sociale,
            cliente.codice_fiscale or '',
            cliente.partita_iva or '',
            cliente.email,
            cliente.telefono or '',
            cliente.cellulare or '',
            cliente.indirizzo or '',
            cliente.cap or '',
            cliente.citta or '',
            cliente.provincia or '',
            cliente.paese or '',
            cliente.settore or '',
            'Sì' if cliente.is_active else 'No',
            cliente.ticket_count,
            cliente.ticket_aperti,
            cliente.created_at.strftime('%Y-%m-%d')
        ])
    
    # Crea response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=clienti.csv'
    
    return response


@clients_bp.route('/stats')
@login_required
def clients_stats():
    """Statistiche sui clienti"""
    from sqlalchemy import func
    
    # Statistiche generali
    total_clienti = Cliente.query.count()
    clienti_attivi = Cliente.query.filter_by(is_active=True).count()
    clienti_inattivi = Cliente.query.filter_by(is_active=False).count()
    
    # Clienti per provincia
    clienti_per_provincia = db.session.query(
        Cliente.provincia,
        func.count(Cliente.id).label('count')
    ).filter(Cliente.provincia.isnot(None)).group_by(Cliente.provincia).order_by(
        func.count(Cliente.id).desc()
    ).limit(10).all()
    
    # Clienti per settore
    clienti_per_settore = db.session.query(
        Cliente.settore,
        func.count(Cliente.id).label('count')
    ).filter(Cliente.settore.isnot(None)).group_by(Cliente.settore).order_by(
        func.count(Cliente.id).desc()
    ).limit(10).all()
    
    # Top clienti per numero di ticket
    top_clienti = db.session.query(
        Cliente.ragione_sociale,
        func.count(Ticket.id).label('ticket_count')
    ).join(Ticket).group_by(Cliente.id, Cliente.ragione_sociale).order_by(
        func.count(Ticket.id).desc()
    ).limit(10).all()
    
    return render_template('clients/stats.html',
                         total_clienti=total_clienti,
                         clienti_attivi=clienti_attivi,
                         clienti_inattivi=clienti_inattivi,
                         clienti_per_provincia=clienti_per_provincia,
                         clienti_per_settore=clienti_per_settore,
                         top_clienti=top_clienti)