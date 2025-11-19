from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateTimeField, SubmitField, FieldList, FormField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
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


def get_users():
    """Funzione per ottenere tutti gli utenti attivi (limitato per performance)"""
    return User.query.filter_by(is_active=True).order_by(User.first_name, User.last_name).limit(100).all()


def get_ricambi():
    """Funzione per ottenere tutti i ricambi disponibili"""
    from app.models.ricambio import Ricambio
    return Ricambio.query.order_by(Ricambio.codice).all()


class TicketForm(FlaskForm):
    titolo = StringField('Titolo', validators=[
        DataRequired(message='Il titolo è obbligatorio')
    ])
    
    descrizione = TextAreaField('Descrizione', validators=[
        DataRequired(message='La descrizione è obbligatoria')
    ])
    
    cliente = SelectField('Cliente', choices=[], coerce=safe_int_or_none,
        validators=[DataRequired(message='Seleziona un cliente')])
    
    # Campo alternativo per ricerca cliente
    cliente_search = StringField('Cerca Cliente', validators=[Optional()])
    
    categoria = SelectField('Categoria', choices=[
        ('Generale', 'Generale'),
        ('Bug', 'Bug/Errore'),
        ('Feature', 'Nuova Funzionalità'),
        ('Supporto', 'Supporto'),
        ('Manutenzione', 'Manutenzione'),
        ('Consulenza', 'Consulenza'),
        ('Installazione', 'Installazione'),
        ('Formazione', 'Formazione')
    ], validators=[DataRequired()])
    
    priorita = SelectField('Priorità', choices=[
        ('Bassa', 'Bassa'),
        ('Media', 'Media'),
        ('Alta', 'Alta'),
        ('Critica', 'Critica')
    ], validators=[DataRequired()])
    
    stato = SelectField('Stato', choices=[
        ('Aperto', 'Aperto'),
        ('In Lavorazione', 'In Lavorazione'),
        ('In Attesa Cliente', 'In Attesa Cliente'),
        ('Risolto', 'Risolto'),
        ('Chiuso', 'Chiuso')
    ], validators=[DataRequired()])

    assigned_to = SelectField('Assegnato a', choices=[], coerce=safe_int_or_none)
    
    due_date = DateTimeField('Scadenza', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    
    tags = StringField('Tag', validators=[Optional()], description='Separa i tag con virgole')
    
    tempo_stimato = IntegerField('Tempo Stimato (minuti)', validators=[Optional()])
    
    note_interne = TextAreaField('Note Interne', validators=[Optional()])
    
    # Campo per macchine collegate (supporta selezione multipla)
    macchine = SelectMultipleField('Macchine Collegate', choices=[], coerce=safe_int_or_none,
        validators=[Optional()], validate_choice=False, description='Seleziona le macchine coinvolte in questo ticket (opzionale)')
    
    # Campo per il tipo di operazione sulle macchine
    tipo_operazione_macchine = SelectField('Tipo Operazione Macchine', choices=[
        ('', 'Nessuna operazione'),
        ('riparazione_cliente', 'Riparazione presso cliente'),
        ('prestito_semplice', 'Prestito d\'uso semplice'),
        ('riparazione_sede_con_prestito', 'Riparazione in sede con prestito'),
        ('riparazione_sede', 'Riparazione in sede (solo ritiro)')
    ], validators=[Optional()], description='Specifica che tipo di operazione stai effettuando sulle macchine')
    
    # Campo per macchine sostitutive (quando si fa riparazione con prestito)
    macchine_sostitutive = SelectMultipleField('Macchine Sostitutive', choices=[], coerce=safe_int_or_none,
        validators=[Optional()], validate_choice=False, description='Seleziona le macchine da dare in prestito durante la riparazione (solo per "Riparazione in sede con prestito")')

    # Campo per ricambi necessari
    ricambi_necessari = SelectMultipleField('Ricambi Necessari', choices=[], coerce=safe_int_or_none,
        validators=[Optional()], validate_choice=False, description='Seleziona i ricambi che potrebbero essere necessari per questo ticket')

    submit = SubmitField('Salva Ticket')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Non popoliamo le scelte per i clienti dato che usiamo autocomplete
        # Questo migliora significativamente le performance
        self.cliente.choices = [(0, 'Seleziona cliente...')]
        
        # Popola le scelte per gli utenti assegnati
        self.assigned_to.choices = [(0, 'Non assegnato')] + [
            (user.id, user.full_name)
            for user in get_users()
        ]
        
        # Popola le scelte per le macchine (inizialmente vuote, verranno caricate dinamicamente dopo selezione cliente)
        self.macchine.choices = []

        # Popola le scelte per le macchine sostitutive (inizialmente vuote, verranno caricate dinamicamente)
        self.macchine_sostitutive.choices = []

        # Popola le scelte per i ricambi solo se necessario (per JavaScript)
        # Non popoliamo le choices del SelectMultipleField per migliorare le performance
        self.ricambi_necessari.choices = []
        
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
    
    def validate_cliente(self, field):
        """Validazione personalizzata per il campo cliente"""
        if field.data and field.data != 0:
            from app.models.cliente import Cliente
            cliente = Cliente.query.get(field.data)
            if not cliente:
                raise ValidationError('Cliente selezionato non valido')
    
    def validate_macchine(self, field):
        """Validazione personalizzata per il campo macchine"""
        if field.data:
            from app.models.macchina import Macchina
            for macchina_id in field.data:
                macchina = Macchina.query.get(macchina_id)
                if not macchina:
                    raise ValidationError(f'Macchina con ID {macchina_id} non trovata')
                # Verifica che la macchina appartenga al cliente selezionato
                if self.cliente.data and macchina.cliente_id != self.cliente.data:
                    raise ValidationError(f'La macchina {macchina.codice} non appartiene al cliente selezionato')
    
    def validate_macchine_sostitutive(self, field):
        """Validazione personalizzata per il campo macchine sostitutive"""
        if field.data:
            from app.models.macchina import Macchina
            for macchina_id in field.data:
                macchina = Macchina.query.get(macchina_id)
                if not macchina:
                    raise ValidationError(f'Macchina sostitutiva con ID {macchina_id} non trovata')
                # Verifica che la macchina sia disponibile o attiva (per prestiti d'uso)
                if macchina.stato not in ['Disponibile', 'Attiva']:
                    raise ValidationError(f'La macchina {macchina.codice} non è disponibile per il prestito (stato: {macchina.stato})')
                # Verifica che la macchina non appartenga al cliente selezionato
                if self.cliente.data and macchina.cliente_id == self.cliente.data:
                    raise ValidationError(f'La macchina {macchina.codice} appartiene al cliente selezionato e non può essere data in prestito')


class SubtaskForm(FlaskForm):
    title = StringField('Sotto-attività', validators=[Optional()])
    is_done = BooleanField('Completata')


class AttachmentUploadForm(FlaskForm):
    # placeholder per validazioni lato server se necessario (gestito via route con request.files)
    submit = SubmitField('Carica Allegato')


class TicketFilterForm(FlaskForm):
    """Form per filtri nella pagina lista ticket"""
    
    search = StringField('Ricerca', validators=[Optional()],
                        description='Cerca nel titolo, descrizione o numero ticket')

    cliente = SelectField('Cliente', choices=[], coerce=safe_int_or_none)
    
    stato = SelectField('Stato', choices=[
        ('', 'Tutti gli stati'),
        ('Aperto', 'Aperti (tutti gli stati attivi)'),
        ('Chiuso', 'Chiusi'),
        ('---', '--- Stati Specifici ---'),
        ('Aperto_exact', 'Solo Aperti'),
        ('In Lavorazione', 'In Lavorazione'),
        ('In Attesa Cliente', 'In Attesa Cliente'),
        ('Risolto', 'Risolto')
    ])
    
    priorita = SelectField('Priorità', choices=[
        ('', 'Tutte le priorità'),
        ('Bassa', 'Bassa'),
        ('Media', 'Media'),
        ('Alta', 'Alta'),
        ('Critica', 'Critica')
    ])
    
    categoria = SelectField('Categoria', choices=[
        ('', 'Tutte le categorie'),
        ('Generale', 'Generale'),
        ('Bug', 'Bug/Errore'),
        ('Feature', 'Nuova Funzionalità'),
        ('Supporto', 'Supporto'),
        ('Manutenzione', 'Manutenzione'),
        ('Consulenza', 'Consulenza'),
        ('Installazione', 'Installazione'),
        ('Formazione', 'Formazione')
    ])

    assigned_to = SelectField('Assegnato a', choices=[], coerce=safe_int_or_none)

    submit = SubmitField('Filtra')
    reset = SubmitField('Reset Filtri')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Popola le scelte per i clienti
        self.cliente.choices = [(0, 'Tutti i clienti')] + [
            (cliente.id, cliente.ragione_sociale)
            for cliente in get_clienti()
        ]
        
        # Popola le scelte per gli utenti assegnati
        self.assigned_to.choices = [(0, 'Tutti gli utenti')] + [
            (user.id, user.full_name)
            for user in get_users()
        ]