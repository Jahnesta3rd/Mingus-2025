import React from 'react';

interface SessionSetupTerminalErrorProps {
  onRetry: () => void;
  /** light = RegisterPage green-card context; dark = LogoSplash gray-900 context */
  variant?: 'light' | 'dark';
  message?: string;
}

const SessionSetupTerminalError: React.FC<SessionSetupTerminalErrorProps> = ({
  onRetry,
  variant = 'light',
  message = 'We could not confirm your session yet. Please try again.',
}) => {
  if (variant === 'dark') {
    return (
      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center px-4 bg-gray-900/95">
        <div className="max-w-md text-center space-y-4">
          <p className="text-sm text-red-300" role="alert">
            {message}
          </p>
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex justify-center rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-gray-900"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md bg-red-50 p-6 max-w-md border border-red-200 shadow-sm">
      <h3 className="text-sm font-medium text-red-800">Could not finish setup</h3>
      <p className="mt-2 text-sm text-red-700" role="alert">
        {message}
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-violet-600 hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-400"
      >
        Try again
      </button>
    </div>
  );
};

export default SessionSetupTerminalError;
