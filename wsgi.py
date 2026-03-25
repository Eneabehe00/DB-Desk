#!/usr/bin/env python3
"""
WSGI entry point per il server di produzione con Waitress
Usa questo file per avviare l'applicazione in produzione
"""
import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from waitress import serve
from app import create_app
from config import config


def setup_logging():
    """Configura il logging su file con rotazione"""
    
    base_log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    app_main_dir = os.path.join(base_log_dir, 'app', 'main')
    app_error_dir = os.path.join(base_log_dir, 'app', 'error')

    os.makedirs(app_main_dir, exist_ok=True)
    os.makedirs(app_error_dir, exist_ok=True)

    # File di log applicazione
    log_file = os.path.join(app_main_dir, 'dbdesk.log')
    error_log_file = os.path.join(app_error_dir, 'dbdesk_error.log')
    
    # Formato log dettagliato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Rotazione giornaliera: i file ruotati finiscono con la data nel nome.
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=14,
        encoding='utf-8',
        utc=False,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    error_handler = TimedRotatingFileHandler(
        error_log_file,
        when='midnight',
        interval=1,
        backupCount=14,
        encoding='utf-8',
        utc=False,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Handler console (opzionale, utile per debugging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Configura root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Log anche per Waitress
    waitress_logger = logging.getLogger('waitress')
    waitress_logger.setLevel(logging.INFO)
    
    return logging.getLogger(__name__)


def main():
    """Avvia il server con Waitress"""
    
    # Configura logging
    logger = setup_logging()
    
    config_name = os.environ.get('FLASK_CONFIG') or 'production'
    
    try:
        app = create_app(config_name)
    except Exception as e:
        logger.error(f"Errore durante la creazione dell'app: {e}", exc_info=True)
        sys.exit(1)
    
    config_obj = config[config_name]
    host = config_obj.FLASK_HOST
    port = config_obj.FLASK_PORT
    
    threads = int(os.environ.get('WAITRESS_THREADS', '4'))
    channel_timeout = int(os.environ.get('WAITRESS_CHANNEL_TIMEOUT', '120'))
    connection_limit = int(os.environ.get('WAITRESS_CONNECTION_LIMIT', '100'))
    
    logger.info("=" * 70)
    logger.info("DB-Desk - Avvio Server di Produzione (Waitress)")
    logger.info("=" * 70)
    logger.info(f"Ambiente: {config_name}")
    logger.info(f"Host: {host}")
    logger.info(f"Porta: {port}")
    logger.info(f"URL: http://{host}:{port}")
    logger.info(f"Threads: {threads}")
    logger.info(f"Channel Timeout: {channel_timeout}s")
    logger.info(f"Connection Limit: {connection_limit}")
    logger.info(f"Debug Mode: {config_obj.FLASK_DEBUG}")
    logger.info(f"Log Directory: {os.path.join(os.path.dirname(__file__), 'logs')}")
    logger.info("=" * 70)
    
    try:
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            channel_timeout=channel_timeout,
            connection_limit=connection_limit,
            url_scheme='http'
        )
    except KeyboardInterrupt:
        logger.info("\nServer fermato dall'utente")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione del server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
