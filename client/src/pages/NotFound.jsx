import { Link } from 'react-router-dom';
import { FaHome, FaExclamationTriangle } from 'react-icons/fa';

const NotFound = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-secondary-50 p-4">
      <div className="card max-w-lg w-full text-center">
        <div className="text-primary-600 mb-6">
          <FaExclamationTriangle size={60} className="mx-auto" />
        </div>
        <h1 className="text-4xl font-bold text-secondary-900 mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-secondary-800 mb-4">Pagina non trovata</h2>
        <p className="text-secondary-600 mb-8">
          La pagina che stai cercando non esiste o è stata spostata.
        </p>
        <Link to="/" className="btn btn-primary inline-flex items-center">
          <FaHome className="mr-2" />
          Torna alla home
        </Link>
      </div>
    </div>
  );
};

export default NotFound; 