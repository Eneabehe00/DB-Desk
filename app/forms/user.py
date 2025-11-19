"""
Form per la gestione degli utenti
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models.user import User


class UserCreateForm(FlaskForm):
    """Form per creare un nuovo utente"""
    
    username = StringField('Username', validators=[
        DataRequired(message='Lo username è obbligatorio'),
        Length(min=3, max=80, message='Lo username deve essere tra 3 e 80 caratteri')
    ], description='Nome utente per il login (univoco)')
    
    email = StringField('Email', validators=[
        DataRequired(message='L\'email è obbligatoria'),
        Email(message='Inserisci un indirizzo email valido'),
        Length(max=120, message='L\'email non può superare i 120 caratteri')
    ], description='Indirizzo email dell\'utente')
    
    password = PasswordField('Password', validators=[
        DataRequired(message='La password è obbligatoria'),
        Length(min=6, message='La password deve essere di almeno 6 caratteri')
    ], description='Password per l\'accesso')
    
    password_confirm = PasswordField('Conferma Password', validators=[
        DataRequired(message='Conferma la password'),
        EqualTo('password', message='Le password non coincidono')
    ], description='Ripeti la password')
    
    first_name = StringField('Nome', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=2, max=100, message='Il nome deve essere tra 2 e 100 caratteri')
    ], description='Nome dell\'utente')
    
    last_name = StringField('Cognome', validators=[
        DataRequired(message='Il cognome è obbligatorio'),
        Length(min=2, max=100, message='Il cognome deve essere tra 2 e 100 caratteri')
    ], description='Cognome dell\'utente')
    
    role_id = SelectField('Ruolo', coerce=int, validators=[
        DataRequired(message='Seleziona un ruolo')
    ], description='Ruolo dell\'utente nel sistema')
    
    department_id = SelectField('Reparto', coerce=int, validators=[
        DataRequired(message='Seleziona un reparto')
    ], description='Reparto di appartenenza dell\'utente')
    
    is_active = BooleanField('Utente attivo', default=True, 
                           description='Se disabilitato, l\'utente non potrà accedere al sistema')
    
    submit = SubmitField('Crea Utente')
    
    def validate_username(self, field):
        """Valida che lo username sia unico"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Questo username è già in uso.')
    
    def validate_email(self, field):
        """Valida che l'email sia unica"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Questa email è già in uso.')
    
    def validate_role_id(self, field):
        """Valida che sia stato selezionato un ruolo"""
        if field.data == 0:
            raise ValidationError('Seleziona un ruolo valido.')
    
    def validate_department_id(self, field):
        """Valida che sia stato selezionato un reparto"""
        if field.data == 0:
            raise ValidationError('Seleziona un reparto valido.')


class UserEditForm(FlaskForm):
    """Form per modificare un utente esistente"""
    
    username = StringField('Username', validators=[
        DataRequired(message='Lo username è obbligatorio'),
        Length(min=3, max=80, message='Lo username deve essere tra 3 e 80 caratteri')
    ], description='Nome utente per il login (univoco)')
    
    email = StringField('Email', validators=[
        DataRequired(message='L\'email è obbligatoria'),
        Email(message='Inserisci un indirizzo email valido'),
        Length(max=120, message='L\'email non può superare i 120 caratteri')
    ], description='Indirizzo email dell\'utente')
    
    password = PasswordField('Nuova Password', validators=[
        Optional(),
        Length(min=6, message='La password deve essere di almeno 6 caratteri')
    ], description='Lascia vuoto per mantenere la password attuale')
    
    password_confirm = PasswordField('Conferma Nuova Password', validators=[
        EqualTo('password', message='Le password non coincidono')
    ], description='Ripeti la nuova password')
    
    first_name = StringField('Nome', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=2, max=100, message='Il nome deve essere tra 2 e 100 caratteri')
    ], description='Nome dell\'utente')
    
    last_name = StringField('Cognome', validators=[
        DataRequired(message='Il cognome è obbligatorio'),
        Length(min=2, max=100, message='Il cognome deve essere tra 2 e 100 caratteri')
    ], description='Cognome dell\'utente')
    
    role_id = SelectField('Ruolo', coerce=int, validators=[
        DataRequired(message='Seleziona un ruolo')
    ], description='Ruolo dell\'utente nel sistema')
    
    department_id = SelectField('Reparto', coerce=int, validators=[
        DataRequired(message='Seleziona un reparto')
    ], description='Reparto di appartenenza dell\'utente')
    
    is_active = BooleanField('Utente attivo', 
                           description='Se disabilitato, l\'utente non potrà accedere al sistema')
    
    submit = SubmitField('Aggiorna Utente')
    
    def __init__(self, user=None, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.user = user
    
    def validate_username(self, field):
        """Valida che lo username sia unico (escludendo l'utente corrente)"""
        query = User.query.filter_by(username=field.data)
        if self.user:
            query = query.filter(User.id != self.user.id)
        if query.first():
            raise ValidationError('Questo username è già in uso.')
    
    def validate_email(self, field):
        """Valida che l'email sia unica (escludendo l'utente corrente)"""
        query = User.query.filter_by(email=field.data)
        if self.user:
            query = query.filter(User.id != self.user.id)
        if query.first():
            raise ValidationError('Questa email è già in uso.')
    
    def validate_role_id(self, field):
        """Valida che sia stato selezionato un ruolo"""
        if field.data == 0:
            raise ValidationError('Seleziona un ruolo valido.')
    
    def validate_department_id(self, field):
        """Valida che sia stato selezionato un reparto"""
        if field.data == 0:
            raise ValidationError('Seleziona un reparto valido.')
