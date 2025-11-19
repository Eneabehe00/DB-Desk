from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from sqlalchemy import func, extract, desc, and_, or_
from app import db
from app.models.ticket import Ticket
from app.models.cliente import Cliente
from app.models.user import User
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
@login_required
def index():
    """Pagina principale dei report"""
    return render_template('reports/index.html')


@reports_bp.route('/tickets')
@login_required
def tickets_report():
    """Report completo sui ticket"""
    
    # Parametri per filtro data
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Statistiche generali
    total_tickets = Ticket.query.count()
    tickets_periodo = Ticket.query.filter(Ticket.created_at >= start_date).count()
    
    # Ticket per stato
    tickets_per_stato = db.session.query(
        Ticket.stato,
        func.count(Ticket.id).label('count')
    ).group_by(Ticket.stato).all()
    
    # Ticket per priorità
    tickets_per_priorita = db.session.query(
        Ticket.priorita,
        func.count(Ticket.id).label('count')
    ).group_by(Ticket.priorita).all()
    
    # Ticket per categoria
    tickets_per_categoria = db.session.query(
        Ticket.categoria,
        func.count(Ticket.id).label('count')
    ).group_by(Ticket.categoria).order_by(desc('count')).all()
    
    # Trend giornalieri (ultimi 30 giorni)
    trend_data = []
    for i in range(30):
        date = datetime.utcnow().date() - timedelta(days=i)
        count = Ticket.query.filter(
            func.date(Ticket.created_at) == date
        ).count()
        trend_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    trend_data.reverse()
    
    # Top utenti per ticket creati
    top_creators = db.session.query(
        User.first_name,
        User.last_name,
        func.count(Ticket.id).label('count')
    ).join(Ticket, User.id == Ticket.created_by_id).group_by(
        User.id, User.first_name, User.last_name
    ).order_by(desc('count')).limit(10).all()
    
    # Top utenti per ticket assegnati
    top_assigned = db.session.query(
        User.first_name,
        User.last_name,
        func.count(Ticket.id).label('count')
    ).join(Ticket, User.id == Ticket.assigned_to_id).group_by(
        User.id, User.first_name, User.last_name
    ).order_by(desc('count')).limit(10).all()
    
    # Tempo medio di risoluzione
    tickets_risolti = Ticket.query.filter(
        Ticket.resolved_at.isnot(None),
        Ticket.created_at >= start_date
    ).all()
    
    tempi_risoluzione = []
    for ticket in tickets_risolti:
        delta = ticket.resolved_at - ticket.created_at
        tempi_risoluzione.append(delta.total_seconds() / 3600)  # In ore
    
    tempo_medio = sum(tempi_risoluzione) / len(tempi_risoluzione) if tempi_risoluzione else 0
    
    # Ticket scaduti
    tickets_scaduti = Ticket.query.filter(
        Ticket.due_date < datetime.utcnow(),
        Ticket.stato.in_(['Aperto', 'In Lavorazione', 'In Attesa Cliente'])
    ).all()
    
    return render_template('reports/tickets.html',
                         total_tickets=total_tickets,
                         tickets_periodo=tickets_periodo,
                         tickets_per_stato=tickets_per_stato,
                         tickets_per_priorita=tickets_per_priorita,
                         tickets_per_categoria=tickets_per_categoria,
                         trend_data=trend_data,
                         top_creators=top_creators,
                         top_assigned=top_assigned,
                         tempo_medio=tempo_medio,
                         tickets_scaduti=tickets_scaduti,
                         days=days)


