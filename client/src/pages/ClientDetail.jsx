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
    <div className="space-y-6">
      <div className="flex items-center mb-6">
        <Link to="/clients" className="text-primary-600 hover:text-primary-800 mr-4">
          <FaArrowLeft />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">
            {client.name}
            <span className="ml-2 text-sm font-normal text-secondary-500">#{client.id.substring(0, 8)}</span>
          </h1>
        </div>
        <div className="ml-auto">
          <div className="relative inline-block text-left">
            <button 
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="btn btn-secondary flex items-center"
            >
              Azioni
              <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {dropdownOpen && (
              <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5">
                <div className="py-1" role="menu" aria-orientation="vertical" aria-labelledby="options-menu">
                  <button
                    onClick={() => {
                      setShowEditModal(true);
                      setDropdownOpen(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-secondary-700 hover:bg-secondary-100 hover:text-secondary-900"
                    role="menuitem"
                  >
                    <FaEdit className="inline mr-2" /> Modifica
                  </button>
                  <button
                    onClick={() => {
                      setShowDeleteModal(true);
                      setDropdownOpen(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-secondary-100 hover:text-red-700"
                    role="menuitem"
                  >
                    <FaTrash className="inline mr-2" /> Elimina
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Client Info */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Informazioni Cliente</h2>
            
            <div className="space-y-3">
              <div className="flex items-start">
                <FaBuilding className="text-secondary-400 mt-1 mr-3" />
                <div>
                  <div className="text-xs text-secondary-500">Nome</div>
                  <div className="font-medium">{client.name}</div>
                </div>
              </div>
              
              <div className="flex items-start">
                <svg className="text-secondary-400 mt-1 mr-3 w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM14 11a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-1a1 1 0 011-1z" />
                </svg>
                <div>
                  <div className="text-xs text-secondary-500">Catena</div>
                  <div className="font-medium">{client.chain || '-'}</div>
                </div>
              </div>
              
              <div className="flex items-start">
                <FaEnvelope className="text-secondary-400 mt-1 mr-3" />
                <div>
                  <div className="text-xs text-secondary-500">Email</div>
                  <div className="font-medium">{client.email}</div>
                </div>
              </div>
              
              <div className="flex items-start">
                <FaPhone className="text-secondary-400 mt-1 mr-3" />
                <div>
                  <div className="text-xs text-secondary-500">Telefono</div>
                  <div className="font-medium">{client.phone || '-'}</div>
                </div>
              </div>
              
              <div className="flex items-start">
                <FaMapMarkerAlt className="text-secondary-400 mt-1 mr-3" />
                <div>
                  <div className="text-xs text-secondary-500">Indirizzo</div>
                  <div className="font-medium">{client.address || '-'}</div>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="text-secondary-400 mt-1 mr-3">📅</div>
                <div>
                  <div className="text-xs text-secondary-500">Cliente dal</div>
                  <div className="font-medium">{formatDate(client.createdAt)}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Client Tickets */}
        <div className="lg:col-span-2">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Ticket Recenti</h2>
            
            {client.tickets && client.tickets.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-secondary-200">
                  <thead className="bg-secondary-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                        Titolo
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                        Stato
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                        Data
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-secondary-200">
                    {client.tickets.map((ticket) => (
                      <tr key={ticket.id} className="hover:bg-secondary-50 cursor-pointer">
                        <td className="px-6 py-4 whitespace-nowrap" onClick={() => navigate(`/tickets/${ticket.id}`)}>
                          <div className="flex items-center">
                            <FaTicketAlt className="text-secondary-400 mr-2" />
                            <div className="text-sm font-medium text-secondary-900">{ticket.title}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap" onClick={() => navigate(`/tickets/${ticket.id}`)}>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(ticket.status)}`}>
                            {translateStatus(ticket.status)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-500" onClick={() => navigate(`/tickets/${ticket.id}`)}>
                          {formatDate(ticket.createdAt)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-secondary-500 text-center py-4">Nessun ticket associato a questo cliente</p>
            )}
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-60">
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl overflow-hidden transform transition-all">
            <div className="bg-gradient-to-r from-primary-500 to-primary-700 p-6">
              <h2 className="text-xl font-bold text-white">Modifica Cliente</h2>
              <p className="text-primary-100 text-sm">Modifica le informazioni del cliente</p>
            </div>
            <div className="p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
              <form onSubmit={handleUpdate}>
                <div className="mb-4">
                  <label htmlFor="name" className="form-label text-secondary-700">Nome *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="chain" className="form-label text-secondary-700">Catena</label>
                  <input
                    type="text"
                    id="chain"
                    name="chain"
                    value={formData.chain}
                    onChange={handleChange}
                    className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    placeholder="es. Carrefour, Eurospin, ecc."
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="email" className="form-label text-secondary-700">Email *</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="phone" className="form-label text-secondary-700">Telefono</label>
                  <input
                    type="text"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    className="form-input w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                  />
                </div>
                <div className="mb-6">
                  <label htmlFor="address" className="form-label text-secondary-700">Indirizzo</label>
                  <textarea
                    id="address"
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    className="form-textarea w-full rounded-lg border-secondary-300 shadow-sm focus:border-primary-500 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    rows="3"
                  ></textarea>
                </div>
                <div className="flex justify-end space-x-3 pt-4 border-t border-secondary-200">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="px-4 py-2 bg-white border border-secondary-300 rounded-lg text-secondary-700 hover:bg-secondary-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 shadow-sm transition-colors"
                  >
                    Annulla
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 shadow-sm transition-colors"
                  >
                    Aggiorna
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-60">
          <div className="bg-white rounded-xl w-full max-w-md shadow-2xl overflow-hidden transform transition-all">
            <div className="bg-gradient-to-r from-red-500 to-red-700 p-6">
              <h2 className="text-xl font-bold text-white">Elimina Cliente</h2>
              <p className="text-red-100 text-sm">Questa azione non può essere annullata</p>
            </div>
            <div className="p-6">
              <p className="mb-6 text-secondary-600">
                Sei sicuro di voler eliminare <span className="font-semibold">{client.name}</span>? 
                Tutti i ticket associati a questo cliente verranno eliminati permanentemente.
              </p>
              <div className="flex justify-end space-x-3 pt-4 border-t border-secondary-200">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="px-4 py-2 bg-white border border-secondary-300 rounded-lg text-secondary-700 hover:bg-secondary-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 shadow-sm transition-colors"
                >
                  Annulla
                </button>
                <button
                  onClick={handleDelete}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 shadow-sm transition-colors"
                >
                  Elimina
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