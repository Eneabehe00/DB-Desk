"""
Servizio di schedulazione per l'import automatico delle email
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import current_app

logger = logging.getLogger(__name__)

class EmailImportScheduler:
    """Scheduler per l'import automatico delle email"""
    
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.job_id = 'email_import_job'
        self.is_running = False
        self.app = app
    
    def start(self):
        """Avvia lo scheduler se l'import automatico è abilitato"""
        if self.is_running:
            return
        
        try:
            # Controlla se l'import email è abilitato
            if not current_app.config.get('EMAIL_IMPORT_ENABLED'):
                logger.info("Email import scheduler: EMAIL_IMPORT_ENABLED è False, scheduler non avviato")
                return
            
            # Ottieni l'intervallo di polling (default 5 minuti)
            poll_seconds = current_app.config.get('EMAIL_POLL_SECONDS', 300)
            
            # Aggiungi il job allo scheduler
            self.scheduler.add_job(
                func=self._import_emails_job,
                trigger=IntervalTrigger(seconds=poll_seconds),
                id=self.job_id,
                name='Import Email Automatico',
                replace_existing=True,
                max_instances=1  # Evita sovrapposizioni
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"Email import scheduler avviato - polling ogni {poll_seconds} secondi")
            
        except Exception as e:
            logger.error(f"Errore nell'avvio dello scheduler email: {e}")
    
    def stop(self):
        """Ferma lo scheduler"""
        if self.is_running and self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                logger.info("Email import scheduler fermato")
            except Exception as e:
                logger.error(f"Errore nel fermare lo scheduler email: {e}")
    
    def _import_emails_job(self):
        """Job eseguito dallo scheduler per importare le email"""
        try:
            from flask import current_app
            from app.services.email_importer import import_new_emails
            
            # Usa l'app context salvato durante l'inizializzazione
            with self.app.app_context():
                # Esegui l'import
                messages, tickets = import_new_emails()
                
                if messages > 0:
                    logger.info(f"Email import scheduler: {messages} email processate, {tickets} ticket creati")
                
        except Exception as e:
            logger.error(f"Errore durante l'import automatico email: {e}")
    
    def is_job_running(self):
        """Controlla se il job è attualmente in esecuzione"""
        if not self.is_running:
            return False
        
        try:
            job = self.scheduler.get_job(self.job_id)
            return job is not None
        except Exception:
            return False
    
    def get_next_run_time(self):
        """Ottieni la prossima esecuzione del job"""
        if not self.is_running:
            return None
        
        try:
            job = self.scheduler.get_job(self.job_id)
            return job.next_run_time if job else None
        except Exception:
            return None


# Istanza globale dello scheduler
email_scheduler = EmailImportScheduler()
