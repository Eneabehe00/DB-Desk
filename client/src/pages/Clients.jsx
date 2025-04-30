import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FaPlus, FaSearch, FaEdit, FaTrash, FaTicketAlt } from 'react-icons/fa';

const Clients = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentClient, setCurrentClient] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    chain: ''
  });

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await api.get('/clients');
      setClients(response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Errore nel caricamento dei clienti');
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    setSearch(e.target.value);
  };

  const filteredClients = clients.filter(client => 
    client.name.toLowerCase().includes(search.toLowerCase()) || 
    client.email.toLowerCase().includes(search.toLowerCase())
  );

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

  const openEditModal = (client) => {
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

  const openDeleteModal = (client) => {
    setCurrentClient(client);
    setShowDeleteModal(true);
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
          <p className="text-secondary-500">Gestisci i clienti</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary mt-4 md:mt-0 flex items-center"
        >
          <FaPlus className="mr-2" />
          Aggiungi Cliente
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <FaSearch className="text-secondary-400" />
        </div>
        <input
          type="text"
          value={search}
          onChange={handleSearch}
          className="form-input pl-10"
          placeholder="Cerca cliente per nome o email..."
        />
      </div>

      {/* Clients Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-secondary-200">
            <thead className="bg-secondary-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Nome
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Catena
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Email
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Telefono
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Ticket
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Azioni
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-secondary-200">
              {filteredClients.map((client) => (
                <tr key={client.id} className="hover:bg-secondary-50 cursor-pointer">
                  <td className="px-6 py-4 whitespace-nowrap" onClick={() => window.location.href = `/clients/${client.id}`}>
                    <div className="text-sm font-medium text-secondary-900">{client.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap" onClick={() => window.location.href = `/clients/${client.id}`}>
                    <div className="text-sm text-secondary-500">{client.chain || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap" onClick={() => window.location.href = `/clients/${client.id}`}>
                    <div className="text-sm text-secondary-500">{client.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap" onClick={() => window.location.href = `/clients/${client.id}`}>
                    <div className="text-sm text-secondary-500">{client.phone || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap" onClick={() => window.location.href = `/clients/${client.id}`}>
                    <div className="flex items-center">
                      <FaTicketAlt className="text-primary-500 mr-1" />
                      <span className="text-sm text-secondary-500">
                        {client.tickets?.length || 0}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => openEditModal(client)}
                      className="text-primary-600 hover:text-primary-900 mr-3"
                    >
                      <FaEdit />
                    </button>
                    <button
                      onClick={() => openDeleteModal(client)}
                      className="text-red-600 hover:text-red-900"
                    >
                      <FaTrash />
                    </button>
                  </td>
                </tr>
              ))}
              
              {filteredClients.length === 0 && (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-sm text-secondary-500">
                    Nessun cliente trovato
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Client Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Aggiungi Cliente</h2>
              <form onSubmit={handleAddClient}>
                <div className="mb-4">
                  <label htmlFor="name" className="form-label">Nome *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="chain" className="form-label">Catena</label>
                  <input
                    type="text"
                    id="chain"
                    name="chain"
                    value={formData.chain}
                    onChange={handleChange}
                    className="form-input"
                    placeholder="es. Carrefour, Eurospin, ecc."
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="email" className="form-label">Email *</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="phone" className="form-label">Telefono</label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    className="form-input"
                  />
                </div>
                <div className="mb-6">
                  <label htmlFor="address" className="form-label">Indirizzo</label>
                  <input
                    type="text"
                    id="address"
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    className="form-input"
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="btn btn-secondary"
                  >
                    Annulla
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                  >
                    Salva
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Client Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Modifica Cliente</h2>
              <form onSubmit={handleEditClient}>
                <div className="mb-4">
                  <label htmlFor="edit-name" className="form-label">Nome *</label>
                  <input
                    type="text"
                    id="edit-name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="edit-chain" className="form-label">Catena</label>
                  <input
                    type="text"
                    id="edit-chain"
                    name="chain"
                    value={formData.chain}
                    onChange={handleChange}
                    className="form-input"
                    placeholder="es. Carrefour, Eurospin, ecc."
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="edit-email" className="form-label">Email *</label>
                  <input
                    type="email"
                    id="edit-email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="edit-phone" className="form-label">Telefono</label>
                  <input
                    type="tel"
                    id="edit-phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    className="form-input"
                  />
                </div>
                <div className="mb-6">
                  <label htmlFor="edit-address" className="form-label">Indirizzo</label>
                  <input
                    type="text"
                    id="edit-address"
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    className="form-input"
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="btn btn-secondary"
                  >
                    Annulla
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                  >
                    Aggiorna
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Conferma Eliminazione</h2>
              <p className="mb-6 text-secondary-600">
                Sei sicuro di voler eliminare il cliente <span className="font-semibold">{currentClient?.name}</span>? 
                Questa azione non può essere annullata e tutti i ticket associati a questo cliente verranno eliminati.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="btn btn-secondary"
                >
                  Annulla
                </button>
                <button
                  onClick={handleDeleteClient}
                  className="btn btn-danger"
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

export default Clients; 