import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { 
  FaArrowLeft, FaUser, FaBuilding, FaEnvelope, 
  FaPhone, FaMapMarkerAlt, FaTag, FaTimes, 
  FaSearch, FaExclamationCircle 
} from 'react-icons/fa';
import { useAuth } from '../hooks/useAuth';

// Componente dropdown personalizzato migliorato
const CustomDropdown = ({ id, name, value, onChange, options, label, required = false, className = "", icon }) => {
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
        <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <button
        id={id}
        type="button"
        className={`w-full flex items-center justify-between px-4 py-2.5 border ${value ? 'border-primary-300' : 'border-gray-300'} bg-white rounded-lg shadow-sm hover:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all ${className}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center">
          {icon && <span className="mr-2 text-gray-500">{icon}</span>}
          <span className={`truncate text-sm ${value ? 'text-gray-900' : 'text-gray-500'}`}>
            {value ? options.find(option => option.value === value)?.label || "Seleziona..." : "Seleziona..."}
          </span>
        </div>
        <svg className={`ml-2 h-5 w-5 text-gray-400 transform transition-transform ${isOpen ? 'rotate-180' : ''}`} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
          {options.map((option) => (
            <div
              key={option.value}
              className={`px-4 py-2.5 cursor-pointer hover:bg-gray-50 text-sm transition-colors ${value === option.value ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700'}`}
              onClick={() => {
                onChange({ target: { name, value: option.value } });
                setIsOpen(false);
              }}
            >
              <div className="flex items-center">
                {option.icon}
                <span className="ml-2">{option.label}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Componente per il campo di ricerca cliente
const ClientSearchField = ({ 
  searchClient, 
  handleClientSearch, 
  showClientDropdown, 
  filteredClients, 
  selectClient, 
  clearClientSelection, 
  searchInputRef,
  selectedClient
}) => {
  return (
    <div className="relative">
      <label htmlFor="client-search" className="block text-sm font-medium text-gray-700 mb-2">
        Cliente <span className="text-red-500">*</span>
      </label>
      <div className="relative rounded-lg shadow-sm">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <FaSearch className="h-4 w-4 text-gray-400" />
        </div>
        <input
          ref={searchInputRef}
          type="text"
          id="client-search"
          value={searchClient}
          onChange={handleClientSearch}
          placeholder="Cerca cliente..."
          className="block w-full pl-10 pr-10 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
          autoComplete="off"
        />
        {searchClient && (
          <button
            type="button"
            onClick={clearClientSelection}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
          >
            <FaTimes className="h-4 w-4" />
          </button>
        )}
      </div>
      
      {/* Dropdown dei clienti */}
      {showClientDropdown && filteredClients.length > 0 && (
        <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredClients.map((client) => (
            <div
              key={client.id}
              onClick={() => selectClient(client)}
              className="px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
            >
              <div className="flex items-center">
                <div className="flex-shrink-0 h-10 w-10 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center">
                  {client.name.charAt(0).toUpperCase()}
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-900">{client.name}</p>
                  <div className="flex items-center mt-1">
                    {client.chain && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-800 mr-2">
                        <FaBuilding className="h-3 w-3 mr-1" />
                        {client.chain}
                      </span>
                    )}
                    {client.email && (
                      <span className="text-xs text-gray-500 truncate">
                        <FaEnvelope className="h-3 w-3 inline mr-1" />
                        {client.email}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Nessun cliente trovato */}
      {showClientDropdown && searchClient.length > 0 && filteredClients.length === 0 && (
        <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-center">
          <FaExclamationCircle className="h-6 w-6 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Nessun cliente trovato</p>
        </div>
      )}
      
      {/* Mostra dettagli del cliente selezionato */}
      {selectedClient && selectedClient.name && (
        <div className="mt-3 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-medium text-gray-900">Dettagli cliente</h4>
            <button 
              type="button"
              onClick={clearClientSelection}
              className="text-gray-400 hover:text-gray-600"
            >
              <FaTimes className="h-4 w-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start">
              <FaUser className="h-4 w-4 text-gray-500 mt-0.5 mr-2" />
              <div>
                <p className="text-xs text-gray-500">Nome</p>
                <p className="text-sm">{selectedClient.name}</p>
              </div>
            </div>
            {selectedClient.chain && (
              <div className="flex items-start">
                <FaBuilding className="h-4 w-4 text-gray-500 mt-0.5 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Catena</p>
                  <p className="text-sm">{selectedClient.chain}</p>
                </div>
              </div>
            )}
            {selectedClient.email && (
              <div className="flex items-start">
                <FaEnvelope className="h-4 w-4 text-gray-500 mt-0.5 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Email</p>
                  <p className="text-sm">{selectedClient.email}</p>
                </div>
              </div>
            )}
            {selectedClient.phone && (
              <div className="flex items-start">
                <FaPhone className="h-4 w-4 text-gray-500 mt-0.5 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Telefono</p>
                  <p className="text-sm">{selectedClient.phone}</p>
                </div>
              </div>
            )}
            {selectedClient.address && (
              <div className="flex items-start col-span-1 md:col-span-2">
                <FaMapMarkerAlt className="h-4 w-4 text-gray-500 mt-0.5 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Indirizzo</p>
                  <p className="text-sm">{selectedClient.address}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const CreateTicket = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
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
  const [clients, setClients] = useState([]);
  const [users, setUsers] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const searchInputRef = useRef(null);

  useEffect(() => {
    fetchClients();
    fetchUsers();
    
    // Focus sul campo di ricerca cliente all'avvio
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);

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

  const handleAddTicket = async (e) => {
    e.preventDefault();
    
    if (!formData.clientId) {
      toast.error('Seleziona un cliente');
      return;
    }
    
    if (!formData.title.trim()) {
      toast.error('Inserisci un titolo per il ticket');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const response = await api.post('/tickets', formData);
      toast.success('Ticket creato con successo');
      navigate(`/tickets/${response.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nella creazione del ticket');
      setIsSubmitting(false);
    }
  };

  // Opzioni di stato con icone
  const statusOptions = [
    { value: 'OPEN', label: 'Aperto', icon: <span className="w-2 h-2 rounded-full bg-blue-500"></span> },
    { value: 'PLANNED', label: 'Pianificato', icon: <span className="w-2 h-2 rounded-full bg-purple-500"></span> },
    { value: 'PLANNED_ONSITE', label: 'Pianificato in loco', icon: <span className="w-2 h-2 rounded-full bg-indigo-500"></span> },
    { value: 'VERIFYING', label: 'In verifica', icon: <span className="w-2 h-2 rounded-full bg-yellow-500"></span> },
    { value: 'WAITING_CLIENT', label: 'In attesa cliente', icon: <span className="w-2 h-2 rounded-full bg-orange-500"></span> },
    { value: 'TO_REPORT', label: 'Da rendicontare', icon: <span className="w-2 h-2 rounded-full bg-green-500"></span> }
  ];

  // Opzioni di priorità con icone
  const priorityOptions = [
    { value: 'LOW', label: 'Bassa', icon: <span className="w-2 h-2 rounded-full bg-green-500"></span> },
    { value: 'MEDIUM', label: 'Media', icon: <span className="w-2 h-2 rounded-full bg-yellow-500"></span> },
    { value: 'HIGH', label: 'Alta', icon: <span className="w-2 h-2 rounded-full bg-orange-500"></span> },
    { value: 'URGENT', label: 'Urgente', icon: <span className="w-2 h-2 rounded-full bg-red-500"></span> }
  ];

  // Opzioni di assegnazione
  const assigneeOptions = [
    { value: '', label: 'Non assegnato' },
    ...users.map(user => ({
      value: user.id,
      label: `${user.firstName || ''} ${user.lastName || ''}`,
      icon: (
        <div className="w-5 h-5 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs mr-2">
          {user.firstName ? user.firstName.charAt(0) : ''}
          {user.lastName ? user.lastName.charAt(0) : ''}
        </div>
      )
    }))
  ];

  return (
    <div className="min-h-screen bg-gray-50 pt-6 pb-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center">
            <Link to="/tickets" className="flex items-center text-gray-500 hover:text-primary-600 transition-colors mr-4">
              <FaArrowLeft className="mr-2 h-4 w-4" />
              <span className="text-sm font-medium">Torna alla lista</span>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">Nuovo Ticket</h1>
          </div>
          <p className="mt-2 text-sm text-gray-600">Crea un nuovo ticket di supporto compilando tutti i campi richiesti</p>
        </div>

        {/* Card del form */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-5 sm:p-6 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Informazioni Ticket</h2>
          </div>
          
          <form onSubmit={handleAddTicket}>
            <div className="p-5 sm:p-6 space-y-6">
              {/* Cliente */}
              <ClientSearchField 
                searchClient={searchClient}
                handleClientSearch={handleClientSearch}
                showClientDropdown={showClientDropdown}
                filteredClients={filteredClients}
                selectClient={selectClient}
                clearClientSelection={clearClientSelection}
                searchInputRef={searchInputRef}
                selectedClient={formData.clientDetails}
              />

              {/* Titolo del ticket */}
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Titolo Ticket <span className="text-red-500">*</span>
                </label>
                <div className="relative rounded-lg shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <FaTag className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Inserisci un titolo descrittivo"
                  />
                </div>
              </div>
              
              {/* Stato, Priorità e Assegnato a */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <CustomDropdown
                  id="status"
                  name="status"
                  label="Stato"
                  value={formData.status}
                  onChange={handleChange}
                  options={statusOptions}
                />
                
                <CustomDropdown
                  id="priority"
                  name="priority"
                  label="Priorità"
                  value={formData.priority}
                  onChange={handleChange}
                  options={priorityOptions}
                />
                
                <CustomDropdown
                  id="assignedToId"
                  name="assignedToId"
                  label="Assegnato a"
                  value={formData.assignedToId}
                  onChange={handleChange}
                  options={assigneeOptions}
                />
              </div>
              
              {/* Descrizione */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Descrizione
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows={5}
                  value={formData.description}
                  onChange={handleChange}
                  className="block w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-y"
                  placeholder="Fornisci una descrizione chiara e dettagliata del problema, inclusi eventuali messaggi di errore, passaggi per riprodurre il problema e altre informazioni rilevanti."
                />
              </div>
            </div>
            
            {/* Footer con i pulsanti */}
            <div className="px-5 sm:px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
              <Link 
                to="/tickets" 
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                Annulla
              </Link>
              <button
                type="submit"
                disabled={isSubmitting}
                className={`inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-lg text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 ${isSubmitting ? 'opacity-75 cursor-not-allowed' : ''}`}
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creazione in corso...
                  </>
                ) : (
                  'Crea Ticket'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateTicket; 