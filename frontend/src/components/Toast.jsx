import { useEffect, useState } from 'react';

export default function Toast({ message, type = 'info', duration = 5000, onClose }) {
  const [isVisible, setIsVisible] = useState(true);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    // Auto-dismiss after duration
    const dismissTimer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300); // Wait for exit animation
    }, duration);

    // Progress bar animation
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev - (100 / (duration / 100));
        return newProgress > 0 ? newProgress : 0;
      });
    }, 100);

    return () => {
      clearTimeout(dismissTimer);
      clearInterval(progressInterval);
    };
  }, [duration, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300);
  };

  const variants = {
    success: {
      bg: 'bg-white',
      border: 'border-l-4 border-green-500',
      icon: (
        <svg className="h-6 w-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      ),
      progressBar: 'bg-green-500',
    },
    error: {
      bg: 'bg-white',
      border: 'border-l-4 border-red-500',
      icon: (
        <svg className="h-6 w-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      ),
      progressBar: 'bg-red-500',
    },
    warning: {
      bg: 'bg-white',
      border: 'border-l-4 border-yellow-500',
      icon: (
        <svg className="h-6 w-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>
      ),
      progressBar: 'bg-yellow-500',
    },
    info: {
      bg: 'bg-white',
      border: 'border-l-4 border-blue-500',
      icon: (
        <svg className="h-6 w-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      ),
      progressBar: 'bg-blue-500',
    },
  };

  const variant = variants[type] || variants.info;

  return (
    <div
      className={`fixed top-4 right-4 max-w-md w-full shadow-lg rounded-lg overflow-hidden transition-all duration-300 z-50 ${
        isVisible ? 'animate-slideInRight' : 'opacity-0 translate-x-full'
      } ${variant.bg} ${variant.border}`}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">{variant.icon}</div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 break-words">{message}</p>
          </div>
          <button
            onClick={handleClose}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-gray-200">
        <div
          className={`h-full transition-all duration-100 ${variant.progressBar}`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
