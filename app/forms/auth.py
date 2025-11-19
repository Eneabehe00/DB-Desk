from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ricordami')
    submit = SubmitField('Accedi')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=80, message='Il username deve essere tra 3 e 80 caratteri')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message='Inserisci un indirizzo email valido'),
        Length(max=120)
    ])
    
    first_name = StringField('Nome', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Il nome deve essere tra 2 e 100 caratteri')
    ])
    
    last_name = StringField('Cognome', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Il cognome deve essere tra 2 e 100 caratteri')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='La password deve essere di almeno 6 caratteri')
    ])
    
    password2 = PasswordField('Conferma Password', validators=[
        DataRequired(),
        EqualTo('password', message='Le password devono coincidere')
    ])
    
    submit = SubmitField('Registrati')
    
    def validate_username(self, username):
        """Valida che il username non sia già utilizzato"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Questo username è già utilizzato. Scegline un altro.')
    
    def validate_email(self, email):
        """Valida che l'email non sia già utilizzata"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Questa email è già registrata. Usa un\'altra email.')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Password Attuale', validators=[DataRequired()])
    
    new_password = PasswordField('Nuova Password', validators=[
        DataRequired(),
        Length(min=6, message='La password deve essere di almeno 6 caratteri')
    ])
    
    new_password2 = PasswordField('Conferma Nuova Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Le password devono coincidere')
    ])
    
    submit = SubmitField('Cambia Password')