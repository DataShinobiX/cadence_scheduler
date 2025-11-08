import { useState, useEffect } from 'react';
import useVoiceRecorder from '../hooks/useVoiceRecorder';

export default function VoiceRecorder() {
  const [transcript, setTranscript] = useState('');
  const {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording
  } = useVoiceRecorder();

  useEffect(() => {
    const sendAudioForTranscription = async () => {
      if (!audioBlob) return;

      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');

      try {
        const res = await fetch('http://localhost:8000/api/transcribe', {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        setTranscript(data.transcript);
      } catch (err) {
        console.error('Transcription failed:', err);
        setTranscript('Error transcribing audio.');
      }
    };

    sendAudioForTranscription();
  }, [audioBlob]);

  return (
    <div className="space-y-4">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        className={`px-6 py-3 rounded-md text-white font-medium ${
          isRecording ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-600 hover:bg-blue-700'
        }`}
      >
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>

      {transcript && (
        <div className="p-4 bg-gray-100 border rounded">
          <p className="text-gray-800 font-medium mb-1">Transcript:</p>
          <p className="text-gray-700">{transcript}</p>
        </div>
      )}
    </div>
  );
}