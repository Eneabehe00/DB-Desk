from datetime import datetime
from app import db


class Cliente(db.Model):
    __tablename__ = 'clienti'
    
    id = db.Column(db.Integer, primary_key=True)
    ragione_sociale = db.Column(db.String(200), nullable=False, index=True)
    codice_fiscale = db.Column(db.String(16), unique=True)
    partita_iva = db.Column(db.String(11), unique=True)
    
    # Dati di contatto
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20))
    cellulare = db.Column(db.String(20))
    
    # Indirizzo
    indirizzo = db.Column(db.String(200))
    citta = db.Column(db.String(100))
    cap = db.Column(db.String(10))
    provincia = db.Column(db.String(2))
    paese = db.Column(db.String(100), default='Italia')
    
    # Informazioni aggiuntive
    settore = db.Column(db.String(100))  # Settore di attività
    note = db.Column(db.Text)
    
    # Reparto di appartenenza
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False, index=True)
    
    # Status e meta info
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indice composto per performance query
    __table_args__ = (
        db.Index('idx_clienti_active_ragione', 'is_active', 'ragione_sociale'),
    )
    
    # Relazione con i ticket (un cliente può avere molti ticket)
    tickets = db.relationship('Ticket', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, ragione_sociale, email, department_id, **kwargs):
        self.ragione_sociale = ragione_sociale
        self.email = email
        self.department_id = department_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def indirizzo_completo(self):
        """Restituisce l'indirizzo completo formattato"""
        parts = []
        if self.indirizzo:
            parts.append(self.indirizzo)
        if self.cap and self.citta:
            parts.append(f"{self.cap} {self.citta}")
        if self.provincia:
            parts.append(f"({self.provincia})")
        if self.paese and self.paese != 'Italia':
            parts.append(self.paese)
        return ', '.join(parts) if parts else ''
    
    @property
    def ticket_count(self):
        """Numero totale di ticket del cliente"""
        return self.tickets.count()
    
    @property
    def ticket_aperti(self):
        """Numero di ticket aperti del cliente"""
        return self.tickets.filter_by(stato='aperto').count()
    
    def __repr__(self):
        return f'<Cliente {self.ragione_sociale}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'ragione_sociale': self.ragione_sociale,
            'codice_fiscale': self.codice_fiscale,
            'partita_iva': self.partita_iva,
            'email': self.email,
            'telefono': self.telefono,
            'cellulare': self.cellulare,
            'indirizzo_completo': self.indirizzo_completo,
            'settore': self.settore,
            'note': self.note,
            'is_active': self.is_active,
            'ticket_count': self.ticket_count,
            'ticket_aperti': self.ticket_aperti,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }