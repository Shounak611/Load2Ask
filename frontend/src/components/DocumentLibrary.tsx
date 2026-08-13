import React, { useState } from 'react';
import { FileText, Globe, Image as ImageIcon, Trash2, Search, CheckCircle2, Clock, AlertTriangle, Layers, Filter } from 'lucide-react';
import type { DocumentItem } from '../types';


interface DocumentLibraryProps {
  documents: DocumentItem[];
  onDeleteDocument: (id: string) => void;
  selectedDoc: DocumentItem | null;
  onSelectDocForScope: (doc: DocumentItem | null) => void;
  onOpenUpload: () => void;
  onOpenUrlModal: () => void;
}

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({
  documents,
  onDeleteDocument,
  selectedDoc,
  onSelectDocForScope,
  onOpenUpload,
  onOpenUrlModal,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (doc.title && doc.title.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'ALL' || doc.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType.toLowerCase()) {
      case 'web':
      case 'html':
        return <Globe className="w-4 h-4 text-purple-400" />;
      case 'image':
        return <ImageIcon className="w-4 h-4 text-pink-400" />;
      default:
        return <FileText className="w-4 h-4 text-indigo-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" />
            COMPLETED
          </span>
        );
      case 'PROCESSING':
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/30">
            <Clock className="w-3 h-3 animate-spin" />
            {status}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-red-500/10 text-red-400 border border-red-500/30">
            <AlertTriangle className="w-3 h-3" />
            FAILED
          </span>
        );
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">Ingested Document Library</h2>
          <p className="text-sm text-slate-400 mt-1">
            Manage vector store knowledge base and select documents for focused scope retrieval.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenUpload}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/20 transition-all"
          >
            + Upload Files
          </button>
          <button
            onClick={onOpenUrlModal}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-purple-600/20 transition-all"
          >
            + Import Web URL
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search documents by name..."
            className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto">
          <Filter className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          {['ALL', 'COMPLETED', 'PROCESSING', 'FAILED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                statusFilter === st
                  ? 'bg-slate-800 text-indigo-400 border border-indigo-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Documents Table Grid */}
      {filteredDocs.length === 0 ? (
        <div className="glass-panel p-12 text-center rounded-2xl border border-slate-800 space-y-3">
          <FileText className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-slate-300">No documents found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Upload PDFs, DOCX, CSV, images, or web URLs to populate your vector database knowledge repository.
          </p>
        </div>
      ) : (
        <div className="glass-panel border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-4">Document Name</th>
                  <th className="p-4">Format</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Chunk Count</th>
                  <th className="p-4">Ingested Date</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredDocs.map((doc) => {
                  const isSelectedForScope = selectedDoc?.id === doc.id;
                  return (
                    <tr
                      key={doc.id}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        isSelectedForScope ? 'bg-indigo-950/40' : ''
                      }`}
                    >
                      <td className="p-4 font-medium text-white flex items-center gap-3">
                        <div className="p-2 bg-slate-800 rounded-lg shrink-0">
                          {getSourceIcon(doc.source_type)}
                        </div>
                        <div>
                          <div className="truncate max-w-xs">{doc.filename}</div>
                          {doc.source_uri && (
                            <div className="text-[10px] text-slate-500 truncate max-w-xs">{doc.source_uri}</div>
                          )}
                        </div>
                      </td>

                      <td className="p-4 uppercase font-mono text-[11px] text-indigo-300">
                        {doc.source_type}
                      </td>

                      <td className="p-4">
                        {getStatusBadge(doc.status)}
                      </td>

                      <td className="p-4 font-mono">
                        {doc.chunk_count} chunks
                      </td>

                      <td className="p-4 text-slate-400">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>

                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => onSelectDocForScope(isSelectedForScope ? null : doc)}
                          className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                            isSelectedForScope
                              ? 'bg-indigo-600 text-white shadow-md'
                              : 'bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700'
                          }`}
                        >
                          <Layers className="w-3 h-3 inline-block mr-1" />
                          {isSelectedForScope ? 'Active Scope' : 'Select Scope'}
                        </button>

                        <button
                          onClick={() => onDeleteDocument(doc.id)}
                          className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                          title="Delete document and vector embeddings"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
