import { useState, useEffect } from 'react';
import useVoiceRecorder from '../hooks/useVoiceRecorder';
import { uploadAudio } from '../utils/api';

export default function VoiceRecorder() {
  const [transcript, setTranscript] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording
  } = useVoiceRecorder();

  useEffect(() => {
    const sendAudioForTranscription = async () => {
      if (!audioBlob) return;

      setLoading(true);
      setError('');

      try {
        const data = await uploadAudio(audioBlob);

        setTranscript(data.transcript);
        setResult(data);

        console.log('Transcription result:', data);
      } catch (err) {
        console.error('Transcription failed:', err);
        setError(err.message || 'Error transcribing audio.');
        setTranscript('');
      } finally {
        setLoading(false);
      }
    };

    sendAudioForTranscription();
  }, [audioBlob]);

  return (
    <div className="space-y-4">
      {/* Recording Button */}
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={loading}
        className={`px-6 py-3 rounded-md text-white font-medium ${
          loading
            ? 'bg-gray-400 cursor-not-allowed'
            : isRecording
            ? 'bg-red-500 hover:bg-red-600'
            : 'bg-blue-600 hover:bg-blue-700'
        }`}
      >
        {loading ? 'Processing...' : isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-700 font-medium">Error: {error}</p>
        </div>
      )}

      {/* Transcript */}
      {transcript && !error && (
        <div className="p-4 bg-gray-100 border rounded">
          <p className="text-gray-800 font-medium mb-1">Transcript:</p>
          <p className="text-gray-700">{transcript}</p>
        </div>
      )}

      {/* Scheduling Results */}
      {result && result.decomposed_tasks && result.decomposed_tasks.length > 0 && (
        <div className="p-4 bg-green-50 border border-green-200 rounded">
          <p className="text-green-800 font-medium mb-2">✅ Tasks Scheduled!</p>

          <div className="mt-3">
            <p className="text-sm text-green-700 font-medium mb-1">Tasks:</p>
            <ul className="list-disc list-inside text-sm text-green-700">
              {result.decomposed_tasks.map((task, index) => (
                <li key={index}>{task.title || task.description}</li>
              ))}
            </ul>
          </div>

          {result.scheduling_plan && result.scheduling_plan.length > 0 && (
            <div className="mt-3">
              <p className="text-sm text-green-700 font-medium mb-1">Scheduled:</p>
              <ul className="list-disc list-inside text-sm text-green-700">
                {result.scheduling_plan.map((plan, index) => (
                  <li key={index}>
                    {plan.description} at {new Date(plan.start_time).toLocaleString()}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.scheduled_events && result.scheduled_events.length > 0 && (
            <p className="mt-2 text-xs text-green-600">
              📅 {result.scheduled_events.length} event(s) created in Google Calendar
            </p>
          )}
        </div>
      )}
    </div>
  );
}