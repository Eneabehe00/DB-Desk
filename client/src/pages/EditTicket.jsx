import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FaArrowLeft, FaUser, FaBuilding, FaEnvelope, FaPhone, FaMapMarkerAlt, FaTag, FaClock, FaHistory } from 'react-icons/fa';
import { useAuth } from '../hooks/useAuth';

// Componente dropdown personalizzato
const CustomDropdown = ({ id, name, value, onChange, options, label, className = "", icon }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    // Chiude il dropdown quando si clicca fuori
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1.5">
          {label}
        </label>
      )}
      <button
        id={id}
        type="button"
        className={`w-full flex items-center justify-between px-4 py-2.5 border border-gray-300 bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all ${className}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center">
          {icon && <span className="mr-2 text-gray-500">{icon}</span>}
          <span className="truncate text-sm">
            {value ? options.find(option => option.value === value)?.label || "Seleziona..." : "Seleziona..."}
          </span>
        </div>
        <svg className={`ml-2 h-5 w-5 text-gray-400 transform transition-transform ${isOpen ? 'rotate-180' : ''}`} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-xl max-h-60 overflow-auto">
          {options.map((option) => (
            <div
              key={option.value}
              className={`px-4 py-2.5 cursor-pointer hover:bg-gray-50 text-sm ${value === option.value ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700'}`}
              onClick={() => {
                onChange({ target: { name, value: option.value } });
                setIsOpen(false);
              }}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const EditTicket = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: '',
    priority: '',
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
  const [clients, setClients] = useState([]);
  const [users, setUsers] = useState([]);
  const [ticket, setTicket] = useState(null);
  const searchInputRef = useRef(null);

  useEffect(() => {
    fetchTicket();
    fetchClients();
    fetchUsers();
  }, [id]);

  const fetchTicket = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/tickets/${id}`);
      const ticket = response.data;
      setTicket(ticket);
      
      // Set the form data from the ticket
      setFormData({
        title: ticket.title,
        description: ticket.description,
        status: ticket.status,
        priority: ticket.priority,
        clientId: ticket.clientId,
        assignedToId: ticket.assignedToId || '',
        clientDetails: {
          name: ticket.client?.name || '',
          email: ticket.client?.email || '',
          phone: ticket.client?.phone || '',
          address: ticket.client?.address || '',
          chain: ticket.client?.chain || ''
        }
      });
      
      // Set the search client field
      if (ticket.client) {
        setSearchClient(ticket.client.name);
      }
      
      setLoading(false);
    } catch (error) {
      toast.error('Errore nel caricamento del ticket');
      navigate('/tickets');
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

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
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
    
    // Focus sul campo di ricerca cliente dopo il reset
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  };

  const handleUpdateTicket = async (e) => {
    e.preventDefault();
    
    if (!formData.clientId) {
      toast.error('Seleziona un cliente');
      return;
    }
    
    try {
      await api.put(`/tickets/${id}`, formData);
      toast.success('Ticket aggiornato con successo');
      navigate(`/tickets/${id}`);
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'aggiornamento del ticket');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'OPEN':
        return <span className="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>;
      case 'CLOSED':
        return <span className="w-2 h-2 rounded-full bg-gray-500 mr-2"></span>;
      case 'PLANNED':
        return <span className="w-2 h-2 rounded-full bg-purple-500 mr-2"></span>;
      case 'CLOSED_REMOTE':
        return <span className="w-2 h-2 rounded-full bg-slate-500 mr-2"></span>;
      case 'CLOSED_ONSITE':
        return <span className="w-2 h-2 rounded-full bg-gray-500 mr-2"></span>;
      case 'PLANNED_ONSITE':
        return <span className="w-2 h-2 rounded-full bg-indigo-500 mr-2"></span>;
      case 'VERIFYING':
        return <span className="w-2 h-2 rounded-full bg-yellow-500 mr-2"></span>;
      case 'WAITING_CLIENT':
        return <span className="w-2 h-2 rounded-full bg-orange-500 mr-2"></span>;
      case 'TO_REPORT':
        return <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>;
      default:
        return <span className="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>;
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'LOW':
        return <span className="w-2 h-2 rounded-full bg-green-500 mr-2"></span>;
      case 'MEDIUM':
        return <span className="w-2 h-2 rounded-full bg-yellow-500 mr-2"></span>;
      case 'HIGH':
        return <span className="w-2 h-2 rounded-full bg-orange-500 mr-2"></span>;
      case 'URGENT':
        return <span className="w-2 h-2 rounded-full bg-red-500 mr-2"></span>;
      default:
        return <span className="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex justify-center items-center bg-gray-50">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-600">Caricamento...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center">
            <Link to={`/tickets/${id}`} className="flex items-center text-gray-500 hover:text-primary-600 transition-colors mr-4">
              <FaArrowLeft className="mr-2 h-4 w-4" />
              <span className="text-sm">Torna al ticket</span>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">Modifica Ticket #{id.substring(0, 8)}</h1>
          </div>
          <p className="mt-2 text-sm text-gray-500">Modifica le informazioni del ticket</p>
        </div>

        {/* Form Container */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-800">Informazioni Ticket</h2>
            {ticket && (
              <div className="flex items-center text-sm text-gray-500">
                <FaHistory className="mr-1.5 h-3.5 w-3.5" />
                <span>Creato: {formatDate(ticket.createdAt)}</span>
                <span className="mx-2">•</span>
                <FaClock className="mr-1.5 h-3.5 w-3.5" />
                <span>Aggiornato: {formatDate(ticket.updatedAt)}</span>
              </div>
            )}
          </div>
          
          <form onSubmit={handleUpdateTicket} className="p-6">
            <div className="grid grid-cols-1 gap-y-8">
              {/* Selezione Cliente con Ricerca */}
              <div className="space-y-6">
                <div>
                  <label htmlFor="clientSearch" className="block text-sm font-medium text-gray-700 mb-1.5">
                    Cliente <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <FaUser className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                      ref={searchInputRef}
                      type="text"
                      id="clientSearch"
                      value={searchClient}
                      onChange={handleClientSearch}
                      placeholder="Cerca cliente per nome, catena o email..."
                      className="pl-10 pr-10 block w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    />
                    {searchClient && (
                      <button
                        type="button"
                        onClick={clearClientSelection}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      </button>
                    )}
                  </div>
                  
                  {/* Dropdown dei risultati */}
                  {showClientDropdown && filteredClients.length > 0 && (
                    <div className="absolute z-10 mt-1 w-full max-w-2xl bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
                      {filteredClients.map(client => (
                        <div
                          key={client.id}
                          className="px-4 py-3 cursor-pointer hover:bg-gray-50 border-b border-gray-100 last:border-0 transition-colors"
                          onClick={() => selectClient(client)}
                        >
                          <div className="flex items-start">
                            <div className="flex-shrink-0">
                              <div 
                                className="h-10 w-10 rounded-full flex items-center justify-center text-sm font-medium"
                                style={{
                                  backgroundColor: `hsl(${client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 85%, 90%)`,
                                  color: `hsl(${client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 75%, 35%)`
                                }}
                              >
                                {client.name.charAt(0)}
                              </div>
                            </div>
                            <div className="ml-3">
                              <div className="font-medium text-gray-900">{client.name}</div>
                              <div className="flex text-xs text-gray-500 mt-0.5">
                                <FaEnvelope className="h-3 w-3 mr-1 mt-0.5" />
                                {client.email}
                              </div>
                              {client.chain && (
                                <div className="flex text-xs text-gray-500 mt-0.5">
                                  <FaBuilding className="h-3 w-3 mr-1 mt-0.5" />
                                  {client.chain}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {showClientDropdown && filteredClients.length === 0 && searchClient && (
                    <div className="absolute z-10 mt-1 w-full max-w-2xl bg-white border border-gray-200 rounded-md shadow-lg p-4 text-center">
                      <p className="text-gray-500 text-sm">Nessun cliente trovato</p>
                      <p className="text-gray-400 text-xs mt-1">Prova con un altro termine di ricerca</p>
                    </div>
                  )}
                </div>
                
                {/* Dettagli del cliente selezionato */}
                {formData.clientId && (
                  <div className="bg-primary-50 border border-primary-100 rounded-lg p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-semibold text-gray-900">Dettagli cliente</h3>
                      <button
                        type="button"
                        onClick={clearClientSelection}
                        className="text-xs text-primary-600 hover:text-primary-800 px-2 py-1 rounded-md bg-primary-100 hover:bg-primary-200 transition-colors"
                      >
                        Cambia cliente
                      </button>
                    </div>
                    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="flex items-start">
                        <div className="flex-shrink-0">
                          <FaUser className="h-5 w-5 text-primary-600" />
                        </div>
                        <div className="ml-3">
                          <p className="text-xs text-gray-500">Nome</p>
                          <p className="text-sm font-medium text-gray-900">{formData.clientDetails.name}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-start">
                        <div className="flex-shrink-0">
                          <FaEnvelope className="h-5 w-5 text-primary-600" />
                        </div>
                        <div className="ml-3">
                          <p className="text-xs text-gray-500">Email</p>
                          <p className="text-sm font-medium text-gray-900">{formData.clientDetails.email}</p>
                        </div>
                      </div>
                      
                      {formData.clientDetails.phone && (
                        <div className="flex items-start">
                          <div className="flex-shrink-0">
                            <FaPhone className="h-5 w-5 text-primary-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-xs text-gray-500">Telefono</p>
                            <p className="text-sm font-medium text-gray-900">{formData.clientDetails.phone}</p>
                          </div>
                        </div>
                      )}
                      
                      {formData.clientDetails.chain && (
                        <div className="flex items-start">
                          <div className="flex-shrink-0">
                            <FaBuilding className="h-5 w-5 text-primary-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-xs text-gray-500">Catena</p>
                            <p className="text-sm font-medium text-gray-900">{formData.clientDetails.chain}</p>
                          </div>
                        </div>
                      )}
                      
                      {formData.clientDetails.address && (
                        <div className="flex items-start sm:col-span-2">
                          <div className="flex-shrink-0">
                            <FaMapMarkerAlt className="h-5 w-5 text-primary-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-xs text-gray-500">Indirizzo</p>
                            <p className="text-sm font-medium text-gray-900">{formData.clientDetails.address}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Titolo */}
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Titolo Ticket <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  className="block w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  placeholder="Inserisci un titolo descrittivo"
                  required
                />
              </div>
              
              {/* Descrizione */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Descrizione <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  className="block w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  rows="6"
                  placeholder="Descrivi il problema in dettaglio..."
                  required
                ></textarea>
                <p className="mt-1.5 text-xs text-gray-500">
                  Fornisci una descrizione chiara e dettagliata del problema, inclusi eventuali messaggi di errore, passaggi per riprodurre il problema e altre informazioni rilevanti.
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Stato */}
                <CustomDropdown
                  id="status"
                  name="status"
                  label="Stato"
                  value={formData.status}
                  onChange={handleChange}
                  icon={getStatusIcon(formData.status)}
                  options={[
                    { value: 'OPEN', label: 'Aperto' },
                    { value: 'PLANNED', label: 'Pianificato' },
                    { value: 'PLANNED_ONSITE', label: 'Previsto onsite' },
                    { value: 'VERIFYING', label: 'In verifica esito' },
                    { value: 'WAITING_CLIENT', label: 'In attesa Cliente' },
                    { value: 'TO_REPORT', label: 'Da riportare' },
                    { value: 'CLOSED', label: 'Chiuso' },
                    { value: 'CLOSED_REMOTE', label: 'Chiuso Remoto' },
                    { value: 'CLOSED_ONSITE', label: 'Chiuso Onsite' }
                  ]}
                />
                
                {/* Priorità */}
                <CustomDropdown
                  id="priority"
                  name="priority"
                  label="Priorità"
                  value={formData.priority}
                  onChange={handleChange}
                  icon={getPriorityIcon(formData.priority)}
                  options={[
                    { value: 'LOW', label: 'Bassa' },
                    { value: 'MEDIUM', label: 'Media' },
                    { value: 'HIGH', label: 'Alta' },
                    { value: 'URGENT', label: 'Urgente' }
                  ]}
                />
                
                {/* Assegnato a */}
                <CustomDropdown
                  id="assignedToId"
                  name="assignedToId"
                  label="Assegnato a"
                  value={formData.assignedToId}
                  onChange={handleChange}
                  icon={<FaUser className="h-3.5 w-3.5 text-gray-400" />}
                  options={[
                    { value: '', label: 'Non assegnato' },
                    ...users.map(user => ({
                      value: user.id,
                      label: `${user.firstName} ${user.lastName}`
                    }))
                  ]}
                />
              </div>
            </div>
            
            <div className="mt-10 pt-6 border-t border-gray-200 flex justify-end gap-3">
              <Link
                to={`/tickets/${id}`}
                className="px-4 py-2.5 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors text-sm font-medium"
              >
                Annulla
              </Link>
              <button
                type="submit"
                className="px-6 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors text-sm font-medium"
              >
                Salva modifiche
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditTicket; 