from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateTimeField, DecimalField, SubmitField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError, Email
from app.models.cliente import Cliente
from app.models.user import User


def safe_int_or_none(value):
    """Converte in int o None se stringa vuota o valore non valido"""
    if value == '' or value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def get_clienti():
    """Funzione per ottenere tutti i clienti attivi"""
    return Cliente.query.filter_by(is_active=True).order_by(Cliente.ragione_sociale).all()


def get_tecnici():
    """Funzione per ottenere tutti i tecnici attivi"""
    return User.query.filter_by(is_active=True).order_by(User.first_name, User.last_name).all()


def get_ricambi():
    """Funzione per ottenere tutti i ricambi disponibili"""
    from app.models.ricambio import Ricambio
    return Ricambio.query.order_by(Ricambio.codice).all()


class FoglioTecnicoStep1Form(FlaskForm):
    """Step 1: Informazioni Base del Cliente e Intervento"""
    
    cliente = HiddenField('Cliente', validators=[DataRequired(message='Seleziona un cliente')])
    
    cliente_search = StringField('Cerca Cliente', validators=[Optional()],
        description='Digita per cercare il cliente')
    
    titolo = StringField('Titolo Intervento', validators=[
        DataRequired(message='Il titolo è obbligatorio'),
        Length(max=200, message='Massimo 200 caratteri')
    ], description='Descrivi brevemente il tipo di intervento')
    
    descrizione = TextAreaField('Descrizione Dettagliata', validators=[
        DataRequired(message='La descrizione è obbligatoria'),
        Length(min=10, message='Minimo 10 caratteri')
    ], description='Descrivi dettagliatamente il lavoro da svolgere o svolto')
    
    data_intervento = DateTimeField('Data e Ora Intervento', 
        validators=[DataRequired(message='Data intervento obbligatoria')],
        format='%Y-%m-%dT%H:%M')
    
    indirizzo_intervento = StringField('Indirizzo Intervento', validators=[
        Optional(),
        Length(max=200, message='Massimo 200 caratteri')
    ], description='Se diverso dall\'indirizzo del cliente')
    
    submit = SubmitField('Avanti →')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def validate_cliente(self, field):
        """Validazione personalizzata per il campo cliente"""
        if field.data:
            from app.models.cliente import Cliente
            cliente = Cliente.query.get(field.data)
            if not cliente:
                raise ValidationError('Cliente selezionato non valido')


class FoglioTecnicoStep2Form(FlaskForm):
    """Step 2: Dettagli Tecnici dell'Intervento"""
    
    macchine = SelectMultipleField('Macchine Coinvolte', choices=[], coerce=safe_int_or_none,
        validators=[Optional()], validate_choice=False,
        description='Seleziona le macchine su cui si è intervenuti')
    
    tipo_operazione_macchine = SelectField('Tipo Operazione Macchine', choices=[
        ('', 'Nessuna operazione'),
        ('riparazione_cliente', 'Riparazione presso cliente'),
        ('prestito_semplice', 'Prestito d\'uso semplice'),
        ('riparazione_sede_con_prestito', 'Riparazione in sede con prestito'),
        ('riparazione_sede', 'Riparazione in sede (solo ritiro)'),
        ('consegna_riparata', 'Consegna macchina riparata'),
        ('ritiro_riparazione', 'Ritiro per riparazione'),
        ('rientro_prestito', 'Rientro da prestito'),
        ('rientro_riparazione', 'Rientro da riparazione'),
        ('altro', 'Altro')
    ], validators=[Optional()], 
    description='Specifica che tipo di operazione stai effettuando sulle macchine')
    
    # Campo per macchine sostitutive (quando si fa riparazione con prestito)
    macchine_sostitutive = SelectMultipleField('Macchine Sostitutive', choices=[], coerce=safe_int_or_none,
        validators=[Optional()], validate_choice=False, 
        description='Seleziona le macchine da dare in prestito durante la riparazione (solo per "Riparazione in sede con prestito")')
    
    durata_intervento = IntegerField('Durata Intervento (minuti)', validators=[
        Optional(),
        NumberRange(min=1, max=1440, message='Da 1 a 1440 minuti (24 ore)')
    ])
    
    km_percorsi = IntegerField('Kilometri Percorsi', validators=[
        Optional(),
        NumberRange(min=0, max=9999, message='Da 0 a 9999 km')
    ])
    
    submit = SubmitField('Avanti →')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le macchine verranno caricate dinamicamente via JavaScript basandosi sul cliente
        self.macchine.choices = []
        # Le macchine sostitutive verranno caricate dinamicamente (macchine disponibili)
        self.macchine_sostitutive.choices = []


