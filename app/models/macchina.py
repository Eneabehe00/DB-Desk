from datetime import datetime
from app import db


# Tabella di associazione per reparti e tipi di macchina
department_tipo_macchina = db.Table('department_tipo_macchina',
    db.Column('department_id', db.Integer, db.ForeignKey('departments.id'), primary_key=True),
    db.Column('tipo_macchina_id', db.Integer, db.ForeignKey('tipi_macchine.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    extend_existing=True
)


class TipoMacchina(db.Model):
    __tablename__ = 'tipi_macchine'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False, index=True)
    descrizione = db.Column(db.Text)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    macchine = db.relationship('Macchina', backref='tipo_macchina', lazy='dynamic', cascade='all, delete-orphan')
    
    # Relazione many-to-many con i reparti
    departments = db.relationship(
        'Department',
        secondary=department_tipo_macchina,
        lazy='dynamic',
        backref=db.backref('tipi_macchine', lazy='dynamic')
    )
    
    def __repr__(self):
        return f'<TipoMacchina {self.nome}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'nome': self.nome,
            'descrizione': self.descrizione,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'numero_macchine': self.macchine.count()
        }


# Tabella di associazione per ticket e macchine
ticket_macchine = db.Table('ticket_macchine',
    db.Column('ticket_id', db.Integer, db.ForeignKey('tickets.id'), primary_key=True),
    db.Column('macchina_id', db.Integer, db.ForeignKey('macchine.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    extend_existing=True
)


class Macchina(db.Model):
    __tablename__ = 'macchine'
    
    id = db.Column(db.Integer, primary_key=True)
    codice = db.Column(db.String(50), unique=True, nullable=False, index=True)
    modello = db.Column(db.String(200), nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    numero_serie = db.Column(db.String(100), unique=True, index=True)
    
    # Tipo di macchina
    tipo_macchina_id = db.Column(db.Integer, db.ForeignKey('tipi_macchine.id'), nullable=False, index=True)
    
    # Stato della macchina
    stato = db.Column(db.String(30), nullable=False, default='Disponibile')  
    # Stati: Disponibile, In prestito, In riparazione, Attiva, Dismessa
    
    # Ubicazione attuale
    ubicazione = db.Column(db.String(200))  # Es: "Magazzino", "Cliente XYZ", "Riparazione"
    
    # Relazione con cliente (se assegnata/venduta)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), index=True)
    data_assegnazione = db.Column(db.DateTime)  # Quando è stata assegnata al cliente
    
    # Informazioni tecniche
    anno_produzione = db.Column(db.Integer)
    peso = db.Column(db.Numeric(8, 2))  # In kg
    dimensioni = db.Column(db.String(100))  # Es: "120x80x150 cm"
    alimentazione = db.Column(db.String(50))  # Es: "220V", "Batteria"
    
    # Informazioni commerciali
    prezzo_acquisto = db.Column(db.Numeric(10, 2))
    prezzo_vendita = db.Column(db.Numeric(10, 2))
    fornitore = db.Column(db.String(100))
    data_acquisto = db.Column(db.Date)
    data_vendita = db.Column(db.Date)
    
    # Garanzia e manutenzione
    data_scadenza_garanzia = db.Column(db.Date)
    prossima_manutenzione = db.Column(db.Date)
    intervallo_manutenzione_giorni = db.Column(db.Integer, default=365)  # Default 1 anno
    
    # Informazioni aggiuntive
    note = db.Column(db.Text)
    foto_filename = db.Column(db.String(255))
    manuale_filename = db.Column(db.String(255))
    
    # Reparto di appartenenza
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False, index=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    cliente = db.relationship('Cliente', backref='macchine_assegnate')
    movimenti = db.relationship('MovimentoMacchina', backref='macchina', lazy='dynamic', cascade='all, delete-orphan')
    
    # Relazione many-to-many con i ticket
    tickets_collegati = db.relationship(
        'Ticket',
        secondary=ticket_macchine,
        lazy='dynamic',
        overlaps="macchine_collegate"
    )
    
    @property
    def is_disponibile(self):
        """Verifica se la macchina è disponibile"""
        return self.stato == 'Disponibile'
    
    @property
    def is_in_prestito(self):
        """Verifica se la macchina è in prestito"""
        return self.stato == 'In prestito'
    
    @property
    def is_in_riparazione(self):
        """Verifica se la macchina è in riparazione"""
        return self.stato == 'In riparazione'
    
    @property
    def is_attiva(self):
        """Verifica se la macchina è attiva (venduta e in uso presso cliente)"""
        return self.stato == 'Attiva'
    
    @property
    def nome_completo(self):
        """Restituisce nome completo della macchina"""
        return f"{self.marca} {self.modello}"
    
    @property
    def eta_anni(self):
        """Calcola l'età della macchina in anni"""
        if not self.anno_produzione:
            return None
        return datetime.now().year - self.anno_produzione
    
    @property
    def giorni_alla_manutenzione(self):
        """Calcola i giorni alla prossima manutenzione"""
        if not self.prossima_manutenzione:
            return None
        delta = self.prossima_manutenzione - datetime.now().date()
        return delta.days
    
    @property
    def necessita_manutenzione(self):
        """Verifica se necessita manutenzione"""
        giorni = self.giorni_alla_manutenzione
        return giorni is not None and giorni <= 30  # Avviso 30 giorni prima
    
    @property
    def garanzia_scaduta(self):
        """Verifica se la garanzia è scaduta"""
        if not self.data_scadenza_garanzia:
            return None
        return datetime.now().date() > self.data_scadenza_garanzia
    
    def assegna_a_cliente(self, cliente_id, stato='In prestito', note=None, salva_stato_originale=False):
        """Assegna la macchina a un cliente"""
        if not self.is_disponibile:
            raise ValueError(f"La macchina non è disponibile (stato attuale: {self.stato})")
        
        # SALVA STATO ORIGINALE SE RICHIESTO (per prestiti temporanei)
        cliente_originale_id = None
        ubicazione_originale = None
        data_assegnazione_originale = None
        
        if salva_stato_originale:
            cliente_originale_id = self.cliente_id
            ubicazione_originale = self.ubicazione
            data_assegnazione_originale = self.data_assegnazione
        
        self.cliente_id = cliente_id
        self.stato = stato
        self.data_assegnazione = datetime.utcnow()
        self.ubicazione = f"Cliente ID: {cliente_id}"
        
        # Registra il movimento
        movimento = MovimentoMacchina(
            macchina_id=self.id,
            tipo_movimento='Assegnazione',
            stato_precedente='Disponibile',
            stato_nuovo=stato,
            cliente_id=cliente_id,
            # SALVA STATO ORIGINALE SE SPECIFICATO
            cliente_originale_id=cliente_originale_id,
            ubicazione_originale=ubicazione_originale,
            data_assegnazione_originale=data_assegnazione_originale,
            note=note or f'Assegnata al cliente ID: {cliente_id}'
        )
        db.session.add(movimento)
        
        return movimento
    
    def presta_temporaneamente(self, cliente_prestito_id, note=None):
        """Presta temporaneamente la macchina a un cliente (anche se attiva presso altro cliente)"""
        # SALVA STATO ORIGINALE COMPLETO
        stato_originale = self.stato
        cliente_originale_id = self.cliente_id
        ubicazione_originale = self.ubicazione
        data_assegnazione_originale = self.data_assegnazione
        data_vendita_originale = self.data_vendita
        prezzo_vendita_originale = self.prezzo_vendita
        prossima_manutenzione_originale = self.prossima_manutenzione
        
        # CAMBIA STATO A PRESTITO
        self.cliente_id = cliente_prestito_id
        self.stato = 'In prestito'
        self.ubicazione = f"Cliente ID: {cliente_prestito_id}"
        # Non cambiamo data_assegnazione per i prestiti temporanei
        
        # REGISTRA MOVIMENTO CON STATO ORIGINALE COMPLETO
        movimento = MovimentoMacchina(
            macchina_id=self.id,
            tipo_movimento='Assegnazione',
            stato_precedente=stato_originale,
            stato_nuovo='In prestito',
            cliente_id=cliente_prestito_id,  # Cliente del prestito
            # SALVA STATO ORIGINALE COMPLETO PER RIPRISTINO
            cliente_originale_id=cliente_originale_id,
            ubicazione_originale=ubicazione_originale,
            data_assegnazione_originale=data_assegnazione_originale,
            data_vendita_originale=data_vendita_originale,
            prezzo_vendita_originale=prezzo_vendita_originale,
            prossima_manutenzione_originale=prossima_manutenzione_originale,
            note=note or f'Prestito temporaneo al cliente ID: {cliente_prestito_id}'
        )
        db.session.add(movimento)
        
        return movimento
    
    def riporta_in_magazzino(self, note=None):
        """Riporta la macchina in magazzino"""
        stato_precedente = self.stato
        cliente_precedente = self.cliente_id
        
        self.cliente_id = None
        self.stato = 'Disponibile'
        self.data_assegnazione = None
        self.ubicazione = 'Magazzino'
        
        # Registra il movimento
        movimento = MovimentoMacchina(
            macchina_id=self.id,
            tipo_movimento='Rientro',
            stato_precedente=stato_precedente,
            stato_nuovo='Disponibile',
            cliente_id=cliente_precedente,
            note=note or 'Rientrata in magazzino'
        )
        db.session.add(movimento)
        
        return movimento
    
    def invia_in_riparazione(self, note=None):
        """Invia la macchina in riparazione"""
        # SALVA STATO ORIGINALE COMPLETO
        stato_originale = self.stato
        cliente_originale_id = self.cliente_id
        ubicazione_originale = self.ubicazione
        data_assegnazione_originale = self.data_assegnazione
        data_vendita_originale = self.data_vendita
        prezzo_vendita_originale = self.prezzo_vendita
        prossima_manutenzione_originale = self.prossima_manutenzione
        
        # CAMBIA STATO A RIPARAZIONE
        self.stato = 'In riparazione'
        self.ubicazione = 'Riparazione'
        # Non cambiamo cliente_id e data_assegnazione per le riparazioni
        
        # REGISTRA MOVIMENTO CON STATO ORIGINALE COMPLETO
        movimento = MovimentoMacchina(
            macchina_id=self.id,
            tipo_movimento='Riparazione',
            stato_precedente=stato_originale,
            stato_nuovo='In riparazione',
            # SALVA STATO ORIGINALE COMPLETO PER RIPRISTINO
            cliente_originale_id=cliente_originale_id,
            ubicazione_originale=ubicazione_originale,
            data_assegnazione_originale=data_assegnazione_originale,
            data_vendita_originale=data_vendita_originale,
            prezzo_vendita_originale=prezzo_vendita_originale,
            prossima_manutenzione_originale=prossima_manutenzione_originale,
            note=note or 'Inviata in riparazione'
        )
        db.session.add(movimento)
        
        return movimento
    
    def completa_riparazione(self, note=None):
        """Completa la riparazione e ripristina stato originale o riporta disponibile"""
        if not self.is_in_riparazione:
            raise ValueError("La macchina non è in riparazione")

        # Trova il movimento di riparazione più recente per ripristinare stato originale
        ultimo_movimento = MovimentoMacchina.query.filter_by(
            macchina_id=self.id,
            tipo_movimento='Riparazione'
        ).order_by(MovimentoMacchina.created_at.desc()).first()

        if ultimo_movimento:
            if ultimo_movimento.cliente_originale_id:
                # Ripristina stato originale completo
                self.cliente_id = ultimo_movimento.cliente_originale_id
                self.stato = ultimo_movimento.stato_precedente or 'Attiva'
                self.ubicazione = ultimo_movimento.ubicazione_originale or f"Cliente: ID {ultimo_movimento.cliente_originale_id}"
                self.data_assegnazione = ultimo_movimento.data_assegnazione_originale
                self.data_vendita = ultimo_movimento.data_vendita_originale
                self.prezzo_vendita = ultimo_movimento.prezzo_vendita_originale
                self.prossima_manutenzione = ultimo_movimento.prossima_manutenzione_originale

                stato_nuovo = ultimo_movimento.stato_precedente or 'Attiva'
                descrizione_note = f'Riparazione completata - ripristinato stato originale'
            elif ultimo_movimento.stato_precedente:
                # Nessun cliente originale ma abbiamo uno stato precedente
                if ultimo_movimento.stato_precedente == 'Attiva':
                    # Se era attiva, mantieni il cliente corrente e riporta attiva
                    self.stato = 'Attiva'
                    stato_nuovo = 'Attiva'
                    descrizione_note = 'Riparazione completata - ripristinato stato Attiva'
                else:
                    # Altrimenti riporta allo stato precedente
                    self.stato = ultimo_movimento.stato_precedente
                    stato_nuovo = ultimo_movimento.stato_precedente
                    descrizione_note = f'Riparazione completata - ripristinato stato {ultimo_movimento.stato_precedente}'
            else:
                # Nessun stato precedente trovato, riporta in magazzino
                self.stato = 'Disponibile'
                self.ubicazione = 'Magazzino'
                self.cliente_id = None
                stato_nuovo = 'Disponibile'
                descrizione_note = 'Riparazione completata - restituita in magazzino'
        else:
            # Nessun movimento di riparazione trovato, riporta in magazzino
            self.stato = 'Disponibile'
            self.ubicazione = 'Magazzino'
            self.cliente_id = None
            stato_nuovo = 'Disponibile'
            descrizione_note = 'Riparazione completata - restituita in magazzino'

        # Aggiorna prossima manutenzione se configurata e non già impostata
        if self.intervallo_manutenzione_giorni and not self.prossima_manutenzione:
            from datetime import timedelta
            self.prossima_manutenzione = datetime.now().date() + timedelta(days=self.intervallo_manutenzione_giorni)

        # Registra il movimento
        movimento = MovimentoMacchina(
            macchina_id=self.id,
            tipo_movimento='Fine Riparazione',
            stato_precedente='In riparazione',
            stato_nuovo=stato_nuovo,
            cliente_id=self.cliente_id,
            note=note or descrizione_note
        )
        db.session.add(movimento)

        return movimento
    
    def attiva(self, cliente_id=None, prezzo_vendita=None, note=None):
        """Marca la macchina come attiva (venduta e in uso presso cliente)"""
        stato_precedente = self.stato
        
        self.stato = 'Attiva'
        self.data_vendita = datetime.now().date()
        if cliente_id:
            self.cliente_id = cliente_id
            self.ubicazione = f"Attiva presso Cliente ID: {cliente_id}"
        else:
            self.ubicazione = 'Attiva'
        
        if prezzo_vendita:
            self.prezzo_vendita = prezzo_vendita
        
        # Registra il movimento
        movimento = MovimentoMacchina(
            macchina_id=self.id,
            tipo_movimento='Attivazione',
            stato_precedente=stato_precedente,
            stato_nuovo='Attiva',
            cliente_id=cliente_id,
            note=note or f'Attivata{" presso cliente ID: " + str(cliente_id) if cliente_id else ""}'
        )
        db.session.add(movimento)
        
        return movimento
    
    def ripristina_stato(self, nuovo_stato, cliente_id=None, note=None):
        """Ripristina la macchina a uno stato specifico (usato per chiusura ticket)"""
        stato_precedente = self.stato
        cliente_precedente = self.cliente_id
        
        self.stato = nuovo_stato
        
        # Gestisci assegnazione cliente
        if nuovo_stato == 'Disponibile':
            # Per stato Disponibile, rimuovi sempre il cliente
            self.cliente_id = None
            self.ubicazione = 'Magazzino'
            self.data_assegnazione = None
        elif cliente_id:
            # Per altri stati con cliente specificato
            self.cliente_id = cliente_id
            if nuovo_stato == 'Attiva':
                self.ubicazione = f"Attiva presso Cliente ID: {cliente_id}"
            elif nuovo_stato == 'In prestito':
                self.ubicazione = f"Cliente ID: {cliente_id}"
            else:
                self.ubicazione = f"Cliente ID: {cliente_id}"
        else:
            # Per altri stati senza cliente specificato
            self.cliente_id = None
            self.ubicazione = nuovo_stato
        
        # Determina il tipo di movimento basandosi sul nuovo stato
        if nuovo_stato == 'Disponibile':
            tipo_movimento = 'Rientro'
        elif nuovo_stato == 'Attiva':
            tipo_movimento = 'Attivazione'
        elif nuovo_stato == 'In prestito':
            tipo_movimento = 'Assegnazione'
        else:
            tipo_movimento = 'Ripristino'
        
        # Registra il movimento
        movimento = MovimentoMacchina(
            macchina_id=self.id,
            tipo_movimento=tipo_movimento,
            stato_precedente=stato_precedente,
            stato_nuovo=nuovo_stato,
            cliente_id=cliente_precedente,  # Usa il cliente precedente per tracciabilità
            note=note or f'Ripristino stato: {nuovo_stato}'
        )
        db.session.add(movimento)
        
        return movimento
    
    def __repr__(self):
        return f'<Macchina {self.codice}: {self.nome_completo}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'codice': self.codice,
            'modello': self.modello,
            'marca': self.marca,
            'numero_serie': self.numero_serie,
            'nome_completo': self.nome_completo,
            'tipo_macchina_id': self.tipo_macchina_id,
            'tipo_macchina_nome': self.tipo_macchina.nome if self.tipo_macchina else None,
            'stato': self.stato,
            'ubicazione': self.ubicazione,
            'cliente_id': self.cliente_id,
            'cliente_nome': self.cliente.ragione_sociale if self.cliente else None,
            'data_assegnazione': self.data_assegnazione.isoformat() if self.data_assegnazione else None,
            'anno_produzione': self.anno_produzione,
            'eta_anni': self.eta_anni,
            'peso': float(self.peso) if self.peso else None,
            'dimensioni': self.dimensioni,
            'alimentazione': self.alimentazione,
            'prezzo_acquisto': float(self.prezzo_acquisto) if self.prezzo_acquisto else None,
            'prezzo_vendita': float(self.prezzo_vendita) if self.prezzo_vendita else None,
            'fornitore': self.fornitore,
            'data_acquisto': self.data_acquisto.isoformat() if self.data_acquisto else None,
            'data_vendita': self.data_vendita.isoformat() if self.data_vendita else None,
            'data_scadenza_garanzia': self.data_scadenza_garanzia.isoformat() if self.data_scadenza_garanzia else None,
            'garanzia_scaduta': self.garanzia_scaduta,
            'prossima_manutenzione': self.prossima_manutenzione.isoformat() if self.prossima_manutenzione else None,
            'giorni_alla_manutenzione': self.giorni_alla_manutenzione,
            'necessita_manutenzione': self.necessita_manutenzione,
            'intervallo_manutenzione_giorni': self.intervallo_manutenzione_giorni,
            'note': self.note,
            'foto_filename': self.foto_filename,
            'manuale_filename': self.manuale_filename,
            'is_disponibile': self.is_disponibile,
            'is_in_prestito': self.is_in_prestito,
            'is_in_riparazione': self.is_in_riparazione,
            'is_attiva': self.is_attiva,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MovimentoMacchina(db.Model):
    __tablename__ = 'movimenti_macchine'
    
    id = db.Column(db.Integer, primary_key=True)
    macchina_id = db.Column(db.Integer, db.ForeignKey('macchine.id'), nullable=False, index=True)
    
    tipo_movimento = db.Column(db.String(30), nullable=False)  
    # Tipi: Assegnazione, Rientro, Riparazione, Fine Riparazione, Attivazione, Manutenzione, Altro
    
    stato_precedente = db.Column(db.String(30))
    stato_nuovo = db.Column(db.String(30))
    
    # Relazioni opzionali
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), index=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), index=True)
    foglio_id = db.Column(db.Integer, db.ForeignKey('fogli_tecnici.id'), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    # CAMPI PER SALVARE STATO ORIGINALE COMPLETO (per ripristino)
    cliente_originale_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), index=True)
    ubicazione_originale = db.Column(db.String(200))
    data_assegnazione_originale = db.Column(db.DateTime)
    data_vendita_originale = db.Column(db.Date)
    prezzo_vendita_originale = db.Column(db.Numeric(10, 2))
    prossima_manutenzione_originale = db.Column(db.Date)
    
    # Informazioni aggiuntive
    note = db.Column(db.Text)
    costo = db.Column(db.Numeric(10, 2))  # Per riparazioni, manutenzioni, etc.
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relazioni
    cliente = db.relationship('Cliente', foreign_keys=[cliente_id])
    cliente_originale = db.relationship('Cliente', foreign_keys=[cliente_originale_id])
    ticket = db.relationship('Ticket')
    foglio = db.relationship('FoglioTecnico')
    user = db.relationship('User')
    
    @property
    def descrizione_movimento(self):
        """Restituisce una descrizione leggibile del movimento"""
        descrizioni = {
            'Assegnazione': f'Assegnata{" al cliente " + self.cliente.ragione_sociale if self.cliente else ""}',
            'Rientro': 'Rientrata in magazzino',
            'Riparazione': 'Inviata in riparazione',
            'Fine Riparazione': 'Riparazione completata',
            'Attivazione': f'Attivata{" presso cliente " + self.cliente.ragione_sociale if self.cliente else ""}',
            'Manutenzione': 'Manutenzione eseguita',
            'Altro': self.note or 'Movimento generico'
        }
        return descrizioni.get(self.tipo_movimento, self.tipo_movimento)
    
    def __repr__(self):
        return f'<MovimentoMacchina {self.tipo_movimento}: {self.macchina.codice}>'
    
    def to_dict(self):
        """Serializzazione per JSON"""
        return {
            'id': self.id,
            'macchina_id': self.macchina_id,
            'macchina_codice': self.macchina.codice if self.macchina else None,
            'macchina_nome': self.macchina.nome_completo if self.macchina else None,
            'tipo_movimento': self.tipo_movimento,
            'descrizione_movimento': self.descrizione_movimento,
            'stato_precedente': self.stato_precedente,
            'stato_nuovo': self.stato_nuovo,
            'cliente_id': self.cliente_id,
            'cliente_nome': self.cliente.ragione_sociale if self.cliente else None,
            'ticket_id': self.ticket_id,
            'ticket_numero': self.ticket.numero_ticket if self.ticket else None,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'note': self.note,
            'costo': float(self.costo) if self.costo else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
