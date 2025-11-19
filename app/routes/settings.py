from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.role import Role
from app.models.department import Department
from app.models.ticket import Ticket
from app.models.cliente import Cliente
from app.forms.auth import ChangePasswordForm
from app.models.email_import import EmailImportLog
from app.models.email_draft import EmailDraft
from app.utils.permissions import require_permission, require_admin
import os

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/')
@login_required
def index():
    """Pagina principale delle impostazioni"""
    return render_template('settings/index.html')


@settings_bp.route('/users')
@login_required
@require_permission('can_manage_users')
def users():
    """Gestione utenti"""
    utenti = User.query.order_by(User.created_at.desc()).all()
    roles = Role.query.filter_by(is_active=True).order_by(Role.display_name).all()
    departments = Department.query.filter_by(is_active=True).order_by(Department.display_name).all()
    
    return render_template('settings/users.html', 
                         utenti=utenti, 
                         roles=roles, 
                         departments=departments)


@settings_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@require_permission('can_manage_users')
def toggle_user_status(user_id):
    """Attiva/disattiva utente"""
    
    user = User.query.get_or_404(user_id)
    
    # Non permettere di disattivare se stesso
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Non puoi disattivare il tuo account'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status_text = 'attivato' if user.is_active else 'disattivato'
    
    return jsonify({
        'success': True,
        'message': f'Utente "{user.full_name}" {status_text}',
        'is_active': user.is_active
    })


@settings_bp.route('/users/<int:user_id>/update_role', methods=['POST'])
@login_required
@require_permission('can_manage_users')
def update_user_role(user_id):
    """Aggiorna il ruolo di un utente"""
    user = User.query.get_or_404(user_id)
    role_id = request.json.get('role_id')
    
    if not role_id:
        return jsonify({'success': False, 'message': 'ID ruolo mancante'}), 400
    
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'success': False, 'message': 'Ruolo non trovato'}), 404
    
    # Non permettere di modificare il proprio ruolo se non si è developer
    if user.id == current_user.id and not current_user.has_permission('can_manage_system'):
        return jsonify({'success': False, 'message': 'Non puoi modificare il tuo ruolo'}), 403
    
    old_role = user.role.display_name if user.role else 'Nessun ruolo'
    user.role_id = role_id
    user.sync_admin_role()  # Sincronizza is_admin
    
    try:
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Ruolo aggiornato da "{old_role}" a "{role.display_name}"',
            'new_role': role.display_name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'}), 500


@settings_bp.route('/users/<int:user_id>/update_department', methods=['POST'])
@login_required
@require_permission('can_manage_users')
def update_user_department(user_id):
    """Aggiorna il reparto di un utente"""
    user = User.query.get_or_404(user_id)
    department_id = request.json.get('department_id')
    
    if not department_id:
        return jsonify({'success': False, 'message': 'ID reparto mancante'}), 400
    
    department = Department.query.get(department_id)
    if not department:
        return jsonify({'success': False, 'message': 'Reparto non trovato'}), 404
    
    old_department = user.department.display_name if user.department else 'Nessun reparto'
    user.department_id = department_id
    
    try:
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Reparto aggiornato da "{old_department}" a "{department.display_name}"',
            'new_department': department.display_name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'}), 500


# ===== GESTIONE REPARTI =====

@settings_bp.route('/departments')
@login_required
@require_permission('can_manage_departments')
def departments():
    """Lista di tutti i reparti"""
    departments = Department.query.order_by(Department.display_name).all()
    
    return render_template('settings/departments.html', departments=departments)


