

import CalendarView from '../components/CalendarView';

export default function Calendar() {
  return (
    <div className="max-w-5xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4 text-gray-800">My Calendar</h2>
      <p className="text-gray-600 mb-6">
        View and manage your schedule. The calendar syncs with your Google Calendar account.
      </p>
      <CalendarView />
    </div>
  );
}