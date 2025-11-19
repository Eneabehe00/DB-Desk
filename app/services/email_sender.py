"""
Servizio per l'invio di email dei fogli tecnici
Gestisce l'invio automatico dei PDF dei fogli tecnici via email
"""

from flask import current_app, render_template
from flask_mail import Mail, Message
import os
from datetime import datetime
from app import db
from app.models.foglio_tecnico import FoglioTecnico
from app.services.pdf_generator import genera_pdf_foglio_tecnico, get_foglio_pdf_path


def init_mail(app):
    """
    Inizializza Flask-Mail con l'app
    Configurazione necessaria in config.py o .env:
    
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True  
    MAIL_USERNAME = 'tuo_email@gmail.com'
    MAIL_PASSWORD = 'tua_password_app'
    MAIL_DEFAULT_SENDER = 'tuo_email@gmail.com'
    """
    mail = Mail(app)
    return mail


def invia_foglio_per_email(foglio_id, email_destinatario, note_aggiuntive=None, genera_pdf_se_mancante=True):
    """
    Invia un foglio tecnico per email
    
    Args:
        foglio_id (int): ID del foglio tecnico
        email_destinatario (str): Email del destinatario
        note_aggiuntive (str, optional): Note aggiuntive da includere nell'email
        genera_pdf_se_mancante (bool): Se generare PDF automaticamente se non esiste
        
    Returns:
        bool: True se inviato con successo
        
    Raises:
        Exception: Se errori nell'invio o configurazione email mancante
    """
    # Carica foglio dal database
    foglio = FoglioTecnico.query.get(foglio_id)
    if not foglio:
        raise ValueError(f"Foglio tecnico {foglio_id} non trovato")
    
    try:
        # Verifica configurazione email
        if not _is_email_configured():
            raise Exception("Configurazione email non presente. Configurare MAIL_SERVER, MAIL_USERNAME, etc. in .env")
        
        # Ottieni o genera PDF
        pdf_path = get_foglio_pdf_path(foglio_id)
        if not pdf_path and genera_pdf_se_mancante:
            current_app.logger.info(f"Generando PDF per foglio {foglio.numero_foglio} prima dell'invio")
            pdf_path = genera_pdf_foglio_tecnico(foglio_id)
        
        if not pdf_path:
            raise Exception("Impossibile ottenere o generare il PDF del foglio tecnico")
        
        # Inizializza Flask-Mail
        from flask_mail import Mail, Message
        mail = Mail(current_app)
        
        # Prepara oggetto email
        oggetto = f"Foglio Tecnico {foglio.numero_foglio} - {foglio.titolo}"
        
        # Prepara corpo email
        corpo_html = render_template(
            'fogli_tecnici/email_template.html',
            foglio=foglio,
            note_aggiuntive=note_aggiuntive,
            destinatario=email_destinatario,
            data_generazione=datetime.now().strftime('%d/%m/%Y alle %H:%M')
        )
        
        corpo_testo = _genera_corpo_testo_email(foglio, note_aggiuntive)
        
        # Crea messaggio
        msg = Message(
            subject=oggetto,
            recipients=[email_destinatario],
            html=corpo_html,
            body=corpo_testo
        )
        
        # Aggiungi allegato PDF
        if pdf_path and os.path.exists(pdf_path):
            filename = f"FoglioTecnico_{foglio.numero_foglio}.pdf"
            with open(pdf_path, 'rb') as f:
                msg.attach(
                    filename=filename,
                    content_type='application/pdf',
                    data=f.read()
                )
        
        # Invia email
        mail.send(msg)
        
        # Aggiorna stato nel database
        foglio.inviato_online = True
        foglio.email_invio = email_destinatario
        foglio.data_invio = datetime.utcnow()
        if foglio.stato == 'Completato':
            foglio.stato = 'Inviato'
        foglio.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"Email inviata con successo per foglio {foglio.numero_foglio} a {email_destinatario}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Errore invio email per foglio {foglio.numero_foglio}: {str(e)}")
        raise Exception(f"Errore nell'invio dell'email: {str(e)}")


