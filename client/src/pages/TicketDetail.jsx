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
        return 'bg-blue-100 text-blue-800 border border-blue-200';
      case 'CLOSED':
        return 'bg-gray-100 text-gray-800 border border-gray-200';
      case 'PLANNED':
        return 'bg-purple-100 text-purple-800 border border-purple-200';
      case 'CLOSED_REMOTE':
        return 'bg-slate-100 text-slate-800 border border-slate-200';
      case 'CLOSED_ONSITE':
        return 'bg-zinc-100 text-zinc-800 border border-zinc-200';
      case 'PLANNED_ONSITE':
        return 'bg-indigo-100 text-indigo-800 border border-indigo-200';
      case 'VERIFYING':
        return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
      case 'WAITING_CLIENT':
        return 'bg-orange-100 text-orange-800 border border-orange-200';
      case 'TO_REPORT':
        return 'bg-green-100 text-green-800 border border-green-200';
      default:
        return 'bg-blue-100 text-blue-800 border border-blue-200';
    }
  };

  const getPriorityBadgeClass = (priority) => {
    switch (priority) {
      case 'LOW':
        return 'bg-green-100 text-green-800 border border-green-200';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border border-orange-200';
      case 'URGENT':
        return 'bg-red-100 text-red-800 border border-red-200';
      default:
        return 'bg-blue-100 text-blue-800 border border-blue-200';
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
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header with breadcrumbs and actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center space-x-4">
          <Link 
            to="/tickets" 
            className="group flex items-center text-sm font-medium text-gray-500 hover:text-primary-600 transition-all duration-200"
          >
            <FaArrowLeft className="mr-2 h-4 w-4 transition-transform duration-200 group-hover:-translate-x-1" />
            <span>Torna ai ticket</span>
          </Link>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => setShowCommentModal(true)}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200"
          >
            <FaPlus className="mr-2 h-3.5 w-3.5" />
            Commento
          </button>
          
          <div className="relative ml-3">
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
                    Modifica ticket
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
                    Elimina ticket
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Ticket title and status */}
      <div className="pb-5 border-b border-gray-200">
        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          {ticket.title}
        </h1>
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
            ID: #{ticket.id.substring(0, 8)}
          </span>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeClass(ticket.status)}`}>
            {translateStatus(ticket.status)}
          </span>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getPriorityBadgeClass(ticket.priority)}`}>
            {translatePriority(ticket.priority)}
          </span>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            {formatDate(ticket.createdAt)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Ticket Info */}
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden transition-all hover:shadow-md">
            <div className="border-b border-gray-100 px-6 py-4 bg-gray-50">
              <h2 className="text-xl font-semibold text-gray-800">Descrizione</h2>
            </div>
            <div className="p-6">
              <p className="text-gray-700 whitespace-pre-line leading-relaxed">{ticket.description}</p>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden transition-all hover:shadow-md">
            <div className="border-b border-gray-100 px-6 py-4 bg-gray-50 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-800">Commenti</h2>
              <button 
                onClick={() => setShowCommentModal(true)}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200"
              >
                <FaPlus className="mr-1.5 h-3 w-3" />
                Aggiungi
              </button>
            </div>
            
            <div className="divide-y divide-gray-100">
              {ticket.comments && ticket.comments.length > 0 ? (
                ticket.comments.map((comment) => (
                  <div key={comment.id} className="p-6 hover:bg-gray-50 transition-colors duration-150">
                    {editCommentId === comment.id ? (
                      <div className="space-y-4">
                        <textarea
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500 transition-all"
                          value={editCommentContent}
                          onChange={(e) => setEditCommentContent(e.target.value)}
                          rows="4"
                        />
                        <div className="flex justify-end space-x-2">
                          <button
                            onClick={() => {
                              setEditCommentId(null);
                              setEditCommentContent('');
                            }}
                            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200"
                          >
                            Annulla
                          </button>
                          <button
                            onClick={handleUpdateComment}
                            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200"
                          >
                            Salva
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex items-center">
                            <div className="bg-primary-100 text-primary-700 rounded-full w-10 h-10 flex items-center justify-center mr-3 shrink-0">
                              <FaUser />
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">{comment.author ? comment.author.name : 'Utente'}</div>
                              <div className="text-sm text-gray-500">
                                {formatDate(comment.createdAt)}
                              </div>
                            </div>
                          </div>
                          <div className="flex space-x-1">
                            <button 
                              onClick={() => handleEditComment(comment)}
                              className="p-1.5 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-full transition-colors"
                              title="Modifica commento"
                            >
                              <FaEdit size={14} />
                            </button>
                            <button 
                              onClick={() => handleConfirmDeleteComment(comment)}
                              className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
                              title="Elimina commento"
                            >
                              <FaTrash size={14} />
                            </button>
                          </div>
                        </div>
                        <p className="text-gray-700 whitespace-pre-line">{comment.content}</p>
                      </>
                    )}
                  </div>
                ))
              ) : (
                <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                  <div className="bg-gray-100 rounded-full p-3 mb-4">
                    <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                    </svg>
                  </div>
                  <h3 className="text-base font-medium text-gray-900">Nessun commento</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Aggiungi il primo commento a questo ticket
                  </p>
                  <button 
                    onClick={() => setShowCommentModal(true)}
                    className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200"
                  >
                    <FaPlus className="mr-2 h-3.5 w-3.5" />
                    Aggiungi commento
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden transition-all hover:shadow-md">
            <div className="border-b border-gray-100 px-6 py-4 bg-gray-50">
              <h2 className="text-xl font-semibold text-gray-800">Dettagli</h2>
            </div>
            <div className="p-6">
              <dl className="divide-y divide-gray-100">
                <div className="flex justify-between py-3 first:pt-0 last:pb-0">
                  <dt className="text-sm font-medium text-gray-500">Cliente</dt>
                  <dd className="text-sm font-medium text-gray-900 ml-6 text-right">
                    <Link to={`/clients/${ticket.client.id}`} className="text-primary-600 hover:text-primary-700 hover:underline">
                      {ticket.client.name}
                    </Link>
                  </dd>
                </div>
                {ticket.client.chain && (
                  <div className="flex justify-between py-3 first:pt-0 last:pb-0">
                    <dt className="text-sm font-medium text-gray-500">Catena</dt>
                    <dd className="text-sm font-medium text-gray-900 ml-6 text-right">{ticket.client.chain}</dd>
                  </div>
                )}
                <div className="flex justify-between py-3 first:pt-0 last:pb-0">
                  <dt className="text-sm font-medium text-gray-500">Email</dt>
                  <dd className="text-sm font-medium text-gray-900 ml-6 text-right">{ticket.client.email}</dd>
                </div>
                <div className="flex justify-between py-3 first:pt-0 last:pb-0">
                  <dt className="text-sm font-medium text-gray-500">Creato da</dt>
                  <dd className="text-sm font-medium text-gray-900 ml-6 text-right">{ticket.createdBy.name}</dd>
                </div>
                <div className="flex justify-between py-3 first:pt-0 last:pb-0">
                  <dt className="text-sm font-medium text-gray-500">Assegnato a</dt>
                  <dd className="text-sm font-medium text-gray-900 ml-6 text-right">
                    {ticket.assignedTo ? ticket.assignedTo.name : 
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        Non assegnato
                      </span>
                    }
                  </dd>
                </div>
                <div className="flex justify-between py-3 first:pt-0 last:pb-0">
                  <dt className="text-sm font-medium text-gray-500">Creato il</dt>
                  <dd className="text-sm font-medium text-gray-900 ml-6 text-right">{formatDate(ticket.createdAt)}</dd>
                </div>
                <div className="flex justify-between py-3 first:pt-0 last:pb-0">
                  <dt className="text-sm font-medium text-gray-500">Aggiornato il</dt>
                  <dd className="text-sm font-medium text-gray-900 ml-6 text-right">{formatDate(ticket.updatedAt)}</dd>
                </div>
              </dl>
            </div>
          </div>

          <button
            onClick={() => setShowEditModal(true)}
            className="w-full py-2.5 px-4 border border-primary-300 font-medium rounded-lg text-primary-700 bg-primary-50 hover:bg-primary-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200 text-sm flex items-center justify-center"
          >
            <FaEdit className="mr-2 h-4 w-4" />
            Modifica questo ticket
          </button>
        </div>
      </div>

      {/* Edit Ticket Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="edit-ticket-modal" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
              <div className="bg-gradient-to-r from-primary-500 to-primary-700 px-4 py-5 sm:px-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg leading-6 font-medium text-white">
                    Modifica Ticket
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
                <div className="bg-white p-6 overflow-y-auto max-h-[calc(100vh-200px)]">
                  {/* Client Information (Read-only) */}
                  <div className="mb-6 bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-base font-semibold text-gray-900 flex items-center">
                        <div className="bg-blue-100 p-1.5 rounded-full mr-2">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-600" viewBox="0 0 20 20" fill="currentColor">
                            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                            <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                        Dettagli Cliente
                      </h3>
                      <Link 
                        to={`/clients/${ticket.client.id}`} 
                        className="text-xs px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full flex items-center border border-blue-200 hover:bg-blue-100 transition-colors duration-200"
                      >
                        <FaEdit className="mr-1" size={10} />
                        Visualizza cliente
                      </Link>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <div className="text-xs text-gray-500 mb-1">Nome:</div>
                        <div className="font-medium text-gray-900">{ticket.client.name}</div>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <div className="text-xs text-gray-500 mb-1">Email:</div>
                        <div className="font-medium text-gray-900">{ticket.client.email}</div>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <div className="text-xs text-gray-500 mb-1">Telefono:</div>
                        <div className="font-medium text-gray-900">{ticket.client.phone || '-'}</div>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <div className="text-xs text-gray-500 mb-1">Catena:</div>
                        <div className="font-medium text-gray-900">{ticket.client.chain || '-'}</div>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-lg md:col-span-2">
                        <div className="text-xs text-gray-500 mb-1">Indirizzo:</div>
                        <div className="font-medium text-gray-900">{ticket.client.address || '-'}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="my-6">
                    <h4 className="text-base font-medium text-gray-700 mb-4">Informazioni Ticket</h4>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                          Stato
                        </label>
                        <select
                          id="status"
                          name="status"
                          value={ticketData.status}
                          onChange={handleChange}
                          className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
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
                        <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
                          Priorità
                        </label>
                        <select
                          id="priority"
                          name="priority"
                          value={ticketData.priority}
                          onChange={handleChange}
                          className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                        >
                          <option value="LOW">Bassa</option>
                          <option value="MEDIUM">Media</option>
                          <option value="HIGH">Alta</option>
                          <option value="URGENT">Urgente</option>
                        </select>
                      </div>
                      <div>
                        <label htmlFor="assignedToId" className="block text-sm font-medium text-gray-700 mb-1">
                          Assegnato a
                        </label>
                        <select
                          id="assignedToId"
                          name="assignedToId"
                          value={ticketData.assignedToId}
                          onChange={handleChange}
                          className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                        >
                          <option value="">Non assegnato</option>
                          {users.map(user => (
                            <option key={user.id} value={user.id}>{user.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    
                    <div className="mb-4">
                      <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                        Titolo <span className="text-red-600">*</span>
                      </label>
                      <input
                        type="text"
                        id="title"
                        name="title"
                        value={ticketData.title}
                        onChange={handleChange}
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg transition-all"
                        required
                      />
                    </div>
                    
                    <div>
                      <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                        Descrizione <span className="text-red-600">*</span>
                      </label>
                      <textarea
                        id="description"
                        name="description"
                        value={ticketData.description}
                        onChange={handleChange}
                        rows="6"
                        className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg resize-none transition-all"
                        required
                      ></textarea>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-lg border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                  >
                    Salva modifiche
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
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="delete-ticket-modal" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-gradient-to-r from-red-500 to-red-700 px-4 py-5 sm:px-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg leading-6 font-medium text-white">
                    Elimina Ticket
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
                        Sei sicuro di voler eliminare il ticket <span className="font-semibold">"{ticket.title}"</span>?
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        Questa azione è irreversibile e tutti i commenti e le informazioni associate a questo ticket verranno eliminati definitivamente.
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
                  Elimina ticket
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

      {/* Add Comment Modal */}
      {showCommentModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="add-comment-modal" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-gradient-to-r from-primary-500 to-primary-700 px-4 py-5 sm:px-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg leading-6 font-medium text-white">
                    Aggiungi Commento
                  </h3>
                  <button
                    type="button"
                    className="bg-primary-600 rounded-md text-primary-200 hover:text-white focus:outline-none"
                    onClick={() => setShowCommentModal(false)}
                  >
                    <span className="sr-only">Close</span>
                    <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <form onSubmit={handleAddComment}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="mb-4">
                    <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-1">
                      Il tuo commento <span className="text-red-600">*</span>
                    </label>
                    <textarea
                      id="comment"
                      name="comment"
                      rows="6"
                      className="shadow-sm block w-full focus:ring-primary-500 focus:border-primary-500 sm:text-sm border border-gray-300 rounded-lg resize-none transition-all"
                      placeholder="Scrivi qui il tuo commento..."
                      value={comment}
                      onChange={handleCommentChange}
                      required
                    ></textarea>
                  </div>
                  
                  <div className="text-xs text-gray-500 italic">
                    Questo commento sarà visibile a tutti gli utenti che hanno accesso a questo ticket.
                  </div>
                </div>
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-lg border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                  >
                    Aggiungi commento
                  </button>
                  <button
                    type="button"
                    className="mt-3 w-full inline-flex justify-center rounded-lg border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                    onClick={() => setShowCommentModal(false)}
                  >
                    Annulla
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Comment Modal */}
      {showDeleteCommentModal && selectedComment && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="delete-comment-modal" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-gradient-to-r from-red-500 to-red-700 px-4 py-5 sm:px-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg leading-6 font-medium text-white">
                    Elimina Commento
                  </h3>
                  <button
                    type="button"
                    className="bg-red-600 rounded-md text-red-200 hover:text-white focus:outline-none"
                    onClick={() => {
                      setShowDeleteCommentModal(false);
                      setSelectedComment(null);
                    }}
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
                        Sei sicuro di voler eliminare questo commento? Questa azione è irreversibile e il commento sarà eliminato definitivamente.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-lg border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                  onClick={handleDeleteComment}
                >
                  Elimina commento
                </button>
                <button
                  type="button"
                  className="mt-3 w-full inline-flex justify-center rounded-lg border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200"
                  onClick={() => {
                    setShowDeleteCommentModal(false);
                    setSelectedComment(null);
                  }}
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

export default TicketDetail; 