import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FaPlus, FaSearch, FaFilter, FaSortAmountDown, FaSortAmountUp, FaEdit, FaCheck, FaTimes, FaThLarge, FaList } from 'react-icons/fa';
import { useAuth } from '../hooks/useAuth';

const Tickets = () => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [sortDirection, setSortDirection] = useState('desc');
  const [sortField, setSortField] = useState('updatedAt');
  const [clients, setClients] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [viewMode, setViewMode] = useState('list');
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    clientId: '',
    assignedToId: ''
  });
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'OPEN',
    priority: 'MEDIUM',
    clientId: '',
    assignedToId: '',
    clientDetails: {
      name: '',
      email: '',
      phone: '',
      address: '',
      chain: ''
    }
  });
  const [searchClient, setSearchClient] = useState('');
  const [filteredClients, setFilteredClients] = useState([]);
  const [showClientDropdown, setShowClientDropdown] = useState(false);
  
  const { user } = useAuth();

  useEffect(() => {
    fetchTickets();
    fetchClients();
    fetchUsers();
  }, []);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const response = await api.get('/tickets');
      setTickets(response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Errore nel caricamento dei ticket');
      setLoading(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await api.get('/clients');
      setClients(response.data);
    } catch (error) {
      toast.error('Errore nel caricamento dei clienti');
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get('/users');
      setUsers(response.data);
    } catch (error) {
      toast.error('Errore nel caricamento degli utenti');
    }
  };

  const handleSearch = (e) => {
    setSearch(e.target.value);
  };

  const handleClientSearch = (e) => {
    const query = e.target.value;
    setSearchClient(query);
    
    if (query.trim() === '') {
      setFilteredClients([]);
      setShowClientDropdown(false);
      return;
    }
    
    const matchingClients = clients.filter(client => 
      client.name.toLowerCase().includes(query.toLowerCase()) || 
      (client.chain && client.chain.toLowerCase().includes(query.toLowerCase())) ||
      client.email.toLowerCase().includes(query.toLowerCase())
    );
    
    setFilteredClients(matchingClients);
    setShowClientDropdown(true);
  };
  
  const selectClient = (client) => {
    setSearchClient(client.name);
    setShowClientDropdown(false);
    
    setFormData({
      ...formData,
      clientId: client.id,
      clientDetails: {
        name: client.name || '',
        email: client.email || '',
        phone: client.phone || '',
        address: client.address || '',
        chain: client.chain || ''
      }
    });
  };
  
  const clearClientSelection = () => {
    setSearchClient('');
    setFormData({
      ...formData,
      clientId: '',
      clientDetails: {
        name: '',
        email: '',
        phone: '',
        address: '',
        chain: ''
      }
    });
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'clientId') {
      // Se è stato selezionato un cliente esistente, popoliamo i dettagli
      if (value) {
        const selectedClient = clients.find(client => client.id === value);
        if (selectedClient) {
          setFormData({
            ...formData,
            clientId: value,
            clientDetails: {
              name: selectedClient.name || '',
              email: selectedClient.email || '',
              phone: selectedClient.phone || '',
              address: selectedClient.address || '',
              chain: selectedClient.chain || ''
            }
          });
          return;
        }
      } else {
        // Reset dei dettagli cliente se viene deselezionato
        setFormData({
          ...formData,
          clientId: '',
          clientDetails: {
            name: '',
            email: '',
            phone: '',
            address: '',
            chain: ''
          }
        });
        return;
      }
    }
    
    // Per i campi nei dettagli cliente
    if (name.startsWith('client_')) {
      const clientField = name.substring(7); // Rimuove 'client_' dal nome
      setFormData({
        ...formData,
        clientDetails: {
          ...formData.clientDetails,
          [clientField]: value
        }
      });
      return;
    }
    
    // Per tutti gli altri campi
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleFilterChange = (e) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value
    });
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const handleAddTicket = async (e) => {
    e.preventDefault();
    
    try {
      let ticketData = { ...formData };
      let clientId = formData.clientId;
      
      // Se non è stato selezionato un cliente esistente ma sono stati inseriti dettagli
      if (!clientId && formData.clientDetails.name && formData.clientDetails.email) {
        // Crea un nuovo cliente
        const clientResponse = await api.post('/clients', {
          name: formData.clientDetails.name,
          email: formData.clientDetails.email,
          phone: formData.clientDetails.phone,
          address: formData.clientDetails.address,
          chain: formData.clientDetails.chain
        });
        
        clientId = clientResponse.data.id;
        toast.success('Nuovo cliente creato con successo');
      }
      
      // Crea il ticket con il clientId (esistente o appena creato)
      await api.post('/tickets', {
        title: formData.title,
        description: formData.description,
        status: formData.status,
        priority: formData.priority,
        clientId: clientId,
        assignedToId: formData.assignedToId
      });
      
      toast.success('Ticket creato con successo');
      setShowModal(false);
      setFormData({
        title: '',
        description: '',
        status: 'OPEN',
        priority: 'MEDIUM',
        clientId: '',
        assignedToId: '',
        clientDetails: {
          name: '',
          email: '',
          phone: '',
          address: '',
          chain: ''
        }
      });
      fetchTickets();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nella creazione del ticket');
    }
  };

  const handleUpdateStatus = async (newStatus, ticket) => {
    if (!ticket) return;
    
    try {
      await api.put(`/tickets/${ticket.id}`, {
        status: newStatus
      });
      toast.success(`Stato del ticket aggiornato a ${translateStatus(newStatus)}`);
      fetchTickets();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'aggiornamento dello stato');
    }
  };

  const openStatusModal = (ticket, e) => {
    e.stopPropagation(); // Impedisce la navigazione alla pagina del ticket
    setSelectedTicket(ticket);
    setShowStatusModal(true);
  };

  const filteredTickets = tickets.filter(ticket => {
    const matchesSearch = ticket.title.toLowerCase().includes(search.toLowerCase()) || 
                         ticket.description.toLowerCase().includes(search.toLowerCase());
    
    const matchesStatus = !filters.status || ticket.status === filters.status;
    const matchesPriority = !filters.priority || ticket.priority === filters.priority;
    const matchesClient = !filters.clientId || ticket.clientId === filters.clientId;
    const matchesAssignee = !filters.assignedToId || ticket.assignedToId === filters.assignedToId;
    
    return matchesSearch && matchesStatus && matchesPriority && matchesClient && matchesAssignee;
  }).sort((a, b) => {
    let comparison = 0;
    if (sortField === 'title') {
      comparison = a.title.localeCompare(b.title);
    } else if (sortField === 'priority') {
      const priorityOrder = { LOW: 0, MEDIUM: 1, HIGH: 2, URGENT: 3 };
      comparison = priorityOrder[a.priority] - priorityOrder[b.priority];
    } else if (sortField === 'status') {
      const statusOrder = { OPEN: 0, IN_PROGRESS: 1, RESOLVED: 2, CLOSED: 3 };
      comparison = statusOrder[a.status] - statusOrder[b.status];
    } else if (sortField === 'client') {
      comparison = (a.client?.name || '').localeCompare(b.client?.name || '');
    } else if (sortField === 'updatedAt') {
      comparison = new Date(a.updatedAt) - new Date(b.updatedAt);
    }
    
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'OPEN':
        return 'badge-blue';
      case 'CLOSED':
        return 'badge-red';
      case 'PLANNED':
        return 'badge-purple';
      case 'CLOSED_REMOTE':
        return 'badge-slate';
      case 'CLOSED_ONSITE':
        return 'badge-gray';
      case 'PLANNED_ONSITE':
        return 'badge-indigo';
      case 'VERIFYING':
        return 'badge-yellow';
      case 'WAITING_CLIENT':
        return 'badge-orange';
      case 'TO_REPORT':
        return 'badge-green';
      default:
        return 'badge-blue';
    }
  };

  const getPriorityBadgeClass = (priority) => {
    switch (priority) {
      case 'LOW':
        return 'bg-green-100 text-green-800';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800';
      case 'URGENT':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const translateStatus = (status) => {
    switch (status) {
      case 'OPEN':
        return 'Aperto';
      case 'CLOSED':
        return 'Chiuso';
      case 'PLANNED':
        return 'Painificato';
      case 'CLOSED_REMOTE':
        return 'Chiuso Remoto';
      case 'CLOSED_ONSITE':
        return 'Chiuso Onsite';
      case 'PLANNED_ONSITE':
        return 'Previsto onsite';
      case 'VERIFYING':
        return 'In verifica esito';
      case 'WAITING_CLIENT':
        return 'In attesa Cliente';
      case 'TO_REPORT':
        return 'Da riportare';
      default:
        return status;
    }
  };

  const translatePriority = (priority) => {
    switch (priority) {
      case 'LOW':
        return 'Bassa';
      case 'MEDIUM':
        return 'Media';
      case 'HIGH':
        return 'Alta';
      case 'URGENT':
        return 'Urgente';
      default:
        return priority;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Ticket</h1>
          <p className="text-secondary-500">Gestisci i ticket di supporto</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary mt-4 md:mt-0 flex items-center"
        >
          <FaPlus className="mr-2" />
          Nuovo Ticket
        </button>
      </div>

      {/* Search and Filter Bar */}
      <div className="card overflow-hidden mb-6">
        <div className="p-4">
          <div className="mb-4">
            <div className="relative flex-grow">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FaSearch className="text-secondary-400" />
              </div>
              <input
                type="text"
                value={search}
                onChange={handleSearch}
                className="form-input pl-10 w-full"
                placeholder="Cerca ticket..."
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label htmlFor="status" className="form-label">Stato</label>
              <select
                id="status"
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
                className="form-input"
              >
                <option value="">Tutti</option>
                <option value="OPEN">Aperto</option>
                <option value="CLOSED">Chiuso</option>
                <option value="PLANNED">Painificato</option>
                <option value="CLOSED_REMOTE">Chiuso Remoto</option>
                <option value="CLOSED_ONSITE">Chiuso Onsite</option>
                <option value="PLANNED_ONSITE">Previsto onsite</option>
                <option value="VERIFYING">In verifica esito</option>
                <option value="WAITING_CLIENT">In attesa Cliente</option>
                <option value="TO_REPORT">Da riportare</option>
              </select>
            </div>
            <div>
              <label htmlFor="priority" className="form-label">Priorità</label>
              <select
                id="priority"
                name="priority"
                value={filters.priority}
                onChange={handleFilterChange}
                className="form-input"
              >
                <option value="">Tutte</option>
                <option value="LOW">Bassa</option>
                <option value="MEDIUM">Media</option>
                <option value="HIGH">Alta</option>
                <option value="URGENT">Urgente</option>
              </select>
            </div>
            <div>
              <label htmlFor="clientId" className="form-label">Cliente</label>
              <select
                id="clientId"
                name="clientId"
                value={filters.clientId}
                onChange={handleFilterChange}
                className="form-input"
              >
                <option value="">Tutti</option>
                {clients.map(client => (
                  <option key={client.id} value={client.id}>{client.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="assignedToId" className="form-label">Assegnato a</label>
              <select
                id="assignedToId"
                name="assignedToId"
                value={filters.assignedToId}
                onChange={handleFilterChange}
                className="form-input"
              >
                <option value="">Tutti</option>
                <option value="null">Non assegnato</option>
                {users.map(user => (
                  <option key={user.id} value={user.id}>{user.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Sort Controls */}
      <div className="flex flex-wrap items-center justify-between mb-4">
        <div className="text-sm text-secondary-600 mb-2 md:mb-0">
          {filteredTickets.length} ticket trovati
        </div>
        <div className="flex items-center space-x-4">
          {/* View Mode Toggle */}
          <div className="bg-white border border-secondary-200 rounded-lg flex mr-2">
            <button
              onClick={() => setViewMode('list')}
              className={`flex items-center justify-center p-1.5 rounded-l-lg ${
                viewMode === 'list' 
                  ? 'bg-primary-50 text-primary-600' 
                  : 'text-secondary-500 hover:bg-secondary-50'
              }`}
              aria-label="Vista Lista"
              title="Vista Lista"
            >
              <FaList className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('card')}
              className={`flex items-center justify-center p-1.5 rounded-r-lg ${
                viewMode === 'card' 
                  ? 'bg-primary-50 text-primary-600' 
                  : 'text-secondary-500 hover:bg-secondary-50'
              }`}
              aria-label="Vista Card"
              title="Vista Card"
            >
              <FaThLarge className="w-4 h-4" />
            </button>
          </div>
          
          <span className="text-sm text-secondary-600">Ordina per:</span>
          <div className="relative">
            <select
              value={sortField}
              onChange={(e) => {
                setSortField(e.target.value);
                setSortDirection('desc');
              }}
              className="form-select py-1 text-sm appearance-none pr-8 bg-white border border-secondary-200 rounded-lg shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
            >
              <option value="updatedAt">Data aggiornamento</option>
              <option value="title">Titolo</option>
              <option value="priority">Priorità</option>
              <option value="status">Stato</option>
              <option value="client">Cliente</option>
            </select>
            <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
              <svg className="w-4 h-4 text-secondary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
              </svg>
            </div>
          </div>
          <button
            onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
            className="p-1.5 rounded-md hover:bg-secondary-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {sortDirection === 'asc' ? (
              <FaSortAmountUp className="w-4 h-4 text-secondary-600" />
            ) : (
              <FaSortAmountDown className="w-4 h-4 text-secondary-600" />
            )}
          </button>
        </div>
      </div>

      {/* Tickets Views */}
      {filteredTickets.length > 0 ? (
        <>
          {/* List View */}
          {viewMode === 'list' && (
            <div className="space-y-3">
              {filteredTickets.map((ticket) => (
                <div 
                  key={ticket.id} 
                  className="bg-white rounded-xl shadow-sm border border-secondary-200 hover:shadow-md hover:border-primary-200 transition-all overflow-hidden cursor-pointer"
                  onClick={() => window.location.href = `/tickets/${ticket.id}`}
                >
                  <div className="p-4 sm:p-5">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                      {/* Cliente con avatar e dettagli */}
                      <div className="flex items-center sm:w-52 sm:min-w-[13rem]">
                        <div className="flex-shrink-0 h-11 w-11 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center mr-3 text-base font-bold shadow-sm">
                          {ticket.client?.name.charAt(0)}
                        </div>
                        <div className="overflow-hidden">
                          <div className="font-medium text-secondary-900 truncate">{ticket.client?.name}</div>
                          {ticket.client?.chain && (
                            <div className="text-xs text-secondary-500 truncate">{ticket.client.chain}</div>
                          )}
                        </div>
                      </div>

                      {/* Contenuto centrale: titolo e descrizione */}
                      <div className="flex-1 sm:border-l sm:border-r sm:border-secondary-100 sm:pl-4 sm:pr-4">
                        <h3 className="font-semibold text-secondary-900 mb-1 line-clamp-1">{ticket.title}</h3>
                        <p className="text-sm text-secondary-600 line-clamp-2">
                          {ticket.description}
                        </p>
                      </div>

                      {/* Informazioni sulla destra */}
                      <div className="flex flex-wrap sm:flex-nowrap items-center gap-3 sm:w-64 sm:justify-end">
                        {/* Status Badge */}
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-${getStatusBadgeClass(ticket.status)} text-white`}>
                          {translateStatus(ticket.status)}
                        </span>
                        
                        {/* Priority Badge */}
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getPriorityBadgeClass(ticket.priority)}`}>
                          {translatePriority(ticket.priority)}
                        </span>
                        
                        {/* Status Dropdown */}
                        <div 
                          onClick={(e) => e.stopPropagation()}
                          className="inline-block"
                        >
                          <select
                            className="form-select py-1 text-xs bg-white border border-secondary-200 rounded shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                            value={ticket.status}
                            onChange={(e) => {
                              e.stopPropagation();
                              handleUpdateStatus(e.target.value, ticket);
                            }}
                          >
                            <option value="OPEN">Aperto</option>
                            <option value="CLOSED">Chiuso</option>
                            <option value="PLANNED">Painificato</option>
                            <option value="CLOSED_REMOTE">Chiuso Remoto</option>
                            <option value="CLOSED_ONSITE">Chiuso Onsite</option>
                            <option value="PLANNED_ONSITE">Previsto onsite</option>
                            <option value="VERIFYING">In verifica esito</option>
                            <option value="WAITING_CLIENT">In attesa Cliente</option>
                            <option value="TO_REPORT">Da riportare</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    
                    {/* Footer della card: data aggiornamento e assegnazione */}
                    <div className="flex justify-between items-center mt-3 pt-3 border-t border-secondary-100 text-xs text-secondary-500">
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-1 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Aggiornato: {new Date(ticket.updatedAt).toLocaleDateString('it-IT')}
                      </div>
                      
                      <div className="flex items-center">
                        {ticket.assignedTo ? (
                          <>
                            <svg className="w-4 h-4 mr-1 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            Assegnato a: {ticket.assignedTo?.name || "Non specificato"}
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4 mr-1 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Non assegnato
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Card View */}
          {viewMode === 'card' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredTickets.map((ticket) => (
                <div 
                  key={ticket.id} 
                  className="bg-white rounded-xl shadow-sm border border-secondary-200 hover:shadow-md transition-shadow overflow-hidden cursor-pointer"
                  onClick={() => window.location.href = `/tickets/${ticket.id}`}
                >
                  <div className="p-4">
                    {/* Client Info */}
                    <div className="flex items-center mb-3">
                      <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center mr-3 text-sm font-bold">
                        {ticket.client?.name.charAt(0)}
                      </div>
                      <div className="overflow-hidden">
                        <div className="font-medium text-secondary-900 truncate">{ticket.client?.name}</div>
                        {ticket.client?.chain && (
                          <div className="text-xs text-secondary-500 truncate">{ticket.client.chain}</div>
                        )}
                      </div>
                    </div>
                    
                    {/* Ticket Details */}
                    <h3 className="font-semibold text-secondary-900 mb-2 line-clamp-1">{ticket.title}</h3>
                    <p className="text-sm text-secondary-600 mb-4 line-clamp-2">
                      {ticket.description}
                    </p>
                    
                    {/* Tags and Badges */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getPriorityBadgeClass(ticket.priority)}`}>
                        {translatePriority(ticket.priority)}
                      </span>
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-${getStatusBadgeClass(ticket.status)} text-white`}>
                        {translateStatus(ticket.status)}
                      </span>
                    </div>
                    
                    <div className="border-t border-secondary-100 pt-3 flex items-center justify-between">
                      <div className="text-xs text-secondary-500 flex items-center">
                        <svg className="w-4 h-4 mr-1 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {new Date(ticket.updatedAt).toLocaleDateString('it-IT')}
                      </div>
                      
                      {/* Status Dropdown */}
                      <div 
                        onClick={(e) => e.stopPropagation()}
                        className="inline-block"
                      >
                        <select
                          className="form-select py-1 text-xs bg-white border border-secondary-200 rounded shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                          value={ticket.status}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleUpdateStatus(e.target.value, ticket);
                          }}
                        >
                          <option value="OPEN">Aperto</option>
                          <option value="CLOSED">Chiuso</option>
                          <option value="PLANNED">Painificato</option>
                          <option value="CLOSED_REMOTE">Chiuso Remoto</option>
                          <option value="CLOSED_ONSITE">Chiuso Onsite</option>
                          <option value="PLANNED_ONSITE">Previsto onsite</option>
                          <option value="VERIFYING">In verifica esito</option>
                          <option value="WAITING_CLIENT">In attesa Cliente</option>
                          <option value="TO_REPORT">Da riportare</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-secondary-200 p-8 text-center">
          <div className="mx-auto h-16 w-16 text-secondary-400 mb-4">
            <svg className="h-full w-full" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-secondary-900 mb-1">Nessun ticket trovato</h3>
          <p className="text-secondary-500 mb-6">I ticket che crei appariranno qui.</p>
          <button
            onClick={() => setShowModal(true)}
            className="btn btn-primary inline-flex items-center"
          >
            <FaPlus className="mr-2" />
            Crea Nuovo Ticket
          </button>
        </div>
      )}

      {/* Add Ticket Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-60">
          <div className="bg-white rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden transform transition-all">
            <div className="bg-gradient-to-r from-primary-500 to-primary-700 p-6">
              <h2 className="text-xl font-bold text-white">Nuovo Ticket</h2>
              <p className="text-primary-100 text-sm">Compila tutti i campi per creare un nuovo ticket</p>
            </div>
            
            <div className="p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
              <form onSubmit={handleAddTicket} className="space-y-6">
                {/* Selezione Cliente con Ricerca */}
                <div className="relative">
                  <label htmlFor="clientId" className="form-label text-secondary-700">Cliente *</label>
                  <div className="relative">
                    <input
                      type="text"
                      id="clientId"
                      name="clientId"
                      value={searchClient}
                      onChange={handleClientSearch}
                      className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50 pl-10"
                      placeholder="Cerca cliente per nome, email o catena"
                      onFocus={() => setShowClientDropdown(true)}
                    />
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg className="h-5 w-5 text-secondary-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                      </svg>
                    </div>
                    {formData.clientId && (
                      <button
                        type="button"
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-secondary-400 hover:text-secondary-600"
                        onClick={clearClientSelection}
                      >
                        <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      </button>
                    )}
                  </div>
                  
                  {showClientDropdown && filteredClients.length > 0 && (
                    <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base overflow-auto focus:outline-none sm:text-sm">
                      {filteredClients.map(client => (
                        <div 
                          key={client.id} 
                          className="cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-primary-50"
                          onClick={() => selectClient(client)}
                        >
                          <div className="flex items-center">
                            <span className="font-medium block truncate">{client.name}</span>
                            {client.chain && (
                              <span className="text-secondary-500 ml-2 text-sm">({client.chain})</span>
                            )}
                          </div>
                          <span className="text-secondary-400 text-xs block">{client.email}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {showClientDropdown && searchClient && filteredClients.length === 0 && (
                    <div className="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md py-2 px-3 text-secondary-500">
                      Nessun cliente trovato. Inserisci i dettagli del nuovo cliente.
                    </div>
                  )}
                </div>
                
                {/* Dettagli cliente */}
                {(!formData.clientId || formData.clientDetails.name) && (
                  <div className="bg-secondary-50 p-4 rounded-lg border border-secondary-200">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-md font-semibold text-secondary-800">{formData.clientId ? 'Dettagli Cliente' : 'Nuovo Cliente'}</h3>
                      {formData.clientId && (
                        <span className="text-xs px-2 py-1 bg-primary-100 text-primary-800 rounded-full">Cliente Esistente</span>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="client_name" className="form-label text-secondary-700">Nome Cliente {!formData.clientId && '*'}</label>
                        <input
                          type="text"
                          id="client_name"
                          name="client_name"
                          value={formData.clientDetails.name}
                          onChange={handleChange}
                          className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                          required={!formData.clientId}
                          disabled={!!formData.clientId}
                          placeholder="Nome"
                        />
                      </div>
                      <div>
                        <label htmlFor="client_email" className="form-label text-secondary-700">Email Cliente {!formData.clientId && '*'}</label>
                        <input
                          type="email"
                          id="client_email"
                          name="client_email"
                          value={formData.clientDetails.email}
                          onChange={handleChange}
                          className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                          required={!formData.clientId}
                          disabled={!!formData.clientId}
                          placeholder="Email"
                        />
                      </div>
                      <div>
                        <label htmlFor="client_phone" className="form-label text-secondary-700">Telefono</label>
                        <input
                          type="text"
                          id="client_phone"
                          name="client_phone"
                          value={formData.clientDetails.phone}
                          onChange={handleChange}
                          className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                          disabled={!!formData.clientId}
                          placeholder="Telefono"
                        />
                      </div>
                      <div>
                        <label htmlFor="client_chain" className="form-label text-secondary-700">Catena</label>
                        <input
                          type="text"
                          id="client_chain"
                          name="client_chain"
                          value={formData.clientDetails.chain}
                          onChange={handleChange}
                          className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                          placeholder="es. Carrefour, Eurospin, ecc."
                          disabled={!!formData.clientId}
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label htmlFor="client_address" className="form-label text-secondary-700">Indirizzo</label>
                        <textarea
                          id="client_address"
                          name="client_address"
                          value={formData.clientDetails.address}
                          onChange={handleChange}
                          className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                          rows="2"
                          disabled={!!formData.clientId}
                          placeholder="Indirizzo completo"
                        ></textarea>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label htmlFor="status" className="form-label text-secondary-700">Stato</label>
                    <select
                      id="status"
                      name="status"
                      value={formData.status}
                      onChange={handleChange}
                      className="form-select w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    >
                      <option value="OPEN">Aperto</option>
                      <option value="CLOSED">Chiuso</option>
                      <option value="PLANNED">Painificato</option>
                      <option value="CLOSED_REMOTE">Chiuso Remoto</option>
                      <option value="CLOSED_ONSITE">Chiuso Onsite</option>
                      <option value="PLANNED_ONSITE">Previsto onsite</option>
                      <option value="VERIFYING">In verifica esito</option>
                      <option value="WAITING_CLIENT">In attesa Cliente</option>
                      <option value="TO_REPORT">Da riportare</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="priority" className="form-label text-secondary-700">Priorità</label>
                    <select
                      id="priority"
                      name="priority"
                      value={formData.priority}
                      onChange={handleChange}
                      className="form-select w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    >
                      <option value="LOW">Bassa</option>
                      <option value="MEDIUM">Media</option>
                      <option value="HIGH">Alta</option>
                      <option value="URGENT">Urgente</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="assignedToId" className="form-label text-secondary-700">Assegna a</label>
                    <select
                      id="assignedToId"
                      name="assignedToId"
                      value={formData.assignedToId}
                      onChange={handleChange}
                      className="form-select w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    >
                      <option value="">Non assegnato</option>
                      {users.map(user => (
                        <option key={user.id} value={user.id}>{user.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div>
                  <label htmlFor="title" className="form-label text-secondary-700">Titolo *</label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    required
                    placeholder="Inserisci un titolo descrittivo"
                  />
                </div>
                
                <div>
                  <label htmlFor="description" className="form-label text-secondary-700">Descrizione *</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    className="form-textarea w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    rows="6"
                    required
                    placeholder="Descrivi il problema o la richiesta in dettaglio"
                  ></textarea>
                </div>
                
                <div className="flex justify-end space-x-3 pt-4 border-t border-secondary-200">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 bg-white border border-secondary-300 rounded-lg text-secondary-700 hover:bg-secondary-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 shadow-sm transition-colors"
                  >
                    Annulla
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 shadow-sm transition-colors"
                  >
                    Crea Ticket
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Status Change Modal */}
      {showStatusModal && selectedTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-60">
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl overflow-hidden transform transition-all">
            <div className="bg-gradient-to-r from-primary-500 to-primary-700 p-6">
              <h2 className="text-xl font-bold text-white">Modifica Stato Ticket</h2>
              <p className="text-primary-100 text-sm">Seleziona il nuovo stato per il ticket</p>
            </div>
            
            <div className="p-6">
              <div className="mb-4">
                <h3 className="font-medium text-secondary-800 mb-2">{selectedTicket.title}</h3>
                <p className="text-sm text-secondary-600">
                  Cliente: <span className="font-medium">{selectedTicket.client?.name}</span>
                  {selectedTicket.client?.chain && (
                    <span className="text-xs text-secondary-500 ml-2">({selectedTicket.client.chain})</span>
                  )}
                </p>
              </div>
              
              <div className="mb-6">
                <label htmlFor="statusChange" className="form-label text-secondary-700">Stato</label>
                <select
                  id="statusChange"
                  name="statusChange"
                  value={selectedTicket.status}
                  onChange={(e) => handleUpdateStatus(e.target.value, selectedTicket)}
                  className="form-select w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                >
                  <option value="OPEN">Aperto</option>
                  <option value="CLOSED">Chiuso</option>
                  <option value="PLANNED">Painificato</option>
                  <option value="CLOSED_REMOTE">Chiuso Remoto</option>
                  <option value="CLOSED_ONSITE">Chiuso Onsite</option>
                  <option value="PLANNED_ONSITE">Previsto onsite</option>
                  <option value="VERIFYING">In verifica esito</option>
                  <option value="WAITING_CLIENT">In attesa Cliente</option>
                  <option value="TO_REPORT">Da riportare</option>
                </select>
              </div>
              
              <div className="flex justify-end space-x-3 pt-4 border-t border-secondary-200">
                <button
                  onClick={() => setShowStatusModal(false)}
                  className="px-4 py-2 bg-white border border-secondary-300 rounded-lg text-secondary-700 hover:bg-secondary-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 shadow-sm transition-colors"
                >
                  Annulla
                </button>
                <button
                  onClick={() => setShowStatusModal(false)}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 shadow-sm transition-colors"
                >
                  Chiudi
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tickets; 