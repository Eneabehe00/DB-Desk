from .user import User
from .role import Role
from .department import Department
from .cliente import Cliente
from .ticket import Ticket
from .ticket_attachment import TicketAttachment
from .ticket_subtask import TicketSubtask
from .foglio_tecnico import FoglioTecnico, foglio_macchine, foglio_ricambi
from .email_import import EmailImportLog
from .email_draft import EmailDraft
from .ricambio import Ricambio, MovimentoMagazzino, PrenotazioneRicambio
from .macchina import TipoMacchina, Macchina, MovimentoMacchina, ticket_macchine, department_tipo_macchina