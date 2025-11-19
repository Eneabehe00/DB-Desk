from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget
from app.models.department import Department
from app.models.user import User
from app.models.macchina import TipoMacchina


class MultiCheckboxField(SelectMultipleField):
    """Campo per selezione multipla con checkbox"""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class DepartmentForm(FlaskForm):
    """Form per la gestione dei reparti"""
    name = StringField(
        'Nome Identificativo',
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={'placeholder': 'es: it, maintenance, sales'}
    )
    
    display_name = StringField(
        'Nome Visualizzato',
        validators=[DataRequired(), Length(min=2, max=100)],
        render_kw={'placeholder': 'es: Reparto IT, Manutenzione, Vendite'}
    )
    
    description = TextAreaField(
        'Descrizione',
        validators=[Length(max=500)],
        render_kw={'rows': 3, 'placeholder': 'Descrizione del reparto...'}
    )
    
    color = StringField(
        'Colore',
        validators=[Length(max=7)],
        render_kw={'type': 'color', 'placeholder': '#007bff'}
    )
    
    manager_id = SelectField(
        'Manager',
        coerce=int,
        validators=[],
        render_kw={'class': 'form-select'}
    )
    
    tipi_macchine = MultiCheckboxField(
        'Tipi di Macchina Associati',
        coerce=int,
        validators=[],
        render_kw={'class': 'form-check-input'}
    )
    
    is_active = BooleanField(
        'Attivo',
        default=True,
        render_kw={'class': 'form-check-input'}
    )
    
    submit = SubmitField('Salva', render_kw={'class': 'btn btn-primary'})
    
    def __init__(self, department=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.department = department
        
        # Popola le scelte per il manager
        users = User.query.filter_by(is_active=True).order_by(User.first_name, User.last_name).all()
        self.manager_id.choices = [(0, 'Nessun manager')] + [(u.id, u.full_name) for u in users]
        
        # Popola le scelte per i tipi di macchina
        tipi = TipoMacchina.query.order_by(TipoMacchina.nome).all()
        self.tipi_macchine.choices = [(t.id, t.nome) for t in tipi]
        
        # Se stiamo modificando un reparto esistente, preseleziona i tipi associati
        if department and hasattr(department, 'tipi_macchine'):
            self.tipi_macchine.data = [t.id for t in department.tipi_macchine.all()]
    
    def validate_name(self, field):
        """Valida l'unicità del nome identificativo"""
        existing = Department.query.filter_by(name=field.data).first()
        if existing and (not self.department or existing.id != self.department.id):
            raise ValidationError('Un reparto con questo nome identificativo esiste già.')
    
    def validate_manager_id(self, field):
        """Valida che il manager esista"""
        if field.data and field.data != 0:
            manager = User.query.get(field.data)
            if not manager or not manager.is_active:
                raise ValidationError('Manager selezionato non valido.')