import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

class DashboardErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
      retryCount: 0
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Track error for analytics
    this.trackError(error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private trackError = (error: Error, errorInfo: ErrorInfo) => {
    try {
      fetch('/api/analytics/errors/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': this.getCSRFToken()
        },
        body: JSON.stringify({
          error_message: error.message,
          error_stack: error.stack,
          component_stack: errorInfo.componentStack,
          user_agent: navigator.userAgent,
          url: window.location.href,
          timestamp: new Date().toISOString(),
          retry_count: this.state.retryCount
        })
      });
    } catch (trackingError) {
      console.error('Failed to track error:', trackingError);
    }
  };

  private getCSRFToken = (): string => {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
      return metaTag.getAttribute('content') || '';
    }
    
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrf_token') {
        return value;
      }
    }
    
    return '';
  };

  private handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1
      }));
    } else {
      // Max retries reached, redirect to home
      window.location.href = '/';
    }
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  private handleReportBug = () => {
    const errorDetails = {
      message: this.state.error?.message,
      stack: this.state.error?.stack,
      componentStack: this.state.errorInfo?.componentStack,
      userAgent: navigator.userAgent,
      url: window.location.href,
      timestamp: new Date().toISOString()
    };

    // Open email client with error details
    const subject = encodeURIComponent('Dashboard Error Report');
    const body = encodeURIComponent(`
Error Details:
${JSON.stringify(errorDetails, null, 2)}

Please describe what you were doing when this error occurred:
[Your description here]
    `);
    
    window.open(`mailto:support@mingus.com?subject=${subject}&body=${body}`);
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl w-full text-center">
            {/* Error Icon */}
            <div className="text-red-500 mb-6">
              <AlertTriangle className="h-16 w-16 mx-auto" />
            </div>

            {/* Error Title */}
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Dashboard Error
            </h1>

            {/* Error Message */}
            <p className="text-gray-600 mb-6">
              We encountered an unexpected error while loading your dashboard. 
              This has been automatically reported to our team.
            </p>

            {/* Error Details (Development Only) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-left">
                <h3 className="font-semibold text-red-900 mb-2">Error Details:</h3>
                <pre className="text-xs text-red-700 whitespace-pre-wrap overflow-auto max-h-32">
                  {this.state.error.message}
                  {this.state.error.stack && `\n\nStack Trace:\n${this.state.error.stack}`}
                </pre>
              </div>
            )}

            {/* Retry Count */}
            {this.state.retryCount > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-6">
                <p className="text-yellow-800 text-sm">
                  Retry attempt {this.state.retryCount} of {this.maxRetries}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {this.state.retryCount < this.maxRetries ? (
                <button
                  onClick={this.handleRetry}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <RefreshCw className="h-5 w-5" />
                  Try Again
                </button>
              ) : (
                <button
                  onClick={this.handleGoHome}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <Home className="h-5 w-5" />
                  Go to Home
                </button>
              )}

              <button
                onClick={this.handleReportBug}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                <Bug className="h-5 w-5" />
                Report Bug
              </button>
            </div>

            {/* Additional Help */}
            <div className="mt-6 text-sm text-gray-500">
              <p>
                If this problem persists, please contact our support team at{' '}
                <a href="mailto:support@mingus.com" className="text-blue-600 hover:text-blue-700">
                  support@mingus.com
                </a>
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default DashboardErrorBoundary;
