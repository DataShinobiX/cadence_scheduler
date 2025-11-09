import { useState, useEffect } from 'react';
import useVoiceRecorder from '../hooks/useVoiceRecorder';
import { uploadAudio } from '../utils/api';
import AgentThinkingFlow from './AgentThinkingFlow';

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
    <div className="space-y-6">
      {/* Assistant Ready State */}
      <div className="text-center space-y-4 animate-fadeIn">
        <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full transition-all duration-300 ${
          loading
            ? 'bg-gradient-to-br from-purple-100 to-blue-100'
            : isRecording
            ? 'bg-gradient-to-br from-red-100 to-pink-100 animate-pulse'
            : 'bg-gradient-to-br from-blue-100 to-indigo-100'
        }`}>
          {loading ? (
            <div className="relative">
              <svg className="animate-spin h-12 w-12 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          ) : isRecording ? (
            <div className="relative">
              <svg className="h-12 w-12 text-red-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
              {/* Recording pulse rings */}
              <div className="absolute inset-0 rounded-full border-2 border-red-400 animate-ping"></div>
              <div className="absolute inset-0 rounded-full border-2 border-red-300 animate-ping" style={{ animationDelay: '0.15s' }}></div>
            </div>
          ) : (
            <svg className="h-12 w-12 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          )}
        </div>

        <div className="space-y-1">
          <h3 className={`text-xl font-semibold transition-colors duration-300 ${
            loading ? 'text-purple-800' : isRecording ? 'text-red-800' : 'text-blue-800'
          }`}>
            {loading
              ? 'Processing your request...'
              : isRecording
              ? 'Listening...'
              : 'Your Assistant is Ready'}
          </h3>
          <p className="text-gray-600 text-sm">
            {loading
              ? 'Analyzing and scheduling your tasks'
              : isRecording
              ? 'Speak naturally about what you need to schedule'
              : 'Click the button below to start'}
          </p>
        </div>
      </div>

      {/* Recording Button */}
      <div className="flex justify-center">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={loading}
          className={`group relative px-8 py-4 rounded-full text-white font-medium text-lg shadow-lg transform transition-all duration-200 ${
            loading
              ? 'bg-gray-400 cursor-not-allowed scale-95'
              : isRecording
              ? 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 hover:scale-105 hover:shadow-xl'
              : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 hover:scale-105 hover:shadow-xl'
          }`}
        >
          <span className="flex items-center gap-3">
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing
              </>
            ) : isRecording ? (
              <>
                <span className="w-3 h-3 bg-white rounded-full"></span>
                Stop Recording
              </>
            ) : (
              <>
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
                Start Recording
              </>
            )}
          </span>
        </button>
      </div>

      {/* Audio Waveform Visualization (when recording) */}
      {isRecording && (
        <div className="flex justify-center items-center gap-1 h-16 animate-fadeIn">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="w-1 bg-gradient-to-t from-red-400 to-red-600 rounded-full animate-soundWave"
              style={{
                height: '100%',
                animationDelay: `${i * 0.05}s`,
                animationDuration: '0.8s'
              }}
            ></div>
          ))}
        </div>
      )}

      {/* Agent Thinking Flow - Show when processing */}
      <AgentThinkingFlow isProcessing={loading} />

      {/* Error Message */}
      {error && (
        <div className="p-5 bg-red-50 border-l-4 border-red-500 rounded-lg shadow-sm animate-slideDown">
          <div className="flex items-start gap-3">
            <svg className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
            </svg>
            <div>
              <p className="text-red-800 font-semibold">Error</p>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Transcript */}
      {transcript && !error && (
        <div className="p-5 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg shadow-sm animate-slideDown">
          <div className="flex items-start gap-3">
            <svg className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
            </svg>
            <div className="flex-1">
              <p className="text-blue-900 font-semibold mb-2">Transcript</p>
              <p className="text-blue-800 leading-relaxed">{transcript}</p>
            </div>
          </div>
        </div>
      )}

      {/* Scheduling Results */}
      {result && result.decomposed_tasks && result.decomposed_tasks.length > 0 && (
        <div className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-l-4 border-green-500 rounded-lg shadow-md animate-slideDown">
          <div className="flex items-start gap-3 mb-4">
            <div className="flex-shrink-0 w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
              <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <div className="flex-1">
              <h4 className="text-green-900 font-bold text-lg">Tasks Scheduled Successfully!</h4>
              <p className="text-green-700 text-sm mt-1">Your tasks have been analyzed and added to your calendar</p>
            </div>
          </div>

          <div className="space-y-4">
            {/* Tasks List */}
            <div className="bg-white/60 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <svg className="h-5 w-5 text-green-700" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
                  <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd"/>
                </svg>
                <p className="text-green-900 font-semibold">Tasks Created</p>
              </div>
              <ul className="space-y-2">
                {result.decomposed_tasks.map((task, index) => (
                  <li key={index} className="flex items-start gap-2 text-green-800">
                    <span className="flex-shrink-0 w-5 h-5 bg-green-200 rounded-full flex items-center justify-center text-xs font-bold text-green-700 mt-0.5">
                      {index + 1}
                    </span>
                    <span className="flex-1">{task.title || task.description}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Scheduling Plan */}
            {result.scheduling_plan && result.scheduling_plan.length > 0 && (
              <div className="bg-white/60 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <svg className="h-5 w-5 text-green-700" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
                  </svg>
                  <p className="text-green-900 font-semibold">Scheduled Events</p>
                </div>
                <ul className="space-y-2">
                  {result.scheduling_plan.map((plan, index) => (
                    <li key={index} className="flex items-start gap-2 text-green-800 bg-green-50/50 p-2 rounded">
                      <svg className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd"/>
                      </svg>
                      <div className="flex-1">
                        <p className="font-medium">{plan.description}</p>
                        <p className="text-sm text-green-700">{new Date(plan.start_time).toLocaleString()}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Calendar Events Badge */}
            {result.scheduled_events && result.scheduled_events.length > 0 && (
              <div className="flex items-center gap-2 bg-green-100 border border-green-300 rounded-lg p-3">
                <svg className="h-5 w-5 text-green-700" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
                </svg>
                <p className="text-green-800 font-medium">
                  {result.scheduled_events.length} event{result.scheduled_events.length !== 1 ? 's' : ''} added to Google Calendar
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}