# DB-Desk CSV Import Utility

Questo strumento importa i dati dei clienti e i ticket da CSV esportati da Zoho Desk nel database dell'applicazione DB-Desk.

## Prerequisiti

- Node.js installato
- Database PostgreSQL configurato
- Prisma client configurato

## Installazione

1. Assicurati di essere nella directory del server:
   ```
   cd server
   ```

2. Installa le dipendenze:
   ```
   npm install
   ```

## Configurazione

1. Assicurati che il file `.env` contenga le corrette credenziali del database.
2. Verifica che i file CSV da importare siano presenti nella directory del server:
   - `CLIENTI_1745825255093.csv`
   - `TICKET_1745825264441.csv`

## Esecuzione dell'importazione

Esegui il seguente comando per importare i dati:

```
npm run import
```

oppure:

```
node import-data.js
```

## Note sull'importazione

- Lo script importa prima i clienti e poi i ticket.
- I clienti duplicati (identificati per nome o email) verranno saltati.
- I ticket che fanno riferimento a clienti non trovati verranno saltati.
- Lo script mappa automaticamente gli stati e le priorità di Zoho Desk agli stati e priorità di DB-Desk.
- Durante l'importazione verranno visualizzati log informativi sullo stato dell'operazione.

## Risoluzione dei problemi

Se riscontri errori durante l'importazione:

1. Verifica che i file CSV abbiano il formato corretto e contengano i campi necessari.
2. Controlla che il database sia accessibile e che le credenziali in `.env` siano corrette.
3. Assicurati che lo schema del database sia stato creato correttamente (`prisma migrate deploy`).
4. Verifica i log degli errori per informazioni specifiche sui record che non è stato possibile importare. 