from datetime import datetime
from app import db


class Department(db.Model):
    """Modello per i reparti aziendali"""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Manager del reparto
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)

    # Stato
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relazioni
    users = db.relationship('User', backref='department', lazy='dynamic', foreign_keys='User.department_id')
    manager = db.relationship('User', backref='managed_department', foreign_keys=[manager_id])
    tickets = db.relationship('Ticket', backref='department', lazy='dynamic')

    def __init__(self, name, display_name, description=None, manager_id=None, is_active=True):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.manager_id = manager_id
        self.is_active = is_active

    @classmethod
    def get_default_departments(cls):
        """Restituisce i reparti di default del sistema"""
        return {
            'it': {
                'name': 'it',
                'display_name': 'IT',
                'description': 'Reparto Informatica e Tecnologie'
            },
            'maintenance': {
                'name': 'maintenance',
                'display_name': 'Manutenzione',
                'description': 'Reparto Manutenzione e Riparazioni'
            },
            'sales': {
                'name': 'sales',
                'display_name': 'Vendite',
                'description': 'Reparto Vendite e Commerciale'
            },
            'support': {
                'name': 'support',
                'display_name': 'Supporto',
                'description': 'Reparto Supporto Clienti'
            }
        }

    @classmethod
    def create_default_departments(cls):
        """Crea i reparti di default se non esistono"""
        default_departments = cls.get_default_departments()

        for dept_data in default_departments.values():
            existing_dept = cls.query.filter_by(name=dept_data['name']).first()
            if not existing_dept:
                dept = cls(**dept_data)
                db.session.add(dept)

        db.session.commit()

    def get_active_users(self):
        """Restituisce gli utenti attivi del reparto"""
        return self.users.filter_by(is_active=True).all()

    def get_open_tickets(self):
        """Restituisce i ticket aperti del reparto"""
        from app.models.ticket import Ticket
        return self.tickets.filter(Ticket.stato.in_(Ticket.get_stati_aperti())).all()

    def __repr__(self):
        return f'<Department {self.name}: {self.display_name}>'

    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'manager_id': self.manager_id,
            'manager_name': self.manager.full_name if self.manager else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'users_count': self.users.count(),
            'active_tickets_count': len(self.get_open_tickets())
        }
