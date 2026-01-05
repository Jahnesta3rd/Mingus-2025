import React from 'react';
import { AlertTriangle, RefreshCw, X } from 'lucide-react';

interface ModalErrorFallbackProps {
  onClose?: () => void;
  onRetry?: () => void;
}

const ModalErrorFallback: React.FC<ModalErrorFallbackProps> = ({ 
  onClose,
  onRetry 
}) => {
  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 backdrop-blur-sm"
      role="alert"
      aria-live="assertive"
      aria-label="Modal error"
    >
      <div className="bg-gray-800 border border-red-500/50 rounded-lg p-6 max-w-md w-full mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <AlertTriangle className="w-6 h-6 text-red-400" aria-hidden="true" />
            </div>
            <h2 className="text-xl font-bold text-white">
              Something went wrong
            </h2>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1"
              aria-label="Close error message"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="mb-6">
          <p className="text-gray-300 mb-2">
            The assessment modal encountered an error. This might be due to:
          </p>
          <ul className="list-disc list-inside text-gray-400 text-sm space-y-1 mb-4">
            <li>Network connectivity issues</li>
            <li>Temporary server problems</li>
            <li>Browser compatibility issues</li>
          </ul>
          <p className="text-gray-300 text-sm">
            Please try again or refresh the page if the problem persists.
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex-1 flex items-center justify-center space-x-2 bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-gray-800"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Try Again</span>
            </button>
          )}
          <button
            onClick={handleReload}
            className="flex-1 flex items-center justify-center space-x-2 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-800"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reload Page</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModalErrorFallback;

