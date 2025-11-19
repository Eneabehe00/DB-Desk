# DB-Desk - Sistema di Gestione Ticket

Sistema completo per la gestione di ticket e clienti, sviluppato in Python con Flask per l'utilizzo in rete locale.

## 🚀 Caratteristiche

- **Sistema di autenticazione** completo (login/registrazione)
- **Dashboard** con statistiche e grafici in tempo reale
- **Gestione ticket** con CRUD completo, filtri, assegnazioni, allegati e checklist
- **Gestione clienti** con anagrafica completa
- **Report e statistiche** avanzate
- **Pagina impostazioni** per configurazione sistema e monitor di sistema
- **Design responsive** con Bootstrap 5
- **Database MySQL** locale
- **Docs**: Archivio documenti con categorie, ricerca, upload e viewer
- **Import email (IMAP)** opzionale per creare ticket da Outlook/Office365
- **Accessibile da rete locale**

## 📋 Prerequisiti

- Python 3.8+ 
- MySQL Server 5.7+ o MariaDB 10.3+
- Browser web moderno

## 🛠️ Installazione

### 1. Clona o scarica il progetto
```bash
git clone <url-repo>
cd DB-Desk
```

### 2. Crea ambiente virtuale Python
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Installa le dipendenze
```bash
pip install -r requirements.txt
```

### 4. Configura MySQL

#### Opzione A: Configurazione automatica
```sql
-- Accedi a MySQL come root
mysql -u root -p

-- Esegui lo script di setup
source db_setup.sql
```

#### Opzione B: Configurazione manuale
```sql
CREATE DATABASE dbdesk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- Opzionale: crea utente dedicato
CREATE USER 'dbdesk_user'@'localhost' IDENTIFIED BY 'tua_password';
GRANT ALL PRIVILEGES ON dbdesk.* TO 'dbdesk_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configura variabili d'ambiente

Crea un file `.env` nella directory root:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=tua_password_mysql
DB_NAME=dbdesk
DB_PORT=3306

# Flask Configuration
SECRET_KEY=cambia-questa-chiave-segreta-in-produzione
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true
```

### 6. Inizializza il database
```bash
# Prima esecuzione per creare le tabelle
python run.py
# Fermia l'app (Ctrl+C) dopo che si avvia

# Inserisci dati di test (opzionale)
python init_data.py
```

## 🎯 Utilizzo

### Avvio dell'applicazione
```bash
python run.py
```

L'applicazione sarà accessibile su:
- **Locale**: http://localhost:5000
- **Rete locale**: http://[IP_TUA_MACCHINA]:5000

### Credenziali di default (se hai eseguito init_data.py)
- **Admin**: `admin` / `admin123`
- **Utente**: `mario.rossi` / `password123`

## 🌐 Accesso dalla Rete Locale

Per rendere l'app accessibile da altri dispositivi sulla rete:

1. **Trova il tuo IP locale**:
   ```bash
   # Windows
   ipconfig
   
   # Linux/Mac
   ifconfig
   ```

2. **Configura il firewall** (se necessario):
   - Windows: Aggiungi eccezione per porta 5000
   - Linux: `sudo ufw allow 5000`

3. **Accedi dall'altro dispositivo**:
   `http://192.168.X.X:5000` (sostituisci con il tuo IP)

## 📁 Struttura del Progetto

```
DB-Desk/
├── app/
│   ├── __init__.py           # Factory Flask app
│   ├── models/               # Modelli database
│   │   ├── user.py
│   │   ├── cliente.py
│   │   └── ticket.py
│   ├── routes/               # Blueprint routes
│   │   ├── auth.py           # Autenticazione
│   │   ├── main.py           # Dashboard
│   │   ├── tickets.py        # Gestione ticket
│   │   ├── clients.py        # Gestione clienti
│   │   ├── reports.py        # Report
│   │   └── settings.py       # Impostazioni
│   ├── forms/                # Form WTF
│   │   ├── auth.py
│   │   ├── ticket.py
│   │   └── cliente.py
│   ├── templates/            # Template HTML
│   └── static/               # File statici (CSS, JS, immagini)
├── config.py                 # Configurazioni
├── run.py                    # Entry point
├── requirements.txt          # Dipendenze Python
├── init_data.py             # Script dati di test
├── db_setup.sql             # Setup database
└── README.md                # Questo file
```

## 🔧 Configurazione Avanzata

### Configurazione per Produzione

1. **Modifica `.env`**:
   ```env
   FLASK_DEBUG=false
   SECRET_KEY=chiave-molto-sicura-e-lunga
   ```

