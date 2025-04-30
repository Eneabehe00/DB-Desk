import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { useAuth } from '../hooks/useAuth';
import { FaArrowLeft, FaEdit, FaTrash, FaPlus, FaUser } from 'react-icons/fa';

const TicketDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [users, setUsers] = useState([]);
  const [comment, setComment] = useState('');
  const [ticketData, setTicketData] = useState({
    title: '',
    description: '',
    status: '',
    priority: '',
    assignedToId: ''
  });
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [editCommentId, setEditCommentId] = useState(null);
  const [editCommentContent, setEditCommentContent] = useState('');
  const [showDeleteCommentModal, setShowDeleteCommentModal] = useState(false);
  const [selectedComment, setSelectedComment] = useState(null);

  useEffect(() => {
    fetchTicket();
    fetchUsers();
  }, [id]);

  const fetchTicket = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/tickets/${id}`);
      setTicket(response.data);
      setTicketData({
        title: response.data.title,
        description: response.data.description,
        status: response.data.status,
        priority: response.data.priority,
        assignedToId: response.data.assignedToId || ''
      });
      setLoading(false);
    } catch (error) {
      toast.error('Errore nel caricamento del ticket');
      navigate('/tickets');
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
    setTicketData({
      ...ticketData,
      [e.target.name]: e.target.value
    });
  };

  const handleCommentChange = (e) => {
    setComment(e.target.value);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    
    try {
      await api.put(`/tickets/${id}`, ticketData);
      toast.success('Ticket aggiornato con successo');
      setShowEditModal(false);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'aggiornamento del ticket');
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/tickets/${id}`);
      toast.success('Ticket eliminato con successo');
      navigate('/tickets');
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'eliminazione del ticket');
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    
    if (!comment.trim()) {
      toast.error('Il commento non può essere vuoto');
      return;
    }
    
    try {
      await api.post(`/tickets/${id}/comments`, { content: comment });
      toast.success('Commento aggiunto con successo');
      setComment('');
      setShowCommentModal(false);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'aggiunta del commento');
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'OPEN':
        return 'bg-blue-100 text-blue-800';
      case 'IN_PROGRESS':
        return 'bg-yellow-100 text-yellow-800';
      case 'RESOLVED':
        return 'bg-green-100 text-green-800';
      case 'CLOSED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-blue-100 text-blue-800';
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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Function to handle edit comment
  const handleEditComment = (comment) => {
    setEditCommentId(comment.id);
    setEditCommentContent(comment.content);
  };

  // Function to save edited comment
  const handleUpdateComment = async () => {
    if (!editCommentContent.trim()) {
      toast.error('Il commento non può essere vuoto');
      return;
    }

    try {
      await api.put(`/tickets/comments/${editCommentId}`, { content: editCommentContent });
      toast.success('Commento aggiornato con successo');
      setEditCommentId(null);
      setEditCommentContent('');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'aggiornamento del commento');
    }
  };

  // Function to handle delete comment confirmation
  const handleConfirmDeleteComment = (comment) => {
    setSelectedComment(comment);
    setShowDeleteCommentModal(true);
  };

  // Function to delete comment
  const handleDeleteComment = async () => {
    try {
      await api.delete(`/tickets/comments/${selectedComment.id}`);
      toast.success('Commento eliminato con successo');
      setShowDeleteCommentModal(false);
      setSelectedComment(null);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'eliminazione del commento');
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
        <Link to="/tickets" className="text-primary-600 hover:text-primary-800 mr-4">
          <FaArrowLeft />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">
            {ticket.title} 
            <span className="ml-2 text-sm font-normal text-secondary-500">#{ticket.id.substring(0, 8)}</span>
          </h1>
          <div className="flex flex-wrap gap-2 mt-1">
            <span className={`badge ${getStatusBadgeClass(ticket.status)}`}>
              {translateStatus(ticket.status)}
            </span>
            <span className={`badge ${getPriorityBadgeClass(ticket.priority)}`}>
              {translatePriority(ticket.priority)}
            </span>
          </div>
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
        {/* Ticket Info */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Descrizione</h2>
            <p className="text-secondary-700 whitespace-pre-line">{ticket.description}</p>
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Commenti</h2>
              <button 
                onClick={() => setShowCommentModal(true)}
                className="btn btn-primary flex items-center"
              >
                <FaPlus className="mr-1" />
                Aggiungi commento
              </button>
            </div>
            
            <div className="space-y-4">
              {ticket.comments && ticket.comments.length > 0 ? (
                ticket.comments.map((comment) => (
                  <div key={comment.id} className="border border-secondary-200 rounded-lg p-4">
                    {editCommentId === comment.id ? (
                      <div className="mb-2">
                        <textarea
                          className="form-input w-full h-24"
                          value={editCommentContent}
                          onChange={(e) => setEditCommentContent(e.target.value)}
                        />
                        <div className="flex justify-end mt-2 space-x-2">
                          <button
                            onClick={() => {
                              setEditCommentId(null);
                              setEditCommentContent('');
                            }}
                            className="btn btn-secondary btn-sm"
                          >
                            Annulla
                          </button>
                          <button
                            onClick={handleUpdateComment}
                            className="btn btn-primary btn-sm"
                          >
                            Salva
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex justify-between mb-2">
                          <div className="flex items-center">
                            <div className="bg-primary-100 text-primary-700 rounded-full w-8 h-8 flex items-center justify-center mr-2">
                              <FaUser />
                            </div>
                            <span className="font-medium">{comment.author ? comment.author.name : 'Utente'}</span>
                            <span className="text-secondary-500 ml-2 text-sm">
                              {formatDate(comment.createdAt)}
                            </span>
                          </div>
                          <div className="flex space-x-2">
                            <button 
                              onClick={() => handleEditComment(comment)}
                              className="text-secondary-600 hover:text-secondary-800"
                              title="Modifica commento"
                            >
                              <FaEdit size={14} />
                            </button>
                            <button 
                              onClick={() => handleConfirmDeleteComment(comment)}
                              className="text-red-600 hover:text-red-800"
                              title="Elimina commento"
                            >
                              <FaTrash size={14} />
                            </button>
                          </div>
                        </div>
                        <p className="text-secondary-700 whitespace-pre-line">{comment.content}</p>
                      </>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-secondary-500 text-center py-4">Nessun commento presente</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Dettagli</h2>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-secondary-500">Cliente</p>
                <p className="font-medium text-secondary-800">{ticket.client.name}</p>
              </div>
              <div>
                <p className="text-sm text-secondary-500">Email</p>
                <p className="font-medium text-secondary-800">{ticket.client.email}</p>
              </div>
              <div>
                <p className="text-sm text-secondary-500">Creato da</p>
                <p className="font-medium text-secondary-800">{ticket.createdBy.name}</p>
              </div>
              <div>
                <p className="text-sm text-secondary-500">Assegnato a</p>
                <p className="font-medium text-secondary-800">
                  {ticket.assignedTo ? ticket.assignedTo.name : 'Non assegnato'}
                </p>
              </div>
              <div>
                <p className="text-sm text-secondary-500">Creato il</p>
                <p className="font-medium text-secondary-800">{formatDate(ticket.createdAt)}</p>
              </div>
              <div>
                <p className="text-sm text-secondary-500">Ultimo aggiornamento</p>
                <p className="font-medium text-secondary-800">{formatDate(ticket.updatedAt)}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Ticket Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-2xl">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Modifica Ticket</h2>
              <form onSubmit={handleUpdate}>
                <div className="mb-4">
                  <label htmlFor="title" className="form-label">Titolo *</label>
                  <input
                    type="text"
                    id="title"
                    name="title"
                    value={ticketData.title}
                    onChange={handleChange}
                    className="form-input"
                    required
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <label htmlFor="status" className="form-label">Stato</label>
                    <select
                      id="status"
                      name="status"
                      value={ticketData.status}
                      onChange={handleChange}
                      className="form-input"
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
                    <label htmlFor="priority" className="form-label">Priorità</label>
                    <select
                      id="priority"
                      name="priority"
                      value={ticketData.priority}
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
                    <label htmlFor="assignedToId" className="form-label">Assegnato a</label>
                    <select
                      id="assignedToId"
                      name="assignedToId"
                      value={ticketData.assignedToId}
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
                    value={ticketData.description}
                    onChange={handleChange}
                    className="form-input h-32"
                    required
                  ></textarea>
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
                    Salva Modifiche
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
                Sei sicuro di voler eliminare il ticket <span className="font-semibold">{ticket.title}</span>? 
                Questa azione non può essere annullata.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="btn btn-secondary"
                >
                  Annulla
                </button>
                <button
                  onClick={handleDelete}
                  className="btn btn-danger"
                >
                  Elimina
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Comment Modal */}
      {showCommentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Aggiungi Commento</h2>
              <form onSubmit={handleAddComment}>
                <div className="mb-6">
                  <label htmlFor="comment" className="form-label">Commento *</label>
                  <textarea
                    id="comment"
                    value={comment}
                    onChange={handleCommentChange}
                    className="form-input h-32"
                    placeholder="Scrivi il tuo commento..."
                    required
                  ></textarea>
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowCommentModal(false)}
                    className="btn btn-secondary"
                  >
                    Annulla
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                  >
                    Aggiungi
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Comment Modal */}
      {showDeleteCommentModal && selectedComment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">Elimina Commento</h2>
              <p className="mb-4 text-secondary-600">
                Sei sicuro di voler eliminare questo commento? Questa azione non può essere annullata.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowDeleteCommentModal(false);
                    setSelectedComment(null);
                  }}
                  className="btn btn-secondary"
                >
                  Annulla
                </button>
                <button
                  onClick={handleDeleteComment}
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

export default TicketDetail; 