import React, { useState, useRef } from 'react';
import { Send, Paperclip, Globe, StopCircle, Layers } from 'lucide-react';
import type { DocumentItem } from '../types';


interface InputAreaProps {
  onSendMessage: (query: string) => void;
  isLoading: boolean;
  onStopStreaming?: () => void;
  selectedDoc: DocumentItem | null;
  onClearDocFilter: () => void;
  onOpenUpload: () => void;
  onOpenUrlModal: () => void;
}

export const InputArea: React.FC<InputAreaProps> = ({
  onSendMessage,
  isLoading,
  onStopStreaming,
  selectedDoc,
  onClearDocFilter,
  onOpenUpload,
  onOpenUrlModal,
}) => {
  const [query, setQuery] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onSendMessage(query.trim());
    setQuery('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="p-4 glass-panel border-t border-slate-800 shrink-0">
      <div className="max-w-4xl mx-auto space-y-2">
        {selectedDoc && (
          <div className="flex items-center gap-2 text-xs text-indigo-300 bg-indigo-950/60 border border-indigo-500/30 px-3 py-1 rounded-lg w-fit">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Scoped to document: <strong className="text-white">{selectedDoc.filename}</strong></span>
            <button
              onClick={onClearDocFilter}
              className="ml-1 text-slate-400 hover:text-white"
              title="Remove scope"
            >
              &times;
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="relative flex items-center">
          <textarea
            ref={textareaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your documents, PDFs, data tables, or imported URLs..."
            rows={1}
            disabled={isLoading}
            className="w-full pl-12 pr-28 py-3 bg-slate-900/90 border border-slate-700/80 focus:border-indigo-500 rounded-2xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 resize-none transition-all"
          />

          {/* Left Input Actions */}
          <div className="absolute left-3 flex items-center gap-1">
            <button
              type="button"
              onClick={onOpenUpload}
              className="p-1.5 text-slate-400 hover:text-indigo-400 rounded-lg hover:bg-slate-800 transition-colors"
              title="Attach documents"
            >
              <Paperclip className="w-4 h-4" />
            </button>
          </div>

          {/* Right Input Actions */}
          <div className="absolute right-3 flex items-center gap-2">
            <button
              type="button"
              onClick={onOpenUrlModal}
              className="p-1.5 text-slate-400 hover:text-purple-400 rounded-lg hover:bg-slate-800 transition-colors"
              title="Import Web URL"
            >
              <Globe className="w-4 h-4" />
            </button>

            {isLoading ? (
              <button
                type="button"
                onClick={onStopStreaming}
                className="p-2 bg-red-600 hover:bg-red-500 text-white rounded-xl shadow-md transition-colors"
                title="Stop response"
              >
                <StopCircle className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!query.trim()}
                className="p-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl shadow-md transition-all disabled:shadow-none hover:scale-105"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
