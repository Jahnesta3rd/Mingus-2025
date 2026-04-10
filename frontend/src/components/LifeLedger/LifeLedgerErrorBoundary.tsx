import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

/**
 * Isolates Life Ledger render failures so the rest of the dashboard still loads.
 */
export default class LifeLedgerErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('LifeLedgerErrorBoundary', error, errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 text-sm text-gray-600">
          Life Ledger could not be loaded. The rest of your dashboard is unchanged.
        </div>
      );
    }
    return this.props.children;
  }
}
