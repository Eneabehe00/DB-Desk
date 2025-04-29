import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { toast } from 'react-toastify';
import { FaUser, FaLock, FaSignInAlt } from 'react-icons/fa';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Per favore inserisci email e password');
      return;
    }
    
    setIsLoading(true);
    
    try {
      await login(email, password);
      toast.success('Login effettuato con successo!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore durante il login');
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
        
        <h2 className="auth-form-title">Accedi</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="email" className="form-label">Email</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FaUser className="text-secondary-400" />
              </div>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="form-input pl-10"
                placeholder="nome@esempio.com"
                required
              />
            </div>
          </div>
          
          <div className="mb-6">
            <label htmlFor="password" className="form-label">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FaLock className="text-secondary-400" />
              </div>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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
              <FaSignInAlt className="mr-2" />
            )}
            {isLoading ? 'Accesso...' : 'Accedi'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-secondary-600">
            Non hai un account?{' '}
            <Link to="/register" className="auth-link">
              Registrati
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login; 