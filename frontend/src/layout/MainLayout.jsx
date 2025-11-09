import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import useNotification from '../hooks/useNotifications';
import NotificationModal from '../components/NotificationModal';
import { getUpcomingNotifications, getWeeklyHighlights } from '../services/notifications';

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

  useEffect(() => {
    let cancelled = false;
    const THROTTLE_MS = 10 * 60 * 1000; // 10 minutes

    // Throttle: only attempt to fetch/show notifications at most every THROTTLE_MS
    const lastShown = Number(localStorage.getItem('notification_last_shown_at') || 0);
    const now = Date.now();
    if (now - lastShown < THROTTLE_MS) {
      return;
    }

    // Defer work so it never blocks initial render or navigation
    const schedule = (cb) => {
      if (typeof window.requestIdleCallback === 'function') {
        const id = window.requestIdleCallback(cb, { timeout: 2000 });
        return () => window.cancelIdleCallback && window.cancelIdleCallback(id);
      }
      const id = setTimeout(cb, 1000); // small delay after mount
      return () => clearTimeout(id);
    };

    const cancelScheduled = schedule(async () => {
      if (cancelled || document.visibilityState !== 'visible') return;
      try {
        const userId = user?.id || user?.user_id || null;
        // Try weekly highlight first
        try {
          const highlight = await getWeeklyHighlights(userId);
          const msg = highlight?.message;
          if (!cancelled && msg) {
            showNotification('This Week', msg);
            localStorage.setItem('notification_last_shown_at', String(Date.now()));
            return;
          }
        } catch (_) {
          // ignore highlight failure and fall back
        }
        // Fall back to first upcoming event
        const list = await getUpcomingNotifications(userId, 7);
        if (!cancelled && list?.notifications?.length) {
          const first = list.notifications[0];
          showNotification(first.title || 'Upcoming', first.message || 'You have an upcoming event.');
          localStorage.setItem('notification_last_shown_at', String(Date.now()));
        }
      } catch (e) {
        // Silently ignore notification errors in UI
      }
    });

    return () => {
      cancelled = true;
      cancelScheduled && cancelScheduled();
    };
  }, [user, showNotification]);

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