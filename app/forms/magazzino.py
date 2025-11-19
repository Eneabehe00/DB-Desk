from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, DecimalField, SelectField, DateTimeField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from wtforms.widgets import TextArea
from app.models.ricambio import Ricambio
from app.models.ticket import Ticket
from app.models.department import Department
from app.utils.permissions import get_accessible_departments
from datetime import datetime


class RicambioForm(FlaskForm):
    """Form per creazione/modifica ricambio"""
    
    codice = StringField('Codice Ricambio', validators=[
        DataRequired(message='Il codice è obbligatorio')
    ], render_kw={'placeholder': 'Es: DIBAL-LCD-001'})
    
    descrizione = StringField('Descrizione', validators=[
        DataRequired(message='La descrizione è obbligatoria')
    ], render_kw={'placeholder': 'Es: Display LCD principale Dibal 1200'})
    
    quantita_disponibile = IntegerField('Quantità Disponibile', validators=[
        DataRequired(message='La quantità è obbligatoria'),
        NumberRange(min=0, message='La quantità non può essere negativa')
    ], default=0)
    
    quantita_minima = IntegerField('Quantità Minima (Sotto Scorta)', validators=[
        Optional(),
        NumberRange(min=0, message='La quantità minima non può essere negativa')
    ], default=0)
    
    ubicazione = StringField('Ubicazione', validators=[Optional()], render_kw={'placeholder': 'Es: Scaffale A-1-2'})
    
    note = TextAreaField('Note', validators=[Optional()], render_kw={'rows': 3, 'placeholder': 'Note aggiuntive sul ricambio...'})
    
    foto = FileField('Foto Ricambio', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo immagini JPG, PNG o GIF')
    ])
    
    prezzo_unitario = DecimalField('Prezzo Unitario (€)', validators=[
        Optional(),
        NumberRange(min=0, message='Il prezzo non può essere negativo')
    ], places=2, render_kw={'step': '0.01', 'placeholder': '0.00'})
    
    fornitore = StringField('Fornitore', validators=[Optional()], render_kw={'placeholder': 'Es: Dibal SpA'})

    department_id = SelectField('Reparto', coerce=int, validators=[
        DataRequired(message='Il reparto è obbligatorio')
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Popola le scelte per department_id basato sui permessi dell'utente
        accessible_departments = get_accessible_departments()
        self.department_id.choices = [
            (d.id, d.display_name) for d in accessible_departments
        ]

    def validate_codice(self, field):
        """Valida che il codice sia univoco"""
        # Se stiamo modificando un ricambio esistente, escludiamo l'ID corrente
        ricambio_id = getattr(self, '_ricambio_id', None)
        
        query = Ricambio.query.filter_by(codice=field.data)
        if ricambio_id:
            query = query.filter(Ricambio.id != ricambio_id)
        
        if query.first():
            raise ValidationError('Questo codice è già utilizzato da un altro ricambio')


class MovimentoMagazzinoForm(FlaskForm):
    """Form per registrare movimenti di magazzino"""
    
    ricambio_id = SelectField('Ricambio', validators=[
        DataRequired(message='Seleziona un ricambio')
    ], coerce=int, choices=[])
    
    tipo_movimento = SelectField('Tipo Movimento', validators=[
        DataRequired(message='Seleziona il tipo di movimento')
    ], choices=[
        ('Carico', 'Carico (+)'),
        ('Scarico', 'Scarico (-)'),
        ('Rettifica', 'Rettifica')
    ])
    
    quantita = IntegerField('Quantità', validators=[
        DataRequired(message='La quantità è obbligatoria'),
        NumberRange(min=1, message='La quantità deve essere maggiore di 0')
    ])
    
    motivo = StringField('Motivo', validators=[
        DataRequired(message='Il motivo è obbligatorio')
    ], render_kw={'placeholder': 'Es: Nuovo arrivo fornitore, Utilizzo per riparazione...'})
    
    ticket_id = SelectField('Ticket Collegato', validators=[Optional()], 
                           coerce=int, choices=[], render_kw={'class': 'select2'})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Popola le scelte per i ricambi
        self.ricambio_id.choices = [(0, 'Seleziona ricambio...')] + [
            (r.id, f"{r.codice} - {r.descrizione[:50]}{'...' if len(r.descrizione) > 50 else ''}")
            for r in Ricambio.query.order_by(Ricambio.codice).all()
        ]
        
        # Popola le scelte per i ticket (solo quelli aperti)
        self.ticket_id.choices = [(0, 'Nessun ticket collegato')] + [
            (t.id, f"{t.numero_ticket} - {t.titolo[:30]}{'...' if len(t.titolo) > 30 else ''}")
            for t in Ticket.query.filter(Ticket.stato.in_(Ticket.get_stati_aperti()))
                                 .order_by(Ticket.created_at.desc()).limit(50).all()
        ]


class PrenotazioneRicambioForm(FlaskForm):
    """Form per prenotare ricambi"""
    
    ricambio_id = HiddenField('Ricambio ID', validators=[DataRequired()])
    
    quantita = IntegerField('Quantità da Prenotare', validators=[
        DataRequired(message='La quantità è obbligatoria'),
        NumberRange(min=1, message='La quantità deve essere maggiore di 0')
    ])
    
    ticket_id = SelectField('Ticket', validators=[
        DataRequired(message='Seleziona un ticket')
    ], coerce=int, choices=[])
    
    data_scadenza = DateTimeField('Data Scadenza Prenotazione', validators=[
        Optional()
    ], format='%Y-%m-%dT%H:%M', render_kw={'type': 'datetime-local'})
    
    note = TextAreaField('Note', validators=[Optional()], render_kw={'rows': 2, 'placeholder': 'Note sulla prenotazione...'})
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Popola le scelte per i ticket (solo quelli aperti)
        self.ticket_id.choices = [(0, 'Seleziona ticket...')] + [
            (t.id, f"{t.numero_ticket} - {t.titolo[:40]}{'...' if len(t.titolo) > 40 else ''}")
            for t in Ticket.query.filter(Ticket.stato.in_(Ticket.get_stati_aperti()))
                                 .order_by(Ticket.created_at.desc()).limit(100).all()
        ]
    
    def validate_quantita(self, field):
        """Valida che la quantità sia disponibile"""
        if self.ricambio_id.data:
            try:
                ricambio_id = int(self.ricambio_id.data)
                ricambio = Ricambio.query.get(ricambio_id)
                if ricambio and field.data > ricambio.quantita_effettiva:
                    raise ValidationError(f'Quantità non disponibile. Disponibile: {ricambio.quantita_effettiva}')
            except (ValueError, TypeError):
                pass
    
    def validate_data_scadenza(self, field):
        """Valida che la data di scadenza sia futura"""
        if field.data and field.data <= datetime.now():
            raise ValidationError('La data di scadenza deve essere futura')


class ScaricoRicambioForm(FlaskForm):
    """Form per scaricare ricambi dal magazzino"""
    
    ricambio_id = HiddenField('Ricambio ID', validators=[DataRequired()])
    
    quantita = IntegerField('Quantità da Scaricare', validators=[
        DataRequired(message='La quantità è obbligatoria'),
        NumberRange(min=1, message='La quantità deve essere maggiore di 0')
    ])
    
    motivo = StringField('Motivo Scarico', validators=[
        DataRequired(message='Il motivo è obbligatorio')
    ], render_kw={'placeholder': 'Es: Utilizzo per riparazione, Pezzo difettoso...'})
    
    ticket_id = SelectField('Ticket Collegato', validators=[Optional()], 
                           coerce=int, choices=[])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Popola le scelte per i ticket (solo quelli aperti)
        self.ticket_id.choices = [(0, 'Nessun ticket collegato')] + [
            (t.id, f"{t.numero_ticket} - {t.titolo[:40]}{'...' if len(t.titolo) > 40 else ''}")
            for t in Ticket.query.filter(Ticket.stato.in_(Ticket.get_stati_aperti()))
                                 .order_by(Ticket.created_at.desc()).limit(50).all()
        ]
    
    def validate_quantita(self, field):
        """Valida che la quantità sia disponibile"""
        if self.ricambio_id.data:
            try:
                ricambio_id = int(self.ricambio_id.data)
                ricambio = Ricambio.query.get(ricambio_id)
                if ricambio and field.data > ricambio.quantita_disponibile:
                    raise ValidationError(f'Quantità non disponibile. Disponibile: {ricambio.quantita_disponibile}')
            except (ValueError, TypeError):
                pass


class RicercaRicambiForm(FlaskForm):
    """Form per la ricerca ricambi"""
    
    search = StringField('Cerca per codice o descrizione', validators=[Optional()], render_kw={'placeholder': 'Inserisci codice o descrizione...', 'class': 'form-control'})
    
    filtro_stato = SelectField('Filtro Stato', validators=[Optional()], choices=[
        ('', 'Tutti'),
        ('disponibili', 'Solo Disponibili'),
        ('prenotati', 'Con Prenotazioni'),
        ('sotto_scorta', 'Sotto Scorta'),
        ('esauriti', 'Esauriti')
    ], render_kw={'class': 'form-select'})
    
    ubicazione = StringField('Ubicazione', validators=[Optional()], render_kw={'placeholder': 'Es: Scaffale A...', 'class': 'form-control'})
    
    fornitore = StringField('Fornitore', validators=[Optional()], render_kw={'placeholder': 'Nome fornitore...', 'class': 'form-control'})


class GestionePrenotazioneForm(FlaskForm):
    """Form per gestire prenotazioni esistenti"""
    
    prenotazione_id = HiddenField('Prenotazione ID', validators=[DataRequired()])
    
    azione = SelectField('Azione', validators=[
        DataRequired(message='Seleziona un\'azione')
    ], choices=[
        ('utilizza_totale', 'Utilizza Completamente'),
        ('utilizza_parziale', 'Utilizza Parzialmente'),
        ('annulla', 'Annulla Prenotazione'),
        ('modifica_scadenza', 'Modifica Scadenza')
    ])
    
    quantita_utilizzo = IntegerField('Quantità da Utilizzare', validators=[
        Optional(),
        NumberRange(min=1, message='La quantità deve essere maggiore di 0')
    ])
    
    nuova_scadenza = DateTimeField('Nuova Data Scadenza', validators=[
        Optional()
    ], format='%Y-%m-%dT%H:%M', render_kw={'type': 'datetime-local'})
    
    note = TextAreaField('Note', validators=[Optional()], render_kw={'rows': 2, 'placeholder': 'Note sull\'operazione...'})
    
    def validate_nuova_scadenza(self, field):
        """Valida che la nuova data di scadenza sia futura"""
        if self.azione.data == 'modifica_scadenza' and field.data:
            if field.data <= datetime.now():
                raise ValidationError('La nuova data di scadenza deve essere futura')
    
    def validate_quantita_utilizzo(self, field):
        """Valida la quantità di utilizzo per utilizzo parziale"""
        if self.azione.data == 'utilizza_parziale':
            if not field.data:
                raise ValidationError('Specifica la quantità da utilizzare')


class ImportRicambiForm(FlaskForm):
    """Form per importare ricambi da file CSV/Excel"""
    
    file_import = FileField('File da Importare', validators=[
        DataRequired(message='Seleziona un file da importare'),
        FileAllowed(['csv', 'xlsx', 'xls'], 'Solo file CSV o Excel')
    ])
    
    modalita_import = SelectField('Modalità Importazione', validators=[
        DataRequired(message='Seleziona la modalità')
    ], choices=[
        ('solo_nuovi', 'Solo Nuovi Ricambi'),
        ('aggiorna_esistenti', 'Aggiorna Esistenti'),
        ('sovrascrivi_tutto', 'Sovrascrivi Tutto')
    ])
    
    separatore_csv = SelectField('Separatore CSV', validators=[Optional()], choices=[
        (';', 'Punto e virgola (;)'),
        (',', 'Virgola (,)'),
        ('\t', 'Tab')
    ], default=';')
    
    prima_riga_intestazioni = SelectField('Prima Riga', validators=[Optional()], choices=[
        ('si', 'Contiene Intestazioni'),
        ('no', 'Contiene Dati')
    ], default='si')


class CalendarioPrenotazioniForm(FlaskForm):
    """Form per la vista calendario prenotazioni"""
    
    mese = SelectField('Mese', validators=[Optional()], coerce=int, choices=[
        (1, 'Gennaio'), (2, 'Febbraio'), (3, 'Marzo'), (4, 'Aprile'),
        (5, 'Maggio'), (6, 'Giugno'), (7, 'Luglio'), (8, 'Agosto'),
        (9, 'Settembre'), (10, 'Ottobre'), (11, 'Novembre'), (12, 'Dicembre')
    ])
    
    anno = IntegerField('Anno', validators=[
        Optional(),
        NumberRange(min=2020, max=2030, message='Anno non valido')
    ])
    
    filtro_ricambio = SelectField('Filtra per Ricambio', validators=[Optional()], 
                                 coerce=int, choices=[])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Imposta mese e anno correnti se non specificati
        now = datetime.now()
        if not self.mese.data:
            self.mese.data = now.month
        if not self.anno.data:
            self.anno.data = now.year
        
        # Popola le scelte per i ricambi
        self.filtro_ricambio.choices = [(0, 'Tutti i ricambi')] + [
            (r.id, f"{r.codice} - {r.descrizione[:40]}{'...' if len(r.descrizione) > 40 else ''}")
            for r in Ricambio.query.order_by(Ricambio.codice).all()
        ]
