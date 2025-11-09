import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ToastContainer';
import { useNotificationHistory } from '../hooks/useNotificationHistory';
import { getUpcomingNotifications, getWeeklyHighlights, getMealSuggestion } from '../services/notifications';
import MealOrderModal from '../components/MealOrderModal';

const tabs = [
  { name: 'Voice Assistant', path: '/dashboard' },
  { name: 'Calendar', path: '/calendar' },
  { name: 'Tasks', path: '/tasks' },
  { name: 'Reminders', path: '/reminders' },
];

export default function MainLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showInfo, showRecommendation, showSuccess } = useToast();
  const [mealModalOpen, setMealModalOpen] = useState(false);
  const [mealModalPayload, setMealModalPayload] = useState({ message: '', meal: 'lunch' });
  const { unreadCount } = useNotificationHistory();

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
            showInfo(`This Week: ${msg}`, 8000);
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
          showInfo(`${first.title || 'Upcoming'}: ${first.message || 'You have an upcoming event.'}`, 8000);
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
  }, [user, showInfo]);

  // Independent "thread" for meal suggestions
  useEffect(() => {
    let cancelled = false;
    const THROTTLE_MS = 10 * 60 * 1000; // 10 minutes, separate cycle for meal suggestions

    const lastShown = Number(localStorage.getItem('meal_suggestion_last_shown_at') || 0);
    const now = Date.now();
    if (now - lastShown < THROTTLE_MS) {
      return;
    }

    const schedule = (cb) => {
      if (typeof window.requestIdleCallback === 'function') {
        const id = window.requestIdleCallback(cb, { timeout: 2000 });
        return () => window.cancelIdleCallback && window.cancelIdleCallback(id);
      }
      const id = setTimeout(cb, 1200);
      return () => clearTimeout(id);
    };

    const cancelScheduled = schedule(async () => {
      if (cancelled || document.visibilityState !== 'visible') return;
      try {
        const userId = user?.id || user?.user_id || null;
        const meal = await getMealSuggestion(userId, { useMock: true });
        if (!cancelled && meal?.should_notify && meal?.message) {
          // Open interactive modal instead of only showing toast
          setMealModalPayload({ message: meal.message, meal: meal.meal || 'lunch' });
          setMealModalOpen(true);
          // Also log a toast entry so it appears in history
          showRecommendation(meal.message, 6000);
          localStorage.setItem('meal_suggestion_last_shown_at', String(Date.now()));
        }
      } catch (_) {
        // ignore errors for meal suggestions
      }
    });

    return () => {
      cancelled = true;
      cancelScheduled && cancelScheduled();
    };
  }, [user, showRecommendation]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 shadow-sm p-4 flex justify-between items-center backdrop-blur-sm bg-white/95 sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-md">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
          </div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            UniGames Assistant
          </h1>
        </div>

        <div className="flex items-center gap-4">
          {user && (
            <div className="hidden sm:flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg border border-blue-200">
              <svg className="h-5 w-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd"/>
              </svg>
              <span className="text-sm text-blue-900 font-medium">
                {user.name || user.email}
              </span>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white text-sm font-medium rounded-lg shadow-md transition-all duration-200 transform hover:scale-105 active:scale-95"
          >
            Logout
          </button>
        </div>
      </header>
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-200 px-4 py-3 flex gap-2 shadow-sm sticky top-16 z-30">
        {tabs.map(tab => (
          <Link
            key={tab.path}
            to={tab.path}
            className={`relative px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 transform ${
              location.pathname === tab.path
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md scale-105'
                : 'text-gray-700 hover:bg-blue-50 hover:text-blue-700 hover:scale-105'
            }`}
          >
            {tab.name}
            {/* Unread badge for Reminders tab */}
            {tab.path === '/reminders' && unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 flex items-center justify-center w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full border-2 border-white shadow-md animate-pulse">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </Link>
        ))}
      </nav>
      <main className="flex-1 p-6 animate-fadeIn">
        {children}
        <MealOrderModal
          isOpen={mealModalOpen}
          onClose={() => setMealModalOpen(false)}
          initialMessage={mealModalPayload.message}
          meal={mealModalPayload.meal}
          onPlaced={(opt) => {
            showSuccess('Order placed!', 5000);
          }}
        />
      </main>
    </div>
  );
}