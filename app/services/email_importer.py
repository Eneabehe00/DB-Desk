from typing import Tuple
from imapclient import IMAPClient
from email import message_from_bytes
from email.policy import default as default_policy
from werkzeug.utils import secure_filename
import os
import uuid
import re
import threading
from datetime import datetime

from flask import current_app
from app import db
from app.models.email_import import EmailImportLog
from app.models.email_draft import EmailDraft
from app.models.ticket import Ticket
from app.models.user import User


def _get_body_from_message(msg) -> str:
    """Estrae il corpo del messaggio gestendo correttamente encoding e contenuti binari"""
    
    def safe_decode_content(content):
        """Decodifica in modo sicuro il contenuto gestendo byte e encoding problematici"""
        if isinstance(content, bytes):
            # Prova diverse codifiche comuni
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    decoded = content.decode(encoding, errors='ignore')
                    # Controlla se il contenuto è principalmente testuale
                    if decoded.isprintable() or any(c in decoded for c in ['\n', '\r', '\t']):
                        return decoded
                except (UnicodeDecodeError, LookupError):
                    continue
            # Fallback: decodifica con errori ignorati
            return content.decode('utf-8', errors='ignore')
        elif isinstance(content, str):
            return content
        else:
            return str(content)
    
    def is_likely_binary(content):
        """Controlla se il contenuto è probabilmente binario"""
        if isinstance(content, bytes):
            # Se contiene molti caratteri di controllo non stampabili, è probabilmente binario
            non_printable = sum(1 for b in content[:1000] if b < 32 and b not in [9, 10, 13])
            return non_printable > len(content[:1000]) * 0.3
        return False
    
    if msg.is_multipart():
        # Preferisci plain text
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == 'text/plain':
                try:
                    content = part.get_content()
                    if isinstance(content, str):
                        return content.strip()
                except Exception:
                    pass
                
                try:
                    payload = part.get_payload(decode=True)
                    if payload and not is_likely_binary(payload):
                        return safe_decode_content(payload).strip()
                except Exception:
                    continue
        
        # Fallback a HTML come testo grezzo
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == 'text/html':
                try:
                    content = part.get_content()
                    if isinstance(content, str):
                        return _strip_html_basic(content)
                except Exception:
                    pass
                
                try:
                    payload = part.get_payload(decode=True)
                    if payload and not is_likely_binary(payload):
                        html = safe_decode_content(payload)
                        return _strip_html_basic(html)
                except Exception:
                    continue
        
        # Se non troviamo contenuto testuale valido, restituisci messaggio di fallback
        return '(Contenuto email non decodificabile - possibile formato binario)'
    else:
        try:
            content = msg.get_content()
            if isinstance(content, str):
                return content.strip()
        except Exception:
            pass
        
        try:
            payload = msg.get_payload(decode=True)
            if payload and not is_likely_binary(payload):
                return safe_decode_content(payload).strip()
        except Exception:
            pass
        
        return '(Contenuto email non decodificabile - possibile formato binario)'


