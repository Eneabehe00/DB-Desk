from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from config import config
import os

# Inizializzazione delle estensioni
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()


def create_app(config_name='default'):
    """Factory pattern per creare l'applicazione Flask"""
    
    app = Flask(__name__)
    
    # Carica la configurazione
    app.config.from_object(config[config_name])
    
    # Inizializza le estensioni
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    
    # Configura Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Devi effettuare il login per accedere a questa pagina.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Context processor per CSRF token
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # Registra i blueprint
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.tickets import tickets_bp
    from app.routes.clients import clients_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp
    from app.routes.docs import docs_bp
    from app.routes.magazzino import magazzino_bp
    from app.routes.macchine import macchine_bp
    from app.routes.fogli_tecnici import fogli_tecnici_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(tickets_bp, url_prefix='/tickets')
    app.register_blueprint(clients_bp, url_prefix='/clients')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(docs_bp, url_prefix='/docs')
    app.register_blueprint(magazzino_bp, url_prefix='/magazzino')
    app.register_blueprint(macchine_bp, url_prefix='/macchine')
    app.register_blueprint(fogli_tecnici_bp, url_prefix='/fogli-tecnici')
    
    # Crea le tabelle del database
    with app.app_context():
        # Assicurati che le cartelle di upload esistano
        os.makedirs(app.config['ATTACHMENTS_FOLDER'], exist_ok=True)
        os.makedirs(app.config['DOCS_FOLDER'], exist_ok=True)
        
        # Crea cartelle per fogli tecnici
        fogli_tecnici_base = os.path.join(app.config['UPLOAD_FOLDER'], 'fogli_tecnici_pdf')
        signatures_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'signatures')
        os.makedirs(fogli_tecnici_base, exist_ok=True)
        os.makedirs(signatures_folder, exist_ok=True)
        
        db.create_all()
        
        # Avvia lo scheduler per l'import email automatico
        from app.services.scheduler import email_scheduler
        email_scheduler.app = app
        email_scheduler.start()
    
    return app