import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Sparkles, BookOpen, RotateCcw, AlertTriangle, ExternalLink } from 'lucide-react';
import type { ChatMessage, Citation } from '../types';


interface ChatAreaProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  onSelectCitation: (citation: Citation) => void;
  onSelectPromptSuggestion: (prompt: string) => void;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  isLoading,
  error,
  onRetry,
  onSelectCitation,
  onSelectPromptSuggestion,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const safeMessages = Array.isArray(messages) ? messages : [];

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6">
      {safeMessages.length === 0 ? (
        <div className="max-w-2xl mx-auto my-12 text-center space-y-6 animate-fadeIn">
          <div className="inline-flex p-4 bg-gradient-to-br from-indigo-500/20 via-purple-500/20 to-pink-500/20 rounded-3xl border border-indigo-500/30">
            <Sparkles className="w-10 h-10 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Multimodal RAG & Knowledge Assistant</h2>
            <p className="text-sm text-slate-400 max-w-md mx-auto">
              Ask questions across PDFs, TXT, DOCX, PPTX, CSV, XLSX, JSON, Markdown, HTML, images, and live websites with verified source citations.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left pt-4">
            {[
              "Summarize the key findings from the uploaded document.",
              "What does page 12 say about memory management?",
              "Compare the features listed in the CSV dataset.",
              "Explain the core concept in the imported website URL."
            ].map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => onSelectPromptSuggestion(prompt)}
                className="p-3.5 bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-indigo-500/40 rounded-xl text-xs text-slate-300 transition-all text-left group"
              >
                <div className="font-semibold text-indigo-400 mb-1 group-hover:text-indigo-300">Sample Query</div>
                <div>{prompt}</div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        safeMessages.map((msg) => {
          const isUser = msg.role === 'user';
          const safeSources = Array.isArray(msg.sources) ? msg.sources : [];
          return (
            <div
              key={msg.id}
              className={`flex gap-4 max-w-4xl mx-auto ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 border border-indigo-400/30 flex items-center justify-center text-white shrink-0 shadow-md">
                  <Bot className="w-5 h-5" />
                </div>
              )}

              <div
                className={`flex flex-col space-y-2 max-w-[85%] ${
                  isUser
                    ? 'items-end'
                    : 'items-start'
                }`}
              >
                {/* Bubble Container */}
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    isUser
                      ? 'bg-indigo-600 text-white rounded-tr-none shadow-md shadow-indigo-600/10'
                      : 'glass-card border border-slate-700/80 text-slate-200 rounded-tl-none prose prose-invert prose-indigo max-w-none'
                  }`}
                >
                  {isUser ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <>
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>

                      {msg.isStreaming && (
                        <span className="inline-block w-2 h-4 ml-1 bg-indigo-400 animate-pulse rounded-full" />
                      )}
                    </>
                  )}
                </div>

                {/* Sources / Citation Tags for Assistant */}
                {!isUser && safeSources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-slate-800/80 w-full">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400 font-semibold mb-2">
                      <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Retrieved Sources ({safeSources.length}):</span>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {safeSources.map((citation, idx) => (
                        <button
                          key={idx}
                          onClick={() => onSelectCitation(citation)}
                          className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800/80 hover:bg-indigo-950/80 border border-slate-700 hover:border-indigo-500/50 rounded-lg text-xs text-slate-300 hover:text-indigo-200 transition-all shadow-sm"
                        >
                          <span className="font-semibold text-indigo-400">[{idx + 1}]</span>
                          <span className="max-w-[140px] truncate">{citation.document}</span>
                          {citation.page && <span className="text-[10px] text-slate-400">p.{citation.page}</span>}
                          {citation.slide && <span className="text-[10px] text-slate-400">slide {citation.slide}</span>}
                          <ExternalLink className="w-3 h-3 text-slate-500" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {isUser && (
                <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0">
                  <User className="w-5 h-5" />
                </div>
              )}
            </div>
          );
        })
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="flex gap-4 max-w-4xl mx-auto justify-start">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shrink-0 animate-pulse">
            <Bot className="w-5 h-5" />
          </div>
          <div className="p-4 rounded-2xl glass-card border border-slate-700/80 text-slate-400 text-sm flex items-center gap-3">
            <Sparkles className="w-4 h-4 text-indigo-400 animate-spin" />
            <span>Analyzing query, retrieving knowledge chunks & engineering context...</span>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="max-w-4xl mx-auto p-4 bg-red-950/40 border border-red-500/40 rounded-2xl flex items-center justify-between text-red-200 text-sm">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={onRetry}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-900/60 hover:bg-red-800/80 border border-red-500/40 rounded-lg text-xs font-semibold transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Retry
          </button>
        </div>
      )}
    </div>
  );
};
