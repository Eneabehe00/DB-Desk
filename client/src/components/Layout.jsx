import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Breadcrumbs from './Breadcrumbs';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const Layout = () => {
  return (
    <div className="flex h-screen overflow-hidden bg-secondary-50">
      <Sidebar />
      <main className="flex-1 overflow-auto transition-all duration-300 ease-in-out">
        <div className="max-w-7xl mx-auto p-6">
          <Breadcrumbs />
          <Outlet />
        </div>
      </main>
      <ToastContainer 
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />
    </div>
  );
};

export default Layout; 