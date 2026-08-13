import React, { useState } from 'react';
import { X, Globe, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import { documentApi } from '../api/documentApi';
import type { DocumentItem } from '../types';


interface UrlIngestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onIngestSuccess: (doc: DocumentItem) => void;
}

export const UrlIngestModal: React.FC<UrlIngestModalProps> = ({
  isOpen,
  onClose,
  onIngestSuccess,
}) => {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsLoading(true);
    setError(null);
    setCurrentStep('Fetching HTML...');

    try {
      setTimeout(() => setCurrentStep('Extracting text & cleaning tags...'), 400);
      setTimeout(() => setCurrentStep('Recursive chunking & metadata tagging...'), 800);
      setTimeout(() => setCurrentStep('Generating dense vector embeddings...'), 1200);

      const doc = await documentApi.ingestUrl(url.trim(), title.trim() || undefined);

      setCurrentStep('Completed!');
      setTimeout(() => {
        setIsLoading(false);
        onIngestSuccess(doc);
        onClose();
        setUrl('');
        setTitle('');
        setCurrentStep(null);
      }, 500);
    } catch (err: any) {
      setIsLoading(false);
      setCurrentStep(null);
      setError(err.message || 'Failed to ingest URL');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden animate-fadeIn">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-purple-600/20 border border-purple-500/30 rounded-xl text-purple-400">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Ingest Web URL</h3>
              <p className="text-xs text-slate-400">Extracts web content with SSRF security protection</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Form */}
        <form onSubmit={handleIngest} className="p-6 space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Website URL *</label>
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/documentation"
              disabled={isLoading}
              className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-slate-700/80 focus:border-purple-500 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Custom Title (Optional)</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Official API Reference Manual"
              disabled={isLoading}
              className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-slate-700/80 focus:border-purple-500 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
            />
          </div>

          {/* Status Steps */}
          {currentStep && (
            <div className="p-3 bg-purple-950/40 border border-purple-500/30 rounded-xl flex items-center gap-2 text-xs text-purple-300">
              <Loader2 className="w-4 h-4 animate-spin shrink-0 text-purple-400" />
              <span>{currentStep}</span>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-950/50 border border-red-500/40 rounded-xl text-xs text-red-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Footer Actions */}
          <div className="pt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!url.trim() || isLoading}
              className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-purple-600/20 transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Importing...</span>
                </>
              ) : (
                <>
                  <span>Import Website</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
