from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, ValidationError
from app.models.cliente import Cliente


class ClienteForm(FlaskForm):
    ragione_sociale = StringField('Ragione Sociale/Nome', validators=[
        DataRequired(message='La ragione sociale è obbligatoria')
    ])
    
    codice_fiscale = StringField('Codice Fiscale', validators=[
        Optional(),
        Length(min=16, max=16, message='Il codice fiscale deve essere di 16 caratteri'),
        Regexp(r'^[A-Z0-9]{16}$', message='Codice fiscale non valido')
    ])
    
    partita_iva = StringField('Partita IVA', validators=[
        Optional(),
        Length(min=11, max=11, message='La partita IVA deve essere di 11 caratteri'),
        Regexp(r'^\d{11}$', message='La partita IVA deve contenere solo numeri')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='L\'email è obbligatoria'),
        Email(message='Inserisci un indirizzo email valido')
    ])
    
    telefono = StringField('Telefono', validators=[Optional()])
    
    cellulare = StringField('Cellulare', validators=[Optional()])
    
    indirizzo = StringField('Indirizzo', validators=[Optional()])
    
    cap = StringField('CAP', validators=[
        Optional(),
        Length(min=5, max=5, message='Il CAP deve essere di 5 caratteri'),
        Regexp(r'^\d{5}$', message='Il CAP deve contenere solo numeri')
    ])
    
    citta = StringField('Città', validators=[Optional()])
    
    provincia = SelectField('Provincia', choices=[
        ('', 'Seleziona provincia'),
        ('AG', 'Agrigento'), ('AL', 'Alessandria'), ('AN', 'Ancona'), ('AO', 'Aosta'),
        ('AR', 'Arezzo'), ('AP', 'Ascoli Piceno'), ('AT', 'Asti'), ('AV', 'Avellino'),
        ('BA', 'Bari'), ('BT', 'Barletta-Andria-Trani'), ('BL', 'Belluno'), ('BN', 'Benevento'),
        ('BG', 'Bergamo'), ('BI', 'Biella'), ('BO', 'Bologna'), ('BZ', 'Bolzano'),
        ('BS', 'Brescia'), ('BR', 'Brindisi'), ('CA', 'Cagliari'), ('CL', 'Caltanissetta'),
        ('CB', 'Campobasso'), ('CI', 'Carbonia-Iglesias'), ('CE', 'Caserta'), ('CT', 'Catania'),
        ('CZ', 'Catanzaro'), ('CH', 'Chieti'), ('CO', 'Como'), ('CS', 'Cosenza'),
        ('CR', 'Cremona'), ('KR', 'Crotone'), ('CN', 'Cuneo'), ('EN', 'Enna'),
        ('FM', 'Fermo'), ('FE', 'Ferrara'), ('FI', 'Firenze'), ('FG', 'Foggia'),
        ('FC', 'Forlì-Cesena'), ('FR', 'Frosinone'), ('GE', 'Genova'), ('GO', 'Gorizia'),
        ('GR', 'Grosseto'), ('IM', 'Imperia'), ('IS', 'Isernia'), ('SP', 'La Spezia'),
        ('AQ', 'L\'Aquila'), ('LT', 'Latina'), ('LE', 'Lecce'), ('LC', 'Lecco'),
        ('LI', 'Livorno'), ('LO', 'Lodi'), ('LU', 'Lucca'), ('MC', 'Macerata'),
        ('MN', 'Mantova'), ('MS', 'Massa-Carrara'), ('MT', 'Matera'), ('VS', 'Medio Campidano'),
        ('ME', 'Messina'), ('MI', 'Milano'), ('MO', 'Modena'), ('MB', 'Monza e Brianza'),
        ('NA', 'Napoli'), ('NO', 'Novara'), ('NU', 'Nuoro'), ('OG', 'Ogliastra'),
        ('OT', 'Olbia-Tempio'), ('OR', 'Oristano'), ('PD', 'Padova'), ('PA', 'Palermo'),
        ('PR', 'Parma'), ('PV', 'Pavia'), ('PG', 'Perugia'), ('PU', 'Pesaro e Urbino'),
        ('PE', 'Pescara'), ('PC', 'Piacenza'), ('PI', 'Pisa'), ('PT', 'Pistoia'),
        ('PN', 'Pordenone'), ('PZ', 'Potenza'), ('PO', 'Prato'), ('RG', 'Ragusa'),
        ('RA', 'Ravenna'), ('RC', 'Reggio Calabria'), ('RE', 'Reggio Emilia'), ('RI', 'Rieti'),
        ('RN', 'Rimini'), ('RM', 'Roma'), ('RO', 'Rovigo'), ('SA', 'Salerno'),
        ('SS', 'Sassari'), ('SV', 'Savona'), ('SI', 'Siena'), ('SR', 'Siracusa'),
        ('SO', 'Sondrio'), ('TA', 'Taranto'), ('TE', 'Teramo'), ('TR', 'Terni'),
        ('TO', 'Torino'), ('TP', 'Trapani'), ('TN', 'Trento'), ('TV', 'Treviso'),
        ('TS', 'Trieste'), ('UD', 'Udine'), ('VA', 'Varese'), ('VE', 'Venezia'),
        ('VB', 'Verbano-Cusio-Ossola'), ('VC', 'Vercelli'), ('VR', 'Verona'), ('VV', 'Vibo Valentia'),
        ('VI', 'Vicenza'), ('VT', 'Viterbo')
    ])
    
    paese = StringField('Paese', validators=[Optional()], default='Italia')
    
    settore = StringField('Settore di Attività', validators=[Optional()])
    
    note = TextAreaField('Note', validators=[Optional()])
    
    is_active = BooleanField('Cliente Attivo', default=True)
    
    submit = SubmitField('Salva Cliente')
    
    def __init__(self, cliente=None, *args, **kwargs):
        super(ClienteForm, self).__init__(*args, **kwargs)
        self.cliente = cliente
    
    def validate_codice_fiscale(self, codice_fiscale):
        """Valida che il codice fiscale non sia già utilizzato"""
        if codice_fiscale.data:
            cliente = Cliente.query.filter_by(codice_fiscale=codice_fiscale.data.upper()).first()
            if cliente and (not self.cliente or cliente.id != self.cliente.id):
                raise ValidationError('Questo codice fiscale è già utilizzato.')
    
    def validate_partita_iva(self, partita_iva):
        """Valida che la partita IVA non sia già utilizzata"""
        if partita_iva.data:
            cliente = Cliente.query.filter_by(partita_iva=partita_iva.data).first()
            if cliente and (not self.cliente or cliente.id != self.cliente.id):
                raise ValidationError('Questa partita IVA è già utilizzata.')