class FoglioTecnicoStep3Form(FlaskForm):
    """Step 3: Ricambi Utilizzati"""
    
    ricambi_utilizzati = SelectMultipleField('Ricambi Utilizzati', choices=[], coerce=safe_int_or_none,
        validators=[Optional()], validate_choice=False,
        description='Seleziona i ricambi utilizzati durante l\'intervento')
    
    note_aggiuntive = TextAreaField('Note Aggiuntive', validators=[Optional()],
        description='Eventuali note tecniche, osservazioni o raccomandazioni')
    
    submit = SubmitField('Avanti →')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Non popoliamo le choices del SelectMultipleField per migliorare le performance
        self.ricambi_utilizzati.choices = []
        
        # Carica i dati ricambi solo per JavaScript (limitato ai primi 1000 per performance)
        from app.models.ricambio import Ricambio
        ricambi = Ricambio.query.order_by(Ricambio.codice).limit(1000).all()
        self.ricambi_data = [
            {
                'id': ricambio.id,
                'code': ricambio.codice,
                'description': ricambio.descrizione,
                'stock': ricambio.quantita_disponibile,
                'stock_status': ricambio.stato_disponibilita
            }
            for ricambio in ricambi
        ]


class FoglioTecnicoStep4Form(FlaskForm):
    """Step 4: Informazioni Commerciali"""
    
    modalita_pagamento = SelectField('Modalità di Pagamento', choices=[
        ('', 'Seleziona modalità...'),
        ('Contanti', 'Contanti'),
        ('Bonifico bancario', 'Bonifico bancario'),
        ('Assegno', 'Assegno'),
        ('Carta di credito/debito', 'Carta di credito/debito'),
        ('PayPal', 'PayPal'),
        ('Fatturazione differita', 'Fatturazione differita'),
        ('Non specificato', 'Non specificato')
    ], validators=[Optional()])
    
    importo_intervento = DecimalField('Importo Intervento (€)', validators=[
        Optional(),
        NumberRange(min=0, max=999999.99, message='Importo non valido')
    ], places=2)
    
    submit = SubmitField('Avanti →')


class FoglioTecnicoStep5Form(FlaskForm):
    """Step 5: Raccolta Firme"""
    
    nome_firmatario_cliente = StringField('Nome Firmatario Cliente', validators=[
        DataRequired(message='Nome firmatario obbligatorio'),
        Length(max=100, message='Massimo 100 caratteri')
    ])
    
    # Campi nascosti per le firme (verranno popolati dal JavaScript)
    firma_tecnico_data = HiddenField('Firma Tecnico')
    firma_cliente_data = HiddenField('Firma Cliente')
    
    submit = SubmitField('Salva Firme')


