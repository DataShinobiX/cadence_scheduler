import CalendarView from '../components/CalendarView';

export default function Calendar() {
  return (
    <div className="max-w-6xl mx-auto animate-fadeIn">
      <div className="mb-6 text-center">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
          My Calendar
        </h2>
        <p className="text-gray-600 text-lg">
          View and manage your schedule synced with Google Calendar
        </p>
      </div>
      <CalendarView />
    </div>
  );
}