class ClienteFilterForm(FlaskForm):
    """Form per filtri nella pagina lista clienti"""
    
    search = StringField('Ricerca', validators=[Optional()],
                        description='Cerca nella ragione sociale, email o città')
    
    settore = StringField('Settore', validators=[Optional()])
    
    provincia = SelectField('Provincia', choices=[
        ('', 'Tutte le province')
    ] + [
        ('AG', 'Agrigento'), ('AL', 'Alessandria'), ('AN', 'Ancona'), ('AO', 'Aosta'),
        ('AR', 'Arezzo'), ('AP', 'Ascoli Piceno'), ('AT', 'Asti'), ('AV', 'Avellino'),
        ('BA', 'Bari'), ('BT', 'Barletta-Andria-Trani'), ('BL', 'Belluno'), ('BN', 'Benevento'),
        ('BG', 'Bergamo'), ('BI', 'Biella'), ('BO', 'Bologna'), ('BZ', 'Bolzano'),
        ('BS', 'Brescia'), ('BR', 'Brindisi'), ('CA', 'Cagliari'), ('CL', 'Caltanissetta'),
        ('CB', 'Campobasso'), ('CI', 'Carbonia-Iglesias'), ('CE', 'Caserta'), ('CT', 'Catania'),
        ('CZ', 'Catanzaro'), ('CH', 'Chieti'), ('CO', 'Como'), ('CS', 'Cosenza'),
        ('CR', 'Cremona'), ('KR', 'Crotone'), ('CN', 'Cuneo'), ('EN', 'Enna'),
        ('FM', 'Fermo'), ('FE', 'Ferrara'), ('FI', 'Firenze'), ('FG', 'Foggia'),
        ('FC', 'Forlì-Cesena'), ('FR', 'Frosinone'), ('GE', 'Genova'), ('GO', 'Gorizia'),
        ('GR', 'Grosseto'), ('IM', 'Imperia'), ('IS', 'Isernia'), ('SP', 'La Spezia'),
        ('AQ', 'L\'Aquila'), ('LT', 'Latina'), ('LE', 'Lecce'), ('LC', 'Lecco'),
        ('LI', 'Livorno'), ('LO', 'Lodi'), ('LU', 'Lucca'), ('MC', 'Macerata'),
        ('MN', 'Mantova'), ('MS', 'Massa-Carrara'), ('MT', 'Matera'), ('VS', 'Medio Campidano'),
        ('ME', 'Messina'), ('MI', 'Milano'), ('MO', 'Modena'), ('MB', 'Monza e Brianza'),
        ('NA', 'Napoli'), ('NO', 'Novara'), ('NU', 'Nuoro'), ('OG', 'Ogliastra'),
        ('OT', 'Olbia-Tempio'), ('OR', 'Oristano'), ('PD', 'Padova'), ('PA', 'Palermo'),
        ('PR', 'Parma'), ('PV', 'Pavia'), ('PG', 'Perugia'), ('PU', 'Pesaro e Urbino'),
        ('PE', 'Pescara'), ('PC', 'Piacenza'), ('PI', 'Pisa'), ('PT', 'Pistoia'),
        ('PN', 'Pordenone'), ('PZ', 'Potenza'), ('PO', 'Prato'), ('RG', 'Ragusa'),
        ('RA', 'Ravenna'), ('RC', 'Reggio Calabria'), ('RE', 'Reggio Emilia'), ('RI', 'Rieti'),
        ('RN', 'Rimini'), ('RM', 'Roma'), ('RO', 'Rovigo'), ('SA', 'Salerno'),
        ('SS', 'Sassari'), ('SV', 'Savona'), ('SI', 'Siena'), ('SR', 'Siracusa'),
        ('SO', 'Sondrio'), ('TA', 'Taranto'), ('TE', 'Teramo'), ('TR', 'Terni'),
        ('TO', 'Torino'), ('TP', 'Trapani'), ('TN', 'Trento'), ('TV', 'Treviso'),
        ('TS', 'Trieste'), ('UD', 'Udine'), ('VA', 'Varese'), ('VE', 'Venezia'),
        ('VB', 'Verbano-Cusio-Ossola'), ('VC', 'Vercelli'), ('VR', 'Verona'), ('VV', 'Vibo Valentia'),
        ('VI', 'Vicenza'), ('VT', 'Viterbo')
    ])
    
    is_active = SelectField('Stato', choices=[
        ('', 'Tutti'),
        ('True', 'Attivi'),
        ('False', 'Non attivi')
    ])
    
    submit = SubmitField('Filtra')
    reset = SubmitField('Reset Filtri')