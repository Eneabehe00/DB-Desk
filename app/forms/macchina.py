from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from app.models.macchina import Macchina, TipoMacchina
from app.models.cliente import Cliente
from app.models.department import Department


def int_or_none(value):
    """Converte in int o None se stringa vuota"""
    if value == '' or value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


class MacchinaForm(FlaskForm):
    codice = StringField('Codice Macchina', validators=[
        DataRequired(message='Il codice macchina è obbligatorio'),
        Length(min=1, max=50, message='Il codice deve essere tra 1 e 50 caratteri')
    ])

    modello = StringField('Modello', validators=[
        DataRequired(message='Il modello è obbligatorio'),
        Length(min=1, max=200, message='Il modello deve essere tra 1 e 200 caratteri')
    ])

    marca = StringField('Marca', validators=[
        DataRequired(message='La marca è obbligatoria'),
        Length(min=1, max=100, message='La marca deve essere tra 1 e 100 caratteri')
    ])

    numero_serie = StringField('Numero di Serie', validators=[
        Optional(),
        Length(min=1, max=100, message='Il numero di serie deve essere tra 1 e 100 caratteri')
    ])

    tipo_macchina_id = SelectField('Tipo Macchina', coerce=int_or_none, validators=[
        DataRequired(message='Il tipo macchina è obbligatorio')
    ])

    stato = SelectField('Stato', choices=[
        ('Disponibile', 'Disponibile'),
        ('In prestito', 'In prestito'),
        ('In riparazione', 'In riparazione'),
        ('Attiva', 'Attiva'),
        ('Dismessa', 'Dismessa')
    ], validators=[DataRequired(message='Lo stato è obbligatorio')])

    ubicazione = StringField('Ubicazione', validators=[
        Optional(),
        Length(min=1, max=200, message='L\'ubicazione deve essere tra 1 e 200 caratteri')
    ])

    anno_produzione = IntegerField('Anno Produzione', validators=[
        Optional(),
        NumberRange(min=1900, max=2100, message='Anno produzione non valido')
    ])

    peso = DecimalField('Peso (kg)', places=2, validators=[
        Optional(),
        NumberRange(min=0, message='Il peso deve essere positivo')
    ])

    dimensioni = StringField('Dimensioni', validators=[
        Optional(),
        Length(min=1, max=100, message='Le dimensioni devono essere tra 1 e 100 caratteri')
    ])

    alimentazione = StringField('Alimentazione', validators=[
        Optional(),
        Length(min=1, max=50, message='L\'alimentazione deve essere tra 1 e 50 caratteri')
    ])

    prezzo_acquisto = DecimalField('Prezzo Acquisto (€)', places=2, validators=[
        Optional(),
        NumberRange(min=0, message='Il prezzo acquisto deve essere positivo')
    ])

    prezzo_vendita = DecimalField('Prezzo Vendita (€)', places=2, validators=[
        Optional(),
        NumberRange(min=0, message='Il prezzo vendita deve essere positivo')
    ])

    fornitore = StringField('Fornitore', validators=[
        Optional(),
        Length(min=1, max=100, message='Il fornitore deve essere tra 1 e 100 caratteri')
    ])

    data_acquisto = DateField('Data Acquisto', validators=[Optional()])

    data_scadenza_garanzia = DateField('Scadenza Garanzia', validators=[Optional()])

    intervallo_manutenzione_giorni = IntegerField('Intervallo Manutenzione (giorni)', validators=[
        Optional(),
        NumberRange(min=1, message='L\'intervallo manutenzione deve essere positivo')
    ])

    note = TextAreaField('Note', validators=[Optional()])

    department_id = SelectField('Reparto', coerce=int_or_none, validators=[
        DataRequired(message='Il reparto è obbligatorio')
    ])

    cliente_id = SelectField('Cliente Assegnato', coerce=int_or_none, validators=[Optional()],
        description='Assegna la macchina direttamente a un cliente (opzionale)')

    submit = SubmitField('Salva')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Popola le scelte per tipo_macchina_id
        self.tipo_macchina_id.choices = [('', 'Seleziona tipo macchina')] + [
            (t.id, t.nome) for t in TipoMacchina.query.order_by(TipoMacchina.nome).all()
        ]

        # Popola le scelte per department_id
        self.department_id.choices = [
            (d.id, d.display_name) for d in Department.query.order_by(Department.display_name).all()
        ]

        # Popola le scelte per cliente_id
        self.cliente_id.choices = [('', 'Nessun cliente assegnato')] + [
            (c.id, c.ragione_sociale) for c in Cliente.query.filter_by(is_active=True).order_by(Cliente.ragione_sociale).all()
        ]

    def validate_codice(self, field):
        """Validazione codice univoco"""
        if hasattr(self, 'macchina') and self.macchina:
            # Modifica esistente - controlla che non esista un altro record con stesso codice
            existing = Macchina.query.filter_by(codice=field.data).first()
            if existing and existing.id != self.macchina.id:
                raise ValidationError('Esiste già una macchina con questo codice')
        else:
            # Nuovo record - controlla che non esista
            if Macchina.query.filter_by(codice=field.data).first():
                raise ValidationError('Esiste già una macchina con questo codice')

    def validate_numero_serie(self, field):
        """Validazione numero serie univoco"""
        if not field.data:
            return

        if hasattr(self, 'macchina') and self.macchina:
            # Modifica esistente - controlla che non esista un altro record con stesso numero serie
            existing = Macchina.query.filter_by(numero_serie=field.data).first()
            if existing and existing.id != self.macchina.id:
                raise ValidationError('Esiste già una macchina con questo numero di serie')
        else:
            # Nuovo record - controlla che non esista
            if Macchina.query.filter_by(numero_serie=field.data).first():
                raise ValidationError('Esiste già una macchina con questo numero di serie')


class MacchinaFilterForm(FlaskForm):
    search = StringField('Ricerca', validators=[Optional()])

    tipo_macchina_id = SelectField('Tipo Macchina', coerce=int_or_none, choices=[('', 'Tutti i tipi')], validators=[Optional()])

    stato = SelectField('Stato', choices=[
        ('', 'Tutti gli stati'),
        ('Disponibile', 'Disponibile'),
        ('In prestito', 'In prestito'),
        ('In riparazione', 'In riparazione'),
        ('Attiva', 'Attiva'),
        ('Dismessa', 'Dismessa')
    ], validators=[Optional()])

    department_id = SelectField('Reparto', coerce=int_or_none, choices=[('', 'Tutti i reparti')], validators=[Optional()])

    cliente_id = SelectField('Cliente Assegnato', coerce=int_or_none, choices=[('', 'Tutti i clienti')], validators=[Optional()])

    submit = SubmitField('Filtra')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Popola le scelte per tipo_macchina_id
        tipi_macchina = TipoMacchina.query.order_by(TipoMacchina.nome).all()
        self.tipo_macchina_id.choices = [('', 'Tutti i tipi')] + [(t.id, t.nome) for t in tipi_macchina]

        # Popola le scelte per department_id
        departments = Department.query.order_by(Department.display_name).all()
        self.department_id.choices = [('', 'Tutti i reparti')] + [(d.id, d.display_name) for d in departments]

        # Popola le scelte per cliente_id
        clienti = Cliente.query.filter_by(is_active=True).order_by(Cliente.ragione_sociale).all()
        self.cliente_id.choices = [('', 'Tutti i clienti')] + [(c.id, c.ragione_sociale) for c in clienti]
