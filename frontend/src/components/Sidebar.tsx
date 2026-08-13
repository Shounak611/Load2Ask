import React from 'react';
import { MessageSquare, Plus, FolderKanban, Globe, Trash2, Database, Cpu } from 'lucide-react';
import type { ChatSession } from '../types';


interface SidebarProps {
  activeTab: 'chat' | 'documents';
  onSelectTab: (tab: 'chat' | 'documents') => void;
  sessions: ChatSession[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  documentsCount: number;
  onOpenUpload: () => void;
  onOpenUrlModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  documentsCount,
  onOpenUpload,
  onOpenUrlModal,
}) => {
  return (
    <aside className="w-64 glass-panel border-r border-slate-800 flex flex-col h-full shrink-0 z-20">
      {/* Action Header */}
      <div className="p-4 border-b border-slate-800 flex flex-col gap-2">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-600/20 transition-all hover:scale-[1.01]"
        >
          <Plus className="w-4 h-4" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Main Navigation */}
      <div className="p-3 border-b border-slate-800 flex flex-col gap-1">
        <button
          onClick={() => onSelectTab('chat')}
          className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'chat'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <MessageSquare className="w-4 h-4 text-indigo-400" />
          <span>Chat Interface</span>
        </button>

        <button
          onClick={() => onSelectTab('documents')}
          className={`flex items-center justify-between px-3 py-2 rounded-xl text-sm font-medium transition-all ${
            activeTab === 'documents'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <div className="flex items-center gap-3">
            <FolderKanban className="w-4 h-4 text-purple-400" />
            <span>Document Library</span>
          </div>
          <span className="px-2 py-0.5 bg-slate-800 text-slate-300 text-xs rounded-full border border-slate-700">
            {documentsCount}
          </span>
        </button>
      </div>

      {/* Quick Ingestion Actions */}
      <div className="p-3 border-b border-slate-800 flex items-center justify-between gap-2">
        <button
          onClick={onOpenUpload}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 bg-slate-800/60 hover:bg-slate-700/60 border border-slate-700/50 text-slate-300 text-xs rounded-lg transition-colors"
        >
          <Database className="w-3.5 h-3.5 text-indigo-400" />
          Upload Files
        </button>
        <button
          onClick={onOpenUrlModal}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 bg-slate-800/60 hover:bg-slate-700/60 border border-slate-700/50 text-slate-300 text-xs rounded-lg transition-colors"
        >
          <Globe className="w-3.5 h-3.5 text-purple-400" />
          Import URL
        </button>
      </div>

      {/* Chat History Sessions */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="px-2 py-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
          Chat Sessions
        </div>

        {(!Array.isArray(sessions) || sessions.length === 0) ? (
          <div className="px-3 py-6 text-center text-xs text-slate-500">
            No past conversations yet
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = currentSessionId === session.id;
            return (
              <div
                key={session.id}
                onClick={() => {
                  onSelectSession(session.id);
                  onSelectTab('chat');
                }}
                className={`group relative flex items-center justify-between px-3 py-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                  isActive
                    ? 'bg-slate-800/90 text-white font-medium border border-slate-700 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center gap-2 overflow-hidden pr-4">
                  <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                  <span className="truncate">{session.title}</span>
                </div>
                <button
                  onClick={(e) => onDeleteSession(session.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 text-slate-500 transition-opacity"
                  title="Delete chat session"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* System Status Footer */}
      <div className="p-3 border-t border-slate-800 text-xs text-slate-500 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-slate-400 font-mono text-[11px]">Backend API Online</span>
        </div>
        <Cpu className="w-3.5 h-3.5 text-slate-600" />
      </div>
    </aside>
  );
};
