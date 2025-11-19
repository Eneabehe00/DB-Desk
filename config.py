import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or ''
    DB_NAME = os.environ.get('DB_NAME') or 'dbdesk'
    DB_PORT = os.environ.get('DB_PORT') or '3306'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask configuration
    FLASK_HOST = os.environ.get('FLASK_HOST') or '0.0.0.0'  # Permette connessioni da rete locale
    FLASK_PORT = int(os.environ.get('FLASK_PORT') or 5000)
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # Uploads configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ATTACHMENTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'attachments')
    DOCS_FOLDER = os.path.join(UPLOAD_FOLDER, 'docs')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH_BYTES') or 25 * 1024 * 1024)  # 25MB di default
    ALLOWED_DOC_EXTENSIONS = set((os.environ.get('ALLOWED_DOC_EXTENSIONS') or 'pdf,doc,docx,xls,xlsx,ppt,pptx,txt,md,png,jpg,jpeg,gif').split(','))
    ALLOWED_ATTACHMENT_EXTENSIONS = set((os.environ.get('ALLOWED_ATTACHMENT_EXTENSIONS') or 'pdf,txt,md,png,jpg,jpeg,gif,zip,rar,7z,log,json,xml').split(','))

    # Email Import (IMAP - Outlook/Office365)
    EMAIL_IMPORT_ENABLED = os.environ.get('EMAIL_IMPORT_ENABLED', 'False').lower() == 'true'
    EMAIL_IMAP_HOST = os.environ.get('EMAIL_IMAP_HOST') or ''
    EMAIL_IMAP_PORT = int(os.environ.get('EMAIL_IMAP_PORT') or 993)
    EMAIL_IMAP_SSL = os.environ.get('EMAIL_IMAP_SSL', 'True').lower() == 'true'
    EMAIL_IMAP_SSL_VERIFY_CERTS = os.environ.get('EMAIL_IMAP_SSL_VERIFY_CERTS', 'True').lower() == 'true'
    EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME') or ''
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD') or ''
    EMAIL_FOLDER = os.environ.get('EMAIL_FOLDER') or 'INBOX'
    EMAIL_POLL_SECONDS = int(os.environ.get('EMAIL_POLL_SECONDS') or 300)  # 5 minuti
    EMAIL_DEFAULT_CLIENT_ID = os.environ.get('EMAIL_DEFAULT_CLIENT_ID')
    
    # Email filtering and rules
    EMAIL_ALLOWED_SENDERS = os.environ.get('EMAIL_ALLOWED_SENDERS', '').split(',') if os.environ.get('EMAIL_ALLOWED_SENDERS') else []
    EMAIL_SUBJECT_KEYWORDS = os.environ.get('EMAIL_SUBJECT_KEYWORDS', '').split(',') if os.environ.get('EMAIL_SUBJECT_KEYWORDS') else []
    EMAIL_SKIP_KEYWORDS = os.environ.get('EMAIL_SKIP_KEYWORDS', '').split(',') if os.environ.get('EMAIL_SKIP_KEYWORDS') else []
    EMAIL_AUTO_IMPORT = os.environ.get('EMAIL_AUTO_IMPORT', 'False').lower() == 'true'  # Se False, salva come bozze
    
    # Target email addresses (per mailing list)
    EMAIL_TARGET_ADDRESSES = os.environ.get('EMAIL_TARGET_ADDRESSES', '')  # Se False, salva come bozze
    
    # Flask-Mail configuration for sending emails (fogli tecnici)
    # Usa le stesse credenziali dell'import email per l'invio
    MAIL_SERVER = 'smtps.aruba.it'  # Server SMTP Aruba
    MAIL_PORT = 465  # SMTP SSL port for Aruba
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False  # SSL e TLS sono mutuamente esclusivi
    MAIL_USERNAME = os.environ.get('EMAIL_USERNAME') or ''
    MAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD') or ''
    MAIL_DEFAULT_SENDER = os.environ.get('EMAIL_USERNAME') or ''
    
    # Timeout per connessioni email
    MAIL_TIMEOUT = 30


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}