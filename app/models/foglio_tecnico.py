from datetime import datetime
from app import db


class FoglioTecnico(db.Model):
    __tablename__ = 'fogli_tecnici'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_foglio = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Campi base dal ticket esistente
    titolo = db.Column(db.String(200), nullable=False)
    descrizione = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=True, default='Intervento')
    priorita = db.Column(db.String(20), nullable=True, default='Media')
    stato = db.Column(db.String(30), nullable=False, default='Bozza')  # Bozza, In compilazione, Completato, Inviato
    
    # Relazioni esistenti
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), nullable=False, index=True)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)  # Tecnico sul posto
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False, index=True)
    
    # CAMPI AGGIUNTIVI SPECIFICI PER FOGLIO TECNICO
    
    # Modalità pagamento
    modalita_pagamento = db.Column(db.String(50))  # Contanti, Bonifico, Assegno, etc.
    importo_intervento = db.Column(db.Numeric(10, 2))
    
    # Informazioni intervento sul posto
    indirizzo_intervento = db.Column(db.String(200))
    data_intervento = db.Column(db.DateTime, nullable=False)
    durata_intervento = db.Column(db.Integer)  # minuti
    km_percorsi = db.Column(db.Integer)
    note_aggiuntive = db.Column(db.Text)  # Note extra per il foglio
    
    # Firme (salvate come path a file immagine)
    firma_tecnico_path = db.Column(db.String(200))  # Path del file firma tecnico
    firma_cliente_path = db.Column(db.String(200))  # Path del file firma cliente
    nome_firmatario_cliente = db.Column(db.String(100))
    
    # Gestione output
    pdf_generato = db.Column(db.Boolean, default=False)
    pdf_path = db.Column(db.String(200))  # Path del PDF generato
    inviato_online = db.Column(db.Boolean, default=False)
    email_invio = db.Column(db.String(120))
    data_invio = db.Column(db.DateTime)
    
    # Gestione operazioni sulle macchine (come nei ticket)
    tipo_operazione_macchine = db.Column(db.String(50))  # prestito_semplice, riparazione_sede, etc.
    
    # Stato compilazione progressiva
    step_corrente = db.Column(db.Integer, default=1)  # 1-N step
    step_completati = db.Column(db.JSON)  # Lista step completati
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)  # Quando completato
    
    # Indici per performance
    __table_args__ = (
        db.Index('idx_fogli_tecnici_cliente_data', 'cliente_id', 'data_intervento'),
        db.Index('idx_fogli_tecnici_tecnico_stato', 'tecnico_id', 'stato'),
    )
    
    # Relazioni
    cliente = db.relationship('Cliente', backref='fogli_tecnici', lazy='select')
    tecnico = db.relationship('User', backref='fogli_tecnici_assegnati', lazy='select')
    
    # Tabelle di collegamento per macchine e ricambi (simili ai ticket)
    macchine_collegate = db.relationship(
        'Macchina',
        secondary='foglio_macchine',
        lazy='dynamic'
    )
    
    ricambi_utilizzati = db.relationship(
        'Ricambio', 
        secondary='foglio_ricambi',
        backref=db.backref('fogli_collegati', lazy='dynamic'),
        lazy='dynamic'
    )
    
    def __init__(self, titolo, data_intervento, cliente_id, tecnico_id, department_id, **kwargs):
        self.titolo = titolo
        self.data_intervento = data_intervento
        self.cliente_id = cliente_id
        self.tecnico_id = tecnico_id
        self.department_id = department_id
        
        # Genera numero foglio automaticamente
        if not kwargs.get('numero_foglio'):
            self.numero_foglio = self._generate_foglio_number()
        
        # Inizializza step completati come lista vuota
        if not kwargs.get('step_completati'):
            self.step_completati = []
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _generate_foglio_number(self):
        """Genera un numero foglio unico in formato FT-YYYY-NNNN"""
        from sqlalchemy import func, desc
        
        current_year = datetime.utcnow().year
        year_str = str(current_year)
        
        # Trova il numero più alto dell'anno corrente
        last_foglio = db.session.query(FoglioTecnico.numero_foglio).filter(
            FoglioTecnico.numero_foglio.like(f'FT-{year_str}-%')
        ).order_by(desc(FoglioTecnico.numero_foglio)).first()
        
        if last_foglio:
            # Estrae il numero dalla stringa FT-YYYY-NNNN
            try:
                last_number = int(last_foglio[0].split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
            
        # Verifica che il numero generato non esista già (sicurezza extra)
        max_attempts = 100
        for attempt in range(max_attempts):
            candidate_number = f'FT-{year_str}-{next_number:04d}'
            existing = db.session.query(FoglioTecnico.id).filter(
                FoglioTecnico.numero_foglio == candidate_number
            ).first()
            
            if not existing:
                return candidate_number
            
            next_number += 1
        
        # Se dopo 100 tentativi non trova un numero libero, usa timestamp
        import time
        timestamp_suffix = int(time.time() * 1000) % 10000
        return f'FT-{year_str}-{timestamp_suffix:04d}'
    
    @property
    def full_name(self):
        """Restituisce nome completo del foglio per la visualizzazione"""
        return f'{self.numero_foglio} - {self.titolo}'
    
    @staticmethod
    def get_stati_disponibili():
        """Restituisce lista degli stati possibili"""
        return ['Bozza', 'In compilazione', 'In attesa firme', 'Completato', 'Inviato', 'Archiviato']
    
    @staticmethod
    def get_modalita_pagamento():
        """Restituisce lista modalità di pagamento disponibili"""
        return [
            'Contanti',
            'Bonifico bancario',
            'Assegno',
            'Carta di credito/debito',
            'PayPal',
            'Fatturazione differita',
            'Non specificato'
        ]
    
    def is_step_completato(self, step_number):
        """Verifica se uno step specifico è stato completato"""
        return step_number in (self.step_completati or [])
    
    def mark_step_completato(self, step_number):
        """Marca uno step come completato"""
        if not self.step_completati:
            self.step_completati = []
        
        if step_number not in self.step_completati:
            self.step_completati.append(step_number)
            # SQLAlchemy needs to know the JSON field changed
            db.session.merge(self)
    
    def get_prossimo_step(self):
        """Restituisce il numero del prossimo step da completare"""
        total_steps = 5  # Aggiorna quando aggiungi step
        
        for step in range(1, total_steps + 1):
            if not self.is_step_completato(step):
                return step
        
        return total_steps  # Tutti completati
    
    def __repr__(self):
        return f'<FoglioTecnico {self.numero_foglio} - {self.titolo}>'


# Tabelle di associazione per macchine e ricambi
foglio_macchine = db.Table('foglio_macchine',
    db.Column('foglio_id', db.Integer, db.ForeignKey('fogli_tecnici.id'), primary_key=True),
    db.Column('macchina_id', db.Integer, db.ForeignKey('macchine.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    extend_existing=True
)

foglio_ricambi = db.Table('foglio_ricambi',
    db.Column('foglio_id', db.Integer, db.ForeignKey('fogli_tecnici.id'), primary_key=True),
    db.Column('ricambio_id', db.Integer, db.ForeignKey('ricambi.id'), primary_key=True),
    db.Column('quantita_utilizzata', db.Integer, default=1),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    extend_existing=True
)
