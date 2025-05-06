import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FaPlus, FaSearch, FaEdit, FaTrash, FaTicketAlt, FaPhone, FaEnvelope, FaMapMarkerAlt, FaStore, FaEllipsisH, FaList, FaThLarge } from 'react-icons/fa';

const Clients = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentClient, setCurrentClient] = useState(null);
  const [viewMode, setViewMode] = useState('list'); // 'list' o 'grid'
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    chain: ''
  });
  
  // Nuovi stati per il caricamento progressivo
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [allClients, setAllClients] = useState([]);
  const clientsPerPage = 10;
  const observer = useRef();
  const lastClientElementRef = useRef();

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await api.get('/clients');
      setAllClients(response.data);
      setClients(response.data.slice(0, clientsPerPage));
      setHasMore(response.data.length > clientsPerPage);
      setLoading(false);
    } catch (error) {
      toast.error('Errore nel caricamento dei clienti');
      setLoading(false);
    }
  };

  // Funzione per caricare altri clienti quando si scorre verso il basso
  const loadMoreClients = () => {
    if (loadingMore || !hasMore) return;
    
    setLoadingMore(true);
    const nextPage = page + 1;
    const start = (nextPage - 1) * clientsPerPage;
    const end = start + clientsPerPage;
    
    // Filtro i clienti in base ai criteri di ricerca
    const filteredResults = getFilteredClients(allClients);
    
    // Aggiungo i prossimi clienti
    if (start < filteredResults.length) {
      setClients(prev => [...prev, ...filteredResults.slice(start, end)]);
      setHasMore(end < filteredResults.length);
      setPage(nextPage);
    } else {
      setHasMore(false);
    }
    
    setLoadingMore(false);
  };

  // Setup dell'IntersectionObserver per rilevare quando l'utente scorre fino alla fine della lista
  useEffect(() => {
    if (loading) return;
    
    const options = {
      root: null,
      rootMargin: '20px',
      threshold: 0.1
    };
    
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        loadMoreClients();
      }
    }, options);
    
    if (lastClientElementRef.current) {
      observer.current.observe(lastClientElementRef.current);
    }
    
    return () => {
      if (observer.current) {
        observer.current.disconnect();
      }
    };
  }, [loading, hasMore, clients]);

  const handleSearch = (e) => {
    setSearch(e.target.value);
  };

  // Funzione per filtrare i clienti in base ai criteri di ricerca
  const getFilteredClients = (clientsToFilter) => {
    return clientsToFilter.filter(client => 
      client.name.toLowerCase().includes(search.toLowerCase()) || 
      (client.email && client.email.toLowerCase().includes(search.toLowerCase())) ||
      (client.chain && client.chain.toLowerCase().includes(search.toLowerCase()))
    );
  };

  // Computed value per i clienti filtrati
  const filteredClients = getFilteredClients(clients);

  // Reset della paginazione quando la ricerca cambia
  useEffect(() => {
    if (allClients.length > 0) {
      const filtered = getFilteredClients(allClients);
      setClients(filtered.slice(0, clientsPerPage));
      setHasMore(filtered.length > clientsPerPage);
      setPage(1);
    }
  }, [search]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleAddClient = async (e) => {
    e.preventDefault();
    
    try {
      await api.post('/clients', formData);
      toast.success('Cliente aggiunto con successo');
      setShowAddModal(false);
      setFormData({
        name: '',
        email: '',
        phone: '',
        address: '',
        chain: ''
      });
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nella creazione del cliente');
    }
  };

  const handleEditClient = async (e) => {
    e.preventDefault();
    
    try {
      await api.put(`/clients/${currentClient.id}`, formData);
      toast.success('Cliente aggiornato con successo');
      setShowEditModal(false);
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'aggiornamento del cliente');
    }
  };

  const handleDeleteClient = async () => {
    try {
      await api.delete(`/clients/${currentClient.id}`);
      toast.success('Cliente eliminato con successo');
      setShowDeleteModal(false);
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'eliminazione del cliente');
    }
  };

  const openEditModal = (client, e) => {
    if (e) e.stopPropagation();
    setCurrentClient(client);
    setFormData({
      name: client.name,
      email: client.email,
      phone: client.phone || '',
      address: client.address || '',
      chain: client.chain || ''
    });
    setShowEditModal(true);
  };

  const openDeleteModal = (client, e) => {
    if (e) e.stopPropagation();
    setCurrentClient(client);
    setShowDeleteModal(true);
  };

  const getInitials = (name) => {
    if (!name) return '';
    return name
      .split(' ')
      .map(part => part.charAt(0))
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };

  const getRandomColor = (id) => {
    const colors = [
      'bg-blue-100 text-blue-700',
      'bg-green-100 text-green-700',
      'bg-purple-100 text-purple-700',
      'bg-yellow-100 text-yellow-700',
      'bg-pink-100 text-pink-700',
      'bg-indigo-100 text-indigo-700',
      'bg-red-100 text-red-700',
      'bg-cyan-100 text-cyan-700'
    ];
    
    // Usa l'ID per determinare un indice stabile
    const index = id ? id.toString().split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % colors.length : 0;
    
    return colors[index];
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
          <h1 className="text-2xl font-bold text-secondary-900">Clienti</h1>
          <p className="text-secondary-500">Gestisci i clienti e i loro ticket</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary mt-4 md:mt-0 flex items-center"
        >
          <FaPlus className="mr-2" />
          Nuovo Cliente
        </button>
      </div>

      {/* Search & Filter Bar */}
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
                placeholder="Cerca cliente per nome, email o catena..."
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-secondary-400 hover:text-secondary-600"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* View Controls */}
      <div className="flex flex-wrap items-center justify-between mb-4">
        <div className="text-sm text-secondary-600 mb-2 md:mb-0">
          {filteredClients.length} clienti trovati
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
              onClick={() => setViewMode('grid')}
              className={`flex items-center justify-center p-1.5 rounded-r-lg ${
                viewMode === 'grid' 
                  ? 'bg-primary-50 text-primary-600' 
                  : 'text-secondary-500 hover:bg-secondary-50'
              }`}
              aria-label="Vista Griglia"
              title="Vista Griglia"
            >
              <FaThLarge className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Clients Display */}
      {filteredClients.length > 0 ? (
        <>
          {/* List View */}
          {viewMode === 'list' && (
            <div className="space-y-3">
              {filteredClients.map((client, index) => (
                <div 
                  key={client.id} 
                  ref={index === filteredClients.length - 1 ? lastClientElementRef : null}
                  className="bg-white rounded-xl shadow-sm border border-secondary-200 hover:shadow-md hover:border-primary-200 transition-all overflow-hidden cursor-pointer"
                  onClick={() => window.location.href = `/clients/${client.id}`}
                >
                  <div className="p-4 sm:p-5">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                      {/* Cliente con avatar e nome */}
                      <div className="flex items-center sm:w-52 sm:min-w-[13rem]">
                        <div 
                          className="flex-shrink-0 h-11 w-11 rounded-full flex items-center justify-center mr-3 text-base font-bold shadow-sm"
                          style={{
                            // Generiamo un colore basato sul nome del cliente
                            backgroundColor: client.name 
                              ? `hsl(${client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 70%, 90%)`
                              : '#e2e8f0',
                            color: client.name 
                              ? `hsl(${client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 70%, 30%)`
                              : '#475569'
                          }}
                        >
                          {getInitials(client.name)}
                        </div>
                        <div className="overflow-hidden">
                          <div className="font-medium text-secondary-900 truncate">{client.name}</div>
                          {client.chain && (
                            <div className="text-xs text-secondary-500 truncate">{client.chain}</div>
                          )}
                        </div>
                      </div>

                      {/* Contatti centrali */}
                      <div className="flex-1 sm:border-l sm:border-r sm:border-secondary-100 sm:pl-4 sm:pr-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {client.email && (
                            <div className="flex items-center text-sm text-secondary-600">
                              <FaEnvelope className="mr-2 text-secondary-400 flex-shrink-0" />
                              <span className="truncate">{client.email}</span>
                            </div>
                          )}
                          {client.phone && (
                            <div className="flex items-center text-sm text-secondary-600">
                              <FaPhone className="mr-2 text-secondary-400 flex-shrink-0" />
                              <span>{client.phone}</span>
                            </div>
                          )}
                          {client.address && (
                            <div className="flex items-center text-sm text-secondary-600 md:col-span-2">
                              <FaMapMarkerAlt className="mr-2 text-secondary-400 flex-shrink-0" />
                              <span className="truncate">{client.address}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Azioni sulla destra */}
                      <div className="flex items-center gap-3 sm:w-48 justify-between sm:justify-end">
                        <div className="flex items-center bg-primary-50 text-primary-700 rounded-full px-3 py-1">
                          <FaTicketAlt className="mr-1.5 h-3 w-3" />
                          <span className="text-xs font-medium">{client.tickets?.length || 0} Ticket</span>
                        </div>
                        
                        <div className="flex items-center space-x-1">
                          <button 
                            className="p-1.5 text-secondary-500 hover:text-primary-600 hover:bg-primary-50 rounded-full transition-colors"
                            onClick={(e) => openEditModal(client, e)}
                            title="Modifica"
                          >
                            <FaEdit className="h-4 w-4" />
                          </button>
                          <button 
                            className="p-1.5 text-secondary-500 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
                            onClick={(e) => openDeleteModal(client, e)}
                            title="Elimina"
                          >
                            <FaTrash className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Grid View */}
          {viewMode === 'grid' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredClients.map((client, index) => (
                <div 
                  key={client.id} 
                  ref={index === filteredClients.length - 1 ? lastClientElementRef : null}
                  className="bg-white rounded-xl shadow-sm border border-secondary-200 hover:shadow-md hover:border-primary-200 transition-all overflow-hidden cursor-pointer"
                  onClick={() => window.location.href = `/clients/${client.id}`}
                >
                  <div className="p-5">
                    {/* Cliente con avatar e nome */}
                    <div className="flex items-center mb-4">
                      <div 
                        className="flex-shrink-0 h-12 w-12 rounded-full flex items-center justify-center mr-3 text-base font-bold shadow-sm"
                        style={{
                          // Generiamo un colore basato sul nome del cliente
                          backgroundColor: client.name 
                            ? `hsl(${client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 70%, 90%)`
                            : '#e2e8f0',
                          color: client.name 
                            ? `hsl(${client.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % 360}, 70%, 30%)`
                            : '#475569'
                        }}
                      >
                        {getInitials(client.name)}
                      </div>
                      <div className="overflow-hidden">
                        <div className="font-medium text-lg text-secondary-900 truncate">{client.name}</div>
                        {client.chain && (
                          <div className="text-sm text-secondary-500 truncate">{client.chain}</div>
                        )}
                      </div>
                    </div>
                    
                    {/* Contatti del cliente */}
                    <div className="space-y-2 mb-4">
                      {client.email && (
                        <div className="flex items-center text-sm text-secondary-600">
                          <FaEnvelope className="mr-2 text-secondary-400 flex-shrink-0" />
                          <span className="truncate">{client.email}</span>
                        </div>
                      )}
                      {client.phone && (
                        <div className="flex items-center text-sm text-secondary-600">
                          <FaPhone className="mr-2 text-secondary-400 flex-shrink-0" />
                          <span>{client.phone}</span>
                        </div>
                      )}
                      {client.address && (
                        <div className="flex items-center text-sm text-secondary-600">
                          <FaMapMarkerAlt className="mr-2 text-secondary-400 flex-shrink-0" />
                          <span className="truncate">{client.address}</span>
                        </div>
                      )}
                    </div>
                    
                    {/* Footer with actions */}
                    <div className="flex items-center justify-between pt-3 border-t border-secondary-100">
                      <div className="flex items-center bg-primary-50 text-primary-700 rounded-full px-3 py-1">
                        <FaTicketAlt className="mr-1.5 h-3 w-3" />
                        <span className="text-xs font-medium">{client.tickets?.length || 0} Ticket</span>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <button 
                          className="p-1.5 text-secondary-500 hover:text-primary-600 hover:bg-primary-50 rounded-full transition-colors"
                          onClick={(e) => openEditModal(client, e)}
                          title="Modifica"
                        >
                          <FaEdit className="h-4 w-4" />
                        </button>
                        <button 
                          className="p-1.5 text-secondary-500 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
                          onClick={(e) => openDeleteModal(client, e)}
                          title="Elimina"
                        >
                          <FaTrash className="h-4 w-4" />
                        </button>
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-secondary-900 mb-1">
            {search ? 'Nessun cliente trovato' : 'Nessun cliente presente'}
          </h3>
          <p className="text-secondary-500 mb-6">
            {search ? `Nessun risultato per "${search}"` : 'Aggiungi il tuo primo cliente per iniziare'}
          </p>
          {!search && (
            <button
              onClick={() => setShowAddModal(true)}
              className="btn btn-primary inline-flex items-center"
            >
              <FaPlus className="mr-2" />
              Aggiungi Cliente
            </button>
          )}
        </div>
      )}

      {/* Add Client Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="add-client-modal" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-gradient-to-r from-primary-500 to-primary-700 px-4 py-5 sm:px-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg leading-6 font-medium text-white">
                    Nuovo Cliente
                  </h3>
                  <button
                    type="button"
                    className="bg-primary-600 rounded-md text-primary-200 hover:text-white focus:outline-none"
                    onClick={() => setShowAddModal(false)}
                  >
                    <span className="sr-only">Close</span>
                    <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <form onSubmit={handleAddClient}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="grid grid-cols-1 gap-4">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                        Nome <span className="text-red-600">*</span>
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="chain" className="block text-sm font-medium text-gray-700 mb-1">
                        Catena
                      </label>
                      <input
                        type="text"
                        id="chain"
                        name="chain"
                        value={formData.chain}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                        placeholder="es. Carrefour, Eurospin, ecc."
                      />
                    </div>
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                        Email <span className="text-red-600">*</span>
                      </label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                        Telefono
                      </label>
                      <input
                        type="tel"
                        id="phone"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                      />
                    </div>
                    <div>
                      <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
                        Indirizzo
                      </label>
                      <textarea
                        id="address"
                        name="address"
                        value={formData.address}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg resize-none transition-all"
                        rows="3"
                      ></textarea>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-lg border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                  >
                    Salva cliente
                  </button>
                  <button
                    type="button"
                    className="mt-3 w-full inline-flex justify-center rounded-lg border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                    onClick={() => setShowAddModal(false)}
                  >
                    Annulla
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Client Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="edit-client-modal" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-gradient-to-r from-primary-500 to-primary-700 px-4 py-5 sm:px-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg leading-6 font-medium text-white">
                    Modifica Cliente
                  </h3>
                  <button
                    type="button"
                    className="bg-primary-600 rounded-md text-primary-200 hover:text-white focus:outline-none"
                    onClick={() => setShowEditModal(false)}
                  >
                    <span className="sr-only">Close</span>
                    <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <form onSubmit={handleEditClient}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="grid grid-cols-1 gap-4">
                    <div>
                      <label htmlFor="edit-name" className="block text-sm font-medium text-gray-700 mb-1">
                        Nome <span className="text-red-600">*</span>
                      </label>
                      <input
                        type="text"
                        id="edit-name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="edit-chain" className="block text-sm font-medium text-gray-700 mb-1">
                        Catena
                      </label>
                      <input
                        type="text"
                        id="edit-chain"
                        name="chain"
                        value={formData.chain}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                        placeholder="es. Carrefour, Eurospin, ecc."
                      />
                    </div>
                    <div>
                      <label htmlFor="edit-email" className="block text-sm font-medium text-gray-700 mb-1">
                        Email <span className="text-red-600">*</span>
                      </label>
                      <input
                        type="email"
                        id="edit-email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="edit-phone" className="block text-sm font-medium text-gray-700 mb-1">
                        Telefono
                      </label>
                      <input
                        type="tel"
                        id="edit-phone"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                      />
                    </div>
                    <div>
                      <label htmlFor="edit-address" className="block text-sm font-medium text-gray-700 mb-1">
                        Indirizzo
                      </label>
                      <textarea
                        id="edit-address"
                        name="address"
                        value={formData.address}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg resize-none transition-all"
                        rows="3"
                      ></textarea>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-lg border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                  >
                    Aggiorna cliente
                  </button>
                  <button
                    type="button"
                    className="mt-3 w-full inline-flex justify-center rounded-lg border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                    onClick={() => setShowEditModal(false)}
                  >
                    Annulla
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="delete-client-modal" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-gradient-to-r from-red-500 to-red-700 px-4 py-5 sm:px-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg leading-6 font-medium text-white">
                    Elimina Cliente
                  </h3>
                  <button
                    type="button"
                    className="bg-red-600 rounded-md text-red-200 hover:text-white focus:outline-none"
                    onClick={() => setShowDeleteModal(false)}
                  >
                    <span className="sr-only">Close</span>
                    <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Conferma eliminazione
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Sei sicuro di voler eliminare il cliente <span className="font-semibold">{currentClient?.name}</span>?
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        Questa azione è irreversibile e tutti i ticket associati a questo cliente verranno eliminati definitivamente.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-lg border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                  onClick={handleDeleteClient}
                >
                  Elimina cliente
                </button>
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-lg border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                  onClick={() => setShowDeleteModal(false)}
                >
                  Annulla
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Clients; 