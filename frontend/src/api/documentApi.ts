import { apiClient } from './client';
import type { DocumentItem, IngestJobStatus } from '../types';



export const documentApi = {
  getDocuments: async (): Promise<DocumentItem[]> => {
    const response = await apiClient.get<DocumentItem[]>('/documents');
    return response.data;
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

    const response = await apiClient.post('/documents/upload', formData, {
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
    return response.data;
  },

  ingestUrl: async (url: string, title?: string): Promise<DocumentItem> => {
    const response = await apiClient.post<DocumentItem>('/documents/url', { url, title });
    return response.data;
  },
};
