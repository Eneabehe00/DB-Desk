import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'react-toastify';
import { FaUser, FaLock, FaEnvelope, FaUserPlus } from 'react-icons/fa';

const Register = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const { name, email, password, confirmPassword } = formData;
    
    if (!name || !email || !password) {
      toast.error('Per favore compila tutti i campi');
      return;
    }
    
    if (password !== confirmPassword) {
      toast.error('Le password non corrispondono');
      return;
    }
    
    if (password.length < 6) {
      toast.error('La password deve essere di almeno 6 caratteri');
      return;
    }
    
    setIsLoading(true);
    
    try {
      await register({ name, email, password });
      toast.success('Registrazione completata con successo!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore durante la registrazione');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="text-center mb-8">
          <h1 className="auth-title">DB Desk</h1>
          <p className="auth-subtitle">Sistema di gestione ticket</p>
        </div>
        
        <h2 className="auth-form-title">Registrati</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="name" className="form-label">Nome completo</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FaUser className="text-secondary-400" />
              </div>
              <input
                id="name"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleChange}
                className="form-input pl-10"
                placeholder="Mario Rossi"
                required
              />
            </div>
          </div>
          
          <div className="mb-4">
            <label htmlFor="email" className="form-label">Email</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FaEnvelope className="text-secondary-400" />
              </div>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                className="form-input pl-10"
                placeholder="nome@esempio.com"
                required
              />
            </div>
          </div>
          
          <div className="mb-4">
            <label htmlFor="password" className="form-label">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FaLock className="text-secondary-400" />
              </div>
              <input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                className="form-input pl-10"
                placeholder="********"
                required
              />
            </div>
          </div>
          
          <div className="mb-6">
            <label htmlFor="confirmPassword" className="form-label">Conferma Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FaLock className="text-secondary-400" />
              </div>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="form-input pl-10"
                placeholder="********"
                required
              />
            </div>
          </div>
          
          <button
            type="submit"
            className="btn btn-primary w-full flex items-center justify-center"
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            ) : (
              <FaUserPlus className="mr-2" />
            )}
            {isLoading ? 'Registrazione...' : 'Registrati'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-secondary-600">
            Hai già un account?{' '}
            <Link to="/login" className="auth-link">
              Accedi
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register; 