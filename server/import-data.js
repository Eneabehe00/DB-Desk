import { PrismaClient } from '@prisma/client';
import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const prisma = new PrismaClient();

const STATUS_MAP = {
  'OPEN': 'OPEN',
  'CLOSED': 'CLOSED',
  'CHIUSO': 'CLOSED',
  'CHIUSA ONSITE': 'CLOSED_ONSITE',
  'CHIUSO ONSITE': 'CLOSED_ONSITE',
  'CHIUSA REMOTO': 'CLOSED_REMOTE',
  'CHIUSO REMOTO': 'CLOSED_REMOTE',
  'PLANNED': 'OPEN',
  'PLANNED_ONSITE': 'OPEN',
  'VERIFYING': 'OPEN',
  'WAITING_CLIENT': 'OPEN',
  'APERTO': 'OPEN',
  'IN ATTESA CLIENTE': 'OPEN',
  'DA RIPORTARE': 'OPEN'
};

const PRIORITY_MAP = {
  'BASSA': 'LOW',
  'MEDIA': 'MEDIUM',
  'ALTA': 'HIGH',
  'URGENTE': 'URGENT'
};

async function deleteAllTicketsAndClients() {
  console.log('Deleting all existing tickets and clients...');
  
  // Prima eliminiamo tutti i ticket (le foreign keys)
  const ticketsDeleted = await prisma.ticket.deleteMany({});
  console.log(`Deleted ${ticketsDeleted.count} tickets`);
  
  // Poi eliminiamo tutti i clienti
  const clientsDeleted = await prisma.client.deleteMany({});
  console.log(`Deleted ${clientsDeleted.count} clients`);
}

async function importClients() {
  console.log('Importing clients...');
  const clientsFilePath = path.join(__dirname, 'CLIENTI_1745825255093.csv');
  const clientsData = fs.readFileSync(clientsFilePath);
  
  const clients = parse(clientsData, {
    columns: true,
    skip_empty_lines: true,
    bom: true
  });
  
  let importedCount = 0;
  let errorCount = 0;
  
  // Raggruppa i client con nomi simili
  const clientGroups = {};
  
  for (const client of clients) {
    const name = (client['Last Name'] || client['Ragione Sociale'] || '').trim();
    if (name) {
      const normName = name.toLowerCase().replace(/\s+/g, ' ');
      if (!clientGroups[normName]) {
        clientGroups[normName] = [];
      }
      clientGroups[normName].push(client);
    }
  }
  
  // Map per tenere traccia degli ID dei clienti unificati
  const mergedClientIds = new Map();
  
  // Importa i client raggruppati
  for (const normName in clientGroups) {
    try {
      const clientsGroup = clientGroups[normName];
      // Usa il primo client del gruppo come riferimento
      const primaryClient = clientsGroup[0];
      
      // Crea o aggiorna il client primario
      const clientData = {
        name: primaryClient['Last Name'] || primaryClient['Ragione Sociale'] || '',
        email: `${normName.replace(/\s+/g, '_')}@placeholder.com`,  // Usa un email univoco basato sul nome normalizzato
        phone: '',  // Lascia vuoto come richiesto
        address: '',  // Lascia vuoto come richiesto
        chain: primaryClient['Nome Catena'] || null
      };
      
      // Ensure name is not empty
      if (!clientData.name || clientData.name.trim() === '') {
        clientData.name = `Cliente ${primaryClient['CLIENTI Id'] || importedCount}`;
      }
      
      // Usa l'ID del primo client del gruppo
      const primaryClientId = primaryClient['CLIENTI Id'];
      
      if (primaryClientId) {
        // Create with specified id
        const newClient = await prisma.client.create({
          data: {
            id: primaryClientId,
            ...clientData
          }
        });
        console.log(`Created unified client with id ${primaryClientId}: ${clientData.name}`);
        
        // Salva le associazioni tra gli ID dei client duplicati e l'ID primario
        for (const dupClient of clientsGroup) {
          if (dupClient['CLIENTI Id'] && dupClient['CLIENTI Id'] !== primaryClientId) {
            mergedClientIds.set(dupClient['CLIENTI Id'], primaryClientId);
            console.log(`Mapped duplicate client ID ${dupClient['CLIENTI Id']} to primary ID ${primaryClientId}`);
          }
        }
      } else {
        // No ID specified, let Prisma generate one
        const newClient = await prisma.client.create({
          data: clientData
        });
        
        // Salva le associazioni per eventuali altri client nel gruppo
        for (const dupClient of clientsGroup) {
          if (dupClient['CLIENTI Id']) {
            mergedClientIds.set(dupClient['CLIENTI Id'], newClient.id);
            console.log(`Mapped duplicate client ID ${dupClient['CLIENTI Id']} to generated ID ${newClient.id}`);
          }
        }
        
        console.log(`Created unified client: ${clientData.name}`);
      }
      
      importedCount++;
    } catch (error) {
      console.error(`Error importing unified client: ${normName}`, error);
      errorCount++;
    }
  }
  
  console.log(`Successfully imported ${importedCount} unified clients, with ${errorCount} errors`);
  console.log(`Mapped ${mergedClientIds.size} duplicate client IDs to primary IDs`);
  
  return { importedCount, mergedClientIds };
}

