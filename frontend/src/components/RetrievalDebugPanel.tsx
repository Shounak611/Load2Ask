import React from 'react';
import { X, Terminal, Sparkles, Layers, FileCode } from 'lucide-react';
import type { RetrievalDebugInfo } from '../types';


interface RetrievalDebugPanelProps {
  isOpen: boolean;
  onClose: () => void;
  debugInfo: RetrievalDebugInfo | null;
}

export const RetrievalDebugPanel: React.FC<RetrievalDebugPanelProps> = ({
  isOpen,
  onClose,
  debugInfo,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md glass-panel border-l border-amber-500/30 shadow-2xl flex flex-col animate-slideInRight">
      {/* Header */}
      <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-amber-950/20">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-amber-500/20 border border-amber-500/30 rounded-xl text-amber-400">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-amber-200">Retrieval Debug Inspector</h3>
            <p className="text-[11px] text-amber-400/80 font-mono">DEVELOPER TELEMETRY & CONTEXT BUDGET</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {!debugInfo ? (
          <div className="text-center py-12 text-slate-500 text-xs">
            No active debug telemetry. Ask a query to inspect query rewriting, hybrid retrieval metrics, and context token budgeting.
          </div>
        ) : (
          <>
            {/* Query Lifecycle */}
            <div className="space-y-3">
              <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                Query Lifecycle & Resolution
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                <div>
                  <span className="text-slate-500 font-mono">Original:</span>
                  <p className="text-slate-200 font-medium mt-0.5">{debugInfo.original_query}</p>
                </div>
                <div className="pt-2 border-t border-slate-800/80">
                  <span className="text-amber-400 font-mono">Resolved / Rewritten:</span>
                  <p className="text-amber-200 font-medium mt-0.5">{debugInfo.rewritten_query}</p>
                </div>
                {(Array.isArray(debugInfo.expanded_queries) && debugInfo.expanded_queries.length > 1) && (
                  <div className="pt-2 border-t border-slate-800/80">
                    <span className="text-purple-400 font-mono">Expanded Queries:</span>
                    <ul className="list-disc list-inside text-slate-300 mt-1 space-y-0.5">
                      {debugInfo.expanded_queries.map((eq, idx) => (
                        <li key={idx} className="truncate">{eq}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="space-y-3">
              <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" />
                Pipeline Funnel Metrics
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-center">
                  <div className="text-xl font-bold text-indigo-400 font-mono">{debugInfo.retrieved_candidates_count || 0}</div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold mt-1">Hybrid Retrieved</div>
                </div>

                <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-center">
                  <div className="text-xl font-bold text-purple-400 font-mono">{debugInfo.reranked_candidates_count || 0}</div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold mt-1">Re-ranked Top-K</div>
                </div>

                <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-center">
                  <div className="text-xl font-bold text-emerald-400 font-mono">{debugInfo.selected_context_count || 0}</div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold mt-1">Selected Chunks</div>
                </div>

                <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-center">
                  <div className="text-xl font-bold text-amber-400 font-mono">{(debugInfo.context_token_count || 0).toLocaleString()}</div>
                  <div className="text-[10px] text-slate-400 uppercase font-semibold mt-1">Context Tokens</div>
                </div>
              </div>
            </div>

            {/* Intent & Extracted Keywords */}
            <div className="space-y-3">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5" />
                Extracted Features
              </div>

              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                <div>
                  <span className="text-slate-500">Query Intent:</span>
                  <span className="ml-2 font-mono uppercase text-indigo-300 font-semibold">{debugInfo.intent || 'GENERAL'}</span>
                </div>
                <div>
                  <span className="text-slate-500">Extracted Keywords:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {(Array.isArray(debugInfo.extracted_keywords) ? debugInfo.extracted_keywords : []).map((kw, idx) => (
                      <span key={idx} className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-mono text-[10px]">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