def invia_notifica_nuovo_foglio(foglio_id, email_manager=None):
    """
    Invia notifica di nuovo foglio tecnico creato al manager del reparto
    
    Args:
        foglio_id (int): ID del foglio tecnico
        email_manager (str, optional): Email del manager (se non specificato, usa quello del reparto)
        
    Returns:
        bool: True se inviato con successo
    """
    try:
        # Carica foglio
        foglio = FoglioTecnico.query.get(foglio_id)
        if not foglio:
            return False
        
        # Determina email destinatario
        if not email_manager:
            # Trova manager del reparto (implementazione dipende dalla struttura del sistema)
            from app.models.user import User
            from app.models.department import Department
            
            # Cerca utenti manager nel reparto del foglio
            managers = User.query.filter_by(
                department_id=foglio.department_id,
                is_active=True
            ).filter(
                User.role.has(name__in=['manager', 'admin'])
            ).all()
            
            if managers:
                email_manager = managers[0].email
            else:
                current_app.logger.warning(f"Nessun manager trovato per reparto {foglio.department_id}")
                return False
        
        # Verifica configurazione email
        if not _is_email_configured():
            current_app.logger.warning("Configurazione email mancante per notifica nuovo foglio")
            return False
        
        # Inizializza Flask-Mail
        from flask_mail import Mail, Message
        mail = Mail(current_app)
        
        # Prepara messaggio
        oggetto = f"Nuovo Foglio Tecnico: {foglio.numero_foglio} - {foglio.titolo}"
        
        corpo_html = render_template(
            'fogli_tecnici/notification_email.html',
            foglio=foglio
        )
        
        corpo_testo = f"""
Nuovo Foglio Tecnico Creato

Numero: {foglio.numero_foglio}
Titolo: {foglio.titolo}
Cliente: {foglio.cliente.ragione_sociale if foglio.cliente else 'N/A'}
Tecnico: {foglio.tecnico.first_name} {foglio.tecnico.last_name}
Data Intervento: {foglio.data_intervento.strftime('%d/%m/%Y %H:%M')}

Stato: {foglio.stato}
Creato: {foglio.created_at.strftime('%d/%m/%Y %H:%M')}

Per visualizzare i dettagli, accedi al sistema DB-Desk.
"""
        
        msg = Message(
            subject=oggetto,
            recipients=[email_manager],
            html=corpo_html,
            body=corpo_testo
        )
        
        # Invia
        mail.send(msg)
        
        current_app.logger.info(f"Notifica inviata per nuovo foglio {foglio.numero_foglio} a {email_manager}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Errore invio notifica per foglio {foglio_id}: {str(e)}")
        return False


def invia_promemoria_fogli_incompleti(giorni_limite=7):
    """
    Invia promemoria per fogli tecnici rimasti incompleti oltre il limite di giorni
    
    Args:
        giorni_limite (int): Giorni dopo i quali considerare un foglio "vecchio"
        
    Returns:
        int: Numero di promemoria inviati
    """
    try:
        if not _is_email_configured():
            current_app.logger.warning("Configurazione email mancante per promemoria fogli")
            return 0
        
        from datetime import timedelta
        from sqlalchemy import and_
        
        data_limite = datetime.utcnow() - timedelta(days=giorni_limite)
        
        # Trova fogli incompleti vecchi
        fogli_vecchi = FoglioTecnico.query.filter(
            and_(
                FoglioTecnico.created_at < data_limite,
                FoglioTecnico.stato.in_(['Bozza', 'In compilazione', 'In attesa firme'])
            )
        ).all()
        
        promemoria_inviati = 0
        
        for foglio in fogli_vecchi:
            try:
                # Invia promemoria al tecnico assegnato
                if foglio.tecnico and foglio.tecnico.email:
                    _invia_promemoria_singolo(foglio, foglio.tecnico.email)
                    promemoria_inviati += 1
                    
            except Exception as e:
                current_app.logger.error(f"Errore invio promemoria per foglio {foglio.numero_foglio}: {str(e)}")
                continue
        
        return promemoria_inviati
        
    except Exception as e:
        current_app.logger.error(f"Errore invio promemoria fogli incompleti: {str(e)}")
        return 0


