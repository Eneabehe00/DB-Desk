import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FaPlus, FaSearch, FaFilter, FaSortAmountDown, FaSortAmountUp } from 'react-icons/fa';
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
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    clientId: '',
    assignedToId: ''
  });
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'MEDIUM',
    clientId: '',
    assignedToId: ''
  });
  
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

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
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
      await api.post('/tickets', formData);
      toast.success('Ticket creato con successo');
      setShowModal(false);
      setFormData({
        title: '',
        description: '',
        priority: 'MEDIUM',
        clientId: '',
        assignedToId: ''
      });
      fetchTickets();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nella creazione del ticket');
    }
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
      case 'IN_PROGRESS':
        return 'badge-yellow';
      case 'RESOLVED':
        return 'badge-green';
      case 'CLOSED':
        return 'badge-red';
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
      case 'IN_PROGRESS':
        return 'In Corso';
      case 'RESOLVED':
        return 'Risolto';
      case 'CLOSED':
        return 'Chiuso';
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
      <div className="flex flex-col md:flex-row gap-4">
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
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="btn btn-secondary flex items-center justify-center"
        >
          <FaFilter className="mr-2" />
          Filtri
        </button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Filtra Ticket</h3>
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
                <option value="IN_PROGRESS">In Corso</option>
                <option value="RESOLVED">Risolto</option>
                <option value="CLOSED">Chiuso</option>
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
      )}

      {/* Tickets Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-secondary-200">
            <thead className="bg-secondary-50">
              <tr>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('title')}
                >
                  <div className="flex items-center">
                    Titolo
                    {sortField === 'title' && (
                      sortDirection === 'asc' ? <FaSortAmountUp className="ml-1" /> : <FaSortAmountDown className="ml-1" />
                    )}
                  </div>
                </th>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('client')}
                >
                  <div className="flex items-center">
                    Cliente
                    {sortField === 'client' && (
                      sortDirection === 'asc' ? <FaSortAmountUp className="ml-1" /> : <FaSortAmountDown className="ml-1" />
                    )}
                  </div>
                </th>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center">
                    Stato
                    {sortField === 'status' && (
                      sortDirection === 'asc' ? <FaSortAmountUp className="ml-1" /> : <FaSortAmountDown className="ml-1" />
                    )}
                  </div>
                </th>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('priority')}
                >
                  <div className="flex items-center">
                    Priorità
                    {sortField === 'priority' && (
                      sortDirection === 'asc' ? <FaSortAmountUp className="ml-1" /> : <FaSortAmountDown className="ml-1" />
                    )}
                  </div>
                </th>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('updatedAt')}
                >
                  <div className="flex items-center">
                    Aggiornato
                    {sortField === 'updatedAt' && (
                      sortDirection === 'asc' ? <FaSortAmountUp className="ml-1" /> : <FaSortAmountDown className="ml-1" />
                    )}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-secondary-200">
              {filteredTickets.map((ticket) => (
                <tr key={ticket.id} className="hover:bg-secondary-50 cursor-pointer" onClick={() => window.location.href = `/tickets/${ticket.id}`}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-secondary-900">{ticket.title}</div>
                    <div className="text-xs text-secondary-500 truncate max-w-xs">
                      {ticket.description.substring(0, 60)}
                      {ticket.description.length > 60 ? '...' : ''}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-secondary-700">{ticket.client?.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${getStatusBadgeClass(ticket.status)}`}>
                      {translateStatus(ticket.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${getPriorityBadgeClass(ticket.priority)}`}>
                      {translatePriority(ticket.priority)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-500">
                    {new Date(ticket.updatedAt).toLocaleDateString('it-IT')}
                  </td>
                </tr>
              ))}
              
              {filteredTickets.length === 0 && (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-sm text-secondary-500">
                    Nessun ticket trovato
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Ticket Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-2xl">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Nuovo Ticket</h2>
              <form onSubmit={handleAddTicket}>
                <div className="mb-4">
                  <label htmlFor="title" className="form-label">Titolo *</label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="clientId" className="form-label">Cliente *</label>
                  <select
                    id="clientId"
                    name="clientId"
                    value={formData.clientId}
                    onChange={handleChange}
                    className="form-input"
                    required
                  >
                    <option value="">Seleziona cliente</option>
                    {clients.map(client => (
                      <option key={client.id} value={client.id}>{client.name}</option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label htmlFor="priority" className="form-label">Priorità</label>
                    <select
                      id="priority"
                      name="priority"
                      value={formData.priority}
                      onChange={handleChange}
                      className="form-input"
                    >
                      <option value="LOW">Bassa</option>
                      <option value="MEDIUM">Media</option>
                      <option value="HIGH">Alta</option>
                      <option value="URGENT">Urgente</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="assignedToId" className="form-label">Assegna a</label>
                    <select
                      id="assignedToId"
                      name="assignedToId"
                      value={formData.assignedToId}
                      onChange={handleChange}
                      className="form-input"
                    >
                      <option value="">Non assegnato</option>
                      {users.map(user => (
                        <option key={user.id} value={user.id}>{user.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mb-6">
                  <label htmlFor="description" className="form-label">Descrizione *</label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    className="form-input h-32"
                    required
                  ></textarea>
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="btn btn-secondary"
                  >
                    Annulla
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                  >
                    Crea Ticket
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tickets; 