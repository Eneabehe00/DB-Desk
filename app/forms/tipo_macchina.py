from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from app.models.macchina import TipoMacchina


class TipoMacchinaForm(FlaskForm):
    nome = StringField('Nome Tipo', validators=[
        DataRequired(message='Il nome del tipo è obbligatorio'),
        Length(min=1, max=100, message='Il nome deve essere tra 1 e 100 caratteri')
    ])

    descrizione = TextAreaField('Descrizione', validators=[
        Optional(),
        Length(max=500, message='La descrizione non può superare i 500 caratteri')
    ])

    submit = SubmitField('Salva')

    def __init__(self, *args, **kwargs):
        self.tipo_macchina = kwargs.pop('tipo_macchina', None)
        super().__init__(*args, **kwargs)

    def validate_nome(self, field):
        """Validazione nome univoco"""
        if self.tipo_macchina:
            # Modifica esistente - controlla che non esista un altro record con stesso nome
            existing = TipoMacchina.query.filter_by(nome=field.data).first()
            if existing and existing.id != self.tipo_macchina.id:
                raise ValidationError('Esiste già un tipo di macchina con questo nome')
        else:
            # Nuovo record - controlla che non esista
            if TipoMacchina.query.filter_by(nome=field.data).first():
                raise ValidationError('Esiste già un tipo di macchina con questo nome')
