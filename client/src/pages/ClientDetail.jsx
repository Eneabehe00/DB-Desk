import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FaArrowLeft, FaEdit, FaTrash, FaTicketAlt, FaBuilding, FaEnvelope, FaPhone, FaMapMarkerAlt } from 'react-icons/fa';

const ClientDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    chain: ''
  });

  useEffect(() => {
    fetchClient();
  }, [id]);

  const fetchClient = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/clients/${id}`);
      setClient(response.data);
      setFormData({
        name: response.data.name || '',
        email: response.data.email || '',
        phone: response.data.phone || '',
        address: response.data.address || '',
        chain: response.data.chain || ''
      });
      setLoading(false);
    } catch (error) {
      toast.error('Errore nel caricamento del cliente');
      navigate('/clients');
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    
    try {
      await api.put(`/clients/${id}`, formData);
      toast.success('Cliente aggiornato con successo');
      setShowEditModal(false);
      fetchClient();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'aggiornamento del cliente');
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/clients/${id}`);
      toast.success('Cliente eliminato con successo');
      navigate('/clients');
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'eliminazione del cliente');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'OPEN':
        return 'bg-blue-100 text-blue-800';
      case 'CLOSED':
        return 'bg-gray-100 text-gray-800';
      case 'PLANNED':
        return 'bg-purple-100 text-purple-800';
      case 'CLOSED_REMOTE':
        return 'bg-slate-100 text-slate-800';
      case 'CLOSED_ONSITE':
        return 'bg-gray-100 text-gray-800';
      case 'PLANNED_ONSITE':
        return 'bg-indigo-100 text-indigo-800';
      case 'VERIFYING':
        return 'bg-yellow-100 text-yellow-800';
      case 'WAITING_CLIENT':
        return 'bg-orange-100 text-orange-800';
      case 'TO_REPORT':
        return 'bg-green-100 text-green-800';
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center space-x-4">
          <Link 
            to="/clients" 
            className="group flex items-center text-sm font-medium text-gray-500 hover:text-primary-600 transition-all duration-200"
          >
            <FaArrowLeft className="mr-2 h-4 w-4 transition-transform duration-200 group-hover:-translate-x-1" />
            <span>Torna ai clienti</span>
          </Link>
        </div>
        
        <div className="relative">
          <button 
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200"
          >
            Azioni
            <svg className={`ml-2 h-4 w-4 text-gray-500 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {dropdownOpen && (
            <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-lg shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50 divide-y divide-gray-100">
              <div className="py-1" role="menu" aria-orientation="vertical">
                <button
                  onClick={() => {
                    setShowEditModal(true);
                    setDropdownOpen(false);
                  }}
                  className="flex w-full items-center px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-150"
                  role="menuitem"
                >
                  <FaEdit className="mr-3 h-4 w-4 text-gray-500" />
                  Modifica cliente
                </button>
              </div>
              <div className="py-1">
                <button
                  onClick={() => {
                    setShowDeleteModal(true);
                    setDropdownOpen(false);
                  }}
                  className="flex w-full items-center px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors duration-150"
                  role="menuitem"
                >
                  <FaTrash className="mr-3 h-4 w-4 text-red-500" />
                  Elimina cliente
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Client header */}
      <div className="pb-5 border-b border-gray-200">
        <div className="flex items-center">
          <div className="bg-primary-100 p-2.5 rounded-full mr-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-primary-600" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-1">
              {client.name}
            </h1>
            <div className="flex items-center">
              {client.chain && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200 mr-2">
                  {client.chain}
                </span>
              )}
              <span className="text-sm text-gray-500">ID: #{client.id.substring(0, 8)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Client Info Card */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden transition-all hover:shadow-md">
            <div className="border-b border-gray-100 px-6 py-4 bg-gray-50">
              <h2 className="text-xl font-semibold text-gray-800">Informazioni Cliente</h2>
            </div>
            <div className="p-6">
              <dl className="divide-y divide-gray-100">
                <div className="grid grid-cols-1 gap-4 py-3 first:pt-0 sm:grid-cols-2">
                  <div className="flex flex-col">
                    <dt className="text-sm font-medium text-gray-500 flex items-center">
                      <FaBuilding className="mr-2 h-4 w-4 text-gray-400" />
                      Nome
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 font-medium">{client.name}</dd>
                  </div>
                  
                  <div className="flex flex-col">
                    <dt className="text-sm font-medium text-gray-500 flex items-center">
                      <svg className="mr-2 h-4 w-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM14 11a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-1a1 1 0 011-1z" />
                      </svg>
                      Catena
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 font-medium">
                      {client.chain ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                          {client.chain}
                        </span>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </dd>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 gap-4 py-3 sm:grid-cols-2">
                  <div className="flex flex-col">
                    <dt className="text-sm font-medium text-gray-500 flex items-center">
                      <FaEnvelope className="mr-2 h-4 w-4 text-gray-400" />
                      Email
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 break-all">
                      <a href={`mailto:${client.email}`} className="text-primary-600 hover:text-primary-800 hover:underline">
                        {client.email}
                      </a>
                    </dd>
                  </div>
                  
                  <div className="flex flex-col">
                    <dt className="text-sm font-medium text-gray-500 flex items-center">
                      <FaPhone className="mr-2 h-4 w-4 text-gray-400" />
                      Telefono
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900 font-medium">
                      {client.phone ? (
                        <a href={`tel:${client.phone}`} className="text-primary-600 hover:text-primary-800 hover:underline">
                          {client.phone}
                        </a>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </dd>
                  </div>
                </div>
                
                <div className="py-3">
                  <dt className="text-sm font-medium text-gray-500 flex items-center mb-1">
                    <FaMapMarkerAlt className="mr-2 h-4 w-4 text-gray-400" />
                    Indirizzo
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900 font-medium">
                    {client.address || <span className="text-gray-500">-</span>}
                  </dd>
                </div>
                
                <div className="py-3">
                  <dt className="text-sm font-medium text-gray-500 flex items-center">
                    <svg className="mr-2 h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Cliente dal
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900 font-medium">{formatDate(client.createdAt)}</dd>
                </div>
              </dl>
            </div>
          </div>
          
          <button
            onClick={() => setShowEditModal(true)}
            className="w-full py-2.5 px-4 border border-primary-300 font-medium rounded-lg text-primary-700 bg-primary-50 hover:bg-primary-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200 text-sm flex items-center justify-center"
          >
            <FaEdit className="mr-2 h-4 w-4" />
            Modifica questo cliente
          </button>
        </div>

        {/* Client Tickets */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden transition-all hover:shadow-md">
            <div className="border-b border-gray-100 px-6 py-4 bg-gray-50 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-800">Ticket Recenti</h2>
              <Link 
                to="/tickets" 
                state={{ clientId: client.id }}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200"
              >
                <FaTicketAlt className="mr-1.5 h-3 w-3" />
                Nuovo Ticket
              </Link>
            </div>
            
            <div>
              {client.tickets && client.tickets.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Titolo
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Stato
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Data
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {client.tickets.map((ticket) => (
                        <tr key={ticket.id} className="hover:bg-gray-50 transition-colors duration-150 cursor-pointer" onClick={() => navigate(`/tickets/${ticket.id}`)}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <FaTicketAlt className="text-gray-400 mr-2 h-4 w-4" />
                              <div className="text-sm font-medium text-gray-900">{ticket.title}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(ticket.status)}`}>
                              {translateStatus(ticket.status)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(ticket.createdAt)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                  <div className="bg-gray-100 rounded-full p-3 mb-4">
                    <FaTicketAlt className="h-8 w-8 text-gray-400" />
                  </div>
                  <h3 className="text-base font-medium text-gray-900">Nessun ticket</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Non ci sono ticket associati a questo cliente
                  </p>
                  <Link 
                    to="/tickets" 
                    state={{ clientId: client.id }}
                    className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200"
                  >
                    <FaTicketAlt className="mr-2 h-4 w-4" />
                    Crea nuovo ticket
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
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
              <form onSubmit={handleUpdate}>
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
                        type="text"
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

      {/* Delete Modal */}
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
                        Sei sicuro di voler eliminare <span className="font-semibold">{client.name}</span>?
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        Questa azione è irreversibile e tutti i ticket associati a questo cliente verranno eliminati permanentemente.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-lg border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                  onClick={handleDelete}
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

export default ClientDetail; 