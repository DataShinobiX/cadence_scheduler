

export default function CalendarView() {
  return (
    <div className="border rounded-md p-6 bg-white shadow-sm">
      <div className="text-gray-600 text-center mb-4">
        Google Calendar integration coming soon!
      </div>
      <div className="grid grid-cols-7 gap-2 text-sm text-center text-gray-800">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="font-medium">{day}</div>
        ))}
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="p-2 border rounded hover:bg-blue-50 cursor-pointer"
          >
            {i + 1}
          </div>
        ))}
      </div>
    </div>
  );
}