def _invia_promemoria_singolo(foglio, email_tecnico):
    """Invia un singolo promemoria per un foglio incompleto"""
    from flask_mail import Mail, Message
    mail = Mail(current_app)
    
    oggetto = f"Promemoria: Foglio Tecnico {foglio.numero_foglio} da completare"
    
    corpo_html = render_template(
        'fogli_tecnici/reminder_email.html',
        foglio=foglio
    )
    
    giorni_passati = (datetime.utcnow() - foglio.created_at).days
    
    corpo_testo = f"""
Promemoria Foglio Tecnico da Completare

Numero: {foglio.numero_foglio}
Titolo: {foglio.titolo}
Cliente: {foglio.cliente.ragione_sociale if foglio.cliente else 'N/A'}
Stato Attuale: {foglio.stato}

Creato: {foglio.created_at.strftime('%d/%m/%Y %H:%M')} ({giorni_passati} giorni fa)
Step Corrente: {foglio.step_corrente}

Ti ricordiamo di completare questo foglio tecnico accedendo al sistema DB-Desk.
"""
    
    msg = Message(
        subject=oggetto,
        recipients=[email_tecnico],
        html=corpo_html,
        body=corpo_testo
    )
    
    mail.send(msg)


def _is_email_configured():
    """Verifica se la configurazione email è presente"""
    return all([
        current_app.config.get('MAIL_SERVER'),
        current_app.config.get('MAIL_USERNAME'),
        current_app.config.get('MAIL_PASSWORD')
    ])


def _genera_corpo_testo_email(foglio, note_aggiuntive=None):
    """Genera il corpo testuale dell'email per compatibilità client che non supportano HTML"""
    
    corpo = f"""
Foglio Tecnico: {foglio.numero_foglio}
{'-' * 50}

INFORMAZIONI GENERALI
Titolo: {foglio.titolo}
Cliente: {foglio.cliente.ragione_sociale if foglio.cliente else 'N/A'}
Tecnico: {foglio.tecnico.first_name} {foglio.tecnico.last_name}
Data Intervento: {foglio.data_intervento.strftime('%d/%m/%Y %H:%M')}

DETTAGLI INTERVENTO
Categoria: {foglio.categoria}
Priorità: {foglio.priorita}
"""

    if foglio.indirizzo_intervento:
        corpo += f"Indirizzo: {foglio.indirizzo_intervento}\n"
    
    if foglio.durata_intervento:
        corpo += f"Durata: {foglio.durata_intervento} minuti\n"
    
    if foglio.km_percorsi:
        corpo += f"Km percorsi: {foglio.km_percorsi} km\n"

    corpo += f"\nDESCRIZIONE:\n{foglio.descrizione}\n"

    if foglio.note_aggiuntive:
        corpo += f"\nNOTE AGGIUNTIVE:\n{foglio.note_aggiuntive}\n"

    # Informazioni commerciali
    if foglio.modalita_pagamento or foglio.importo_intervento:
        corpo += "\nINFORMAZIONI COMMERCIALI\n"
        if foglio.modalita_pagamento:
            corpo += f"Modalità pagamento: {foglio.modalita_pagamento}\n"
        if foglio.importo_intervento:
            corpo += f"Importo: €{foglio.importo_intervento}\n"

    # Firme
    if foglio.nome_firmatario_cliente:
        corpo += f"\nFIRMATARIO CLIENTE: {foglio.nome_firmatario_cliente}\n"

    # Note aggiuntive dell'email
    if note_aggiuntive:
        corpo += f"\nNOTE AGGIUNTIVE:\n{note_aggiuntive}\n"

    corpo += f"""
{'-' * 50}
Generato automaticamente da DB-Desk
Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
    
    return corpo


def test_configurazione_email():
    """
    Testa la configurazione email inviando un'email di prova
    
    Returns:
        dict: Risultato del test con successo/errore
    """
    try:
        if not _is_email_configured():
            return {
                'success': False,
                'message': 'Configurazione email mancante'
            }
        
        from flask_mail import Mail, Message
        mail = Mail(current_app)
        
        # Invia email di test all'admin
        admin_email = current_app.config.get('MAIL_USERNAME')
        
        msg = Message(
            subject='Test Configurazione Email DB-Desk',
            recipients=[admin_email],
            body='Email di test per verificare la configurazione di invio fogli tecnici.'
        )
        
        mail.send(msg)
        
        return {
            'success': True,
            'message': f'Email di test inviata con successo a {admin_email}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Errore nel test email: {str(e)}'
        }
