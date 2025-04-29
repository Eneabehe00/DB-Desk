import { useState } from 'react';
import { toast } from 'react-toastify';
import { useAuth } from '../hooks/useAuth';
import api from '../api/axios';
import { FaUser, FaEnvelope, FaLock, FaCheck, FaTimes } from 'react-icons/fa';

const Settings = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || ''
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const handleProfileChange = (e) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value
    });
  };

  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value
    });
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    
    if (!profileData.name || !profileData.email) {
      toast.error('Tutti i campi sono obbligatori');
      return;
    }
    
    setLoading(true);
    
    try {
      await api.put(`/users/${user.id}`, {
        name: profileData.name,
        email: profileData.email
      });
      
      toast.success('Profilo aggiornato con successo');
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'aggiornamento del profilo');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    
    if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      toast.error('Tutti i campi password sono obbligatori');
      return;
    }
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('Le password non corrispondono');
      return;
    }
    
    if (passwordData.newPassword.length < 6) {
      toast.error('La nuova password deve essere di almeno 6 caratteri');
      return;
    }
    
    setPasswordLoading(true);
    
    try {
      await api.put(`/users/${user.id}`, {
        password: passwordData.newPassword,
        currentPassword: passwordData.currentPassword
      });
      
      toast.success('Password aggiornata con successo');
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'aggiornamento della password');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await api.delete(`/users/${user.id}`);
      toast.success('Account eliminato con successo');
      logout();
    } catch (error) {
      toast.error(error.response?.data?.message || 'Errore nell\'eliminazione dell\'account');
      setShowDeleteModal(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900">Impostazioni</h1>
        <p className="text-secondary-500">Gestisci il tuo account e le preferenze</p>
      </div>
      
      <div className="card">
        <h2 className="text-xl font-semibold mb-6">Informazioni Profilo</h2>
        <form onSubmit={handleUpdateProfile}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label htmlFor="name" className="form-label">Nome completo</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FaUser className="text-secondary-400" />
                </div>
                <input
                  id="name"
                  name="name"
                  type="text"
                  value={profileData.name}
                  onChange={handleProfileChange}
                  className="form-input pl-10"
                  placeholder="Mario Rossi"
                />
              </div>
            </div>
            <div>
              <label htmlFor="email" className="form-label">Email</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FaEnvelope className="text-secondary-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={profileData.email}
                  onChange={handleProfileChange}
                  className="form-input pl-10"
                  placeholder="nome@esempio.com"
                />
              </div>
            </div>
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              className="btn btn-primary flex items-center"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Aggiornamento...
                </>
              ) : (
                <>
                  <FaCheck className="mr-2" />
                  Salva Modifiche
                </>
              )}
            </button>
          </div>
        </form>
      </div>
      
      <div className="card">
        <h2 className="text-xl font-semibold mb-6">Modifica Password</h2>
        <form onSubmit={handleUpdatePassword}>
          <div className="space-y-4 mb-6">
            <div>
              <label htmlFor="currentPassword" className="form-label">Password attuale</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FaLock className="text-secondary-400" />
                </div>
                <input
                  id="currentPassword"
                  name="currentPassword"
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={handlePasswordChange}
                  className="form-input pl-10"
                  placeholder="********"
                />
              </div>
            </div>
            <div>
              <label htmlFor="newPassword" className="form-label">Nuova password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FaLock className="text-secondary-400" />
                </div>
                <input
                  id="newPassword"
                  name="newPassword"
                  type="password"
                  value={passwordData.newPassword}
                  onChange={handlePasswordChange}
                  className="form-input pl-10"
                  placeholder="********"
                />
              </div>
            </div>
            <div>
              <label htmlFor="confirmPassword" className="form-label">Conferma nuova password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <FaLock className="text-secondary-400" />
                </div>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={handlePasswordChange}
                  className="form-input pl-10"
                  placeholder="********"
                />
              </div>
            </div>
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              className="btn btn-primary flex items-center"
              disabled={passwordLoading}
            >
              {passwordLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Aggiornamento...
                </>
              ) : (
                <>
                  <FaCheck className="mr-2" />
                  Aggiorna Password
                </>
              )}
            </button>
          </div>
        </form>
      </div>
      
      <div className="card border border-red-200">
        <h2 className="text-xl font-semibold text-red-600 mb-4">Zona Pericolosa</h2>
        <p className="text-secondary-600 mb-6">
          L'eliminazione del tuo account è permanente e rimuoverà tutti i tuoi dati e informazioni.
          Questa azione non può essere annullata.
        </p>
        <div className="flex justify-end">
          <button
            onClick={() => setShowDeleteModal(true)}
            className="btn bg-red-600 text-white hover:bg-red-700 flex items-center"
          >
            <FaTimes className="mr-2" />
            Elimina Account
          </button>
        </div>
      </div>
      
      {/* Delete Account Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4 text-red-600">Conferma Eliminazione Account</h2>
              <p className="mb-6 text-secondary-600">
                Sei sicuro di voler eliminare il tuo account? Questa azione non può essere annullata
                e tutti i tuoi dati verranno persi permanentemente.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="btn btn-secondary"
                >
                  Annulla
                </button>
                <button
                  onClick={handleDeleteAccount}
                  className="btn bg-red-600 text-white hover:bg-red-700"
                >
                  Elimina definitivamente
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings; 