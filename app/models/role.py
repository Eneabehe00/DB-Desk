from datetime import datetime
from app import db


class Role(db.Model):
    """Modello per i ruoli utente"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Permessi
    can_manage_users = db.Column(db.Boolean, default=False, nullable=False)
    can_manage_departments = db.Column(db.Boolean, default=False, nullable=False)
    can_manage_system = db.Column(db.Boolean, default=False, nullable=False)
    can_view_all_departments = db.Column(db.Boolean, default=False, nullable=False)
    can_manage_all_tickets = db.Column(db.Boolean, default=False, nullable=False)
    can_manage_all_clients = db.Column(db.Boolean, default=False, nullable=False)
    can_manage_all_inventory = db.Column(db.Boolean, default=False, nullable=False)
    can_view_reports = db.Column(db.Boolean, default=True, nullable=False)
    can_export_data = db.Column(db.Boolean, default=False, nullable=False)
    
    # Meta info
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __init__(self, name, display_name, description=None, **permissions):
        self.name = name
        self.display_name = display_name
        self.description = description
        
        # Imposta i permessi
        for perm, value in permissions.items():
            if hasattr(self, perm):
                setattr(self, perm, value)
    
    @classmethod
    def get_default_roles(cls):
        """Restituisce i ruoli di default del sistema"""
        return {
            'employee': {
                'name': 'employee',
                'display_name': 'Dipendente',
                'description': 'Utente normale con accesso limitato al proprio reparto',
                'can_view_reports': True
            },
            'admin': {
                'name': 'admin', 
                'display_name': 'Amministratore',
                'description': 'Amministratore con accesso completo al sistema',
                'can_manage_users': True,
                'can_manage_departments': True,
                'can_view_all_departments': True,
                'can_manage_all_tickets': True,
                'can_manage_all_clients': True,
                'can_manage_all_inventory': True,
                'can_view_reports': True,
                'can_export_data': True
            },
            'developer': {
                'name': 'developer',
                'display_name': 'Developer',
                'description': 'Sviluppatore con accesso completo al sistema e funzioni avanzate',
                'can_manage_users': True,
                'can_manage_departments': True,
                'can_manage_system': True,
                'can_view_all_departments': True,
                'can_manage_all_tickets': True,
                'can_manage_all_clients': True,
                'can_manage_all_inventory': True,
                'can_view_reports': True,
                'can_export_data': True
            }
        }
    
    @classmethod
    def create_default_roles(cls):
        """Crea i ruoli di default se non esistono"""
        default_roles = cls.get_default_roles()
        
        for role_data in default_roles.values():
            existing_role = cls.query.filter_by(name=role_data['name']).first()
            if not existing_role:
                role = cls(**role_data)
                db.session.add(role)
        
        db.session.commit()
    
    def has_permission(self, permission):
        """Verifica se il ruolo ha un determinato permesso"""
        return getattr(self, permission, False)
    
    def __repr__(self):
        return f'<Role {self.name}: {self.display_name}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'permissions': {
                'can_manage_users': self.can_manage_users,
                'can_manage_departments': self.can_manage_departments,
                'can_manage_system': self.can_manage_system,
                'can_view_all_departments': self.can_view_all_departments,
                'can_manage_all_tickets': self.can_manage_all_tickets,
                'can_manage_all_clients': self.can_manage_all_clients,
                'can_manage_all_inventory': self.can_manage_all_inventory,
                'can_view_reports': self.can_view_reports,
                'can_export_data': self.can_export_data
            },
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
