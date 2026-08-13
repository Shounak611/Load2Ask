import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { InputArea } from './components/InputArea';
import { FileUploadModal } from './components/FileUploadModal';
import { UrlIngestModal } from './components/UrlIngestModal';
import { DocumentLibrary } from './components/DocumentLibrary';
import { SourcePanel } from './components/SourcePanel';
import { RetrievalDebugPanel } from './components/RetrievalDebugPanel';

import { documentApi } from './api/documentApi';
import { sessionApi } from './api/sessionApi';
import { queryApi } from './api/queryApi';
import type { ChatSession, ChatMessage, DocumentItem, Citation, RetrievalDebugInfo } from './types';


export function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [debugMode, setDebugMode] = useState(false);
  const [activeDebugInfo, setActiveDebugInfo] = useState<RetrievalDebugInfo | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isUrlModalOpen, setIsUrlModalOpen] = useState(false);
  const [isDebugPanelOpen, setIsDebugPanelOpen] = useState(false);

  const abortStreamRef = useRef<(() => void) | null>(null);

  // Initial Load: Fetch documents & sessions from backend
  useEffect(() => {
    loadDocuments();
    loadSessions();
  }, []);

  // Load Session Messages when active session changes
  useEffect(() => {
    if (currentSessionId) {
      loadSessionMessages(currentSessionId);
    } else {
      setMessages([]);
    }
  }, [currentSessionId]);

  const loadDocuments = async () => {
    try {
      const docs = await documentApi.getDocuments();
      setDocuments(Array.isArray(docs) ? docs : []);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
      setDocuments([]);
    }
  };

  const loadSessions = async () => {
    try {
      const sessList = await sessionApi.getSessions();
      const safeSessList = Array.isArray(sessList) ? sessList : [];
      setSessions(safeSessList);
      if (safeSessList.length > 0 && !currentSessionId) {
        setCurrentSessionId(safeSessList[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load sessions:', err);
      setSessions([]);
    }
  };

  const loadSessionMessages = async (sessionId: string) => {
    try {
      const msgs = await sessionApi.getSessionMessages(sessionId);
      setMessages(Array.isArray(msgs) ? msgs : []);
    } catch (err: any) {
      console.error('Failed to load messages:', err);
      setMessages([]);
    }
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setActiveDebugInfo(null);
    setActiveTab('chat');
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await sessionApi.deleteSession(id);
      setSessions((prev) => (Array.isArray(prev) ? prev.filter((s) => s.id !== id) : []));
      if (currentSessionId === id) {
        handleNewChat();
      }
    } catch (err: any) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    try {
      await documentApi.deleteDocument(docId);
      setDocuments((prev) => (Array.isArray(prev) ? prev.filter((d) => d.id !== docId) : []));
      if (selectedDoc?.id === docId) {
        setSelectedDoc(null);
      }
    } catch (err: any) {
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  const handleSendMessage = (query: string) => {
    setError(null);
    setIsLoading(true);

    const userMsgId = 'msg-' + Date.now();
    const assistantMsgId = 'msg-ast-' + (Date.now() + 1);

    const userMsg: ChatMessage = {
      id: userMsgId,
      session_id: currentSessionId || '',
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };

    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      session_id: currentSessionId || '',
      role: 'assistant',
      content: '',
      isStreaming: true,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    const abortFn = queryApi.streamQuery(
      query,
      currentSessionId || undefined,
      selectedDoc?.id,
      (meta) => {
        if (!currentSessionId || currentSessionId !== meta.session_id) {
          setCurrentSessionId(meta.session_id);
          loadSessions();
        }
        setActiveDebugInfo(meta.debug);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  session_id: meta.session_id,
                  sources: meta.sources,
                  retrieval_debug: meta.debug,
                }
              : msg
          )
        );
      },
      (token) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: msg.content + token,
                }
              : msg
          )
        );
      },
      (err) => {
        setIsLoading(false);
        setError(err.message || 'Stream generation failed');
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content:
                    msg.content ||
                    'I encountered a communication error with the retrieval engine.',
                  isStreaming: false,
                }
              : msg
          )
        );
      },
      () => {
        setIsLoading(false);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, isStreaming: false } : msg
          )
        );
      }
    );

    abortStreamRef.current = abortFn;
  };

  const handleStopStreaming = () => {
    if (abortStreamRef.current) {
      abortStreamRef.current();
      abortStreamRef.current = null;
    }
    setIsLoading(false);
    setMessages((prev) =>
      prev.map((msg) => (msg.isStreaming ? { ...msg, isStreaming: false } : msg))
    );
  };

  const handleRetry = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      handleSendMessage(lastUserMsg.content);
    }
  };

  return (
    <div className="flex h-screen bg-[#090d16] text-slate-100 overflow-hidden font-sans select-none">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        documentsCount={documents.length}
        onOpenUpload={() => setIsUploadModalOpen(true)}
        onOpenUrlModal={() => setIsUrlModalOpen(true)}
      />

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        <Header
          selectedDoc={selectedDoc}
          onClearDocFilter={() => setSelectedDoc(null)}
          debugMode={debugMode}
          onToggleDebug={() => {
            setDebugMode(!debugMode);
            setIsDebugPanelOpen(!debugMode);
          }}
          onOpenUpload={() => setIsUploadModalOpen(true)}
          onOpenUrlModal={() => setIsUrlModalOpen(true)}
        />

        {activeTab === 'chat' ? (
          <main className="flex-1 flex flex-col h-[calc(100vh-4rem)] overflow-hidden relative">
            <ChatArea
              messages={messages}
              isLoading={isLoading}
              error={error}
              onRetry={handleRetry}
              onSelectCitation={(citation) => setActiveCitation(citation)}
              onSelectPromptSuggestion={(prompt) => handleSendMessage(prompt)}
            />

            <InputArea
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              onStopStreaming={handleStopStreaming}
              selectedDoc={selectedDoc}
              onClearDocFilter={() => setSelectedDoc(null)}
              onOpenUpload={() => setIsUploadModalOpen(true)}
              onOpenUrlModal={() => setIsUrlModalOpen(true)}
            />
          </main>
        ) : (
          <DocumentLibrary
            documents={documents}
            onDeleteDocument={handleDeleteDocument}
            selectedDoc={selectedDoc}
            onSelectDocForScope={(doc) => {
              setSelectedDoc(doc);
              setActiveTab('chat');
            }}
            onOpenUpload={() => setIsUploadModalOpen(true)}
            onOpenUrlModal={() => setIsUrlModalOpen(true)}
          />
        )}
      </div>

      {/* Modals & Slide-over Panels */}
      <FileUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={() => loadDocuments()}
      />

      <UrlIngestModal
        isOpen={isUrlModalOpen}
        onClose={() => setIsUrlModalOpen(false)}
        onIngestSuccess={() => loadDocuments()}
      />

      <SourcePanel
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />

      <RetrievalDebugPanel
        isOpen={isDebugPanelOpen}
        onClose={() => setIsDebugPanelOpen(false)}
        debugInfo={activeDebugInfo}
      />
    </div>
  );
}

export default App;
