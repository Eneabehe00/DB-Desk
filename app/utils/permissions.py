"""
Sistema di gestione permessi per il CRM
Decoratori e funzioni di utilità per controllare l'accesso basato su ruoli e reparti
"""

from functools import wraps
from flask import abort, request, jsonify
from flask_login import current_user


def require_permission(permission):
    """
    Decoratore per richiedere un permesso specifico
    
    Args:
        permission (str): Nome del permesso richiesto
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if not current_user.has_permission(permission):
                if request.is_json:
                    return jsonify({'error': 'Permesso negato'}), 403
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_department_access(department_id_param='department_id'):
    """
    Decoratore per richiedere l'accesso a un reparto specifico
    
    Args:
        department_id_param (str): Nome del parametro che contiene l'ID del reparto
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Ottieni l'ID del reparto dai parametri della richiesta
            department_id = None
            
            # Prova prima dai kwargs della route
            if department_id_param in kwargs:
                department_id = kwargs[department_id_param]
            # Poi dai parametri GET
            elif department_id_param in request.args:
                department_id = request.args.get(department_id_param, type=int)
            # Infine dai dati POST/JSON
            elif request.is_json and department_id_param in request.json:
                department_id = request.json[department_id_param]
            elif request.form and department_id_param in request.form:
                department_id = request.form.get(department_id_param, type=int)
            
            if department_id and not current_user.can_access_department(department_id):
                if request.is_json:
                    return jsonify({'error': 'Accesso al reparto negato'}), 403
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_role(*allowed_roles):
    """
    Decoratore per richiedere uno specifico ruolo
    
    Args:
        *allowed_roles: Lista dei ruoli consentiti
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if not current_user.role or current_user.role.name not in allowed_roles:
                if request.is_json:
                    return jsonify({'error': 'Ruolo non autorizzato'}), 403
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin():
    """Decoratore per richiedere privilegi di amministratore"""
    return require_role('admin', 'developer')


def require_developer():
    """Decoratore per richiedere privilegi di developer"""
    return require_role('developer')


def filter_by_department_access(query, model_class, user=None):
    """
    Filtra una query per mostrare solo i dati accessibili all'utente
    
    Args:
        query: Query SQLAlchemy da filtrare
        model_class: Classe del modello che ha department_id
        user: Utente per cui filtrare (default: current_user)
    
    Returns:
        Query filtrata
    """
    if user is None:
        user = current_user
    
    if not user.is_authenticated:
        return query.filter(False)  # Nessun risultato per utenti non autenticati
    
    # Admin e developer vedono tutto
    if user.has_permission('can_view_all_departments') or user.has_permission('can_manage_system'):
        return query
    
    # Utenti normali vedono solo il loro reparto
    if user.department_id:
        return query.filter(model_class.department_id == user.department_id)
    
    # Utenti senza reparto non vedono nulla
    return query.filter(False)


def get_accessible_departments(user=None):
    """
    Restituisce i reparti accessibili per un utente
    
    Args:
        user: Utente (default: current_user)
    
    Returns:
        Lista di oggetti Department
    """
    if user is None:
        user = current_user
    
    if not user.is_authenticated:
        return []
    
    return user.get_accessible_departments()


def can_manage_user(target_user, current_user=None):
    """
    Verifica se l'utente corrente può gestire un altro utente
    
    Args:
        target_user: Utente da gestire
        current_user: Utente corrente (default: current_user)
    
    Returns:
        bool: True se può gestire l'utente
    """
    if current_user is None:
        from flask_login import current_user as cu
        current_user = cu
    
    if not current_user.is_authenticated:
        return False
    
    # Non può gestire se stesso per alcune operazioni
    if current_user.id == target_user.id:
        return False
    
    # Admin e developer possono gestire tutti
    if current_user.has_permission('can_manage_users'):
        return True
    
    # Manager di reparto può gestire gli utenti del suo reparto
    if (current_user.is_department_manager() and 
        current_user.department_id == target_user.department_id):
        return True
    
    return False


def can_access_resource(resource, user=None):
    """
    Verifica se un utente può accedere a una risorsa specifica
    
    Args:
        resource: Oggetto con department_id
        user: Utente (default: current_user)
    
    Returns:
        bool: True se può accedere
    """
    if user is None:
        user = current_user
    
    if not user.is_authenticated:
        return False
    
    # Admin e developer possono accedere a tutto
    if user.has_permission('can_view_all_departments') or user.has_permission('can_manage_system'):
        return True
    
    # Verifica accesso al reparto della risorsa
    if hasattr(resource, 'department_id') and resource.department_id:
        return user.can_access_department(resource.department_id)
    
    return False


class PermissionManager:
    """Classe helper per gestire i permessi in modo centralizzato"""
    
    @staticmethod
    def check_ticket_access(ticket, user=None):
        """Verifica accesso a un ticket specifico"""
        if user is None:
            user = current_user
        
        # Accesso base alla risorsa
        if not can_access_resource(ticket, user):
            return False
        
        # Controlli aggiuntivi per i ticket
        # Il creatore può sempre vedere i suoi ticket
        if ticket.created_by_id == user.id:
            return True
        
        # L'assegnatario può vedere i ticket assegnati
        if ticket.assigned_to_id == user.id:
            return True
        
        # Admin possono vedere tutti i ticket del sistema
        if user.has_permission('can_manage_all_tickets'):
            return True
        
        # Manager di reparto può vedere tutti i ticket del reparto
        if (user.is_department_manager() and 
            user.department_id == ticket.department_id):
            return True
        
        return False
    
    @staticmethod
    def check_client_access(client, user=None):
        """Verifica accesso a un cliente specifico - I clienti sono condivisi tra tutti i reparti"""
        if user is None:
            user = current_user
        
        # I clienti sono sempre accessibili a tutti gli utenti autenticati
        return user.is_authenticated if user else False
    
    @staticmethod
    def check_inventory_access(item, user=None):
        """Verifica accesso a un articolo di magazzino"""
        if user is None:
            user = current_user
        
        # Accesso base alla risorsa
        if not can_access_resource(item, user):
            return False
        
        # Admin possono gestire tutto l'inventario
        if user.has_permission('can_manage_all_inventory'):
            return True

        return True

    @staticmethod
    def can_view_machine(user, machine):
        """Verifica se l'utente può visualizzare una macchina"""
        if not user.is_authenticated:
            return False

        # Admin e developer possono vedere tutto
        if user.has_permission('can_view_all_departments') or user.has_permission('can_manage_system'):
            return True

        # Verifica accesso al reparto della macchina
        if hasattr(machine, 'department_id') and machine.department_id:
            return user.can_access_department(machine.department_id)

        return False

    @staticmethod
    def can_create_machine(user):
        """Verifica se l'utente può creare macchine"""
        if not user.is_authenticated:
            return False

        # Admin e developer possono creare macchine
        if user.has_permission('can_manage_system'):
            return True

        # Manager di reparto possono creare macchine nel loro reparto
        if user.is_department_manager():
            return True

        # Utenti con permesso specifico
        return user.has_permission('can_create_machines')

    @staticmethod
    def can_edit_machine(user, machine):
        """Verifica se l'utente può modificare una macchina"""
        if not user.is_authenticated:
            return False

        # Admin e developer possono modificare tutto
        if user.has_permission('can_manage_system'):
            return True

        # Manager di reparto possono modificare macchine del loro reparto
        if (user.is_department_manager() and
            hasattr(machine, 'department_id') and
            machine.department_id == user.department_id):
            return True

        # Utenti con permesso specifico e accesso al reparto
        if user.has_permission('can_edit_machines'):
            return PermissionManager.can_view_machine(user, machine)

        return False

    @staticmethod
    def can_delete_machine(user, machine):
        """Verifica se l'utente può eliminare una macchina"""
        if not user.is_authenticated:
            return False

        # Solo admin e developer possono eliminare macchine
        return user.has_permission('can_manage_system')

    @staticmethod
    def can_assign_machine(user, machine):
        """Verifica se l'utente può assegnare una macchina"""
        if not user.is_authenticated:
            return False

        # Admin e developer possono assegnare tutto
        if user.has_permission('can_manage_system'):
            return True

        # Manager di reparto possono assegnare macchine del loro reparto
        if (user.is_department_manager() and
            hasattr(machine, 'department_id') and
            machine.department_id == user.department_id):
            return True

        # Utenti con permesso specifico
        return user.has_permission('can_assign_machines') and PermissionManager.can_view_machine(user, machine)

    @staticmethod
    def can_return_machine(user, machine):
        """Verifica se l'utente può far rientrare una macchina"""
        return PermissionManager.can_assign_machine(user, machine)

    @staticmethod
    def can_repair_machine(user, machine):
        """Verifica se l'utente può gestire riparazioni"""
        if not user.is_authenticated:
            return False

        # Admin e developer possono gestire tutto
        if user.has_permission('can_manage_system'):
            return True

        # Manager di reparto possono gestire riparazioni del loro reparto
        if (user.is_department_manager() and
            hasattr(machine, 'department_id') and
            machine.department_id == user.department_id):
            return True

        # Utenti tecnici
        return user.has_permission('can_manage_repairs') and PermissionManager.can_view_machine(user, machine)

    @staticmethod
    def can_sell_machine(user, machine):
        """Verifica se l'utente può vendere una macchina"""
        if not user.is_authenticated:
            return False

        # Solo admin e developer possono vendere macchine
        return user.has_permission('can_manage_system')
    
    # ===== FOGLI TECNICI PERMISSIONS =====
    
    @staticmethod
    def can_view_foglio_tecnico(user, foglio):
        """Verifica se l'utente può visualizzare un foglio tecnico"""
        if not user.is_authenticated:
            return False
        
        # Admin e developer possono vedere tutto
        if user.has_permission('can_view_all_departments') or user.has_permission('can_manage_system'):
            return True
        
        # Il tecnico assegnato può sempre vedere il suo foglio
        if foglio.tecnico_id == user.id:
            return True
        
        # Manager di reparto può vedere tutti i fogli del reparto
        if (user.is_department_manager() and 
            user.department_id == foglio.department_id):
            return True
        
        # Utenti dello stesso reparto possono vedere i fogli
        if user.department_id == foglio.department_id:
            return True
        
        return False
    
    @staticmethod
    def can_edit_foglio_tecnico(user, foglio):
        """Verifica se l'utente può modificare un foglio tecnico"""
        if not user.is_authenticated:
            return False
        
        # Admin e developer possono modificare tutto
        if user.has_permission('can_manage_system'):
            return True
        
        # Il tecnico assegnato può modificare il suo foglio se non è completato
        if (foglio.tecnico_id == user.id and 
            foglio.stato not in ['Inviato', 'Archiviato']):
            return True
        
        # Manager di reparto può modificare fogli del reparto
        if (user.is_department_manager() and 
            user.department_id == foglio.department_id and
            foglio.stato not in ['Inviato', 'Archiviato']):
            return True
        
        return False
    
    @staticmethod
    def can_create_foglio_tecnico(user):
        """Verifica se l'utente può creare fogli tecnici"""
        if not user.is_authenticated:
            return False
        
        # Admin e developer possono creare sempre
        if user.has_permission('can_manage_system'):
            return True
        
        # Manager di reparto possono creare fogli
        if user.is_department_manager():
            return True
        
        # Tecnici possono creare fogli per il loro reparto
        if user.has_permission('can_create_fogli_tecnici'):
            return True
        
        # Per default, utenti con department possono creare fogli
        return bool(user.department_id)
    
    @staticmethod
    def can_delete_foglio_tecnico(user, foglio):
        """Verifica se l'utente può eliminare un foglio tecnico"""
        if not user.is_authenticated:
            return False
        
        # Solo admin possono eliminare fogli
        return user.has_permission('can_manage_system')
    
    @staticmethod
    def can_finalize_foglio_tecnico(user, foglio):
        """Verifica se l'utente può finalizzare un foglio tecnico (PDF/invio)"""
        if not user.is_authenticated:
            return False
        
        # Admin possono sempre finalizzare
        if user.has_permission('can_manage_system'):
            return True
        
        # Il tecnico assegnato può finalizzare se ha completato tutti gli step
        if (foglio.tecnico_id == user.id and 
            foglio.is_step_completato(5)):  # Step 5 = firme raccolte
            return True
        
        # Manager di reparto può finalizzare fogli del reparto
        if (user.is_department_manager() and 
            user.department_id == foglio.department_id and
            foglio.is_step_completato(5)):
            return True
        
        return False
    
    @staticmethod
    def can_view_client(user, client):
        """Verifica se l'utente può visualizzare un cliente"""
        return PermissionManager.check_client_access(client, user)