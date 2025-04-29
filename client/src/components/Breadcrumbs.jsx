import { Link, useLocation } from 'react-router-dom';
import { FaChevronRight, FaHome } from 'react-icons/fa';

const Breadcrumbs = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter(x => x);

  // Mapping per i nomi delle pagine in italiano
  const pageNames = {
    dashboard: 'Dashboard',
    tickets: 'Ticket',
    clients: 'Clienti',
    reports: 'Report',
    settings: 'Impostazioni'
  };

  // Non mostrare breadcrumbs nelle pagine di login/register
  if (['/login', '/register'].includes(location.pathname)) {
    return null;
  }

  return (
    <nav className="flex items-center text-sm mb-6" aria-label="Breadcrumb">
      <ol className="flex items-center flex-wrap">
        <li className="flex items-center">
          <Link to="/dashboard" className="text-primary-600 hover:text-primary-800 flex items-center">
            <FaHome className="mr-1" />
            Home
          </Link>
        </li>
        
        {pathnames.map((path, index) => {
          // Costruisci l'URL per questo livello di breadcrumb
          const url = `/${pathnames.slice(0, index + 1).join('/')}`;
          const isLast = index === pathnames.length - 1;
          
          // Controlla se è un ID (assumendo che un ID sia numerico o abbia un formato specifico)
          const isId = !isNaN(path) || path.length > 20;
          
          // Se è un ID, cerca di ottenere un nome più descrittivo
          let name = isId ? 'Dettaglio' : (pageNames[path] || path.charAt(0).toUpperCase() + path.slice(1));
          
          return (
            <li key={url} className="flex items-center">
              <FaChevronRight className="mx-2 text-secondary-400" />
              {isLast ? (
                <span className="text-secondary-600 font-medium">{name}</span>
              ) : (
                <Link to={url} className="text-primary-600 hover:text-primary-800">
                  {name}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumbs; 