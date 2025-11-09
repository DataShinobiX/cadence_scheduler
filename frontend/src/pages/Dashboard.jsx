import VoiceRecorder from '../components/VoiceRecorder';

export default function Dashboard() {
  return (
    <div className="max-w-3xl mx-auto animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-200">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-3">
            Voice Assistant
          </h2>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Tell me what you need to schedule, and I'll take care of the rest
          </p>
        </div>
        <VoiceRecorder />
      </div>

      {/* Quick Tips */}
      <div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
        <h3 className="text-sm font-bold text-blue-900 mb-3 flex items-center gap-2">
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
          </svg>
          Quick Tips
        </h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>Speak naturally: "Schedule a meeting with my team tomorrow at 2pm"</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>Include deadlines: "Submit the report by Friday 5pm"</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>Set reminders: "Remind me to call mom next Tuesday"</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
