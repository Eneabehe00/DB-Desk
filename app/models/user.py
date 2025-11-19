from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False, index=True)
    last_name = db.Column(db.String(100), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Sistema ruoli e reparti
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), index=True)
    
    # Manteniamo is_admin per compatibilità con il codice esistente
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Indice composto per performance query
    __table_args__ = (
        db.Index('idx_users_active_name', 'is_active', 'first_name', 'last_name'),
    )
    
    # Relazione con i ticket creati dall'utente
    created_tickets = db.relationship('Ticket', foreign_keys='Ticket.created_by_id', 
                                      backref='created_by_user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Relazione con i ticket assegnati all'utente
    assigned_tickets = db.relationship(
        'Ticket',
        foreign_keys='Ticket.assigned_to_id',
        back_populates='assigned_to',
        lazy='dynamic'
    )
    
    def __init__(self, username, email, password, first_name, last_name, is_admin=False, is_active=True, role_id=None, department_id=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.is_admin = is_admin
        self.is_active = is_active
        self.role_id = role_id
        self.department_id = department_id
    
    def set_password(self, password):
        """Imposta la password con hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la password"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Restituisce il nome completo"""
        return f"{self.first_name} {self.last_name}"
    
    def update_last_login(self):
        """Aggiorna timestamp ultimo login"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def reassign_tickets_to_admin(self):
        """Riassegna tutti i ticket di questo utente al primo admin disponibile"""
        from app.models.ticket import Ticket
        
        # Trova il primo admin attivo (escludendo questo utente se è admin)
        admin_user = User.query.filter(
            User.is_admin == True,
            User.is_active == True,
            User.id != self.id
        ).first()
        
        if not admin_user:
            raise ValueError("Nessun amministratore attivo disponibile per la riassegnazione dei ticket")
        
        # Riassegna i ticket creati dall'utente
        created_tickets = self.created_tickets.all()
        for ticket in created_tickets:
            ticket.created_by_id = admin_user.id
        
        # Riassegna i ticket assegnati all'utente
        assigned_tickets = self.assigned_tickets.all()
        for ticket in assigned_tickets:
            ticket.assigned_to_id = admin_user.id
        
        return admin_user, len(created_tickets), len(assigned_tickets)
    
    # Metodi per il sistema di permessi
    def has_permission(self, permission):
        """Verifica se l'utente ha un determinato permesso"""
        if not self.role:
            return False
        return self.role.has_permission(permission)
    
    def can_access_department(self, department_id):
        """Verifica se l'utente può accedere ai dati di un reparto"""
        if not self.is_active:
            return False
        
        # Admin e developer possono accedere a tutti i reparti
        if self.has_permission('can_view_all_departments') or self.has_permission('can_manage_system'):
            return True
        
        # Gli utenti possono accedere solo al loro reparto
        return self.department_id == department_id
    
    def get_accessible_departments(self):
        """Restituisce i reparti accessibili per questo utente"""
        from app.models.department import Department
        
        # Admin e developer vedono tutti i reparti
        if self.has_permission('can_view_all_departments') or self.has_permission('can_manage_system'):
            return Department.query.filter_by(is_active=True).all()
        
        # Utenti normali vedono solo il loro reparto
        if self.department:
            return [self.department]
        
        return []
    
    def is_department_manager(self):
        """Verifica se l'utente è responsabile di un reparto"""
        if not self.department:
            return False
        return self.department.manager_id == self.id
    
    def sync_admin_role(self):
        """Sincronizza is_admin con il ruolo per compatibilità"""
        if self.role:
            if self.role.name in ['admin', 'developer']:
                self.is_admin = True
            else:
                self.is_admin = False
    
    @property
    def role_display_name(self):
        """Restituisce il nome visualizzato del ruolo"""
        return self.role.display_name if self.role else 'Nessun ruolo'
    
    @property
    def department_display_name(self):
        """Restituisce il nome visualizzato del reparto"""
        return self.department.display_name if self.department else 'Nessun reparto'

    def can_be_deleted(self):
        """Verifica se l'utente può essere eliminato"""
        # Non può essere eliminato se è l'unico admin attivo
        if self.is_admin:
            active_admins = User.query.filter(
                User.is_admin == True,
                User.is_active == True,
                User.id != self.id
            ).count()
            if active_admins == 0:
                return False, "Non puoi eliminare l'unico amministratore attivo"
        
        return True, "OK"
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }