from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app import db
from app.models.ticket import Ticket
from app.models.cliente import Cliente
from app.models.user import User
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Pagina home - redirect a dashboard se loggato, altrimenti al login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principale con statistiche e widget"""
    
    # Statistiche generali
    total_tickets = Ticket.query.count()
    total_clienti = Cliente.query.filter_by(is_active=True).count()
    
    # Ticket per stato
    tickets_aperti = Ticket.query.filter_by(stato='Aperto').count()
    tickets_in_lavorazione = Ticket.query.filter_by(stato='In Lavorazione').count()
    tickets_risolti = Ticket.query.filter_by(stato='Risolto').count()
    tickets_chiusi = Ticket.query.filter_by(stato='Chiuso').count()
    
    # Ticket per priorità (solo stati attivi)
    tickets_critici = Ticket.query.filter_by(priorita='Critica').filter(
        Ticket.stato.in_(Ticket.get_stati_aperti())
    ).count()
    
    tickets_alta_priorita = Ticket.query.filter_by(priorita='Alta').filter(
        Ticket.stato.in_(Ticket.get_stati_aperti())
    ).count()
    
    # Ticket scaduti (solo stati attivi)
    now = datetime.utcnow()
    tickets_scaduti = Ticket.query.filter(
        Ticket.due_date < now,
        Ticket.stato.in_(Ticket.get_stati_aperti())
    ).count()
    
    # Ultimi ticket creati
    ultimi_tickets = Ticket.query.order_by(desc(Ticket.created_at)).limit(5).all()
    
    # Ticket assegnati all'utente corrente (solo stati attivi)
    miei_tickets = Ticket.query.filter_by(assigned_to_id=current_user.id).filter(
        Ticket.stato.in_(Ticket.get_stati_aperti())
    ).order_by(desc(Ticket.created_at)).limit(5).all()
    
    # Statistiche per l'ultimo mese
    ultimo_mese = datetime.utcnow() - timedelta(days=30)
    tickets_ultimo_mese = Ticket.query.filter(Ticket.created_at >= ultimo_mese).count()
    
    # Top 5 clienti per numero di ticket
    top_clienti = db.session.query(
        Cliente.ragione_sociale,
        func.count(Ticket.id).label('ticket_count')
    ).join(Ticket).group_by(Cliente.id, Cliente.ragione_sociale).order_by(
        desc('ticket_count')
    ).limit(5).all()
    
    # Ticket per categoria (ultimi 30 giorni)
    tickets_per_categoria = db.session.query(
        Ticket.categoria,
        func.count(Ticket.id).label('count')
    ).filter(Ticket.created_at >= ultimo_mese).group_by(Ticket.categoria).all()
    
    # Calcola macro-stati per il grafico principale
    tickets_tutti_aperti = Ticket.query.filter(Ticket.stato.in_(Ticket.get_stati_aperti())).count()
    tickets_tutti_chiusi = Ticket.query.filter(Ticket.stato.in_(Ticket.get_stati_chiusi())).count()
    
    # Prepara i dati per i grafici
    chart_data = {
        'stati': {
            'labels': ['Aperti (Tutti)', 'Chiusi'],
            'data': [tickets_tutti_aperti, tickets_tutti_chiusi]
        },
        'stati_dettagliati': {
            'labels': ['Solo Aperti', 'In Lavorazione', 'In Attesa', 'Risolti', 'Chiusi'],
            'data': [tickets_aperti, tickets_in_lavorazione, 
                    Ticket.query.filter_by(stato='In Attesa Cliente').count(),
                    tickets_risolti, tickets_chiusi]
        },
        'categorie': {
            'labels': [cat[0] for cat in tickets_per_categoria],
            'data': [cat[1] for cat in tickets_per_categoria]
        },
        'top_clienti': {
            'labels': [cliente[0] for cliente in top_clienti],
            'data': [cliente[1] for cliente in top_clienti]
        }
    }
    
    return render_template('main/dashboard.html',
                         total_tickets=total_tickets,
                         total_clienti=total_clienti,
                         tickets_aperti=tickets_aperti,
                         tickets_in_lavorazione=tickets_in_lavorazione,
                         tickets_risolti=tickets_risolti,
                         tickets_chiusi=tickets_chiusi,
                         tickets_critici=tickets_critici,
                         tickets_alta_priorita=tickets_alta_priorita,
                         tickets_scaduti=tickets_scaduti,
                         tickets_ultimo_mese=tickets_ultimo_mese,
                         ultimi_tickets=ultimi_tickets,
                         miei_tickets=miei_tickets,
                         top_clienti=top_clienti,
                         chart_data=chart_data)


@main_bp.route('/quick_stats')
@login_required
def quick_stats():
    """Endpoint per statistiche rapide (AJAX)"""
    from flask import jsonify
    
    stats = {
        'tickets_aperti': Ticket.query.filter(Ticket.stato.in_(Ticket.get_stati_aperti())).count(),
        'tickets_critici': Ticket.query.filter_by(priorita='Critica').filter(
            Ticket.stato.in_(Ticket.get_stati_aperti())
        ).count(),
        'tickets_scaduti': Ticket.query.filter(
            Ticket.due_date < datetime.utcnow(),
            Ticket.stato.in_(Ticket.get_stati_aperti())
        ).count(),
        'miei_tickets': Ticket.query.filter_by(assigned_to_id=current_user.id).filter(
            Ticket.stato.in_(Ticket.get_stati_aperti())
        ).count()
    }
    
    return jsonify(stats)