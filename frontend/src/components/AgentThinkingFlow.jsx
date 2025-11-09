import { useEffect, useState } from 'react';

export default function AgentThinkingFlow({ isProcessing }) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      id: 1,
      agent: 'Transcription Agent',
      icon: '🎤',
      title: 'Converting speech to text',
      description: 'Using OpenAI Whisper to transcribe your voice...',
      duration: 1500,
    },
    {
      id: 2,
      agent: 'Task Decomposition Agent',
      icon: '🧠',
      title: 'Understanding your request',
      description: 'Breaking down tasks, extracting deadlines and priorities...',
      duration: 1800,
    },
    {
      id: 3,
      agent: 'Scheduling Agent',
      icon: '📅',
      title: 'Finding optimal time slots',
      description: 'Checking calendar conflicts and optimizing schedule...',
      duration: 1800,
    },
    {
      id: 4,
      agent: 'Calendar Integration Agent',
      icon: '✅',
      title: 'Creating calendar events',
      description: 'Syncing with Google Calendar API...',
      duration: 1200,
    },
  ];

  useEffect(() => {
    if (!isProcessing) {
      setCurrentStep(0);
      return;
    }

    let stepIndex = 0;
    const advanceStep = () => {
      if (stepIndex < steps.length) {
        setCurrentStep(stepIndex);
        stepIndex++;
        if (stepIndex < steps.length) {
          setTimeout(advanceStep, steps[stepIndex - 1].duration);
        }
      }
    };

    advanceStep();
  }, [isProcessing]);

  if (!isProcessing) return null;

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-2xl p-6 shadow-lg animate-slideDown">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center shadow-lg">
            <svg className="w-6 h-6 text-white animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
          </div>
          <div className="absolute inset-0 rounded-full border-2 border-purple-400 animate-ping"></div>
        </div>
        <div>
          <h3 className="text-lg font-bold text-purple-900">AI Agents Working</h3>
          <p className="text-sm text-purple-700">Multi-agent orchestration in progress</p>
        </div>
      </div>

      {/* Agent Steps */}
      <div className="space-y-4">
        {steps.map((step, index) => {
          const isActive = index === currentStep;
          const isCompleted = index < currentStep;
          const isPending = index > currentStep;

          return (
            <div
              key={step.id}
              className={`flex items-start gap-4 p-4 rounded-xl transition-all duration-500 ${
                isActive
                  ? 'bg-white shadow-md border-2 border-purple-400 scale-105'
                  : isCompleted
                  ? 'bg-green-50 border-2 border-green-300'
                  : 'bg-white/50 border-2 border-gray-200 opacity-60'
              }`}
            >
              {/* Step Icon/Status */}
              <div className="flex-shrink-0">
                {isCompleted ? (
                  <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center shadow-md">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"/>
                    </svg>
                  </div>
                ) : isActive ? (
                  <div className="relative">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center shadow-md text-xl animate-pulse">
                      {step.icon}
                    </div>
                    <div className="absolute inset-0 rounded-full border-2 border-purple-400 animate-ping"></div>
                  </div>
                ) : (
                  <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-xl opacity-50">
                    {step.icon}
                  </div>
                )}
              </div>

              {/* Step Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <p className={`text-xs font-semibold uppercase tracking-wide mb-1 ${
                      isActive ? 'text-purple-600' : isCompleted ? 'text-green-600' : 'text-gray-400'
                    }`}>
                      {step.agent}
                    </p>
                    <h4 className={`font-bold mb-1 ${
                      isActive ? 'text-purple-900' : isCompleted ? 'text-green-800' : 'text-gray-500'
                    }`}>
                      {step.title}
                    </h4>
                    <p className={`text-sm ${
                      isActive ? 'text-purple-700' : isCompleted ? 'text-green-700' : 'text-gray-400'
                    }`}>
                      {isCompleted ? '✓ Completed' : step.description}
                    </p>
                  </div>

                  {/* Status Badge */}
                  {isActive && (
                    <span className="flex-shrink-0 px-3 py-1 bg-purple-500 text-white text-xs font-bold rounded-full animate-pulse">
                      Active
                    </span>
                  )}
                </div>

                {/* Progress Bar for Active Step */}
                {isActive && (
                  <div className="mt-3 h-1.5 bg-purple-200 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-progress"></div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="mt-6 flex items-center gap-2 text-sm text-purple-700 bg-purple-100 border border-purple-300 rounded-lg p-3">
        <svg className="h-5 w-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
        </svg>
        <span className="font-medium">
          Processing step {currentStep + 1} of {steps.length}...
        </span>
      </div>
    </div>
  );
}
