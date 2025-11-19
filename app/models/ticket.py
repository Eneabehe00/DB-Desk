from datetime import datetime
from app import db


# Tabella di associazione per ticket e ricambi necessari
ticket_ricambi = db.Table('ticket_ricambi',
    db.Column('ticket_id', db.Integer, db.ForeignKey('tickets.id'), primary_key=True),
    db.Column('ricambio_id', db.Integer, db.ForeignKey('ricambi.id'), primary_key=True),
    db.Column('quantita_necessaria', db.Integer, default=1),
    db.Column('quantita_utilizzata', db.Integer, default=0),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    extend_existing=True  # Permette di estendere una tabella esistente
)


class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_ticket = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Informazioni principali
    titolo = db.Column(db.String(200), nullable=False)
    descrizione = db.Column(db.Text, nullable=False)
    
    # Classificazione
    categoria = db.Column(db.String(50), nullable=False, default='Generale')  # Bug, Feature, Supporto, etc.
    priorita = db.Column(db.String(20), nullable=False, default='Media')    # Bassa, Media, Alta, Critica
    stato = db.Column(db.String(20), nullable=False, default='Aperto')      # Aperto, In Lavorazione, Risolto, Chiuso
    
    # Relazioni
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), nullable=False, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)  # Utente assegnato (opzionale)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False, index=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = db.Column(db.DateTime)  # Scadenza
    resolved_at = db.Column(db.DateTime)  # Quando è stato risolto
    closed_at = db.Column(db.DateTime)    # Quando è stato chiuso
    
    # Informazioni aggiuntive
    tags = db.Column(db.String(200))  # Tag separati da virgola
    note_interne = db.Column(db.Text)
    tempo_stimato = db.Column(db.Integer)  # In minuti
    tempo_impiegato = db.Column(db.Integer)  # In minuti
    
    # Relazione con l'utente assegnato (opzionale)
    assigned_to = db.relationship(
        'User',
        foreign_keys=[assigned_to_id],
        back_populates='assigned_tickets'
    )

    # Allegati e sotto-attività
    attachments = db.relationship(
        'TicketAttachment', backref='ticket', lazy='dynamic', cascade='all, delete-orphan'
    )
    subtasks = db.relationship(
        'TicketSubtask', backref='ticket', order_by='TicketSubtask.position', lazy='dynamic', cascade='all, delete-orphan'
    )
    
    # Ricambi necessari per questo ticket
    ricambi_necessari = db.relationship(
        'Ricambio', 
        secondary=ticket_ricambi,
        backref=db.backref('tickets_collegati', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # Macchine collegate a questo ticket
    macchine_collegate = db.relationship(
        'Macchina',
        secondary='ticket_macchine',
        lazy='dynamic'
    )
    
    def __init__(self, titolo, descrizione, cliente_id, created_by_id, **kwargs):
        self.titolo = titolo
        self.descrizione = descrizione
        self.cliente_id = cliente_id
        self.created_by_id = created_by_id
        
        # Genera numero ticket automaticamente
        if not kwargs.get('numero_ticket'):
            self.numero_ticket = self._generate_ticket_number()
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _generate_ticket_number(self):
        """Genera un numero ticket unico"""
        from datetime import datetime
        today = datetime.now()
        prefix = f"TK{today.year}{today.month:02d}"
        
        # Trova l'ultimo numero del mese
        last_ticket = Ticket.query.filter(
            Ticket.numero_ticket.like(f"{prefix}%")
        ).order_by(Ticket.id.desc()).first()
        
        if last_ticket:
            try:
                last_number = int(last_ticket.numero_ticket[-4:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    @property
    def giorni_apertura(self):
        """Calcola i giorni da quando il ticket è stato aperto"""
        if self.stato == 'Chiuso' and self.closed_at:
            delta = self.closed_at - self.created_at
        else:
            delta = datetime.utcnow() - self.created_at
        return delta.days
    
    @property
    def is_scaduto(self):
        """Verifica se il ticket è scaduto"""
        if not self.due_date or self.stato in ['Risolto', 'Chiuso']:
            return False
        return datetime.utcnow() > self.due_date
    
    @property
    def giorni_alla_scadenza(self):
        """Calcola i giorni alla scadenza"""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.utcnow()
        return delta.days
    
    @property
    def tag_list(self):
        """Restituisce i tag come lista"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def set_tags(self, tag_list):
        """Imposta i tag da una lista"""
        if tag_list:
            self.tags = ', '.join(str(tag).strip() for tag in tag_list if str(tag).strip())
        else:
            self.tags = None
    
    def chiudi_ticket(self):
        """Chiude il ticket e sottrae automaticamente i ricambi necessari"""
        self.stato = 'Chiuso'
        self.closed_at = datetime.utcnow()
        if not self.resolved_at:
            self.resolved_at = self.closed_at
        
        # Sottrai automaticamente i ricambi necessari
        self._sottrai_ricambi_automaticamente()
    
    def risolvi_ticket(self):
        """Risolve il ticket"""
        self.stato = 'Risolto'
        self.resolved_at = datetime.utcnow()
    
    def riapri_ticket(self):
        """Riapre un ticket chiuso"""
        self.stato = 'Aperto'
        self.resolved_at = None
        self.closed_at = None
    
    def _sottrai_ricambi_automaticamente(self):
        """Sottrae automaticamente i ricambi necessari dal magazzino"""
        from app.models.ricambio import Ricambio
        
        # Query per ottenere i ricambi con quantità necessaria
        ricambi_query = db.session.query(
            ticket_ricambi.c.ricambio_id,
            ticket_ricambi.c.quantita_necessaria,
            ticket_ricambi.c.quantita_utilizzata
        ).filter(ticket_ricambi.c.ticket_id == self.id)
        
        for ricambio_id, quantita_necessaria, quantita_utilizzata in ricambi_query:
            if quantita_utilizzata < quantita_necessaria:
                ricambio = Ricambio.query.get(ricambio_id)
                if ricambio:
                    quantita_da_sottrarre = quantita_necessaria - quantita_utilizzata
                    
                    try:
                        # Sottrai dal magazzino
                        ricambio.scarica_quantita(
                            quantita=quantita_da_sottrarre,
                            motivo=f'Utilizzo automatico per ticket {self.numero_ticket}',
                            ticket_id=self.id,
                            user_id=self.assigned_to_id or self.created_by_id
                        )
                        
                        # Aggiorna la quantità utilizzata nella tabella di associazione
                        db.session.execute(
                            ticket_ricambi.update()
                            .where(ticket_ricambi.c.ticket_id == self.id)
                            .where(ticket_ricambi.c.ricambio_id == ricambio_id)
                            .values(quantita_utilizzata=quantita_necessaria)
                        )
                        
                    except ValueError as e:
                        # Se non c'è abbastanza quantità, registra comunque quello che è possibile
                        quantita_disponibile = ricambio.quantita_disponibile
                        if quantita_disponibile > 0:
                            ricambio.scarica_quantita(
                                quantita=quantita_disponibile,
                                motivo=f'Utilizzo parziale automatico per ticket {self.numero_ticket} (quantità insufficiente)',
                                ticket_id=self.id,
                                user_id=self.assigned_to_id or self.created_by_id
                            )
                            
                            # Aggiorna con la quantità effettivamente utilizzata
                            db.session.execute(
                                ticket_ricambi.update()
                                .where(ticket_ricambi.c.ticket_id == self.id)
                                .where(ticket_ricambi.c.ricambio_id == ricambio_id)
                                .values(quantita_utilizzata=quantita_utilizzata + quantita_disponibile)
                            )
    
    @property
    def is_aperto(self):
        """Verifica se il ticket è considerato "aperto" (include tutti gli stati attivi)"""
        return self.stato != 'Chiuso'
    
    @property
    def is_chiuso(self):
        """Verifica se il ticket è definitivamente chiuso"""
        return self.stato == 'Chiuso'
    
    @staticmethod
    def get_stati_aperti():
        """Restituisce tutti gli stati considerati "aperti" """
        return ['Aperto', 'In Lavorazione', 'In Attesa Cliente', 'Risolto']
    
    @staticmethod
    def get_stati_chiusi():
        """Restituisce tutti gli stati considerati "chiusi" """
        return ['Chiuso']
    
    def __repr__(self):
        return f'<Ticket {self.numero_ticket}: {self.titolo}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'numero_ticket': self.numero_ticket,
            'titolo': self.titolo,
            'descrizione': self.descrizione,
            'categoria': self.categoria,
            'priorita': self.priorita,
            'stato': self.stato,
            'cliente_id': self.cliente_id,
            'cliente_nome': self.cliente.ragione_sociale if self.cliente else None,
            'created_by_id': self.created_by_id,
            'created_by_name': self.created_by_user.full_name if self.created_by_user else None,
            'assigned_to_id': self.assigned_to_id,
            'assigned_to_name': self.assigned_to.full_name if self.assigned_to else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'tags': self.tag_list,
            'giorni_apertura': self.giorni_apertura,
            'is_scaduto': self.is_scaduto,
            'giorni_alla_scadenza': self.giorni_alla_scadenza,
            'tempo_stimato': self.tempo_stimato,
            'tempo_impiegato': self.tempo_impiegato
        }