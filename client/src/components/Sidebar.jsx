import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { 
  FaChartLine, 
  FaTicketAlt, 
  FaUsers, 
  FaFileAlt, 
  FaCog, 
  FaSignOutAlt,
  FaBars,
  FaTimes
} from 'react-icons/fa';

const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { path: '/dashboard', name: 'Dashboard', icon: <FaChartLine /> },
    { path: '/tickets', name: 'Tickets', icon: <FaTicketAlt /> },
    { path: '/clients', name: 'Clienti', icon: <FaUsers /> },
    { path: '/reports', name: 'Report', icon: <FaFileAlt /> },
    { path: '/settings', name: 'Impostazioni', icon: <FaCog /> },
  ];

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="fixed top-4 left-4 z-40 lg:hidden">
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-md bg-white shadow-md text-secondary-800"
        >
          {isOpen ? <FaTimes /> : <FaBars />}
        </button>
      </div>

      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={toggleSidebar}
        ></div>
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed top-0 left-0 h-full w-64 bg-white shadow-lg z-30 transition-transform duration-300 transform ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } lg:static lg:translate-x-0`}
      >
        <div className="p-5">
          <div className="flex items-center justify-center mb-8">
            <h1 className="text-xl font-bold text-primary-700">DB Desk</h1>
          </div>

          <div className="mb-8">
            <div className="flex flex-col items-center">
              <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center text-2xl font-bold text-primary-700 mb-2">
                {user?.name.split(' ').map(n => n[0]).join('').toUpperCase()}
              </div>
              <p className="text-sm font-medium text-secondary-800">{user?.name}</p>
              <p className="text-xs text-secondary-500">{user?.role === 'ADMIN' ? 'Admin' : 'Staff'}</p>
            </div>
          </div>

          <nav>
            <ul className="space-y-2">
              {menuItems.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center p-3 rounded-md transition-colors duration-200 ${
                      location.pathname === item.path
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-secondary-600 hover:bg-secondary-50'
                    }`}
                  >
                    <span className="mr-3">{item.icon}</span>
                    <span>{item.name}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-5">
          <button
            onClick={logout}
            className="flex items-center w-full p-3 rounded-md text-secondary-600 hover:bg-secondary-50 transition-colors duration-200"
          >
            <FaSignOutAlt className="mr-3" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar; 