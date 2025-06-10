import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import api from '../api/axios';
import { FaFileDownload, FaCalendarAlt } from 'react-icons/fa';
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

const Reports = () => {
  const [loading, setLoading] = useState(true);
  const [ticketData, setTicketData] = useState({
    byStatus: {},
    byPriority: {},
    byMonth: [],
    ticketsPerClient: []
  });
  const [reportRange, setReportRange] = useState('month');

  useEffect(() => {
    fetchReportData();
  }, [reportRange]);

  const fetchReportData = async () => {
    try {
      setLoading(true);
      // In una implementazione reale, ci sarebbe un endpoint specifico per i report
      // Qui simuliamo estraendo i dati dalle chiamate esistenti
      const ticketsResponse = await api.get('/tickets');
      const clientsResponse = await api.get('/clients');
      
      const tickets = ticketsResponse.data;
      const clients = clientsResponse.data;
      
      processTicketData(tickets, clients);
      setLoading(false);
    } catch (error) {
      toast.error('Errore nel caricamento dei dati per i report');
      setLoading(false);
    }
  };

  const processTicketData = (tickets, clients) => {
    // Count by status
    const byStatus = tickets.reduce((acc, ticket) => {
      acc[ticket.status] = (acc[ticket.status] || 0) + 1;
      return acc;
    }, {});

    // Count by priority
    const byPriority = tickets.reduce((acc, ticket) => {
      acc[ticket.priority] = (acc[ticket.priority] || 0) + 1;
      return acc;
    }, {});

    // Count by month (for the selected time range)
    const monthNames = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'];
    const now = new Date();
    let monthsToShow = 12;
    
    if (reportRange === 'quarter') {
      monthsToShow = 3;
    } else if (reportRange === 'month') {
      monthsToShow = 1;
    }
    
    // Initialize months data
    const byMonth = Array(monthsToShow).fill().map((_, i) => {
      const d = new Date(now);
      d.setMonth(now.getMonth() - (monthsToShow - 1) + i);
      return {
        month: `${monthNames[d.getMonth()]} ${d.getFullYear()}`,
        open: 0,
        closed: 0,
        timestamp: d.getTime()
      };
    });
    
    // Count tickets by month
    tickets.forEach(ticket => {
      const ticketDate = new Date(ticket.createdAt);
      const monthItem = byMonth.find(m => {
        const mDate = new Date(m.timestamp);
        return mDate.getMonth() === ticketDate.getMonth() && mDate.getFullYear() === ticketDate.getFullYear();
      });
      
      if (monthItem) {
        if (ticket.status === 'OPEN' || ticket.status === 'IN_PROGRESS') {
          monthItem.open++;
        } else {
          monthItem.closed++;
        }
      }
    });

    // Tickets per client (top 5)
    let ticketsPerClient = clients.map(client => {
      const clientTickets = tickets.filter(ticket => ticket.clientId === client.id);
      return {
        name: client.name,
        count: clientTickets.length
      };
    });
    
    // Sort and get top 5
    ticketsPerClient = ticketsPerClient
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    setTicketData({
      byStatus,
      byPriority,
      byMonth,
      ticketsPerClient
    });
  };

  const statusChartData = {
    labels: [
      'Aperto',
      'In Corso',
      'Risolto',
      'Chiuso'
    ],
    datasets: [
      {
        label: 'Ticket per stato',
        data: [
          ticketData.byStatus.OPEN || 0,
          ticketData.byStatus.IN_PROGRESS || 0,
          ticketData.byStatus.RESOLVED || 0,
          ticketData.byStatus.CLOSED || 0
        ],
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)'
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)'
        ],
        borderWidth: 1
      }
    ]
  };

  const priorityChartData = {
    labels: [
      'Bassa',
      'Media',
      'Alta',
      'Urgente'
    ],
    datasets: [
      {
        label: 'Ticket per priorità',
        data: [
          ticketData.byPriority.LOW || 0,
          ticketData.byPriority.MEDIUM || 0,
          ticketData.byPriority.HIGH || 0,
          ticketData.byPriority.URGENT || 0
        ],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(255, 159, 64, 0.6)',
          'rgba(255, 99, 132, 0.6)'
        ],
        borderColor: [
          'rgba(75, 192, 192, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(255, 99, 132, 1)'
        ],
        borderWidth: 1
      }
    ]
  };

  const monthlyChartData = {
    labels: ticketData.byMonth.map(m => m.month),
    datasets: [
      {
        label: 'Ticket aperti',
        data: ticketData.byMonth.map(m => m.open),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      },
      {
        label: 'Ticket chiusi',
        data: ticketData.byMonth.map(m => m.closed),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }
    ]
  };

  const clientChartData = {
    labels: ticketData.ticketsPerClient.map(c => c.name),
    datasets: [
      {
        label: 'Ticket per cliente',
        data: ticketData.ticketsPerClient.map(c => c.count),
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
          'rgba(255, 159, 64, 0.6)'
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)'
        ],
        borderWidth: 1
      }
    ]
  };

  const handleRangeChange = (e) => {
    setReportRange(e.target.value);
  };

  const handleDownloadReport = () => {
    toast.info('Funzionalità di download report non ancora implementata');
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
          <h1 className="text-2xl font-bold text-secondary-900">Report</h1>
          <p className="text-secondary-500">Analisi e statistiche dei ticket</p>
        </div>
        <div className="flex flex-col md:flex-row gap-3 mt-4 md:mt-0">
          <div className="flex items-center">
            <FaCalendarAlt className="text-secondary-500 mr-2" />
            <select
              value={reportRange}
              onChange={handleRangeChange}
              className="form-input"
            >
              <option value="month">Ultimo mese</option>
              <option value="quarter">Ultimo trimestre</option>
              <option value="year">Ultimo anno</option>
            </select>
          </div>
          <button
            onClick={handleDownloadReport}
            className="btn btn-primary flex items-center justify-center"
          >
            <FaFileDownload className="mr-2" />
            Download Report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Ticket per Stato</h2>
          <div className="h-64">
            <Pie data={statusChartData} options={{ maintainAspectRatio: false }} />
          </div>
        </div>
        
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Ticket per Priorità</h2>
          <div className="h-64">
            <Pie data={priorityChartData} options={{ maintainAspectRatio: false }} />
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Trend Ticket per Periodo</h2>
        <div className="h-80">
          <Bar 
            data={monthlyChartData} 
            options={{ 
              maintainAspectRatio: false,
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

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Top 5 Clienti per Numero di Ticket</h2>
        <div className="h-80">
          <Bar 
            data={clientChartData} 
            options={{ 
              maintainAspectRatio: false,
              indexAxis: 'y',
              scales: {
                x: {
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

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Statistiche Generali</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-blue-600 font-semibold">Ticket Totali</p>
            <p className="text-2xl font-bold">
              {Object.values(ticketData.byStatus).reduce((a, b) => a + b, 0)}
            </p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <p className="text-yellow-600 font-semibold">Ticket Aperti</p>
            <p className="text-2xl font-bold">
              {(ticketData.byStatus.OPEN || 0) + (ticketData.byStatus.IN_PROGRESS || 0)}
            </p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-green-600 font-semibold">Ticket Risolti</p>
            <p className="text-2xl font-bold">
              {(ticketData.byStatus.RESOLVED || 0) + (ticketData.byStatus.CLOSED || 0)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports; 