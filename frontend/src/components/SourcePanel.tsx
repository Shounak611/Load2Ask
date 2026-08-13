import React from 'react';
import { X, BookOpen, Hash, FileText } from 'lucide-react';
import type { Citation } from '../types';


interface SourcePanelProps {
  citation: Citation | null;
  onClose: () => void;
}

export const SourcePanel: React.FC<SourcePanelProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md glass-panel border-l border-slate-800 shadow-2xl flex flex-col animate-slideInRight">
      {/* Drawer Header */}
      <div className="p-5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Retrieved Source Details</h3>
            <p className="text-[11px] text-slate-400 font-mono">CITATION EVIDENCE INSPECTOR</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Drawer Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Source Title & Meta */}
        <div className="glass-card p-4 rounded-xl border border-slate-700/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="px-2.5 py-0.5 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full text-[10px] font-semibold uppercase">
              {citation.source_type}
            </span>
            <span className="text-xs font-mono text-emerald-400 font-semibold">
              Relevance: {(citation.score * 100).toFixed(1)}%
            </span>
          </div>

          <h4 className="text-sm font-bold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
            <span className="break-all">{citation.document}</span>
          </h4>

          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs text-slate-400">
            {citation.page && (
              <div>Page: <strong className="text-slate-200">{citation.page}</strong></div>
            )}
            {citation.slide && (
              <div>Slide: <strong className="text-slate-200">{citation.slide}</strong></div>
            )}
            {citation.section && (
              <div>Section: <strong className="text-slate-200">{citation.section}</strong></div>
            )}
            {citation.url && (
              <div className="col-span-2 truncate">
                URL: <a href={citation.url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">{citation.url}</a>
              </div>
            )}
          </div>
        </div>

        {/* Chunk Identifier */}
        <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
          <Hash className="w-3.5 h-3.5" />
          <span>Chunk ID: {citation.chunk_id}</span>
        </div>

        {/* Content Snippet */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300">Grounding Evidence Context</label>
          <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-wrap">
            {citation.document ? (
              `Retrieved context block supporting the answer generated from ${citation.document}.`
            ) : (
              "No raw content payload captured."
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