def _strip_html_basic(html: str) -> str:
    import re
    text = re.sub(r'<br\s*/?>', '\n', html, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return text


def _clean_email_body(body: str) -> str:
    """Pulisce il corpo dell'email rimuovendo contenuto concatenato/inoltrato"""
    if not body:
        return body
    
    import re
    
    # Patterns comuni per identificare email concatenate/inoltrate
    forward_patterns = [
        # Italiano
        r'-----\s*Messaggio originale\s*-----',
        r'-----\s*Messaggio inoltrato\s*-----',
        r'>\s*Da:\s*.*',
        r'>\s*Inviato:\s*.*',
        r'>\s*A:\s*.*',
        r'>\s*Oggetto:\s*.*',
        r'Il\s+\d{1,2}\/\d{1,2}\/\d{4}.*ha scritto:',
        r'Da:\s*[^\n]+\nInviato:\s*[^\n]+',
        
        # Inglese
        r'-----\s*Original Message\s*-----',
        r'-----\s*Forwarded message\s*-----',
        r'From:\s*[^\n]+\nSent:\s*[^\n]+',
        r'On\s+\w+,.*wrote:',
        
        # Pattern generici
        r'_{10,}',  # Linee di underscore
        r'-{10,}',  # Linee di trattini
        r'={10,}',  # Linee di uguale
    ]
    
    # Trova il primo pattern di separazione
    earliest_match = len(body)
    for pattern in forward_patterns:
        match = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
        if match:
            earliest_match = min(earliest_match, match.start())
    
    # Se trovato un pattern, taglia tutto dopo di esso
    if earliest_match < len(body):
        body = body[:earliest_match]
    
    # Rimuovi citazioni multiple (linee che iniziano con > o >>) 
    lines = body.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Rimuovi spazi iniziali per il controllo
        stripped_line = line.strip()
        
        # Se la linea inizia con > o >>, considerala una citazione
        if stripped_line.startswith('>'):
            continue
            
        # Se la linea è vuota dopo aver rimosso citazioni, può essere rimossa
        if not stripped_line:
            # Ma mantieni una linea vuota se quella precedente non lo era
            if cleaned_lines and cleaned_lines[-1].strip():
                cleaned_lines.append('')
            continue
            
        cleaned_lines.append(line)
    
    # Rimuovi linee vuote finali
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    return '\n'.join(cleaned_lines).strip()


def _save_attachment_from_part(ticket_id: int, part) -> None:
    filename = part.get_filename() or f"attachment_{uuid.uuid4().hex}"
    original_name = secure_filename(filename)
    unique_name = f"{ticket_id}_{uuid.uuid4().hex}_{original_name}"
    content = part.get_payload(decode=True)
    if not content:
        return
    save_path = os.path.join(current_app.config['ATTACHMENTS_FOLDER'], unique_name)
    with open(save_path, 'wb') as f:
        f.write(content)
    from app.models.ticket_attachment import TicketAttachment
    attach = TicketAttachment(
        ticket_id=ticket_id,
        filename=original_name,
        stored_filename=unique_name,
        content_type=part.get_content_type(),
        size_bytes=os.path.getsize(save_path),
        uploaded_by_id=_get_system_user_id()
    )
    db.session.add(attach)


def _get_system_user_id() -> int:
    # Utente creatore per ticket via email: preferisci admin
    admin = User.query.filter_by(is_admin=True, is_active=True).first()
    if admin:
        return admin.id
    any_user = User.query.first()
    if any_user:
        return any_user.id
    # In mancanza, solleva: l'app dovrebbe avere almeno un utente
    raise RuntimeError('Nessun utente presente per assegnare i ticket importati')


def _get_default_department_id() -> int:
    """Ottieni l'ID del dipartimento di default per i ticket email (preferisci 'support')"""
    from app.models.department import Department

    # Prima prova a trovare il dipartimento 'support'
    support_dept = Department.query.filter_by(name='support', is_active=True).first()
    if support_dept:
        return support_dept.id

    # Fallback: primo dipartimento attivo disponibile
    any_dept = Department.query.filter_by(is_active=True).first()
    if any_dept:
        return any_dept.id

    # Se non ci sono dipartimenti, creane uno di default
    Department.create_default_departments()
    support_dept = Department.query.filter_by(name='support').first()
    if support_dept:
        return support_dept.id

    # Ultimo fallback: qualsiasi dipartimento
    any_dept = Department.query.first()
    if any_dept:
        return any_dept.id

    raise RuntimeError('Nessun dipartimento disponibile per assegnare i ticket importati')


def _find_client_by_email(from_email: str) -> int:
    """Trova il cliente corrispondente all'email del mittente - usa sempre il cliente di default per le email"""
    # Per le email di assistenza, usa sempre il cliente di default configurato
    default_client_id = current_app.config.get('EMAIL_DEFAULT_CLIENT_ID')
    if default_client_id:
        return int(default_client_id)
    
    # Fallback se non c'è cliente di default configurato
    from app.models.cliente import Cliente
    first_client = Cliente.query.filter_by(is_active=True).first()
    if first_client:
        current_app.logger.warning(f"Nessun cliente di default configurato, uso primo cliente attivo ID {first_client.id}")
        return first_client.id
    
    raise RuntimeError('Nessun cliente trovato per assegnare il ticket da email')



def _check_email_recipients(msg, target_emails):
    """Controlla se l'email è destinata a uno degli indirizzi target"""
    if not target_emails:
        return True  # Se non ci sono target specifici, accetta tutto
    
    target_emails_lower = [email.strip().lower() for email in target_emails if email.strip()]
    if not target_emails_lower:
        return True
    
    # Controlla header To
    to_addresses = []
    try:
        to_header = msg.get('to', '')
        if hasattr(to_header, 'addresses'):
            to_addresses.extend([addr.addr_spec.lower() for addr in to_header.addresses])
        else:
            # Fallback per parsing manuale
            to_str = str(to_header).lower()
            for target in target_emails_lower:
                if target in to_str:
                    to_addresses.append(target)
    except Exception:
        pass
    
    # Controlla header Cc
    cc_addresses = []
    try:
        cc_header = msg.get('cc', '')
        if hasattr(cc_header, 'addresses'):
            cc_addresses.extend([addr.addr_spec.lower() for addr in cc_header.addresses])
        else:
            # Fallback per parsing manuale
            cc_str = str(cc_header).lower()
            for target in target_emails_lower:
                if target in cc_str:
                    cc_addresses.append(target)
    except Exception:
        pass
    
    # Controlla se almeno uno dei target è presente
    all_recipients = to_addresses + cc_addresses
    for target in target_emails_lower:
        if target in all_recipients:
            return True
    
    return False


def _should_process_email(from_email: str, subject: str, body: str, cfg) -> bool:
    """Determina se un'email deve essere processata in base ai filtri configurati
    
    LOGICA DI PRIORITÀ:
    1. Le keyword di esclusione (EMAIL_SKIP_KEYWORDS) hanno PRIORITÀ ASSOLUTA
       - Se trovata anche una sola keyword da escludere, l'email viene sempre rifiutata
       - Questo avviene PRIMA di controllare le keyword accettate
    2. Controllo mittenti permessi (EMAIL_ALLOWED_SENDERS)
    3. Controllo keyword accettate nell'oggetto (EMAIL_SUBJECT_KEYWORDS)
    
    Esempio: Se un'email contiene sia "supporto" (accettata) che "newsletter" (da escludere),
    l'email viene rifiutata perché "newsletter" ha priorità assoluta.
    """
    
    # 1. PRIORITÀ MASSIMA: Controllo parole da escludere
    # Se trova una keyword da rifiutare, l'email viene sempre rifiutata
    # indipendentemente da altre keyword accettate presenti
    skip_keywords = [k.strip().lower() for k in cfg.get('EMAIL_SKIP_KEYWORDS', []) if k.strip()]
    if skip_keywords:
        text_to_check = f"{from_email} {subject} {body}".lower()
        if any(skip_keyword in text_to_check for skip_keyword in skip_keywords):
            return False
    
    # 2. Controllo mittenti permessi (se configurato)
    allowed_senders = [s.strip().lower() for s in cfg.get('EMAIL_ALLOWED_SENDERS', []) if s.strip()]
    if allowed_senders:
        from_email_lower = from_email.lower()
        # Controlla se il mittente è in lista o se il dominio è permesso
        sender_allowed = False
        for allowed in allowed_senders:
            if allowed.startswith('@'):  # Dominio: @example.com
                if from_email_lower.endswith(allowed):
                    sender_allowed = True
                    break
            elif allowed in from_email_lower:  # Email completa o parte
                sender_allowed = True
                break
        if not sender_allowed:
            return False
    
    # 3. Controllo parole chiave nell'oggetto (se configurato)
    subject_keywords = [k.strip().lower() for k in cfg.get('EMAIL_SUBJECT_KEYWORDS', []) if k.strip()]
    if subject_keywords:
        subject_lower = subject.lower()
        keyword_found = any(keyword in subject_lower for keyword in subject_keywords)
        if not keyword_found:
            return False
    
    return True


def _get_available_folders(client) -> list:
    """Ottieni la lista delle cartelle IMAP disponibili"""
    try:
        folders = client.list_folders()
        return [folder[2] for folder in folders if len(folder) >= 3]  # folder[2] è il nome della cartella
    except Exception as e:
        current_app.logger.warning(f"Impossibile ottenere lista cartelle: {e}")
        return []


def _try_select_folder(client, folder_name: str) -> str:
    """Prova a selezionare una cartella, restituisce il nome se riesce, None se fallisce"""
    try:
        client.select_folder(folder_name, readonly=False)
        return folder_name
    except Exception:
        return None


def _process_single_email_with_timeout(uid, fetch_data, cfg, app_context, timeout_seconds=30):
    """
    Processa un singolo messaggio email con timeout per evitare blocchi
    """
    def process_email():
        try:
            # Usa il contesto dell'applicazione nei thread
            with app_context:
                raw = fetch_data[uid][b'RFC822']
                msg = message_from_bytes(raw, policy=default_policy)

                subject = msg['subject'] or '(Senza oggetto)'
                from_email = ''
                try:
                    from_email = msg['from'].addresses[0].addr_spec
                except Exception:
                    pass
                body = _get_body_from_message(msg)
                # Pulisci il corpo dell'email rimuovendo contenuto concatenato
                clean_body = _clean_email_body(body)

                # Parse della data
                received_at = None
                try:
                    received_at = datetime.fromtimestamp(msg.get('Date').timestamp()) if msg.get('Date') else None
                except Exception:
                    pass

                # Controlla destinatari email (per mailing list)
                target_emails = cfg.get('EMAIL_TARGET_ADDRESSES', '').split(',') if cfg.get('EMAIL_TARGET_ADDRESSES') else []
                recipients_match = _check_email_recipients(msg, target_emails)

                # Verifica se l'email deve essere processata
                should_process = _should_process_email(from_email, subject, clean_body, cfg) and recipients_match

                if should_process and cfg.get('EMAIL_AUTO_IMPORT', False):
                    try:
                        # Trova il cliente corrispondente al mittente
                        try:
                            cliente_id = _find_client_by_email(from_email)
                        except Exception as e:
                            # Fallback al cliente di default se la ricerca fallisce
                            cliente_id = int(cfg.get('EMAIL_DEFAULT_CLIENT_ID'))
                            current_app.logger.warning(f"Cliente non trovato per email da {from_email}, uso default ID {cliente_id}: {e}")

                        # Crea ticket automaticamente
                        ticket = Ticket(
                            titolo=subject[:200],
                            descrizione=clean_body or '(nessun contenuto)',
                            cliente_id=cliente_id,
                            created_by_id=_get_system_user_id(),
                            department_id=_get_default_department_id(),
                            categoria='Supporto',
                            priorita='Media',
                            stato='Aperto'
                        )
                        db.session.add(ticket)
                        db.session.flush()  # ottieni id

                        # Allegati
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_disposition() == 'attachment':
                                    _save_attachment_from_part(ticket.id, part)

                        # Log import (creato prima del commit per tracciare il tentativo)
                        log = EmailImportLog(
                            imap_uid=str(uid),
                            message_id=str(msg.get('Message-Id') or ''),
                            from_email=from_email,
                            subject=subject,
                            created_ticket_id=ticket.id,
                            received_at=received_at
                        )
                        db.session.add(log)

                        # Il commit avviene dopo il processamento di ogni email
                        # Se arriva qui senza errori, il log di successo verrà scritto dopo il commit

                    except Exception as e:
                        current_app.logger.error(f"❌ ERRORE CREAZIONE TICKET: Impossibile creare ticket da email {from_email} - {subject[:50]}: {str(e)}")
                        # Anche in caso di errore, marca come processato per evitare riprocessamenti infiniti
                        try:
                            error_log = EmailImportLog(
                                imap_uid=str(uid),
                                message_id=str(msg.get('Message-Id') or ''),
                                from_email=from_email,
                                subject=subject,
                                created_ticket_id=None,  # Nessun ticket creato
                                received_at=received_at
                            )
                            db.session.add(error_log)
                        except Exception:
                            pass  # Se anche il log fallisce, continua
                        return None
                else:
                    # Salva come bozza per revisione manuale
                    draft_status = 'pending' if should_process else 'ignored'
                    draft = EmailDraft(
                        imap_uid=str(uid),
                        message_id=str(msg.get('Message-Id') or ''),
                        from_email=from_email,
                        subject=subject,
                        body=clean_body,
                        received_at=received_at,
                        status=draft_status
                    )
                    db.session.add(draft)

            return True

        except Exception as e:
            # Gestisci il logging anche fuori dal contesto dell'app
            try:
                with app_context:
                    current_app.logger.error(f"❌ ERRORE PROCESSAMENTO EMAIL UID {uid}: {str(e)}")
                    # Anche in caso di errore generale, marca come processato per evitare loop infiniti
                    try:
                        error_log = EmailImportLog(
                            imap_uid=str(uid),
                            message_id='',
                            from_email='unknown',
                            subject='Errore processamento',
                            created_ticket_id=None,
                            received_at=None
                        )
                        db.session.add(error_log)
                    except Exception:
                        pass
            except Exception:
                # Fallback se anche il logging fallisce
                print(f"❌ ERRORE PROCESSAMENTO EMAIL UID {uid}: {str(e)}")
            return None

    result = [None]  # Lista per passare il risultato dal thread

    def target():
        result[0] = process_email()

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        current_app.logger.warning(f"⚠️ TIMEOUT PROCESSAMENTO EMAIL UID {uid}: messaggio saltato dopo {timeout_seconds}s")
        return None

    return result[0]


def import_new_emails() -> Tuple[int, int]:
    current_app.logger.info("=== AVVIO IMPORTAZIONE EMAIL ===")
    cfg = current_app.config
    if not cfg.get('EMAIL_IMPORT_ENABLED'):
        return (0, 0)

    imap_host = cfg.get('EMAIL_IMAP_HOST')
    username = cfg.get('EMAIL_USERNAME')
    password = cfg.get('EMAIL_PASSWORD')
    folder = cfg.get('EMAIL_FOLDER', 'INBOX')
    use_ssl = cfg.get('EMAIL_IMAP_SSL', True)
    port = cfg.get('EMAIL_IMAP_PORT', 993)
    default_client_id = cfg.get('EMAIL_DEFAULT_CLIENT_ID')
    auto_import = cfg.get('EMAIL_AUTO_IMPORT', False)

    if not (imap_host and username and password and default_client_id):
        current_app.logger.warning("Configurazione IMAP incompleta")
        return (0, 0)

    new_messages = 0
    new_tickets = 0

    if use_ssl:
        # Configurazione SSL con gestione dei certificati
        import ssl
        ssl_context = ssl.create_default_context()

        # Opzione 1: Disabilita la verifica dei certificati (meno sicuro ma funziona)
        # Utile per ambienti di sviluppo o server con certificati self-signed
        verify_certs = cfg.get('EMAIL_IMAP_SSL_VERIFY_CERTS', True)
        if not verify_certs:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        client = IMAPClient(host=imap_host, port=port, ssl=True, ssl_context=ssl_context)
    else:
        client = IMAPClient(host=imap_host, port=port, ssl=False)

    with client:
        client.login(username, password)

        # Usa semplicemente la cartella configurata senza provare varianti
        selected_folder = _try_select_folder(client, folder)
        if not selected_folder:
            # Se non funziona, mostra le cartelle disponibili per aiutare l'utente
            available_folders = _get_available_folders(client)
            error_msg = f"Impossibile selezionare la cartella '{folder}'. "
            error_msg += f"Cartelle disponibili: {', '.join(available_folders[:20])}"  # Limita a 20 per leggibilità
            if len(available_folders) > 20:
                error_msg += f" ... e altre {len(available_folders) - 20}"
            current_app.logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Filtra per messaggi recenti usando un timestamp di controllo
        # Questo approccio è più affidabile del filtro IMAP SINCE
        import os
        from datetime import datetime, timedelta

        # File per salvare l'ultimo timestamp di controllo
        last_check_file = os.path.join(current_app.root_path, 'last_email_check.txt')

        # Leggi l'ultimo timestamp di controllo
        last_check_time = None
        if os.path.exists(last_check_file):
            try:
                with open(last_check_file, 'r') as f:
                    timestamp_str = f.read().strip()
                    last_check_time = datetime.fromisoformat(timestamp_str)
            except Exception as e:
                current_app.logger.warning(f"Errore lettura timestamp ultimo controllo: {e}")

        # Se non c'è timestamp precedente, usa ultime 24 ore
        if last_check_time is None:
            last_check_time = datetime.now() - timedelta(hours=24)

        # Aggiorna il timestamp per il prossimo controllo
        current_check_time = datetime.now()
        try:
            with open(last_check_file, 'w') as f:
                f.write(current_check_time.isoformat())
        except Exception as e:
            current_app.logger.warning(f"Errore scrittura timestamp controllo: {e}")

        # Ottieni tutti i messaggi e filtra per data programmaticamente
        all_uids = client.search(['NOT', 'DELETED'])
        current_app.logger.info(f"Trovati {len(all_uids)} messaggi totali nella cartella")

        # Filtra per data ricevimento
        uids = []
        for uid in all_uids:
            try:
                # Ottieni la data del messaggio
                fetch_data = client.fetch([uid], ['ENVELOPE'])
                envelope = fetch_data[uid][b'ENVELOPE']
                if envelope and hasattr(envelope, 'date') and envelope.date:
                    # Converte la data IMAP in datetime
                    msg_date = envelope.date
                    if msg_date and msg_date > last_check_time:
                        uids.append(uid)
            except Exception as e:
                current_app.logger.warning(f"Errore controllo data messaggio UID {uid}: {e}")
                continue

        current_app.logger.info(f"Dopo filtro data (dal {last_check_time.strftime('%Y-%m-%d %H:%M:%S')}): {len(uids)} messaggi da processare")

        for uid in uids:
            # evita duplicati già importati o processati
            if (EmailImportLog.query.filter_by(imap_uid=str(uid)).first() or
                EmailDraft.query.filter_by(imap_uid=str(uid)).first()):
                continue

            new_messages += 1

                # Processa l'email con timeout per evitare blocchi
            try:
                fetch_data = client.fetch([uid], ['RFC822', 'ENVELOPE'])
                # Passa il contesto dell'applicazione per i thread
                from flask import has_app_context
                if has_app_context():
                    app_context = current_app.app_context()
                else:
                    # Se non siamo in un contesto, creane uno nuovo
                    app_context = current_app.app_context()
                result = _process_single_email_with_timeout(uid, fetch_data, cfg, app_context, timeout_seconds=30)

                if result is True:
                    new_tickets += 1
                elif result is None:
                    # Timeout o errore - logga e continua
                    current_app.logger.warning(f"⚠️ EMAIL UID {uid} non processata correttamente")

                # Commit per ogni email processata
                try:
                    db.session.commit()

                    # Dopo commit riuscito, logga i successi
                    if result is True:
                        # Trova il log appena creato per ottenere i dettagli del ticket
                        log_entry = EmailImportLog.query.filter_by(imap_uid=str(uid)).first()
                        if log_entry and log_entry.created_ticket_id:
                            current_app.logger.info(f"✅ TICKET CREATO: ID {log_entry.created_ticket_id} da email {log_entry.from_email} - {log_entry.subject[:50]}")
                except Exception as commit_error:
                    current_app.logger.error(f"❌ ERRORE COMMIT DATABASE per UID {uid}: {str(commit_error)}")
                    db.session.rollback()
                    continue

            except Exception as e:
                current_app.logger.error(f"❌ ERRORE CRITICO PROCESSAMENTO EMAIL UID {uid}: {str(e)}")
                # Continua con il prossimo messaggio invece di fermare tutto
                continue

            # opzionale: marca come SEEN anche in caso di errore
            try:
                client.add_flags([uid], [b'\\Seen'])
            except Exception:
                pass

    current_app.logger.info(f"=== IMPORTAZIONE COMPLETATA: {new_messages} messaggi processati, {new_tickets} ticket creati ===")
    return (new_messages, new_tickets)


def get_email_drafts(status='pending'):
    """Ottieni le bozze email in attesa di conversione"""
    return EmailDraft.query.filter_by(status=status).order_by(EmailDraft.received_at.desc()).all()


def test_imap_connection() -> Tuple[bool, str, list]:
    """Testa la connessione IMAP e restituisce (successo, messaggio, lista_cartelle)"""
    cfg = current_app.config

    imap_host = cfg.get('EMAIL_IMAP_HOST')
    username = cfg.get('EMAIL_USERNAME')
    password = cfg.get('EMAIL_PASSWORD')
    use_ssl = cfg.get('EMAIL_IMAP_SSL', True)
    port = cfg.get('EMAIL_IMAP_PORT', 993)

    if not (imap_host and username and password):
        return (False, "Configurazione IMAP incompleta", [])

    try:
        if use_ssl:
            import ssl
            ssl_context = ssl.create_default_context()
            verify_certs = cfg.get('EMAIL_IMAP_SSL_VERIFY_CERTS', True)
            if not verify_certs:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            client = IMAPClient(host=imap_host, port=port, ssl=True, ssl_context=ssl_context)
        else:
            client = IMAPClient(host=imap_host, port=port, ssl=False)

        with client:
            client.login(username, password)
            folders = _get_available_folders(client)
            return (True, "Connessione riuscita", folders)

    except Exception as e:
        return (False, f"Errore connessione: {str(e)}", [])


def convert_draft_to_ticket(draft_id: int, cliente_id: int = None) -> Ticket:
    """Converte una bozza email in ticket"""
    draft = EmailDraft.query.get_or_404(draft_id)
    
    if draft.status == 'converted':
        raise ValueError("Bozza già convertita")
    
    try:
        # Se il cliente non è specificato, prova a trovarlo automaticamente
        if cliente_id is None:
            try:
                cliente_id = _find_client_by_email(draft.from_email)
            except Exception:
                # Fallback al cliente di default
                cfg = current_app.config
                cliente_id = int(cfg.get('EMAIL_DEFAULT_CLIENT_ID'))
        
        ticket = Ticket(
            titolo=draft.subject[:200],
            descrizione=draft.body or '(nessun contenuto)',
            cliente_id=cliente_id,
            created_by_id=_get_system_user_id(),
            department_id=_get_default_department_id(),
            categoria='Supporto',
            priorita='Media',
            stato='Aperto'
        )
        db.session.add(ticket)
        db.session.flush()
        
        # Aggiorna la bozza
        draft.status = 'converted'
        draft.converted_ticket_id = ticket.id
        
        # Log import
        log = EmailImportLog(
            imap_uid=draft.imap_uid,
            message_id=draft.message_id,
            from_email=draft.from_email,
            subject=draft.subject,
            created_ticket_id=ticket.id,
            received_at=draft.received_at
        )
        db.session.add(log)
        db.session.commit()
        
        current_app.logger.info(f"✅ CONVERSIONE MANUALE: Bozza ID {draft_id} convertita in ticket ID {ticket.id} - {draft.from_email}")
        return ticket
        
    except Exception as e:
        current_app.logger.error(f"❌ ERRORE CONVERSIONE: Impossibile convertire bozza ID {draft_id} da {draft.from_email}: {str(e)}")
        raise