@settings_bp.route('/departments/new', methods=['GET', 'POST'])
@login_required
@require_admin()
def new_department():
    """Crea nuovo reparto"""
    from app.forms.department import DepartmentForm
    form = DepartmentForm()
    
    # Popola la lista dei manager possibili
    form.manager_id.choices = [(0, 'Nessun manager')] + [
        (u.id, u.full_name) for u in User.query.filter_by(is_active=True).order_by(User.first_name, User.last_name).all()
    ]
    
    if form.validate_on_submit():
        department = Department(
            name=form.name.data,
            display_name=form.display_name.data,
            description=form.description.data,
            color=form.color.data,
            manager_id=form.manager_id.data if form.manager_id.data != 0 else None
        )
        
        try:
            db.session.add(department)
            db.session.flush()  # Per ottenere l'ID
            
            # Associa i tipi di macchina selezionati
            from app.models.macchina import TipoMacchina
            selected_tipi = TipoMacchina.query.filter(TipoMacchina.id.in_(form.tipi_macchine.data)).all()
            for tipo in selected_tipi:
                department.tipi_macchine.append(tipo)
            
            db.session.commit()
            flash(f'Reparto "{department.display_name}" creato con successo!', 'success')
            return redirect(url_for('settings.departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione del reparto: {str(e)}', 'error')
    
    return render_template('settings/department_form.html', form=form, title='Nuovo Reparto')


@settings_bp.route('/departments/<int:id>')
@login_required
@require_permission('can_manage_departments')
def view_department(id):
    """Visualizza dettagli reparto"""
    department = Department.query.get_or_404(id)
    
    # Utenti del reparto
    users = department.users.filter_by(is_active=True).order_by(User.first_name, User.last_name).all()
    
    # Tipi di macchina associati al reparto
    tipi_macchine = department.tipi_macchine.all()
    
    # Statistiche dettagliate
    stats = {
        'total_users': len(users),
        'active_tickets': department.tickets.filter_by(stato='Aperto').count() if hasattr(department, 'tickets') else 0,
        'total_tickets': department.tickets.count() if hasattr(department, 'tickets') else 0,
        'active_clients': 0,  # I clienti sono condivisi tra tutti i reparti
        'total_inventory': department.ricambi.count() if hasattr(department, 'ricambi') else 0,
        'total_tipi_macchine': len(tipi_macchine)
    }
    
    return render_template('settings/department_detail.html', 
                         department=department, 
                         users=users, 
                         tipi_macchine=tipi_macchine,
                         stats=stats)


@settings_bp.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_admin()
def edit_department(id):
    """Modifica reparto"""
    department = Department.query.get_or_404(id)
    from app.forms.department import DepartmentForm
    form = DepartmentForm(obj=department, department=department)
    
    # Popola la lista dei manager possibili
    form.manager_id.choices = [(0, 'Nessun manager')] + [
        (u.id, u.full_name) for u in User.query.filter_by(is_active=True).order_by(User.first_name, User.last_name).all()
    ]
    
    # Pre-seleziona il manager corrente
    if request.method == 'GET':
        form.manager_id.data = department.manager_id if department.manager_id else 0
    
    if form.validate_on_submit():
        department.name = form.name.data
        department.display_name = form.display_name.data
        department.description = form.description.data
        department.color = form.color.data
        department.manager_id = form.manager_id.data if form.manager_id.data != 0 else None
        
        # Aggiorna le associazioni con i tipi di macchina
        from app.models.macchina import TipoMacchina
        selected_tipi = TipoMacchina.query.filter(TipoMacchina.id.in_(form.tipi_macchine.data)).all()
        department.tipi_macchine.clear()
        for tipo in selected_tipi:
            department.tipi_macchine.append(tipo)
        
        try:
            db.session.commit()
            flash(f'Reparto "{department.display_name}" aggiornato con successo!', 'success')
            return redirect(url_for('settings.view_department', id=department.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento del reparto: {str(e)}', 'error')
    
    return render_template('settings/department_form.html', 
                         form=form, 
                         title=f'Modifica Reparto: {department.display_name}',
                         department=department)


@settings_bp.route('/departments/<int:id>/delete', methods=['POST'])
@login_required
@require_admin()
def delete_department(id):
    """Elimina reparto"""
    department = Department.query.get_or_404(id)
    
    # Verifica che non sia l'ultimo reparto attivo
    active_departments = Department.query.filter_by(is_active=True).count()
    if active_departments <= 1:
        flash('Non è possibile eliminare l\'ultimo reparto attivo.', 'error')
        return redirect(url_for('settings.view_department', id=id))
    
    # Verifica che non ci siano utenti attivi nel reparto
    active_users = department.users.filter_by(is_active=True).count()
    if active_users > 0:
        flash(f'Non è possibile eliminare il reparto. Ci sono ancora {active_users} utenti attivi.', 'error')
        return redirect(url_for('settings.view_department', id=id))
    
    # Verifica che non ci siano dati associati
    total_tickets = department.tickets.count() if hasattr(department, 'tickets') else 0
    total_clients = department.clients.count() if hasattr(department, 'clients') else 0
    total_inventory = department.ricambi.count() if hasattr(department, 'ricambi') else 0
    
    if total_tickets > 0 or total_clients > 0 or total_inventory > 0:
        flash(f'Non è possibile eliminare il reparto. Ci sono ancora dati associati (Ticket: {total_tickets}, Clienti: {total_clients}, Magazzino: {total_inventory}).', 'error')
        return redirect(url_for('settings.view_department', id=id))
    
    department_name = department.display_name
    
    try:
        db.session.delete(department)
        db.session.commit()
        flash(f'Reparto "{department_name}" eliminato con successo.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('settings.departments'))


@settings_bp.route('/departments/<int:id>/toggle_status', methods=['POST'])
@login_required
@require_admin()
def toggle_department_status(id):
    """Attiva/disattiva reparto"""
    department = Department.query.get_or_404(id)
    
    if department.is_active:
        # Disattivazione
        active_departments = Department.query.filter_by(is_active=True).count()
        if active_departments <= 1:
            return jsonify({'success': False, 'message': 'Non è possibile disattivare l\'ultimo reparto attivo.'}), 400
        
        active_users = department.users.filter_by(is_active=True).count()
        if active_users > 0:
            return jsonify({'success': False, 'message': f'Non è possibile disattivare il reparto. Ci sono ancora {active_users} utenti attivi.'}), 400
    
    department.is_active = not department.is_active
    
    try:
        db.session.commit()
        status_text = 'attivato' if department.is_active else 'disattivato'
        return jsonify({
            'success': True,
            'message': f'Reparto "{department.display_name}" {status_text}',
            'is_active': department.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Errore: {str(e)}'}), 500


# ===== DETTAGLIO UTENTE =====

@settings_bp.route('/users/<int:user_id>')
@login_required
@require_permission('can_manage_users')
def view_user(user_id):
    """Visualizza dettagli utente"""
    user = User.query.get_or_404(user_id)
    
    # Statistiche utente
    stats = {
        'total_tickets_created': user.created_tickets.count(),
        'total_tickets_assigned': user.assigned_tickets.count(),
        'open_tickets_created': user.created_tickets.filter_by(stato='Aperto').count(),
        'open_tickets_assigned': user.assigned_tickets.filter_by(stato='Aperto').count(),
    }
    
    # Ticket recenti creati
    recent_created_tickets = user.created_tickets.order_by(Ticket.created_at.desc()).limit(5).all()
    
    # Ticket recenti assegnati
    recent_assigned_tickets = user.assigned_tickets.order_by(Ticket.updated_at.desc()).limit(5).all()
    
    return render_template('settings/user_detail.html', 
                         user=user, 
                         stats=stats,
                         recent_created_tickets=recent_created_tickets,
                         recent_assigned_tickets=recent_assigned_tickets)


@settings_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('can_manage_users')
def edit_user(user_id):
    """Modifica utente"""
    user = User.query.get_or_404(user_id)
    
    from app.forms.user import UserEditForm
    form = UserEditForm(obj=user)
    
    # Popola le scelte per ruoli e reparti
    form.role_id.choices = [(0, 'Seleziona ruolo')] + [
        (r.id, r.display_name) for r in Role.query.filter_by(is_active=True).order_by(Role.display_name).all()
    ]
    
    form.department_id.choices = [(0, 'Seleziona reparto')] + [
        (d.id, d.display_name) for d in Department.query.filter_by(is_active=True).order_by(Department.display_name).all()
    ]
    
    # Pre-popola i valori attuali
    if request.method == 'GET':
        form.role_id.data = user.role_id if user.role_id else 0
        form.department_id.data = user.department_id if user.department_id else 0
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_active = form.is_active.data
        user.role_id = form.role_id.data if form.role_id.data != 0 else None
        user.department_id = form.department_id.data if form.department_id.data != 0 else None
        
        # Aggiorna password se fornita
        if form.password.data:
            user.set_password(form.password.data)
        
        # Sincronizza is_admin con il ruolo
        user.sync_admin_role()
        
        try:
            db.session.commit()
            flash(f'Utente "{user.full_name}" aggiornato con successo!', 'success')
            return redirect(url_for('settings.view_user', user_id=user.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return render_template('settings/user_form.html', 
                         form=form, 
                         user=user,
                         title=f'Modifica Utente: {user.full_name}')


@settings_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@require_permission('can_manage_users')
def new_user():
    """Crea nuovo utente"""
    from app.forms.user import UserCreateForm
    form = UserCreateForm()
    
    # Popola le scelte per ruoli e reparti
    form.role_id.choices = [(0, 'Seleziona ruolo')] + [
        (r.id, r.display_name) for r in Role.query.filter_by(is_active=True).order_by(Role.display_name).all()
    ]
    
    form.department_id.choices = [(0, 'Seleziona reparto')] + [
        (d.id, d.display_name) for d in Department.query.filter_by(is_active=True).order_by(Department.display_name).all()
    ]
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_active=form.is_active.data,
            role_id=form.role_id.data if form.role_id.data != 0 else None,
            department_id=form.department_id.data if form.department_id.data != 0 else None
        )
        
        # Sincronizza is_admin con il ruolo
        user.sync_admin_role()
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'Utente "{user.full_name}" creato con successo!', 'success')
            return redirect(url_for('settings.view_user', user_id=user.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione: {str(e)}', 'error')
    
    return render_template('settings/user_form.html', 
                         form=form, 
                         title='Nuovo Utente')


@settings_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@require_permission('can_manage_users')
def delete_user(user_id):
    """Elimina utente"""
    user = User.query.get_or_404(user_id)
    
    # Non permettere di eliminare se stesso
    if user.id == current_user.id:
        flash('Non puoi eliminare il tuo account.', 'error')
        return redirect(url_for('settings.view_user', user_id=user_id))
    
    # Verifica se può essere eliminato
    if not user.can_be_deleted():
        flash('Non è possibile eliminare questo utente. Potrebbe essere l\'ultimo amministratore attivo o avere dati associati.', 'error')
        return redirect(url_for('settings.view_user', user_id=user_id))
    
    user_name = user.full_name
    
    try:
        # Riassegna i ticket se necessario
        if user.created_tickets.count() > 0 or user.assigned_tickets.count() > 0:
            admin_user, created_count, assigned_count = user.reassign_tickets_to_admin()
            flash(f'Riassegnati {created_count} ticket creati e {assigned_count} ticket assegnati a {admin_user.full_name}.', 'info')
        
        db.session.delete(user)
        db.session.commit()
        flash(f'Utente "{user_name}" eliminato con successo.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
        return redirect(url_for('settings.view_user', user_id=user_id))
    
    return redirect(url_for('settings.users'))


@settings_bp.route('/users/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
def toggle_admin_status(user_id):
    """Promuovi/declassa admin (solo admin)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Non permettere di rimuovere admin da se stesso se è l'unico admin
    if user.id == current_user.id and user.is_admin:
        admin_count = User.query.filter_by(is_admin=True, is_active=True).count()
        if admin_count <= 1:
            return jsonify({
                'success': False, 
                'message': 'Non puoi rimuovere i privilegi admin da te stesso se sei l\'unico amministratore'
            }), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status_text = 'promosso ad amministratore' if user.is_admin else 'declassato da amministratore'
    
    return jsonify({
        'success': True,
        'message': f'Utente "{user.full_name}" {status_text}',
        'is_admin': user.is_admin
    })


@settings_bp.route('/database')
@login_required
def database():
    """Informazioni e gestione database (solo admin)"""
    if not current_user.is_admin:
        flash('Non hai i permessi per accedere a questa sezione.', 'error')
        return redirect(url_for('settings.index'))
    
    # Statistiche database
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'admin_users': User.query.filter_by(is_admin=True).count(),
        'total_clients': Cliente.query.count(),
        'active_clients': Cliente.query.filter_by(is_active=True).count(),
        'total_tickets': Ticket.query.count(),
        'open_tickets': Ticket.query.filter_by(stato='Aperto').count(),
        'closed_tickets': Ticket.query.filter_by(stato='Chiuso').count()
    }
    
    # Informazioni database
    from config import Config
    db_info = {
        'host': Config.DB_HOST,
        'database': Config.DB_NAME,
        'port': Config.DB_PORT
    }
    
    return render_template('settings/database.html', stats=stats, db_info=db_info)


@settings_bp.route('/backup_db', methods=['POST'])
@login_required
def backup_database():
    """Backup del database (solo admin)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403
    
    try:
        from datetime import datetime
        import subprocess
        from config import Config
        
        # Nome file backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"dbdesk_backup_{timestamp}.sql"
        backup_path = os.path.join('backups', backup_filename)
        
        # Crea directory backup se non esiste
        os.makedirs('backups', exist_ok=True)
        
        # Comando mysqldump
        cmd = [
            'mysqldump',
            '-h', Config.DB_HOST,
            '-P', str(Config.DB_PORT),
            '-u', Config.DB_USER,
            f'-p{Config.DB_PASSWORD}' if Config.DB_PASSWORD else '',
            Config.DB_NAME
        ]
        
        # Rimuovi parametro password vuoto
        if not Config.DB_PASSWORD:
            cmd.remove('')
        
        with open(backup_path, 'w') as backup_file:
            result = subprocess.run(cmd, stdout=backup_file, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'Backup creato con successo: {backup_filename}',
                'filename': backup_filename
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Errore durante il backup: {result.stderr}'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Errore durante il backup: {str(e)}'
        }), 500


@settings_bp.route('/system')
@login_required
def system():
    """Informazioni di sistema"""
    import platform
    import psutil
    from flask import __version__ as flask_version
    
    # Informazioni sistema
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'flask_version': flask_version,
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
    }
    
    # Informazioni applicazione
    app_info = {
        'debug_mode': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
        'config_name': os.environ.get('FLASK_CONFIG', 'default'),
        'host': os.environ.get('FLASK_HOST', '0.0.0.0'),
        'port': os.environ.get('FLASK_PORT', '5000'),
        'email_import_enabled': current_app.config.get('EMAIL_IMPORT_ENABLED', False)
    }
    
    return render_template('settings/system.html', system_info=system_info, app_info=app_info)


@settings_bp.route('/email_import')
@login_required
def email_import():
    """Gestione import email (solo admin)"""
    if not current_user.is_admin:
        flash('Non hai i permessi per accedere a questa sezione.', 'error')
        return redirect(url_for('settings.index'))
    
    # Statistiche email import
    pending_drafts = EmailDraft.query.filter_by(status='pending').count()
    converted_drafts = EmailDraft.query.filter_by(status='converted').count()
    ignored_drafts = EmailDraft.query.filter_by(status='ignored').count()
    total_tickets_from_email = EmailImportLog.query.count()
    
    # Ultimi draft in attesa
    recent_drafts = EmailDraft.query.filter_by(status='pending').order_by(
        EmailDraft.received_at.desc()
    ).limit(10).all()
    
    # Configurazioni email per il template
    email_config = {
        'EMAIL_IMPORT_ENABLED': current_app.config.get('EMAIL_IMPORT_ENABLED', False),
        'EMAIL_IMAP_HOST': current_app.config.get('EMAIL_IMAP_HOST', ''),
        'EMAIL_IMAP_PORT': current_app.config.get('EMAIL_IMAP_PORT', 993),
        'EMAIL_IMAP_SSL': current_app.config.get('EMAIL_IMAP_SSL', True),
        'EMAIL_FOLDER': current_app.config.get('EMAIL_FOLDER', 'INBOX'),
        'EMAIL_AUTO_IMPORT': current_app.config.get('EMAIL_AUTO_IMPORT', False)
    }
    
    return render_template('settings/email_import.html',
                         pending_drafts=pending_drafts,
                         converted_drafts=converted_drafts,
                         ignored_drafts=ignored_drafts,
                         total_tickets_from_email=total_tickets_from_email,
                         recent_drafts=recent_drafts,
                         email_config=email_config)


@settings_bp.route('/email_import/run', methods=['POST'])
@login_required
def run_email_import():
    """Esegue manualmente l'import email (solo admin)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403
    try:
        from app.services.email_importer import import_new_emails
        messages, tickets = import_new_emails()
        return jsonify({'success': True, 'messages_processed': messages, 'tickets_created': tickets})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/email_import/test_connection', methods=['POST'])
@login_required
def test_imap_connection():
    """Testa la connessione IMAP e mostra le cartelle disponibili (solo admin)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403
    try:
        from app.services.email_importer import test_imap_connection
        success, message, folders = test_imap_connection()
        return jsonify({
            'success': success,
            'message': message,
            'folders': folders
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/email_import/scheduler/status', methods=['GET'])
@login_required
def email_scheduler_status():
    """Ottieni lo status dello scheduler email (solo admin)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403
    
    try:
        from app.services.scheduler import email_scheduler
        
        status = {
            'is_running': email_scheduler.is_job_running(),
            'next_run_time': email_scheduler.get_next_run_time().isoformat() if email_scheduler.get_next_run_time() else None,
            'poll_seconds': current_app.config.get('EMAIL_POLL_SECONDS', 300),
            'auto_import_enabled': current_app.config.get('EMAIL_AUTO_IMPORT', False),
            'email_import_enabled': current_app.config.get('EMAIL_IMPORT_ENABLED', False)
        }
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/email_import/scheduler/restart', methods=['POST'])
@login_required
def restart_email_scheduler():
    """Riavvia lo scheduler email (solo admin)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403
    
    try:
        from app.services.scheduler import email_scheduler
        
        # Ferma e riavvia lo scheduler
        email_scheduler.stop()
        email_scheduler.start()
        
        return jsonify({'success': True, 'message': 'Scheduler riavviato con successo'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/email_import/start_scheduler', methods=['POST'])
@login_required
def start_email_scheduler():
    """Avvia lo scheduler email"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403

    try:
        from app.services.scheduler import email_scheduler
        email_scheduler.start()

        return jsonify({'success': True, 'message': 'Scheduler avviato con successo'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/email_import/stop_scheduler', methods=['POST'])
@login_required
def stop_email_scheduler():
    """Arresta lo scheduler email"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403

    try:
        from app.services.scheduler import email_scheduler
        email_scheduler.stop()

        return jsonify({'success': True, 'message': 'Scheduler arrestato con successo'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/email_import/drafts')
@login_required
def email_drafts():
    """Lista email draft per conversione manuale (solo admin)"""
    if not current_user.is_admin:
        flash('Non hai i permessi per accedere a questa sezione.', 'error')
        return redirect(url_for('settings.index'))
    
    status = request.args.get('status', 'pending')
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Numero di draft per pagina
    
    drafts = EmailDraft.query.filter_by(status=status).order_by(
        EmailDraft.received_at.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('settings/email_drafts.html', drafts=drafts, status=status)


@settings_bp.route('/email_import/drafts/<int:draft_id>/convert', methods=['POST'])
@login_required
def convert_email_draft(draft_id):
    """Converte una email draft in ticket (solo admin)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403
    
    cliente_id = request.json.get('cliente_id') if request.json else None
    
    try:
        from app.services.email_importer import convert_draft_to_ticket
        ticket = convert_draft_to_ticket(draft_id, cliente_id)
        return jsonify({
            'success': True, 
            'message': f'Email convertita in ticket {ticket.numero_ticket}',
            'ticket_id': ticket.id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/email_import/drafts/<int:draft_id>/ignore', methods=['POST'])
@login_required
def ignore_email_draft(draft_id):
    """Ignora una email draft (solo admin)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403
    
    draft = EmailDraft.query.get_or_404(draft_id)
    draft.status = 'ignored'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Email ignorata'})


@settings_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Gestione profilo utente"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password cambiata con successo!', 'success')
            return redirect(url_for('settings.profile'))
        else:
            flash('Password attuale non corretta.', 'error')
    
    return render_template('settings/profile.html', form=form, user=current_user)


@settings_bp.route('/logs')
@login_required
def logs():
    """Visualizza log dell'applicazione (solo admin)"""
    if not current_user.is_admin:
        flash('Non hai i permessi per accedere a questa sezione.', 'error')
        return redirect(url_for('settings.index'))
    
    # Qui potresti implementare la lettura dei file di log
    # Per ora mostriamo una pagina placeholder
    log_entries = [
        {
            'timestamp': '2024-01-15 10:30:00',
            'level': 'INFO',
            'message': 'Applicazione avviata correttamente'
        },
        {
            'timestamp': '2024-01-15 10:31:15',
            'level': 'INFO',
            'message': 'Nuovo utente registrato: mario.rossi'
        },
        {
            'timestamp': '2024-01-15 10:35:22',
            'level': 'WARNING',
            'message': 'Tentativo di login fallito per utente: admin'
        }
    ]
    
    return render_template('settings/logs.html', log_entries=log_entries)


@settings_bp.route('/config')
@login_required
def config():
    """Configurazione applicazione (solo admin)"""
    if not current_user.is_admin:
        flash('Non hai i permessi per accedere a questa sezione.', 'error')
        return redirect(url_for('settings.index'))
    
    # Configurazioni modificabili
    config_options = {
        'tickets_per_page': 20,
        'clients_per_page': 20,
        'session_timeout': 30,  # minuti
        'auto_assign_tickets': False,
        'email_notifications': True,
        'backup_retention_days': 30,
        'default_ticket_priority': 'Media',
        'maintenance_mode': False
    }
    
    return render_template('settings/config.html', config_options=config_options)