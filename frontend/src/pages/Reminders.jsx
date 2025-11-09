import { useNotificationHistory } from '../hooks/useNotificationHistory';

export default function Reminders() {
  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll,
  } = useNotificationHistory();

  const getTypeIcon = (type) => {
    switch (type) {
      case 'success':
        return (
          <svg className="h-6 w-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        );
      case 'error':
        return (
          <svg className="h-6 w-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        );
      case 'warning':
        return (
          <svg className="h-6 w-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        );
      default:
        return (
          <svg className="h-6 w-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        );
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'success':
        return 'border-green-300 bg-green-50';
      case 'error':
        return 'border-red-300 bg-red-50';
      case 'warning':
        return 'border-yellow-300 bg-yellow-50';
      default:
        return 'border-blue-300 bg-blue-50';
    }
  };

  const formatTimestamp = (isoString) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  const getTimeOfDay = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <div className="max-w-4xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
              Reminders & Notifications
            </h2>
            <p className="text-gray-600 text-lg">
              Your notification history and reminders
            </p>
          </div>
          {unreadCount > 0 && (
            <div className="flex items-center gap-2">
              <span className="px-4 py-2 bg-blue-100 text-blue-800 font-bold rounded-full text-sm border-2 border-blue-300">
                {unreadCount} new
              </span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        {notifications.length > 0 && (
          <div className="flex gap-3">
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg shadow-md transition-all duration-200 transform hover:scale-105"
              >
                Mark all as read
              </button>
            )}
            <button
              onClick={clearAll}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg shadow-md transition-all duration-200 transform hover:scale-105"
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Notifications Timeline */}
      {notifications.length === 0 ? (
        <div className="bg-white border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center">
          <svg className="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
          </svg>
          <h3 className="text-xl font-bold text-gray-700 mb-2">No notifications yet</h3>
          <p className="text-gray-500">
            You'll see all your notifications and reminders here
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {notifications.map((notification, index) => (
            <div
              key={notification.id}
              className={`group relative bg-white border-2 rounded-xl shadow-sm transition-all duration-200 hover:shadow-md hover:scale-[1.01] animate-slideDown ${
                notification.read ? 'border-gray-200' : 'border-l-4 ' + getTypeColor(notification.type)
              }`}
              style={{ animationDelay: `${index * 0.05}s` }}
              onClick={() => !notification.read && markAsRead(notification.id)}
            >
              {/* Unread indicator dot */}
              {!notification.read && (
                <div className="absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow-md"></div>
              )}

              <div className="flex items-start gap-4 p-5">
                {/* Icon */}
                <div className="flex-shrink-0 mt-1">
                  {getTypeIcon(notification.type)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <p className={`text-base leading-relaxed ${
                      notification.read ? 'text-gray-700' : 'text-gray-900 font-medium'
                    }`}>
                      {notification.message}
                    </p>

                    {/* Delete button (visible on hover) */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteNotification(notification.id);
                      }}
                      className="flex-shrink-0 opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded-lg transition-all duration-200"
                      title="Delete notification"
                    >
                      <svg className="h-5 w-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                      </svg>
                    </button>
                  </div>

                  {/* Timestamp */}
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                      {formatTimestamp(notification.timestamp)}
                    </span>
                    <span className="text-gray-400">•</span>
                    <span>{getTimeOfDay(notification.timestamp)}</span>
                  </div>
                </div>
              </div>

              {/* Read status indicator */}
              {!notification.read && (
                <div className="absolute top-3 right-3">
                  <span className="px-2 py-1 bg-blue-500 text-white text-xs font-bold rounded-full">
                    NEW
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