class FoglioTecnicoFinalizeForm(FlaskForm):
    """Form per finalizzazione del foglio tecnico"""
    
    azione = SelectField('Azione da Eseguire', choices=[
        ('salva_bozza', 'Salva come Bozza'),
        ('genera_pdf', 'Genera PDF'),
        ('invia_email', 'Invia per Email'),
        ('genera_e_invia', 'Genera PDF e Invia per Email')
    ], validators=[DataRequired()])
    
    email_destinatario = StringField('Email Destinatario', validators=[
        Optional(),
        Email(message='Formato email non valido')
    ], description='Email per l\'invio (se non specificata, userà quella del cliente)')
    
    note_finali = TextAreaField('Note Finali', validators=[Optional()],
        description='Note aggiuntive da includere nell\'email')
    
    submit = SubmitField('Finalizza Foglio')
    
    def validate_email_destinatario(self, field):
        """Validazione email quando l'azione richiede invio"""
        if self.azione.data in ['invia_email', 'genera_e_invia']:
            if not field.data:
                raise ValidationError('Email destinatario obbligatoria per l\'invio')


class FoglioTecnicoFilterForm(FlaskForm):
    """Form per filtri nella pagina lista fogli tecnici"""
    
    search = StringField('Ricerca', validators=[Optional()],
                        description='Cerca nel titolo, descrizione o numero foglio')

    cliente = SelectField('Cliente', choices=[], coerce=safe_int_or_none)
    
    stato = SelectField('Stato', choices=[
        ('', 'Tutti gli stati'),
        ('Bozza', 'Bozza'),
        ('In compilazione', 'In compilazione'),
        ('In attesa firme', 'In attesa firme'),
        ('Completato', 'Completato'),
        ('Inviato', 'Inviato'),
        ('Archiviato', 'Archiviato')
    ])
    
    categoria = SelectField('Categoria', choices=[
        ('', 'Tutte le categorie'),
        ('Intervento', 'Intervento Generico'),
        ('Riparazione', 'Riparazione'),
        ('Manutenzione', 'Manutenzione Preventiva'),
        ('Installazione', 'Installazione'),
        ('Consulenza', 'Consulenza Tecnica'),
        ('Formazione', 'Formazione'),
        ('Sopralluogo', 'Sopralluogo'),
        ('Collaudo', 'Collaudo'),
        ('Altro', 'Altro')
    ])

    tecnico = SelectField('Tecnico', choices=[], coerce=safe_int_or_none)
    
    modalita_pagamento = SelectField('Modalità Pagamento', choices=[
        ('', 'Tutte le modalità'),
        ('Contanti', 'Contanti'),
        ('Bonifico bancario', 'Bonifico bancario'),
        ('Assegno', 'Assegno'),
        ('Carta di credito/debito', 'Carta di credito/debito'),
        ('PayPal', 'PayPal'),
        ('Fatturazione differita', 'Fatturazione differita'),
        ('Non specificato', 'Non specificato')
    ])

    submit = SubmitField('Filtra')
    reset = SubmitField('Reset Filtri')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Popola le scelte per i clienti
        self.cliente.choices = [(0, 'Tutti i clienti')] + [
            (cliente.id, cliente.ragione_sociale)
            for cliente in get_clienti()
        ]
        
        # Popola le scelte per i tecnici
        self.tecnico.choices = [(0, 'Tutti i tecnici')] + [
            (user.id, f"{user.first_name} {user.last_name}")
            for user in get_tecnici()
        ]


# Form per la modifica rapida (editing di fogli già esistenti)
class FoglioTecnicoQuickEditForm(FlaskForm):
    """Form semplificata per editing rapido di fogli esistenti"""
    
    titolo = StringField('Titolo', validators=[DataRequired()])
    descrizione = TextAreaField('Descrizione', validators=[DataRequired()])
    stato = SelectField('Stato', choices=[
        ('Bozza', 'Bozza'),
        ('In compilazione', 'In compilazione'),
        ('In attesa firme', 'In attesa firme'),
        ('Completato', 'Completato'),
        ('Inviato', 'Inviato'),
        ('Archiviato', 'Archiviato')
    ], validators=[DataRequired()])
    
    note_aggiuntive = TextAreaField('Note Aggiuntive', validators=[Optional()])
    
    submit = SubmitField('Aggiorna Foglio')
