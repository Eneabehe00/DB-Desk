import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FaPlus, FaSearch, FaFilter, FaSortAmountDown, FaSortAmountUp, FaEdit, FaCheck, FaTimes, FaThLarge, FaList, FaChevronDown, FaCalendarAlt } from 'react-icons/fa';
import { useAuth } from '../hooks/useAuth';

// Componente dropdown personalizzato
const CustomDropdown = ({ id, name, value, onChange, options, label, className = "" }) => {
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
      {label && <label htmlFor={id} className="form-label">{label}</label>}
      <button
        id={id}
        type="button"
        className={`w-full flex items-center justify-between px-3 py-2 border border-secondary-300 bg-white rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${className}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="truncate">
          {value ? options.find(option => option.value === value)?.label || "Seleziona..." : "Seleziona..."}
        </span>
        <FaChevronDown className={`ml-2 h-4 w-4 text-secondary-500 transform transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-[100] mt-1 w-full bg-white border border-secondary-200 rounded-md shadow-xl max-h-60 overflow-auto">
          {options.map((option) => (
            <div
              key={option.value}
              className={`px-3 py-2 cursor-pointer hover:bg-primary-50 ${value === option.value ? 'bg-primary-100 text-primary-800' : 'text-secondary-800'}`}
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

const Tickets = () => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
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
    assignedToId: '',
    dateRange: ''
  });
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [allTickets, setAllTickets] = useState([]);
  const ticketsPerPage = 10;
  const observer = useRef();
  const lastTicketElementRef = useRef();
  
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
      setAllTickets(response.data);
      // Don't apply filtering here - we'll handle it in useEffect
      setTickets(response.data.slice(0, ticketsPerPage));
      setHasMore(response.data.length > ticketsPerPage);
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

  const openStatusModal = (ticket, e) => {
    e.preventDefault();
    e.stopPropagation();
    setSelectedTicket(ticket);
    setShowStatusModal(true);
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

  const loadMoreTickets = () => {
    if (loadingMore || !hasMore) return;
    
    setLoadingMore(true);
    
    // Simply increment the page counter, which will show more tickets
    // through the slicing in the filteredTickets calculation
    const nextPage = page + 1;
    setPage(nextPage);
    setHasMore(nextPage * ticketsPerPage < filteredAndSortedTickets.length);
    
    setLoadingMore(false);
  };

  const formatDate = (date) => {
    if (!date) return "";
    return new Date(date).toLocaleDateString('it-IT');
  };
  
  const getDateDaysAgo = (days) => {
    const date = new Date();
    date.setDate(date.getDate() - days);
    return date;
  };

  const getFilteredTickets = (ticketsToFilter) => {
    return ticketsToFilter.filter(ticket => {
      // Filtro per ricerca testuale
      const matchesSearch = search === '' || 
        ticket.title.toLowerCase().includes(search.toLowerCase()) ||
        ticket.description.toLowerCase().includes(search.toLowerCase()) ||
        (ticket.client?.name && ticket.client.name.toLowerCase().includes(search.toLowerCase()));
      
      // Filtro per stato
      const matchesStatus = filters.status === '' || ticket.status === filters.status;
      
      // Filtro per priorità
      const matchesPriority = filters.priority === '' || ticket.priority === filters.priority;
      
      // Filtro per cliente
      const matchesClient = filters.clientId === '' || ticket.clientId === filters.clientId;
      
      // Filtro per assegnato a
      const matchesAssignedTo = filters.assignedToId === '' ||
        (filters.assignedToId === 'null' && !ticket.assignedToId) ||
        ticket.assignedToId === filters.assignedToId;
      
      // Filtro per intervallo date
      let matchesDateRange = true;
      if (filters.dateRange) {
        const ticketDate = new Date(ticket.updatedAt);
        
        if (filters.dateRange === 'today') {
          const today = new Date();
          matchesDateRange = 
            ticketDate.getDate() === today.getDate() &&
            ticketDate.getMonth() === today.getMonth() &&
            ticketDate.getFullYear() === today.getFullYear();
        } else if (filters.dateRange === 'yesterday') {
          const yesterday = getDateDaysAgo(1);
          matchesDateRange = 
            ticketDate.getDate() === yesterday.getDate() &&
            ticketDate.getMonth() === yesterday.getMonth() &&
            ticketDate.getFullYear() === yesterday.getFullYear();
        } else if (filters.dateRange === 'last7days') {
          const last7Days = getDateDaysAgo(7);
          matchesDateRange = ticketDate >= last7Days;
        } else if (filters.dateRange === 'last30days') {
          const last30Days = getDateDaysAgo(30);
          matchesDateRange = ticketDate >= last30Days;
        } else if (filters.dateRange === 'thisMonth') {
          const now = new Date();
          matchesDateRange = 
            ticketDate.getMonth() === now.getMonth() &&
            ticketDate.getFullYear() === now.getFullYear();
        }
      }
      
      return matchesSearch && matchesStatus && matchesPriority && matchesClient && matchesAssignedTo && matchesDateRange;
    }).sort((a, b) => {
      // Applicazione dell'ordinamento
      let comparison = 0;
      
      if (sortField === 'updatedAt') {
        comparison = new Date(b.updatedAt) - new Date(a.updatedAt);
      } else if (sortField === 'title') {
        comparison = a.title.localeCompare(b.title);
      } else if (sortField === 'priority') {
        const priorityOrder = { LOW: 1, MEDIUM: 2, HIGH: 3, URGENT: 4 };
        comparison = priorityOrder[a.priority] - priorityOrder[b.priority];
      } else if (sortField === 'status') {
        comparison = a.status.localeCompare(b.status);
      } else if (sortField === 'client') {
        const clientA = a.client?.name || '';
        const clientB = b.client?.name || '';
        comparison = clientA.localeCompare(clientB);
      }
      
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  };

  // Apply all filters to allTickets first, then use this for pagination and display
  const filteredAndSortedTickets = getFilteredTickets(allTickets);

  // Then slice the filtered tickets for display according to current pagination
  const filteredTickets = filteredAndSortedTickets.slice(0, page * ticketsPerPage);

  // Intersection Observer for infinite scroll
  useEffect(() => {
    if (loading) return;
    
    const options = {
      root: null,
      rootMargin: '20px',
      threshold: 0.1
    };
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        loadMoreTickets();
      }
    }, options);
    
    if (lastTicketElementRef.current) {
      observer.current.observe(lastTicketElementRef.current);
    }
    
    return () => {
      if (observer.current) {
        observer.current.disconnect();
      }
    };
  }, [loading, hasMore, tickets]);

  // Update hasMore whenever filteredAndSortedTickets changes
  useEffect(() => {
    setHasMore(page * ticketsPerPage < filteredAndSortedTickets.length);
  }, [filteredAndSortedTickets, page, ticketsPerPage]);

  // When filters change, reset pagination
  useEffect(() => {
    // Reset to page 1 whenever filters change
    setPage(1);
    // hasMore is now calculated based on filteredAndSortedTickets.length in the component render
  }, [search, filters, sortField, sortDirection]);

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'OPEN':
        return 'bg-blue-600';
      case 'CLOSED':
        return 'bg-red-600';
      case 'PLANNED':
        return 'bg-purple-600';
      case 'CLOSED_REMOTE':
        return 'bg-slate-600';
      case 'CLOSED_ONSITE':
        return 'bg-gray-600';
      case 'PLANNED_ONSITE':
        return 'bg-indigo-600';
      case 'VERIFYING':
        return 'bg-yellow-600';
      case 'WAITING_CLIENT':
        return 'bg-orange-600';
      case 'TO_REPORT':
        return 'bg-green-600';
      default:
        return 'bg-blue-600';
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
    <div className="container mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-secondary-900 mb-4 md:mb-0">Tickets</h1>
        <Link
          to="/tickets/create"
          className="btn-primary flex items-center md:w-auto"
        >
          <FaPlus className="mr-2" />
          Nuovo Ticket
        </Link>
      </div>

      {/* Search and Filter Bar */}
      <div className="card overflow-visible mb-6">
        <div className="p-4">
          {/* Filtri rapidi */}
          <div className="mb-4 flex flex-wrap gap-2">
            <button
              onClick={() => setFilters({...filters, status: 'OPEN'})}
              className={`px-3 py-1.5 rounded-lg flex items-center text-sm font-medium transition-colors ${
                filters.status === 'OPEN' 
                ? 'bg-blue-600 text-white' 
                : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-blue-300 mr-2"></span>
              Aperti
            </button>
            
            <button
              onClick={() => setFilters({...filters, priority: 'URGENT'})}
              className={`px-3 py-1.5 rounded-lg flex items-center text-sm font-medium transition-colors ${
                filters.priority === 'URGENT' 
                ? 'bg-red-600 text-white' 
                : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-red-300 mr-2"></span>
              Urgenti
            </button>
            
            <button
              onClick={() => setFilters({...filters, assignedToId: user.id})}
              className={`px-3 py-1.5 rounded-lg flex items-center text-sm font-medium transition-colors ${
                filters.assignedToId === user.id 
                ? 'bg-green-600 text-white' 
                : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-green-300 mr-2"></span>
              Assegnati a me
            </button>
            
            <button
              onClick={() => setFilters({...filters, assignedToId: 'null'})}
              className={`px-3 py-1.5 rounded-lg flex items-center text-sm font-medium transition-colors ${
                filters.assignedToId === 'null' 
                ? 'bg-yellow-600 text-white' 
                : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-yellow-300 mr-2"></span>
              Non assegnati
            </button>
            
            <button
              onClick={() => setFilters({...filters, dateRange: 'today'})}
              className={`px-3 py-1.5 rounded-lg flex items-center text-sm font-medium transition-colors ${
                filters.dateRange === 'today' 
                ? 'bg-purple-600 text-white' 
                : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-purple-300 mr-2"></span>
              Oggi
            </button>
          </div>
        
          <div className="mb-4">
            <div className="relative flex-grow">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FaSearch className="text-secondary-400" />
              </div>
              <input
                type="text"
                value={search}
                onChange={handleSearch}
                className="form-input pl-10 pr-20 w-full"
                placeholder="Cerca per titolo, cliente, descrizione..."
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute inset-y-0 right-10 flex items-center text-secondary-400 hover:text-secondary-600 px-2"
                >
                  <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="absolute inset-y-0 right-0 flex items-center text-secondary-500 hover:text-primary-600 px-3"
                title={showFilters ? "Nascondi filtri" : "Mostra filtri"}
              >
                <FaFilter className={`${showFilters ? 'text-primary-600' : ''}`} />
              </button>
            </div>
            
            {/* Recent Search Suggestions */}
            {search && (
              <div className="absolute z-10 mt-1 bg-white rounded-md shadow-lg border border-secondary-200 w-full max-w-3xl max-h-60 overflow-auto">
                <div className="p-2 border-b border-secondary-100 flex justify-between items-center">
                  <span className="text-xs text-secondary-500">Suggerimenti</span>
                  <span className="text-xs text-secondary-500">Premi invio per cercare</span>
                </div>
                <div className="p-2">
                  <div className="flex flex-wrap gap-2">
                    {['assistenza remota', 'problema stampante', 'errore login', 'rete wifi']
                      .filter(s => s.includes(search.toLowerCase()))
                      .map((suggestion, idx) => (
                        <button 
                          key={idx} 
                          className="px-3 py-1 bg-secondary-50 text-secondary-800 rounded-full text-sm hover:bg-primary-50 hover:text-primary-700"
                          onClick={() => setSearch(suggestion)}
                        >
                          {suggestion}
                        </button>
                      ))}
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Filtri collassabili */}
          <div className={`transition-all duration-300 ease-in-out ${showFilters ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4 relative">
              <div className="z-50">
                <CustomDropdown
                  id="status"
                  name="status"
                  value={filters.status}
                  onChange={handleFilterChange}
                  label="Stato"
                  options={[
                    { value: "", label: "Tutti" },
                    { value: "OPEN", label: "Aperto" },
                    { value: "CLOSED", label: "Chiuso" },
                    { value: "PLANNED", label: "Painificato" },
                    { value: "CLOSED_REMOTE", label: "Chiuso Remoto" },
                    { value: "CLOSED_ONSITE", label: "Chiuso Onsite" },
                    { value: "PLANNED_ONSITE", label: "Previsto onsite" },
                    { value: "VERIFYING", label: "In verifica esito" },
                    { value: "WAITING_CLIENT", label: "In attesa Cliente" },
                    { value: "TO_REPORT", label: "Da riportare" },
                  ]}
                />
              </div>
              <div className="z-45">
                <CustomDropdown
                  id="priority"
                  name="priority"
                  value={filters.priority}
                  onChange={handleFilterChange}
                  label="Priorità"
                  options={[
                    { value: "", label: "Tutte" },
                    { value: "LOW", label: "Bassa" },
                    { value: "MEDIUM", label: "Media" },
                    { value: "HIGH", label: "Alta" },
                    { value: "URGENT", label: "Urgente" },
                  ]}
                />
              </div>
              <div className="z-40">
                <CustomDropdown
                  id="clientId"
                  name="clientId"
                  value={filters.clientId}
                  onChange={handleFilterChange}
                  label="Cliente"
                  options={[
                    { value: "", label: "Tutti" },
                    ...clients.map(client => ({ value: client.id, label: client.name }))
                  ]}
                />
              </div>
              <div className="z-35">
                <CustomDropdown
                  id="assignedToId"
                  name="assignedToId"
                  value={filters.assignedToId}
                  onChange={handleFilterChange}
                  label="Assegnato a"
                  options={[
                    { value: "", label: "Tutti" },
                    { value: "null", label: "Non assegnato" },
                    ...users.map(user => ({ value: user.id, label: user.name }))
                  ]}
                />
              </div>
              <div className="z-30">
                <CustomDropdown
                  id="dateRange"
                  name="dateRange"
                  value={filters.dateRange}
                  onChange={handleFilterChange}
                  label={
                    <div className="flex items-center">
                      <FaCalendarAlt className="mr-1 text-secondary-500" />
                      <span>Periodo</span>
                    </div>
                  }
                  options={[
                    { value: "", label: "Tutti" },
                    { value: "today", label: "Oggi" },
                    { value: "yesterday", label: "Ieri" },
                    { value: "last7days", label: "Ultimi 7 giorni" },
                    { value: "last30days", label: "Ultimi 30 giorni" },
                    { value: "thisMonth", label: "Questo mese" }
                  ]}
                />
              </div>
            </div>
          </div>
          
          {/* Pill filters for active filters */}
          {Object.entries(filters).some(([_, value]) => value !== '') && (
            <div className="mt-4 flex flex-wrap gap-2 items-center">
              <span className="text-xs text-secondary-500 mr-1">Filtri attivi:</span>
              
              {filters.status && (
                <div className="bg-primary-50 text-primary-700 rounded-full px-3 py-1 text-sm flex items-center">
                  <span>Stato: {translateStatus(filters.status)}</span>
                  <button 
                    className="ml-2 text-primary-500 hover:text-primary-700"
                    onClick={() => setFilters({...filters, status: ''})}
                  >
                    <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}
              
              {filters.priority && (
                <div className="bg-primary-50 text-primary-700 rounded-full px-3 py-1 text-sm flex items-center">
                  <span>Priorità: {translatePriority(filters.priority)}</span>
                  <button 
                    className="ml-2 text-primary-500 hover:text-primary-700"
                    onClick={() => setFilters({...filters, priority: ''})}
                  >
                    <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}
              
              {filters.clientId && (
                <div className="bg-primary-50 text-primary-700 rounded-full px-3 py-1 text-sm flex items-center">
                  <span>Cliente: {clients.find(c => c.id === filters.clientId)?.name || 'ID: ' + filters.clientId}</span>
                  <button 
                    className="ml-2 text-primary-500 hover:text-primary-700"
                    onClick={() => setFilters({...filters, clientId: ''})}
                  >
                    <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}
              
              {filters.assignedToId && (
                <div className="bg-primary-50 text-primary-700 rounded-full px-3 py-1 text-sm flex items-center">
                  <span>Assegnato a: {filters.assignedToId === 'null' 
                    ? 'Non assegnato' 
                    : users.find(u => u.id === filters.assignedToId)?.name || 'ID: ' + filters.assignedToId}</span>
                  <button 
                    className="ml-2 text-primary-500 hover:text-primary-700"
                    onClick={() => setFilters({...filters, assignedToId: ''})}
                  >
                    <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}
              
              {filters.dateRange && (
                <div className="bg-primary-50 text-primary-700 rounded-full px-3 py-1 text-sm flex items-center">
                  <span>Periodo: {
                    filters.dateRange === 'today' ? 'Oggi' :
                    filters.dateRange === 'yesterday' ? 'Ieri' :
                    filters.dateRange === 'last7days' ? 'Ultimi 7 giorni' :
                    filters.dateRange === 'last30days' ? 'Ultimi 30 giorni' :
                    filters.dateRange === 'thisMonth' ? 'Questo mese' :
                    filters.dateRange
                  }</span>
                  <button 
                    className="ml-2 text-primary-500 hover:text-primary-700"
                    onClick={() => setFilters({...filters, dateRange: ''})}
                  >
                    <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}
              
              <button 
                className="text-secondary-500 hover:text-primary-600 text-sm underline"
                onClick={() => setFilters({
                  status: '',
                  priority: '',
                  clientId: '',
                  assignedToId: '',
                  dateRange: ''
                })}
              >
                Cancella tutti
              </button>
            </div>
          )}
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
          <div className="relative w-44 z-40">
            <CustomDropdown
              id="sortField"
              name="sortField"
              value={sortField}
              onChange={(e) => {
                setSortField(e.target.value);
                setSortDirection('desc');
              }}
              className="py-1 text-sm"
              options={[
                { value: "updatedAt", label: "Data aggiornamento" },
                { value: "title", label: "Titolo" },
                { value: "priority", label: "Priorità" },
                { value: "status", label: "Stato" },
                { value: "client", label: "Cliente" },
              ]}
            />
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
              {filteredTickets.map((ticket, index) => (
                <div 
                  key={ticket.id} 
                  ref={index === filteredTickets.length - 1 ? lastTicketElementRef : null}
                  className="bg-white rounded-xl shadow-sm border border-secondary-200 hover:shadow-md hover:border-primary-200 transition-all overflow-hidden cursor-pointer group"
                  onClick={() => window.location.href = `/tickets/${ticket.id}`}
                >
                  <div className="p-4 sm:p-5">
                    {/* Top row with status badge and date info */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(ticket.status)} text-white mr-2`}>
                          {translateStatus(ticket.status)}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getPriorityBadgeClass(ticket.priority)}`}>
                          {translatePriority(ticket.priority)}
                        </span>
                      </div>
                      <div className="text-xs text-secondary-500 flex items-center">
                        <svg className="w-4 h-4 mr-1 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {new Date(ticket.updatedAt).toLocaleDateString('it-IT')}
                      </div>
                    </div>

                    {/* Main content with left sidebar for client avatar */}
                    <div className="flex gap-4">
                      {/* Cliente con avatar */}
                      <div className="flex-shrink-0">
                        <div 
                          className="h-14 w-14 rounded-xl flex items-center justify-center text-base font-bold shadow-sm"
                          style={{
                            backgroundColor: ticket.client?.name 
                              ? `hsl(${ticket.client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 85%, 90%)`
                              : '#e2e8f0',
                            color: ticket.client?.name 
                              ? `hsl(${ticket.client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 75%, 35%)`
                              : '#475569'
                          }}
                        >
                          {ticket.client?.name.charAt(0)}
                        </div>
                      </div>

                      {/* Central content: title, description, client details */}
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg text-secondary-900 mb-1 group-hover:text-primary-700 transition-colors">
                          {ticket.title}
                        </h3>
                        
                        <div className="text-sm text-secondary-800 font-medium mb-2">
                          {ticket.client?.name}
                          {ticket.client?.chain && (
                            <span className="text-secondary-500 ml-1">
                              ({ticket.client.chain})
                            </span>
                          )}
                        </div>
                        
                        <p className="text-sm text-secondary-600 line-clamp-2 mb-3">
                          {ticket.description}
                        </p>
                        
                        {/* Footer with meta information */}
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center">
                            {ticket.assignedTo ? (
                              <div className="flex items-center text-secondary-600 bg-secondary-50 px-2 py-1 rounded-md">
                                <svg className="w-3.5 h-3.5 mr-1 text-secondary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                                {ticket.assignedTo?.name}
                              </div>
                            ) : (
                              <div className="flex items-center text-yellow-600 bg-yellow-50 px-2 py-1 rounded-md">
                                <svg className="w-3.5 h-3.5 mr-1 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Non assegnato
                              </div>
                            )}
                          </div>
                          
                          {/* Status Dropdown */}
                          <div 
                            onClick={(e) => e.stopPropagation()}
                            className="inline-block"
                          >
                            <CustomDropdown
                              id={`ticket-status-${ticket.id}`}
                              name="status"
                              value={ticket.status}
                              onChange={(e) => {
                                e.stopPropagation();
                                handleUpdateStatus(e.target.value, ticket);
                              }}
                              className="py-1 text-xs min-w-[120px]"
                              options={[
                                { value: "OPEN", label: "Aperto" },
                                { value: "CLOSED", label: "Chiuso" },
                                { value: "PLANNED", label: "Painificato" },
                                { value: "CLOSED_REMOTE", label: "Chiuso Remoto" },
                                { value: "CLOSED_ONSITE", label: "Chiuso Onsite" },
                                { value: "PLANNED_ONSITE", label: "Previsto onsite" },
                                { value: "VERIFYING", label: "In verifica esito" },
                                { value: "WAITING_CLIENT", label: "In attesa Cliente" },
                                { value: "TO_REPORT", label: "Da riportare" },
                              ]}
                            />
                          </div>
                        </div>
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
              {filteredTickets.map((ticket, index) => (
                <div 
                  key={ticket.id} 
                  ref={index === filteredTickets.length - 1 ? lastTicketElementRef : null}
                  className="bg-white rounded-xl shadow-sm border border-secondary-200 hover:shadow-md transition-shadow overflow-hidden cursor-pointer flex flex-col h-full group"
                  onClick={() => window.location.href = `/tickets/${ticket.id}`}
                >
                  {/* Header with status ribbon */}
                  <div 
                    className={`h-2 w-full ${getStatusBadgeClass(ticket.status)}`}
                  ></div>
                  
                  <div className="p-5 flex-1 flex flex-col">
                    {/* Client info */}
                    <div className="flex items-center mb-4">
                      <div 
                        className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold shadow-sm mr-3"
                        style={{
                          backgroundColor: ticket.client?.name 
                            ? `hsl(${ticket.client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 85%, 90%)`
                            : '#e2e8f0',
                          color: ticket.client?.name 
                            ? `hsl(${ticket.client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 75%, 35%)`
                            : '#475569'
                        }}
                      >
                        {ticket.client?.name.charAt(0)}
                      </div>
                      <div className="overflow-hidden">
                        <div className="font-medium text-secondary-900 truncate">
                          {ticket.client?.name}
                        </div>
                        {ticket.client?.chain && (
                          <div className="text-xs text-secondary-500 truncate">
                            {ticket.client.chain}
                          </div>
                        )}
                      </div>
                      
                      {/* Priority Indicator */}
                      <div className="ml-auto">
                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${getPriorityBadgeClass(ticket.priority)}`}>
                          {translatePriority(ticket.priority)}
                        </span>
                      </div>
                    </div>
                    
                    {/* Ticket Details */}
                    <h3 className="font-semibold text-secondary-900 mb-2 line-clamp-1 group-hover:text-primary-700 transition-colors">
                      {ticket.title}
                    </h3>
                    
                    <p className="text-sm text-secondary-600 mb-4 line-clamp-3 flex-1">
                      {ticket.description}
                    </p>
                    
                    {/* Footer */}
                    <div className="flex items-center justify-between mt-auto pt-3 border-t border-secondary-100">
                      <div className="flex flex-col">
                        <div className="text-xs text-secondary-500 flex items-center">
                          <svg className="w-3.5 h-3.5 mr-1 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {new Date(ticket.updatedAt).toLocaleDateString('it-IT')}
                        </div>
                        
                        <div className="text-xs mt-1">
                          {ticket.assignedTo ? (
                            <div className="flex items-center text-secondary-600">
                              <svg className="w-3.5 h-3.5 mr-1 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                              {ticket.assignedTo.name}
                            </div>
                          ) : (
                            <div className="flex items-center text-yellow-600">
                              <svg className="w-3.5 h-3.5 mr-1 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              Non assegnato
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Status Dropdown */}
                      <div 
                        onClick={(e) => e.stopPropagation()}
                        className="inline-block z-20"
                      >
                        <CustomDropdown
                          id={`card-ticket-status-${ticket.id}`}
                          name="status"
                          value={ticket.status}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleUpdateStatus(e.target.value, ticket);
                          }}
                          className="py-1 text-xs min-w-[120px]"
                          options={[
                            { value: "OPEN", label: "Aperto" },
                            { value: "CLOSED", label: "Chiuso" },
                            { value: "PLANNED", label: "Painificato" },
                            { value: "CLOSED_REMOTE", label: "Chiuso Remoto" },
                            { value: "CLOSED_ONSITE", label: "Chiuso Onsite" },
                            { value: "PLANNED_ONSITE", label: "Previsto onsite" },
                            { value: "VERIFYING", label: "In verifica esito" },
                            { value: "WAITING_CLIENT", label: "In attesa Cliente" },
                            { value: "TO_REPORT", label: "Da riportare" },
                          ]}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Loading indicator */}
          {loadingMore && (
            <div className="flex justify-center py-4">
              <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
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
          <Link
            to="/tickets/create"
            className="btn btn-primary inline-flex items-center"
          >
            <FaPlus className="mr-2" />
            Crea Nuovo Ticket
          </Link>
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