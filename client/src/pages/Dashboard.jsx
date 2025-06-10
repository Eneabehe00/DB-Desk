import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { FaTicketAlt, FaUsers, FaClock, FaCheckCircle } from 'react-icons/fa';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

ChartJS.register(
  ArcElement, 
  Tooltip, 
  Legend, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  Title
);

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalTickets: 0,
    openTickets: 0,
    resolvedTickets: 0,
    totalClients: 0,
    ticketsByPriority: { LOW: 0, MEDIUM: 0, HIGH: 0, URGENT: 0 },
    ticketsByStatus: { OPEN: 0, IN_PROGRESS: 0, RESOLVED: 0, CLOSED: 0 },
    recentTickets: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // In una implementazione reale, avremo un endpoint specifico per i dati dashboard
        // Qui simuliamo estraendo i dati dalle chiamate esistenti
        const ticketsResponse = await api.get('/tickets');
        const clientsResponse = await api.get('/clients');
        
        const tickets = ticketsResponse.data;
        const clients = clientsResponse.data;
        
        // Calcola statistiche
        const openTickets = tickets.filter(t => t.status === 'OPEN' || t.status === 'IN_PROGRESS').length;
        const resolvedTickets = tickets.filter(t => t.status === 'RESOLVED' || t.status === 'CLOSED').length;
        
        // Conta ticket per priorità
        const ticketsByPriority = {
          LOW: tickets.filter(t => t.priority === 'LOW').length,
          MEDIUM: tickets.filter(t => t.priority === 'MEDIUM').length,
          HIGH: tickets.filter(t => t.priority === 'HIGH').length,
          URGENT: tickets.filter(t => t.priority === 'URGENT').length
        };
        
        // Conta ticket per stato
        const ticketsByStatus = {
          OPEN: tickets.filter(t => t.status === 'OPEN').length,
          IN_PROGRESS: tickets.filter(t => t.status === 'IN_PROGRESS').length,
          RESOLVED: tickets.filter(t => t.status === 'RESOLVED').length,
          CLOSED: tickets.filter(t => t.status === 'CLOSED').length
        };
        
        // Ordina i ticket per data di creazione (più recenti prima)
        const sortedTickets = [...tickets].sort((a, b) => 
          new Date(b.createdAt) - new Date(a.createdAt)
        );
        
        setStats({
          totalTickets: tickets.length,
          openTickets,
          resolvedTickets,
          totalClients: clients.length,
          ticketsByPriority,
          ticketsByStatus,
          recentTickets: sortedTickets.slice(0, 5) // prendi i 5 ticket più recenti
        });
        
        setLoading(false);
      } catch (error) {
        toast.error('Errore nel caricamento dei dati dashboard');
        console.error(error);
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const priorityChartData = {
    labels: ['Bassa', 'Media', 'Alta', 'Urgente'],
    datasets: [
      {
        label: 'Ticket per priorità',
        data: [
          stats.ticketsByPriority.LOW,
          stats.ticketsByPriority.MEDIUM,
          stats.ticketsByPriority.HIGH,
          stats.ticketsByPriority.URGENT
        ],
        backgroundColor: [
          'rgba(74, 222, 128, 0.6)',
          'rgba(250, 204, 21, 0.6)',
          'rgba(249, 115, 22, 0.6)',
          'rgba(239, 68, 68, 0.6)'
        ],
        borderColor: [
          'rgba(74, 222, 128, 1)',
          'rgba(250, 204, 21, 1)',
          'rgba(249, 115, 22, 1)',
          'rgba(239, 68, 68, 1)'
        ],
        borderWidth: 1
      }
    ]
  };

  const statusChartData = {
    labels: ['Aperto', 'In Corso', 'Risolto', 'Chiuso'],
    datasets: [
      {
        label: 'Ticket per stato',
        data: [
          stats.ticketsByStatus.OPEN,
          stats.ticketsByStatus.IN_PROGRESS,
          stats.ticketsByStatus.RESOLVED,
          stats.ticketsByStatus.CLOSED
        ],
        backgroundColor: [
          'rgba(99, 102, 241, 0.6)',
          'rgba(14, 165, 233, 0.6)',
          'rgba(34, 197, 94, 0.6)',
          'rgba(107, 114, 128, 0.6)'
        ],
        borderWidth: 1
      }
    ]
  };

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Dashboard</h1>
        <p className="text-secondary-500">Panoramica del sistema di ticket</p>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card bg-gradient-to-br from-blue-100 to-blue-50 border-l-4 border-blue-500">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-500 text-white mr-4">
              <FaTicketAlt size={24} />
            </div>
            <div>
              <p className="text-secondary-600 text-sm">Ticket Totali</p>
              <p className="text-2xl font-bold text-secondary-900">{stats.totalTickets}</p>
            </div>
          </div>
        </div>
        
        <div className="card bg-gradient-to-br from-yellow-100 to-yellow-50 border-l-4 border-yellow-500">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-500 text-white mr-4">
              <FaClock size={24} />
            </div>
            <div>
              <p className="text-secondary-600 text-sm">Ticket Aperti</p>
              <p className="text-2xl font-bold text-secondary-900">{stats.openTickets}</p>
            </div>
          </div>
        </div>
        
        <div className="card bg-gradient-to-br from-green-100 to-green-50 border-l-4 border-green-500">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-500 text-white mr-4">
              <FaCheckCircle size={24} />
            </div>
            <div>
              <p className="text-secondary-600 text-sm">Ticket Risolti</p>
              <p className="text-2xl font-bold text-secondary-900">{stats.resolvedTickets}</p>
            </div>
          </div>
        </div>
        
        <div className="card bg-gradient-to-br from-purple-100 to-purple-50 border-l-4 border-purple-500">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-500 text-white mr-4">
              <FaUsers size={24} />
            </div>
            <div>
              <p className="text-secondary-600 text-sm">Clienti</p>
              <p className="text-2xl font-bold text-secondary-900">{stats.totalClients}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-semibold mb-4 text-secondary-900">Ticket per Priorità</h2>
          <div className="h-64">
            <Pie data={priorityChartData} options={{ maintainAspectRatio: false }} />
          </div>
        </div>
        
        <div className="card">
          <h2 className="text-xl font-semibold mb-4 text-secondary-900">Ticket per Stato</h2>
          <div className="h-64">
            <Bar 
              data={statusChartData} 
              options={{ 
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    display: false
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      precision: 0
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>
      
      {/* Recent Tickets */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-secondary-900">Ticket Recenti</h2>
          <Link to="/tickets" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
            Vedi tutti
          </Link>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-secondary-200">
            <thead className="bg-secondary-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  ID
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Titolo
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                  Cliente
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
              {stats.recentTickets.map((ticket) => (
                <tr key={ticket.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-500">
                    {ticket.id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link to={`/tickets/${ticket.id}`} className="text-sm font-medium text-secondary-900 hover:text-primary-600">
                      {ticket.title}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-700">
                    {ticket.client?.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${getStatusBadgeClass(ticket.status)}`}>
                      {ticket.status === 'OPEN' ? 'Aperto' : 
                       ticket.status === 'IN_PROGRESS' ? 'In Corso' : 
                       ticket.status === 'RESOLVED' ? 'Risolto' : 'Chiuso'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-500">
                    {new Date(ticket.createdAt).toLocaleDateString('it-IT')}
                  </td>
                </tr>
              ))}
              
              {stats.recentTickets.length === 0 && (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-sm text-secondary-500">
                    Nessun ticket recente
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 