import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import useNotification from '../hooks/useNotifications';
import NotificationModal from '../components/NotificationModal';

const tabs = [
  { name: 'Voice Assistant', path: '/dashboard' },
  { name: 'Calendar', path: '/calendar' },
  { name: 'Tasks', path: '/tasks' },
];

export default function MainLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const {
    isOpen,
    title,
    message,
    showNotification,
    closeNotification,
  } = useNotification();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-gray-800">UniGames Assistant</h1>

        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-gray-600">
              Welcome, <strong>{user.name || user.email}</strong>
            </span>
          )}
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-md transition-colors"
          >
            Logout
          </button>
        </div>
      </header>
      <nav className="bg-gray-100 border-b px-4 py-2 flex gap-4">
        {tabs.map(tab => (
          <Link
            key={tab.path}
            to={tab.path}
            className={`px-3 py-2 rounded-md text-sm font-medium ${
              location.pathname === tab.path
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-200'
            }`}
          >
            {tab.name}
          </Link>
        ))}
      </nav>
      <main className="flex-1 p-6">{children}</main>
      <NotificationModal
        isOpen={isOpen}
        onClose={closeNotification}
        title={title}
        message={message}
      />
    </div>
  );
}