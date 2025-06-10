import { createContext, useState, useEffect } from 'react';
import api from '../api/axios';
import { jwtDecode } from 'jwt-decode';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Verifica il token all'avvio e imposta l'utente
  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          // Controlla se il token è scaduto
          const decodedToken = jwtDecode(token);
          const currentTime = Date.now() / 1000;
          
          if (decodedToken.exp < currentTime) {
            // Token scaduto, fa il logout
            logout();
          } else {
            // Carica i dati dell'utente
            const response = await api.get('/auth/me');
            setUser(response.data.user);
          }
        } catch (error) {
          console.error('Auth initialization error:', error);
          logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [token]);

  // Login
  const login = async (email, password) => {
    try {
      setError(null);
      const response = await api.post('/auth/login', { email, password });
      const { token, user } = response.data;
      
      localStorage.setItem('token', token);
      setToken(token);
      setUser(user);
      return user;
    } catch (error) {
      setError(error.response?.data?.message || 'Failed to login');
      throw error;
    }
  };

  // Register
  const register = async (userData) => {
    try {
      setError(null);
      const response = await api.post('/auth/register', userData);
      const { token, user } = response.data;
      
      localStorage.setItem('token', token);
      setToken(token);
      setUser(user);
      return user;
    } catch (error) {
      setError(error.response?.data?.message || 'Failed to register');
      throw error;
    }
  };

  // Logout
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        error,
        login,
        register,
        logout,
        isAuthenticated: !!token
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}; 