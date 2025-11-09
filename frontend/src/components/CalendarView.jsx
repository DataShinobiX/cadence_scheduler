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
      setError('Failed to load calendar events. Please try again.');
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
    <div className="border rounded-md p-6 bg-white shadow-sm">
      {/* Calendar Header */}
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={() => navigateMonth(-1)}
          className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
          aria-label="Previous month"
        >
          ←
        </button>
        <div className="flex items-center gap-4">
          <h3 className="text-xl font-semibold text-gray-800">{formatMonthYear()}</h3>
          <button
            onClick={goToToday}
            className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
          >
            Today
          </button>
        </div>
        <button
          onClick={() => navigateMonth(1)}
          className="px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
          aria-label="Next month"
        >
          →
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8 text-gray-600">
          Loading calendar events...
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="text-center py-8 text-red-600 bg-red-50 border border-red-200 rounded-md mb-4">
          {error}
          <button
            onClick={loadCalendarEvents}
            className="ml-4 px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Calendar Grid */}
      {!loading && (
        <>
          {/* Day Headers */}
          <div className="grid grid-cols-7 gap-2 mb-2">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center font-medium text-gray-600 py-2">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Days */}
          <div className="grid grid-cols-7 gap-2">
            {calendarDays.map((day, index) => {
              const dateKey = getDateKey(day);
              const dayEvents = dateKey ? (eventsByDate[dateKey] || []) : [];
              const isTodayDate = isToday(day);

              return (
                <div
                  key={index}
                  className={`min-h-[100px] p-2 border rounded ${
                    day === null
                      ? 'bg-gray-50 border-gray-100'
                      : isTodayDate
                      ? 'bg-blue-50 border-blue-300 border-2'
                      : 'bg-white border-gray-200 hover:bg-gray-50'
                  } transition-colors`}
                >
                  {day !== null && (
                    <>
                      <div
                        className={`text-sm font-medium mb-1 ${
                          isTodayDate ? 'text-blue-700' : 'text-gray-800'
                        }`}
                      >
                        {day}
                      </div>
                      <div className="space-y-1">
                        {dayEvents.slice(0, 3).map((event, eventIndex) => (
                          <div
                            key={eventIndex}
                            className={`text-xs p-1 rounded truncate ${
                              event.is_external
                                ? 'bg-purple-100 text-purple-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}
                            title={`${event.summary} - ${event.startTime} to ${event.endTime}`}
                          >
                            <div className="font-medium truncate">{event.summary}</div>
                            <div className="text-xs opacity-75">
                              {event.startTime} - {event.endTime}
                            </div>
                          </div>
                        ))}
                        {dayEvents.length > 3 && (
                          <div className="text-xs text-gray-500 font-medium">
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
          <div className="mt-6 flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-100 border border-purple-300 rounded"></div>
              <span className="text-gray-600">External Event</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-100 border border-blue-300 rounded"></div>
              <span className="text-gray-600">Your Event</span>
            </div>
          </div>

          {/* Events Summary */}
          {events.length > 0 && (
            <div className="mt-4 text-sm text-gray-600">
              Showing {events.length} event{events.length !== 1 ? 's' : ''} for {formatMonthYear()}
            </div>
          )}

          {!error && events.length === 0 && !loading && (
            <div className="mt-4 text-center text-gray-500 py-4">
              No events found for this month. Your Google Calendar events will appear here once synced.
            </div>
          )}
        </>
      )}
    </div>
  );
}
