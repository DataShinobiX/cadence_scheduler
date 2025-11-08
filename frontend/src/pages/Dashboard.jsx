import VoiceRecorder from '../components/VoiceRecorder';

export default function Dashboard() {
  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4 text-gray-800">Voice Assistant</h2>
      <p className="text-gray-600 mb-6">
        Press the button below and start speaking. The assistant will convert your voice to text and take action.
      </p>
      <VoiceRecorder />
    </div>
  );
}
