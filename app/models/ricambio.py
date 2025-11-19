from datetime import datetime
from app import db


class Ricambio(db.Model):
    __tablename__ = 'ricambi'
    
    id = db.Column(db.Integer, primary_key=True)
    codice = db.Column(db.String(50), unique=True, nullable=False, index=True)
    descrizione = db.Column(db.String(200), nullable=False)
    
    # Quantità
    quantita_disponibile = db.Column(db.Integer, default=0, nullable=False)
    quantita_prenotata = db.Column(db.Integer, default=0, nullable=False)
    quantita_minima = db.Column(db.Integer, default=0, nullable=False)  # Soglia sotto scorta
    
    # Ubicazione
    ubicazione = db.Column(db.String(100))  # Es: "Scaffale A-3-2"
    
    # Informazioni aggiuntive
    note = db.Column(db.Text)
    foto_filename = db.Column(db.String(255))  # Nome file foto
    
    # Prezzo e fornitore (opzionali)
    prezzo_unitario = db.Column(db.Numeric(10, 2))
    fornitore = db.Column(db.String(100))
    
    # Reparto di appartenenza
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False, index=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indice composto per performance query
    __table_args__ = (
        db.Index('idx_ricambi_codice_dept', 'codice', 'department_id'),
    )
    
    # Relazioni
    movimenti = db.relationship('MovimentoMagazzino', backref='ricambio', lazy='dynamic', cascade='all, delete-orphan')
    prenotazioni = db.relationship('PrenotazioneRicambio', backref='ricambio', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def quantita_effettiva(self):
        """Quantità effettivamente disponibile (disponibile - prenotata)"""
        return max(0, self.quantita_disponibile - self.quantita_prenotata)
    
    @property
    def is_sotto_scorta(self):
        """Verifica se il ricambio è sotto la quantità minima"""
        # Solo se è stata impostata una soglia minima (> 0)
        return (self.quantita_minima and self.quantita_minima > 0 and 
                self.quantita_disponibile <= self.quantita_minima)
    
    @property
    def has_prenotazioni(self):
        """Verifica se ci sono prenotazioni attive"""
        return self.quantita_prenotata > 0
    
    @property
    def stato_disponibilita(self):
        """Restituisce lo stato di disponibilità"""
        if self.quantita_effettiva == 0:
            return 'Esaurito'
        elif self.is_sotto_scorta:
            return 'Sotto scorta'
        elif self.has_prenotazioni:
            return 'Parzialmente prenotato'
        else:
            return 'Disponibile'
    
    def prenota_quantita(self, quantita, ticket_id=None, data_prenotazione=None):
        """Prenota una quantità di ricambio"""
        if quantita > self.quantita_effettiva:
            raise ValueError(f"Quantità non disponibile. Disponibile: {self.quantita_effettiva}")
        
        self.quantita_prenotata += quantita
        
        # Crea la prenotazione
        prenotazione = PrenotazioneRicambio(
            ricambio_id=self.id,
            quantita=quantita,
            ticket_id=ticket_id,
            data_prenotazione=data_prenotazione or datetime.utcnow()
        )
        db.session.add(prenotazione)
        
        return prenotazione
    
    def scarica_quantita(self, quantita, motivo='Utilizzo', ticket_id=None, user_id=None):
        """Scarica una quantità dal magazzino"""
        if quantita > self.quantita_disponibile:
            raise ValueError(f"Quantità non disponibile. Disponibile: {self.quantita_disponibile}")
        
        self.quantita_disponibile -= quantita
        
        # Se c'erano prenotazioni, riduci anche quelle
        if self.quantita_prenotata > 0:
            riduzione_prenotata = min(quantita, self.quantita_prenotata)
            self.quantita_prenotata -= riduzione_prenotata
        
        # Registra il movimento
        movimento = MovimentoMagazzino(
            ricambio_id=self.id,
            tipo_movimento='Scarico',
            quantita=-quantita,
            motivo=motivo,
            ticket_id=ticket_id,
            user_id=user_id
        )
        db.session.add(movimento)
        
        return movimento
    
    def carica_quantita(self, quantita, motivo='Carico', user_id=None):
        """Carica una quantità nel magazzino"""
        self.quantita_disponibile += quantita
        
        # Registra il movimento
        movimento = MovimentoMagazzino(
            ricambio_id=self.id,
            tipo_movimento='Carico',
            quantita=quantita,
            motivo=motivo,
            user_id=user_id
        )
        db.session.add(movimento)
        
        return movimento
    
    def __repr__(self):
        return f'<Ricambio {self.codice}: {self.descrizione}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'codice': self.codice,
            'descrizione': self.descrizione,
            'quantita_disponibile': self.quantita_disponibile,
            'quantita_prenotata': self.quantita_prenotata,
            'quantita_effettiva': self.quantita_effettiva,
            'quantita_minima': self.quantita_minima,
            'ubicazione': self.ubicazione,
            'note': self.note,
            'foto_filename': self.foto_filename,
            'prezzo_unitario': float(self.prezzo_unitario) if self.prezzo_unitario else None,
            'fornitore': self.fornitore,
            'stato_disponibilita': self.stato_disponibilita,
            'is_sotto_scorta': self.is_sotto_scorta,
            'has_prenotazioni': self.has_prenotazioni,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MovimentoMagazzino(db.Model):
    __tablename__ = 'movimenti_magazzino'
    
    id = db.Column(db.Integer, primary_key=True)
    ricambio_id = db.Column(db.Integer, db.ForeignKey('ricambi.id'), nullable=False, index=True)
    
    tipo_movimento = db.Column(db.String(20), nullable=False)  # Carico, Scarico, Rettifica
    quantita = db.Column(db.Integer, nullable=False)  # Positivo per carico, negativo per scarico
    motivo = db.Column(db.String(100), nullable=False)
    
    # Relazioni opzionali
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relazioni
    ticket = db.relationship('Ticket')
    user = db.relationship('User')
    
    @property
    def is_carico(self):
        return self.quantita > 0
    
    @property
    def is_scarico(self):
        return self.quantita < 0
    
    @property
    def quantita_assoluta(self):
        return abs(self.quantita)
    
    def __repr__(self):
        return f'<MovimentoMagazzino {self.tipo_movimento}: {self.quantita} - {self.ricambio.codice}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'ricambio_id': self.ricambio_id,
            'ricambio_codice': self.ricambio.codice if self.ricambio else None,
            'ricambio_descrizione': self.ricambio.descrizione if self.ricambio else None,
            'tipo_movimento': self.tipo_movimento,
            'quantita': self.quantita,
            'quantita_assoluta': self.quantita_assoluta,
            'motivo': self.motivo,
            'ticket_id': self.ticket_id,
            'ticket_numero': self.ticket.numero_ticket if self.ticket else None,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_carico': self.is_carico,
            'is_scarico': self.is_scarico
        }


