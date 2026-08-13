import React from 'react';
import { Sparkles, Terminal, FileText, Globe, Layers } from 'lucide-react';
import type { DocumentItem } from '../types';


interface HeaderProps {
  selectedDoc: DocumentItem | null;
  onClearDocFilter: () => void;
  debugMode: boolean;
  onToggleDebug: () => void;
  onOpenUpload: () => void;
  onOpenUrlModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  selectedDoc,
  onClearDocFilter,
  debugMode,
  onToggleDebug,
  onOpenUpload,
  onOpenUrlModal,
}) => {
  return (
    <header className="h-16 glass-panel border-b border-slate-800 px-6 flex items-center justify-between z-10 shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400 bg-clip-text text-transparent">
              Load2Ask
            </h1>
            <p className="text-[10px] text-slate-400 font-mono tracking-wider">MULTIMODAL RAG & CONTEXT ENGINE</p>
          </div>
        </div>

        {selectedDoc && (
          <div className="ml-4 flex items-center gap-2 px-3 py-1 bg-indigo-950/80 border border-indigo-500/40 rounded-full text-xs text-indigo-200 animate-fadeIn">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Scope: <strong className="font-semibold text-white">{selectedDoc.filename}</strong></span>
            <button
              onClick={onClearDocFilter}
              className="ml-1 text-slate-400 hover:text-white transition-colors"
              title="Clear scope filter"
            >
              &times;
            </button>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onOpenUpload}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-slate-200 text-xs font-medium rounded-lg transition-all"
        >
          <FileText className="w-4 h-4 text-indigo-400" />
          Upload Document
        </button>

        <button
          onClick={onOpenUrlModal}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-slate-200 text-xs font-medium rounded-lg transition-all"
        >
          <Globe className="w-4 h-4 text-purple-400" />
          Import URL
        </button>

        <button
          onClick={onToggleDebug}
          className={`flex items-center gap-1.5 px-3 py-1.5 border rounded-lg text-xs font-medium transition-all ${
            debugMode
              ? 'bg-amber-500/20 border-amber-500/50 text-amber-300 shadow-sm shadow-amber-500/20'
              : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:text-slate-200'
          }`}
          title="Toggle Retrieval Debug Mode"
        >
          <Terminal className="w-4 h-4" />
          <span>Debug Mode</span>
          <span className={`w-2 h-2 rounded-full ${debugMode ? 'bg-amber-400 animate-ping' : 'bg-slate-600'}`} />
        </button>
      </div>
    </header>
  );
};
