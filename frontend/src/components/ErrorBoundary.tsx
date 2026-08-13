import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught React Error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#090d16] text-slate-100 flex items-center justify-center p-6 font-sans">
          <div className="max-w-md w-full glass-panel border border-red-500/30 rounded-3xl p-8 text-center space-y-6 shadow-2xl">
            <div className="inline-flex p-4 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400">
              <AlertTriangle className="w-10 h-10" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white mb-2">Something went wrong</h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                The application encountered an unexpected runtime error.
              </p>
            </div>
            {this.state.error && (
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl text-left font-mono text-[11px] text-red-300 max-h-32 overflow-y-auto">
                {this.state.error.message}
              </div>
            )}
            <button
              onClick={this.handleReset}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-semibold rounded-xl shadow-lg transition-all"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reload Application</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