class PrenotazioneRicambio(db.Model):
    __tablename__ = 'prenotazioni_ricambi'
    
    id = db.Column(db.Integer, primary_key=True)
    ricambio_id = db.Column(db.Integer, db.ForeignKey('ricambi.id'), nullable=False, index=True)
    
    quantita = db.Column(db.Integer, nullable=False)
    data_prenotazione = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_scadenza = db.Column(db.DateTime)  # Quando scade la prenotazione
    
    # Relazioni opzionali
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    # Stato
    stato = db.Column(db.String(20), default='Attiva', nullable=False)  # Attiva, Utilizzata, Annullata, Scaduta
    note = db.Column(db.Text)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    ticket = db.relationship('Ticket')
    user = db.relationship('User')
    
    @property
    def is_attiva(self):
        return self.stato == 'Attiva'
    
    @property
    def is_scaduta(self):
        if not self.data_scadenza:
            return False
        return datetime.utcnow() > self.data_scadenza and self.stato == 'Attiva'
    
    @property
    def giorni_alla_scadenza(self):
        if not self.data_scadenza:
            return None
        delta = self.data_scadenza - datetime.utcnow()
        return delta.days
    
    def annulla_prenotazione(self):
        """Annulla la prenotazione e libera la quantità"""
        if self.stato == 'Attiva':
            self.stato = 'Annullata'
            self.ricambio.quantita_prenotata -= self.quantita
            return True
        return False
    
    def utilizza_prenotazione(self, quantita_utilizzata=None):
        """Utilizza la prenotazione (totalmente o parzialmente)"""
        if self.stato != 'Attiva':
            return False
        
        if quantita_utilizzata is None:
            quantita_utilizzata = self.quantita
        
        if quantita_utilizzata > self.quantita:
            raise ValueError("Quantità utilizzata maggiore della prenotazione")
        
        # Scarica dal magazzino
        self.ricambio.scarica_quantita(
            quantita_utilizzata, 
            motivo=f'Utilizzo prenotazione #{self.id}',
            ticket_id=self.ticket_id,
            user_id=self.user_id
        )
        
        if quantita_utilizzata == self.quantita:
            self.stato = 'Utilizzata'
        else:
            # Prenotazione parziale - riduci la quantità
            self.quantita -= quantita_utilizzata
        
        return True
    
    def __repr__(self):
        return f'<PrenotazioneRicambio {self.ricambio.codice}: {self.quantita} - {self.stato}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'ricambio_id': self.ricambio_id,
            'ricambio_codice': self.ricambio.codice if self.ricambio else None,
            'ricambio_descrizione': self.ricambio.descrizione if self.ricambio else None,
            'quantita': self.quantita,
            'data_prenotazione': self.data_prenotazione.isoformat() if self.data_prenotazione else None,
            'data_scadenza': self.data_scadenza.isoformat() if self.data_scadenza else None,
            'ticket_id': self.ticket_id,
            'ticket_numero': self.ticket.numero_ticket if self.ticket else None,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'stato': self.stato,
            'note': self.note,
            'is_attiva': self.is_attiva,
            'is_scaduta': self.is_scaduta,
            'giorni_alla_scadenza': self.giorni_alla_scadenza,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