async function getOrCreateAdminUser() {
  // Create a default admin user if none exists
  let admin = await prisma.user.findFirst({
    where: { role: 'ADMIN' }
  });
  
  if (!admin) {
    admin = await prisma.user.create({
      data: {
        email: 'admin@dbdesk.com',
        password: '$2b$10$EpRnTzVlqHNP0.fUbXUwSOyuiXe/QLSUG6xNekdHgTGmrpHEfIoxm', // 'password'
        name: 'Admin',
        role: 'ADMIN'
      }
    });
    console.log('Created default admin user');
  }
  
  return admin;
}

async function importTickets(mergedClientIds) {
  console.log('Importing tickets...');
  const ticketsFilePath = path.join(__dirname, 'TICKET_1745825264441.csv');
  const ticketsData = fs.readFileSync(ticketsFilePath);
  
  const tickets = parse(ticketsData, {
    columns: true,
    skip_empty_lines: true,
    bom: true
  });
  
  // Get or create admin user for ticket assignment
  const admin = await getOrCreateAdminUser();
  
  let importedCount = 0;
  let errorCount = 0;
  let notFoundCount = 0;
  
  // Get all clients to match with tickets
  const allClients = await prisma.client.findMany();
  console.log(`Found ${allClients.length} clients in database`);
  
  // Create a map of client IDs for quick lookup
  const clientIdMap = new Map();
  allClients.forEach(client => {
    clientIdMap.set(client.id, client);
  });
  
  // Create a map of client names per ID for further matching
  const clientNameMap = new Map();
  allClients.forEach(client => {
    if (client.name) {
      // Normalizziamo i nomi per il confronto
      const normName = client.name.toLowerCase().replace(/\s+/g, ' ');
      clientNameMap.set(normName, client.id);
    }
  });
  
  // For logging which clients have tickets
  const clientsWithTickets = new Set();
  
  for (const ticket of tickets) {
    try {
      // La chiave di corrispondenza è "Nome CLIENTI Id" nel ticket, che corrisponde al "CLIENTI Id" nei clienti
      let clientId = ticket['Nome CLIENTI Id'];
      
      // Controlla se questo ID è stato unificato con un altro client
      if (mergedClientIds.has(clientId)) {
        const originalId = clientId;
        clientId = mergedClientIds.get(clientId);
        console.log(`Using unified client ID ${clientId} instead of duplicate ID ${originalId}`);
      }
      
      let client = clientId ? clientIdMap.get(clientId) : null;
      
      if (!client) {
        // Se non troviamo una corrispondenza diretta, proviamo con il nome
        if (ticket['Nome CLIENTI']) {
          const clientName = ticket['Nome CLIENTI'].toLowerCase().replace(/\s+/g, ' ');
          
          // Cerca una corrispondenza esatta nel map normalizzato
          if (clientNameMap.has(clientName)) {
            clientId = clientNameMap.get(clientName);
            client = clientIdMap.get(clientId);
            console.log(`Found client by exact normalized name: ${clientName} -> ID: ${clientId}`);
          }
          
          // Se ancora non trovato, cerca corrispondenze parziali
          if (!client) {
            // Cerca un client con nome simile
            for (const [id, clientObj] of clientIdMap.entries()) {
              if (clientObj.name) {
                const normClientName = clientObj.name.toLowerCase().replace(/\s+/g, ' ');
                if (normClientName === clientName ||
                    normClientName.includes(clientName) || 
                    clientName.includes(normClientName)) {
                  clientId = id;
                  client = clientObj;
                  console.log(`Found client by partial name matching: ${ticket['Nome CLIENTI']} -> ${clientObj.name}`);
                  break;
                }
              }
            }
          }
        }
      }
      
      if (!client) {
        notFoundCount++;
        console.log(`Client not found for ticket: ${ticket['TICKET Number'] || ticket['TICKET Id'] || 'unknown'} - Cliente ID: ${ticket['Nome CLIENTI Id'] || 'n/a'} - Nome: ${ticket['Nome CLIENTI'] || 'n/a'}`);
        continue;
      }
      
      // Track which clients have tickets
      clientsWithTickets.add(clientId);
      
      // Map CSV fields to Ticket schema fields con la logica modificata per gli stati
      let status = STATUS_MAP[ticket['Status'] || ticket['Stato'] || ''] || 'OPEN';
      const priority = PRIORITY_MAP[ticket['Priority'] || ticket['Priorità'] || ''] || 'MEDIUM';
      
      const ticketData = {
        title: ticket['Subject'] || 'No Subject',
        description: ticket['Description'] || '',
        status,
        priority,
        clientId,
        assignedToId: admin.id,
        createdById: admin.id
      };
      
      // Create new ticket with specified id or let Prisma generate one
      if (ticket['TICKET Id']) {
        // Create with specified id
        await prisma.ticket.create({
          data: {
            id: ticket['TICKET Id'],
            ...ticketData
          }
        });
        console.log(`Created ticket with id ${ticket['TICKET Id']} for ${client.name}: ${ticketData.title} (Status: ${status})`);
      } else {
        // No ID specified, let Prisma generate one
        await prisma.ticket.create({
          data: ticketData
        });
        console.log(`Created ticket for ${client.name}: ${ticketData.title}`);
      }
      
      importedCount++;
    } catch (error) {
      console.error(`Error importing ticket: ${ticket['TICKET Number'] || ticket['TICKET Id']}`, error);
      errorCount++;
    }
  }
  
  console.log(`Successfully imported ${importedCount} tickets, with ${errorCount} errors`);
  console.log(`Clients without matching tickets: ${notFoundCount}`);
  console.log(`Number of clients with tickets: ${clientsWithTickets.size}`);
  
  return importedCount;
}

async function main() {
  try {
    // Prima eliminiamo tutti i ticket e i clienti esistenti
    await deleteAllTicketsAndClients();
    
    // Poi importiamo i clienti unificati e otteniamo la mappa per i client unificati
    const { importedCount, mergedClientIds } = await importClients();
    
    if (importedCount > 0) {
      // Importiamo i ticket e li associamo ai clienti unificati
      await importTickets(mergedClientIds);
    } else {
      console.log('No clients were imported, skipping ticket import');
    }
    
    console.log('Import completed successfully');
  } catch (error) {
    console.error('Import failed:', error);
  } finally {
    await prisma.$disconnect();
  }
}

main(); 