@reports_bp.route('/clients')
@login_required
def clients_report():
    """Report sui clienti"""
    
    # Statistiche generali
    total_clienti = Cliente.query.count()
    clienti_attivi = Cliente.query.filter_by(is_active=True).count()
    
    # Clienti per numero di ticket
    clienti_stats = db.session.query(
        Cliente.ragione_sociale,
        Cliente.id,
        func.count(Ticket.id).label('ticket_count')
    ).outerjoin(Ticket).group_by(Cliente.id, Cliente.ragione_sociale).order_by(
        desc('ticket_count')
    ).limit(20).all()
    
    # Aggiungi conteggi separati per ogni cliente
    clienti_stats_enhanced = []
    for cliente in clienti_stats:
        tickets_aperti = Ticket.query.filter_by(cliente_id=cliente.id, stato='Aperto').count()
        tickets_risolti = Ticket.query.filter_by(cliente_id=cliente.id, stato='Risolto').count()
        
        # Crea un oggetto simile al risultato della query originale
        cliente_enhanced = type('ClienteStats', (), {
            'ragione_sociale': cliente.ragione_sociale,
            'id': cliente.id,
            'ticket_count': cliente.ticket_count,
            'tickets_aperti': tickets_aperti,
            'tickets_risolti': tickets_risolti
        })()
        
        clienti_stats_enhanced.append(cliente_enhanced)
    
    clienti_stats = clienti_stats_enhanced
    
    # Clienti per provincia
    clienti_per_provincia = db.session.query(
        Cliente.provincia,
        func.count(Cliente.id).label('count')
    ).filter(Cliente.provincia.isnot(None)).group_by(Cliente.provincia).order_by(
        desc('count')
    ).all()
    
    # Clienti per settore
    clienti_per_settore = db.session.query(
        Cliente.settore,
        func.count(Cliente.id).label('count')
    ).filter(Cliente.settore.isnot(None)).group_by(Cliente.settore).order_by(
        desc('count')
    ).all()
    
    # Nuovi clienti per mese (ultimi 12 mesi)
    nuovi_clienti_per_mese = db.session.query(
        extract('year', Cliente.created_at).label('year'),
        extract('month', Cliente.created_at).label('month'),
        func.count(Cliente.id).label('count')
    ).filter(
        Cliente.created_at >= datetime.utcnow() - timedelta(days=365)
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    return render_template('reports/clients.html',
                         total_clienti=total_clienti,
                         clienti_attivi=clienti_attivi,
                         clienti_stats=clienti_stats,
                         clienti_per_provincia=clienti_per_provincia,
                         clienti_per_settore=clienti_per_settore,
                         nuovi_clienti_per_mese=nuovi_clienti_per_mese)


@reports_bp.route('/performance')
@login_required
def performance_report():
    """Report sulle performance degli utenti"""
    
    # Parametri per filtro data
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Performance per utente - approccio semplificato
    users = User.query.filter_by(is_active=True).all()
    user_performance = []
    
    for user in users:
        created_count = Ticket.query.filter(
            Ticket.created_by_id == user.id,
            Ticket.created_at >= start_date
        ).count()
        assigned_count = Ticket.query.filter(
            Ticket.assigned_to_id == user.id,
            Ticket.created_at >= start_date
        ).count()
        resolved_count = Ticket.query.filter(
            Ticket.assigned_to_id == user.id,
            Ticket.stato == 'Risolto',
            Ticket.created_at >= start_date
        ).count()
        
        # Crea un oggetto simile al risultato della query originale
        user_perf = type('UserPerformance', (), {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'id': user.id,
            'created_count': created_count,
            'assigned_count': assigned_count,
            'resolved_count': resolved_count
        })()
        
        user_performance.append(user_perf)
    
    # Tempo medio di risoluzione per utente
    tempo_risoluzione_utenti = []
    for user in User.query.filter_by(is_active=True).all():
        tickets_risolti = Ticket.query.filter(
            Ticket.assigned_to_id == user.id,
            Ticket.resolved_at.isnot(None),
            Ticket.created_at >= start_date
        ).all()
        
        if tickets_risolti:
            tempi = [(t.resolved_at - t.created_at).total_seconds() / 3600 for t in tickets_risolti]
            tempo_medio = sum(tempi) / len(tempi)
        else:
            tempo_medio = 0
        
        tempo_risoluzione_utenti.append({
            'user': user,
            'tickets_count': len(tickets_risolti),
            'tempo_medio': tempo_medio
        })
    
    # Ordina per tempo medio (escludendo chi non ha risolto ticket)
    tempo_risoluzione_utenti = sorted(
        [u for u in tempo_risoluzione_utenti if u['tickets_count'] > 0],
        key=lambda x: x['tempo_medio']
    )
    
    return render_template('reports/performance.html',
                         user_performance=user_performance,
                         tempo_risoluzione_utenti=tempo_risoluzione_utenti,
                         days=days)


@reports_bp.route('/api/chart_data')
@login_required
def chart_data():
    """API per dati dei grafici (AJAX)"""
    chart_type = request.args.get('type')
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    if chart_type == 'tickets_trend':
        # Trend giornaliero ticket
        data = []
        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            count = Ticket.query.filter(
                func.date(Ticket.created_at) == date
            ).count()
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': count
            })
        data.reverse()
        return jsonify(data)
    
    elif chart_type == 'priority_distribution':
        # Distribuzione per priorità
        data = db.session.query(
            Ticket.priorita,
            func.count(Ticket.id).label('count')
        ).group_by(Ticket.priorita).all()
        
        return jsonify([{'label': d[0], 'value': d[1]} for d in data])
    
    elif chart_type == 'status_distribution':
        # Distribuzione per stato
        data = db.session.query(
            Ticket.stato,
            func.count(Ticket.id).label('count')
        ).group_by(Ticket.stato).all()
        
        return jsonify([{'label': d[0], 'value': d[1]} for d in data])
    
    elif chart_type == 'top_clients':
        # Top clienti per ticket
        data = db.session.query(
            Cliente.ragione_sociale,
            func.count(Ticket.id).label('count')
        ).join(Ticket).group_by(Cliente.id, Cliente.ragione_sociale).order_by(
            desc('count')
        ).limit(10).all()
        
        return jsonify([{'label': d[0], 'value': d[1]} for d in data])
    
    return jsonify({'error': 'Tipo di grafico non valido'}), 400


