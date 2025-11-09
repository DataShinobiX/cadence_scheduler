import { useState, useEffect, useCallback } from 'react';
import { fetchCalendarEvents, groupEventsByDate } from '../services/calendar';

export default function CalendarView() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [eventsByDate, setEventsByDate] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch calendar events when component mounts or date changes
  const loadCalendarEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Calculate date range for the current month view
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const startDate = new Date(year, month, 1);
      const endDate = new Date(year, month + 1, 0, 23, 59, 59);

      const startDateStr = startDate.toISOString().split('T')[0];
      const endDateStr = endDate.toISOString().split('T')[0];

      const response = await fetchCalendarEvents(startDateStr, endDateStr);
      setEvents(response.events || []);
      setEventsByDate(groupEventsByDate(response.events || []));
    } catch (err) {
      console.error('Error loading calendar events:', err);

      // Check if it's a 401 error (Google not connected)
      if (err.message && err.message.includes('401')) {
        setError('google_not_connected');
      } else {
        setError('Failed to load calendar events. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [currentDate]);

  useEffect(() => {
    loadCalendarEvents();
  }, [loadCalendarEvents]);

  const navigateMonth = (direction) => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + direction, 1));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // Get calendar days for the current month
  const getCalendarDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }

    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(day);
    }

    return days;
  };

  const formatMonthYear = () => {
    return currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const isToday = (day) => {
    const today = new Date();
    return (
      day !== null &&
      day === today.getDate() &&
      currentDate.getMonth() === today.getMonth() &&
      currentDate.getFullYear() === today.getFullYear()
    );
  };

  const getDateKey = (day) => {
    if (day === null) return null;
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const date = new Date(year, month, day);
    return date.toISOString().split('T')[0];
  };

  const calendarDays = getCalendarDays();

  return (
    <div className="border border-gray-200 rounded-2xl p-6 bg-white shadow-lg animate-fadeIn">
      {/* Calendar Header */}
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={() => navigateMonth(-1)}
          className="p-2 text-gray-600 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-all duration-200 transform hover:scale-110"
          aria-label="Previous month"
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"/>
          </svg>
        </button>
        <div className="flex items-center gap-4">
          <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            {formatMonthYear()}
          </h3>
          <button
            onClick={goToToday}
            className="px-4 py-2 text-sm bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg shadow-md transition-all duration-200 transform hover:scale-105 active:scale-95"
          >
            Today
          </button>
        </div>
        <button
          onClick={() => navigateMonth(1)}
          className="p-2 text-gray-600 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-all duration-200 transform hover:scale-110"
          aria-label="Next month"
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"/>
          </svg>
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <svg className="animate-spin h-12 w-12 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-gray-600 font-medium">Loading calendar events...</p>
        </div>
      )}

      {/* Error State - Google Not Connected */}
      {error === 'google_not_connected' && !loading && (
        <div className="p-8 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl mb-4 animate-slideDown">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="h-10 w-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Connect Your Google Calendar
              </h3>
              <p className="text-gray-600 mb-4 max-w-md">
                To view and manage your calendar events, connect your Google Calendar account.
                This allows the app to sync your schedule and create events for you.
              </p>
            </div>
            <button
              onClick={() => {
                const user = JSON.parse(localStorage.getItem('user') || '{}');
                const userId = user.user_id;
                if (userId) {
                  window.location.href = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/google/connect?user_id=${userId}`;
                } else {
                  alert('Please log in first');
                }
              }}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105 active:scale-95 flex items-center gap-2"
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
              </svg>
              Connect Google Calendar
            </button>
            <p className="text-sm text-gray-500 mt-2">
              You'll be redirected to Google to authorize access
            </p>
          </div>
        </div>
      )}

      {/* Error State - Other Errors */}
      {error && error !== 'google_not_connected' && !loading && (
        <div className="p-5 bg-red-50 border-l-4 border-red-500 rounded-lg mb-4 animate-slideDown">
          <div className="flex items-start gap-3">
            <svg className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
            </svg>
            <div className="flex-1">
              <p className="text-red-800 font-semibold">Failed to load events</p>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
            <button
              onClick={loadCalendarEvents}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg shadow-md transition-all duration-200 transform hover:scale-105"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Calendar Grid */}
      {!loading && (
        <>
          {/* Day Headers */}
          <div className="grid grid-cols-7 gap-2 mb-3">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center font-bold text-gray-700 py-2 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Days */}
          <div className="grid grid-cols-7 gap-3">
            {calendarDays.map((day, index) => {
              const dateKey = getDateKey(day);
              const dayEvents = dateKey ? (eventsByDate[dateKey] || []) : [];
              const isTodayDate = isToday(day);

              return (
                <div
                  key={index}
                  className={`min-h-[110px] p-3 border-2 rounded-xl transition-all duration-200 animate-scaleIn ${
                    day === null
                      ? 'bg-gray-50/50 border-gray-100'
                      : isTodayDate
                      ? 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-400 shadow-md'
                      : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md hover:scale-105'
                  }`}
                  style={{ animationDelay: `${index * 0.01}s` }}
                >
                  {day !== null && (
                    <>
                      <div className="flex items-center justify-between mb-2">
                        <div
                          className={`text-sm font-bold ${
                            isTodayDate
                              ? 'w-7 h-7 flex items-center justify-center bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-full shadow-md'
                              : 'text-gray-800'
                          }`}
                        >
                          {day}
                        </div>
                        {dayEvents.length > 0 && (
                          <div className="w-5 h-5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center font-bold shadow-sm">
                            {dayEvents.length}
                          </div>
                        )}
                      </div>
                      <div className="space-y-1.5">
                        {dayEvents.slice(0, 3).map((event, eventIndex) => (
                          <div
                            key={eventIndex}
                            className={`group text-xs p-2 rounded-lg shadow-sm transition-all duration-200 hover:scale-105 cursor-pointer ${
                              event.is_external
                                ? 'bg-gradient-to-br from-purple-100 to-purple-200 border border-purple-300 hover:from-purple-200 hover:to-purple-300'
                                : 'bg-gradient-to-br from-blue-100 to-indigo-200 border border-blue-300 hover:from-blue-200 hover:to-indigo-300'
                            }`}
                            title={`${event.summary} - ${event.startTime} to ${event.endTime}`}
                          >
                            <div className={`font-semibold truncate ${event.is_external ? 'text-purple-900' : 'text-blue-900'}`}>
                              {event.summary}
                            </div>
                            <div className={`text-xs flex items-center gap-1 mt-0.5 ${event.is_external ? 'text-purple-700' : 'text-blue-700'}`}>
                              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                              </svg>
                              <span>{event.startTime}</span>
                            </div>
                          </div>
                        ))}
                        {dayEvents.length > 3 && (
                          <div className="text-xs text-gray-600 font-semibold bg-gray-100 px-2 py-1 rounded-md text-center">
                            +{dayEvents.length - 3} more
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-6 flex items-center gap-6 text-sm bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gradient-to-br from-purple-100 to-purple-200 border-2 border-purple-400 rounded shadow-sm"></div>
              <span className="text-gray-700 font-medium">External Event</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gradient-to-br from-blue-100 to-indigo-200 border-2 border-blue-400 rounded shadow-sm"></div>
              <span className="text-gray-700 font-medium">Your Event</span>
            </div>
          </div>

          {/* Events Summary */}
          {events.length > 0 && (
            <div className="mt-4 flex items-center gap-2 text-sm bg-green-50 border border-green-200 rounded-lg p-3">
              <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
              </svg>
              <span className="text-green-800 font-medium">
                Showing {events.length} event{events.length !== 1 ? 's' : ''} for {formatMonthYear()}
              </span>
            </div>
          )}

          {!error && events.length === 0 && !loading && (
            <div className="mt-6 text-center py-8 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg">
              <svg className="h-12 w-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
              <p className="text-gray-600 font-medium">No events this month</p>
              <p className="text-gray-500 text-sm mt-1">Your Google Calendar events will appear here once synced</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