2. **Usa un server web** (Nginx + Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

### Backup del Database
```bash
# Backup
mysqldump -u root -p dbdesk > backup_dbdesk.sql

# Ripristino
mysql -u root -p dbdesk < backup_dbdesk.sql
```

## 🔍 Funzionalità Principali

### Dashboard
- Statistiche in tempo reale
- Grafici interattivi
- Widget informativi
- Quick actions

### Gestione Ticket
- CRUD completo
- Sistema di priorità e stati
- Assegnazione utenti
- Filtri avanzati
- Timeline attività
- Export CSV
- Allegati (upload/download/elimina)
- Checklist/sotto-attività

### Gestione Clienti
- Anagrafica completa
- Gestione contatti
- Storico ticket
- Statistiche cliente
- Export dati

### Report
- Statistiche ticket
- Performance utenti
- Analisi clienti
- Grafici interattivi
- Export report

### Impostazioni
- Gestione utenti (admin)
- Configurazioni sistema
- Backup database
- Monitoraggio sistema

### Docs
- Categorie: manuali, contratti, procedure, altri
- Ricerca e filtri per nome
- Upload documenti
- Visualizzazione inline (browser) con apertura in nuova scheda

### Import Email (IMAP)
Per creare ticket automaticamente dalle email ricevute su Outlook/Office365:

#### 1. Configurazione .env
Copia il template da `env_template.txt` nel tuo `.env` e compila:

```env
# Abilita import email
EMAIL_IMPORT_ENABLED=True
EMAIL_IMAP_HOST=imap.office365.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_SSL=True
# IMPORTANTE: Se hai errori SSL certificate verify failed, imposta a False
EMAIL_IMAP_SSL_VERIFY_CERTS=False
EMAIL_USERNAME=tuo_email@dominio.com
EMAIL_PASSWORD=tua_password_email
EMAIL_FOLDER=INBOX
# Per sottocartelle: INBOX/Assistenza (viene automaticamente provato con diversi separatori / e .)
# Usa il pulsante "Test Connessione" nelle impostazioni per vedere le cartelle disponibili
EMAIL_DEFAULT_CLIENT_ID=1

# Filtri opzionali
EMAIL_ALLOWED_SENDERS=mario.rossi@example.com,@clienti.com
EMAIL_SUBJECT_KEYWORDS=supporto,problema,errore
EMAIL_SKIP_KEYWORDS=newsletter,marketing,spam
EMAIL_AUTO_IMPORT=False
```

#### 2. Come funziona
- **Modalità Manuale** (`EMAIL_AUTO_IMPORT=False`): Le email vengono salvate come bozze e puoi decidere manualmente quali convertire in ticket tramite interfaccia web
- **Modalità Automatica** (`EMAIL_AUTO_IMPORT=True`): Le email che passano i filtri vengono convertite automaticamente in ticket

#### 3. Filtri disponibili
- **Mittenti permessi**: Lista di email o domini (usa `@dominio.com` per interi domini)
- **Parole chiave oggetto**: L'email deve contenere almeno una di queste parole nell'oggetto
- **Parole da escludere**: Se trova queste parole ignora l'email
- **Cliente di default**: ID del cliente a cui assegnare i ticket creati da email

#### 4. Test Connessione IMAP
Prima di abilitare l'import, testa la connessione per verificare:
- Credenziali corrette
- Cartelle disponibili sul server
- Formato corretto dei nomi delle cartelle

**Come fare:**
1. Vai in Settings → Import Email
2. Clicca "Test Connessione"
3. Se ha successo, vedrai le cartelle disponibili
4. Scegli la cartella corretta dal `.env` (es. `INBOX/Assistenza`)

#### 5. Esecuzione Import
- **Manuale**: Vai in Settings → Import Email e clicca "Importa Ora"
- **Automatica**: Imposta un cron job che chiama `app.services.email_importer.import_new_emails()`
- **Endpoint API**: `POST /settings/email_import/run` (solo admin)

#### 6. Gestione Email
- Accedi a Settings → Import Email per vedere statistiche e email in attesa
- Converti manualmente le email in ticket
- Visualizza cronologia import e ticket creati

#### 6. Risoluzione Problemi SSL
Se ricevi errori come `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed`:

1. **Soluzione Rapida**: Aggiungi nel tuo `.env`:
   ```env
   EMAIL_IMAP_SSL_VERIFY_CERTS=False
   ```

2. **Cause comuni**:
   - Certificati SSL aziendali o self-signed
   - Proxy aziendale che intercetta il traffico SSL
   - Certificati di sistema Windows non aggiornati

3. **Soluzioni alternative**:
   - Aggiorna i certificati di sistema
   - Configura il proxy aziendale se necessario
   - Usa una connessione non SSL (sconsigliato): `EMAIL_IMAP_SSL=False` e `EMAIL_IMAP_PORT=143`

### Upload e limiti
- Cartelle create automaticamente: `uploads/attachments`, `uploads/docs`
- Variabili `.env` opzionali:
  - `MAX_CONTENT_LENGTH_BYTES` (default 26214400 = 25MB)
  - `ALLOWED_DOC_EXTENSIONS` (default `pdf,doc,docx,xls,xlsx,ppt,pptx,txt,md,png,jpg,jpeg,gif`)
  - `ALLOWED_ATTACHMENT_EXTENSIONS` (default `pdf,txt,md,png,jpg,jpeg,gif,zip,rar,7z,log,json,xml`)

## 🚨 Troubleshooting

### Errore di connessione al database
```
- Verifica che MySQL sia in esecuzione
- Controlla le credenziali in .env
- Assicurati che il database esista
```

### Errore di permessi
```bash
# Linux/Mac - problemi di permessi file
chmod +x run.py
chmod +x init_data.py
```

### App non accessibile da rete
```
- Verifica firewall
- Controlla FLASK_HOST=0.0.0.0 in .env
- Verifica IP locale
```

### Errore dipendenze Python
```bash
# Aggiorna pip
pip install --upgrade pip

# Reinstalla dipendenze
pip install -r requirements.txt --force-reinstall
```

## 📝 Log e Debug

Per abilitare i log dettagliati:
```env
FLASK_DEBUG=true
```

I log verranno mostrati nel terminale dove esegui `python run.py`.

## 🔒 Sicurezza

- **Password**: Cambiale dalle credenziali di default
- **SECRET_KEY**: Usa una chiave sicura in produzione
- **Database**: Configura utente dedicato con permessi limitati
- **Firewall**: Limita l'accesso alle porte necessarie

## 🤝 Supporto

Per problemi o domande:
1. Controlla la sezione Troubleshooting
2. Verifica i log per errori specifici
3. Controlla la configurazione MySQL e Python

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT.

## 🔄 Versioni

- **v1.0**: Release iniziale con tutte le funzionalità base

---

**DB-Desk** - Sistema di gestione ticket per reti locali 🎫