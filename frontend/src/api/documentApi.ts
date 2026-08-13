import { apiClient } from './client';
import type { DocumentItem, IngestJobStatus } from '../types';



export const documentApi = {
  getDocuments: async (): Promise<DocumentItem[]> => {
    const response = await apiClient.get<any>('/documents');
    if (Array.isArray(response.data)) {
      return response.data;
    }
    if (response.data && Array.isArray(response.data.documents)) {
      return response.data.documents;
    }
    return [];
  },

  deleteDocument: async (id: string): Promise<void> => {
    await apiClient.delete(`/documents/${id}`);
  },

  getJobStatus: async (documentId: string): Promise<IngestJobStatus> => {
    const response = await apiClient.get<IngestJobStatus>(`/documents/${documentId}/status`);
    return response.data;
  },

  uploadFiles: async (
    files: File[],
    onProgress?: (percent: number) => void
  ): Promise<{ successful_uploads: DocumentItem[]; failed_uploads: any[] }> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const response = await apiClient.post<any>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return {
      successful_uploads: Array.isArray(response.data?.successful_uploads) ? response.data.successful_uploads : [],
      failed_uploads: Array.isArray(response.data?.failed_uploads) ? response.data.failed_uploads : [],
    };
  },

  ingestUrl: async (url: string, title?: string): Promise<DocumentItem> => {
    const response = await apiClient.post<any>('/documents/url', { url, title });
    if (response.data && response.data.document) {
      return response.data.document;
    }
    return response.data;
  },
};
