# Forms package
from .auth import LoginForm, RegistrationForm, ChangePasswordForm
from .ticket import TicketForm, TicketFilterForm, SubtaskForm
from .cliente import ClienteForm, ClienteFilterForm
from .magazzino import (
    RicambioForm, MovimentoMagazzinoForm, PrenotazioneRicambioForm,
    ScaricoRicambioForm, RicercaRicambiForm, GestionePrenotazioneForm,
    CalendarioPrenotazioniForm, ImportRicambiForm
)