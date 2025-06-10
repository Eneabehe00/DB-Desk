# DB Desk - Sistema Gestione Ticket

Applicazione web per la gestione dei ticket di supporto, realizzata con React per il frontend e Node.js con Express e Prisma per il backend.

## Configurazione del Database

Il sistema utilizza PostgreSQL tramite Neon.tech. Per configurare la connessione al database:

1. Crea un account su [Neon.tech](https://neon.tech/) se non ne hai già uno
2. Crea un nuovo progetto e un database chiamato "dbdesk"
3. Crea il file `.env` nella cartella `server` con il seguente contenuto:

```
# Configurazione Database
DATABASE_URL="postgresql://username:password@db.neon.tech/dbdesk?sslmode=require"

# JWT per autenticazione
JWT_SECRET="inserisci-un-segreto-complesso-qui"

# Configurazione Server
PORT=5000
```

4. Sostituisci `username`, `password` e l'host del server con i tuoi dati di connessione Neon

## Creazione delle tabelle nel database

Per creare le tabelle nel database, esegui i seguenti comandi:

```bash
cd server
npm install
npx prisma db push
```

Questo comando creerà automaticamente le tabelle definite nello schema Prisma.

## Avvio dell'applicazione

### Per avviare il server (backend):

```bash
cd server
npm install
npm run dev
```

### Per avviare il client (frontend):

```bash
cd client
npm install
npm run dev
```

## Primo accesso

Quando ti registri, il primo utente creato otterrà automaticamente il ruolo di amministratore. 