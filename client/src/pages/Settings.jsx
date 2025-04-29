import { useState } from 'react';
import { toast } from 'react-toastify';
import { useAuth } from '../hooks/useAuth';
import api from '../api/axios';
import { 
  FaUser, FaEnvelope, FaLock, FaCheck, FaTimes, FaBell, 
  FaPalette, FaShieldAlt, FaLanguage, FaInfoCircle
} from 'react-icons/fa';

const Settings = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    jobTitle: user?.jobTitle || '',
    phone: user?.phone || ''
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    newTicketAlerts: true,
    ticketUpdates: true,
    marketingEmails: false
  });
  const [appearanceSettings, setAppearanceSettings] = useState({
    theme: 'light',
    fontSize: 'medium',
    compactMode: false
  });
  
  // Liste di tab disponibili nella pagina
  const tabs = [
    { id: 'profile', name: 'Profilo', icon: <FaUser /> },
    { id: 'security', name: 'Sicurezza', icon: <FaShieldAlt /> },
    { id: 'notifications', name: 'Notifiche', icon: <FaBell /> },
    { id: 'appearance', name: 'Aspetto', icon: <FaPalette /> },
    { id: 'locale', name: 'Lingua e Regione', icon: <FaLanguage /> },
    { id: 'advanced', name: 'Avanzate', icon: <FaInfoCircle /> }
  ];

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
  
  const handleNotificationChange = (e) => {
    setNotificationSettings({
      ...notificationSettings,
      [e.target.name]: e.target.checked
    });
  };
  
  const handleAppearanceChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setAppearanceSettings({
      ...appearanceSettings,
      [e.target.name]: value
    });
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    
    if (!profileData.name || !profileData.email) {
      toast.error('I campi Nome e Email sono obbligatori');
      return;
    }
    
    setLoading(true);
    
    try {
      await api.put(`/users/${user.id}`, {
        name: profileData.name,
        email: profileData.email,
        jobTitle: profileData.jobTitle,
        phone: profileData.phone
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
  
  const handleSaveNotifications = () => {
    toast.success('Impostazioni notifiche salvate con successo');
  };
  
  const handleSaveAppearance = () => {
    toast.success('Impostazioni aspetto salvate con successo');
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
      
      {/* Tabs di navigazione */}
      <div className="border-b border-secondary-200">
        <nav className="flex overflow-x-auto pb-1 -mb-px">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`mr-6 py-4 px-1 inline-flex items-center border-b-2 font-medium text-sm whitespace-nowrap
                ${activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-secondary-500 hover:text-secondary-700 hover:border-secondary-300'
                }
              `}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>
      
      {/* Contenuto dei tab */}
      <div className="mt-8">
        {/* Tab Profilo */}
        {activeTab === 'profile' && (
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
                <div>
                  <label htmlFor="jobTitle" className="form-label">Ruolo/Posizione</label>
                  <input
                    id="jobTitle"
                    name="jobTitle"
                    type="text"
                    value={profileData.jobTitle}
                    onChange={handleProfileChange}
                    className="form-input"
                    placeholder="IT Manager"
                  />
                </div>
                <div>
                  <label htmlFor="phone" className="form-label">Telefono</label>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    value={profileData.phone}
                    onChange={handleProfileChange}
                    className="form-input"
                    placeholder="+39 123 456 7890"
                  />
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
        )}
        
        {/* Tab Sicurezza */}
        {activeTab === 'security' && (
          <div className="space-y-6">
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
                    <p className="text-xs text-secondary-500 mt-1">
                      La password deve contenere almeno 6 caratteri.
                    </p>
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
          </div>
        )}
        
        {/* Tab Notifiche */}
        {activeTab === 'notifications' && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-6">Preferenze Notifiche</h2>
            <div className="space-y-4 mb-6">
              <div className="flex items-start">
                <div className="flex h-5 items-center">
                  <input
                    id="emailNotifications"
                    name="emailNotifications"
                    type="checkbox"
                    checked={notificationSettings.emailNotifications}
                    onChange={handleNotificationChange}
                    className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="emailNotifications" className="font-medium text-secondary-700">Notifiche email</label>
                  <p className="text-secondary-500">Ricevi aggiornamenti via email quando ci sono nuove attività</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="flex h-5 items-center">
                  <input
                    id="newTicketAlerts"
                    name="newTicketAlerts"
                    type="checkbox"
                    checked={notificationSettings.newTicketAlerts}
                    onChange={handleNotificationChange}
                    className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="newTicketAlerts" className="font-medium text-secondary-700">Nuovi ticket</label>
                  <p className="text-secondary-500">Ricevi notifiche quando vengono creati nuovi ticket</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="flex h-5 items-center">
                  <input
                    id="ticketUpdates"
                    name="ticketUpdates"
                    type="checkbox"
                    checked={notificationSettings.ticketUpdates}
                    onChange={handleNotificationChange}
                    className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="ticketUpdates" className="font-medium text-secondary-700">Aggiornamenti ticket</label>
                  <p className="text-secondary-500">Ricevi notifiche quando i ticket vengono aggiornati</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="flex h-5 items-center">
                  <input
                    id="marketingEmails"
                    name="marketingEmails"
                    type="checkbox"
                    checked={notificationSettings.marketingEmails}
                    onChange={handleNotificationChange}
                    className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="marketingEmails" className="font-medium text-secondary-700">Email marketing</label>
                  <p className="text-secondary-500">Ricevi email riguardanti aggiornamenti e nuove funzionalità</p>
                </div>
              </div>
            </div>
            <div className="flex justify-end">
              <button
                onClick={handleSaveNotifications}
                className="btn btn-primary flex items-center"
              >
                <FaCheck className="mr-2" />
                Salva Preferenze
              </button>
            </div>
          </div>
        )}
        
        {/* Tab Aspetto */}
        {activeTab === 'appearance' && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-6">Preferenze Aspetto</h2>
            <div className="space-y-6 mb-6">
              <div>
                <label htmlFor="theme" className="form-label">Tema</label>
                <select
                  id="theme"
                  name="theme"
                  value={appearanceSettings.theme}
                  onChange={handleAppearanceChange}
                  className="form-select"
                >
                  <option value="light">Chiaro</option>
                  <option value="dark">Scuro</option>
                  <option value="system">Sistema</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="fontSize" className="form-label">Dimensione testo</label>
                <select
                  id="fontSize"
                  name="fontSize"
                  value={appearanceSettings.fontSize}
                  onChange={handleAppearanceChange}
                  className="form-select"
                >
                  <option value="small">Piccolo</option>
                  <option value="medium">Medio</option>
                  <option value="large">Grande</option>
                </select>
              </div>
              
              <div className="flex items-start">
                <div className="flex h-5 items-center">
                  <input
                    id="compactMode"
                    name="compactMode"
                    type="checkbox"
                    checked={appearanceSettings.compactMode}
                    onChange={handleAppearanceChange}
                    className="h-4 w-4 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="compactMode" className="font-medium text-secondary-700">Modalità compatta</label>
                  <p className="text-secondary-500">Riduci lo spazio per visualizzare più contenuti</p>
                </div>
              </div>
            </div>
            <div className="flex justify-end">
              <button
                onClick={handleSaveAppearance}
                className="btn btn-primary flex items-center"
              >
                <FaCheck className="mr-2" />
                Salva Preferenze
              </button>
            </div>
          </div>
        )}
        
        {/* Tab Lingua e Regione */}
        {activeTab === 'locale' && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-6">Lingua e Regione</h2>
            <div className="space-y-6 mb-6">
              <div>
                <label htmlFor="language" className="form-label">Lingua</label>
                <select
                  id="language"
                  name="language"
                  className="form-select"
                  defaultValue="it"
                >
                  <option value="it">Italiano</option>
                  <option value="en">Inglese</option>
                  <option value="fr">Francese</option>
                  <option value="de">Tedesco</option>
                  <option value="es">Spagnolo</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="dateFormat" className="form-label">Formato data</label>
                <select
                  id="dateFormat"
                  name="dateFormat"
                  className="form-select"
                  defaultValue="dd/mm/yyyy"
                >
                  <option value="dd/mm/yyyy">DD/MM/YYYY</option>
                  <option value="mm/dd/yyyy">MM/DD/YYYY</option>
                  <option value="yyyy-mm-dd">YYYY-MM-DD</option>
                </select>
              </div>
              
              <div>
                <label htmlFor="timeZone" className="form-label">Fuso orario</label>
                <select
                  id="timeZone"
                  name="timeZone"
                  className="form-select"
                  defaultValue="Europe/Rome"
                >
                  <option value="Europe/Rome">Europa/Roma (CET)</option>
                  <option value="Europe/London">Europa/Londra (GMT)</option>
                  <option value="America/New_York">America/New York (EST)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end">
              <button
                className="btn btn-primary flex items-center"
              >
                <FaCheck className="mr-2" />
                Salva Preferenze
              </button>
            </div>
          </div>
        )}
        
        {/* Tab Avanzate */}
        {activeTab === 'advanced' && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-6">Impostazioni Avanzate</h2>
            <div className="space-y-6 mb-6">
              <div>
                <p className="text-secondary-700 mb-4">
                  Esporta i tuoi dati in formato JSON o CSV.
                </p>
                <div className="flex space-x-4">
                  <button className="btn btn-secondary">Esporta JSON</button>
                  <button className="btn btn-secondary">Esporta CSV</button>
                </div>
              </div>
              
              <div className="pt-4 border-t border-secondary-200">
                <p className="text-secondary-700 mb-4">
                  Svuota la cache dell'applicazione e ripristina le impostazioni predefinite.
                </p>
                <div className="flex space-x-4">
                  <button className="btn btn-secondary text-yellow-700 border-yellow-300 hover:bg-yellow-50">
                    Svuota Cache
                  </button>
                  <button className="btn btn-secondary text-yellow-700 border-yellow-300 hover:bg-yellow-50">
                    Ripristina Predefiniti
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
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