@reports_bp.route('/export/<report_type>')
@login_required
def export_report(report_type):
    """Esporta report in formato CSV"""
    import csv
    from flask import make_response
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    if report_type == 'tickets_summary':
        # Header
        writer.writerow([
            'Numero Ticket', 'Titolo', 'Cliente', 'Stato', 'Priorità', 'Categoria',
            'Creato da', 'Assegnato a', 'Data Creazione', 'Data Risoluzione',
            'Giorni Apertura', 'Tempo Stimato (ore)', 'Tempo Impiegato (ore)'
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
                ticket.resolved_at.strftime('%Y-%m-%d %H:%M') if ticket.resolved_at else '',
                ticket.giorni_apertura,
                round(ticket.tempo_stimato / 60, 2) if ticket.tempo_stimato else '',
                round(ticket.tempo_impiegato / 60, 2) if ticket.tempo_impiegato else ''
            ])
        
        filename = 'tickets_summary.csv'
    
    elif report_type == 'clients_summary':
        # Header
        writer.writerow([
            'Ragione Sociale', 'Email', 'Telefono', 'Città', 'Provincia',
            'Settore', 'Ticket Totali', 'Ticket Aperti', 'Ticket Risolti', 'Data Registrazione'
        ])
        
        # Dati
        clienti = Cliente.query.order_by(Cliente.ragione_sociale.asc()).all()
        for cliente in clienti:
            writer.writerow([
                cliente.ragione_sociale,
                cliente.email,
                cliente.telefono or '',
                cliente.citta or '',
                cliente.provincia or '',
                cliente.settore or '',
                cliente.ticket_count,
                cliente.ticket_aperti,
                cliente.tickets.filter_by(stato='Risolto').count(),
                cliente.created_at.strftime('%Y-%m-%d')
            ])
        
        filename = 'clients_summary.csv'
    
    else:
        return jsonify({'error': 'Tipo di report non valido'}), 400
    
    # Crea response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response