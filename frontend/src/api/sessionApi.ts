import { apiClient } from './client';
import type { ChatSession, ChatMessage } from '../types';


export const sessionApi = {
  getSessions: async (): Promise<ChatSession[]> => {
    const response = await apiClient.get<any>('/sessions');
    if (Array.isArray(response.data)) {
      return response.data;
    }
    if (response.data && Array.isArray(response.data.sessions)) {
      return response.data.sessions;
    }
    return [];
  },

  createSession: async (title?: string): Promise<ChatSession> => {
    const response = await apiClient.post<ChatSession>('/sessions', null, {
      params: { title: title || 'New Chat' },
    });
    return response.data;
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/sessions/${sessionId}`);
  },

  getSessionMessages: async (sessionId: string): Promise<ChatMessage[]> => {
    const response = await apiClient.get<any>(`/sessions/${sessionId}/messages`);
    if (Array.isArray(response.data)) {
      return response.data;
    }
    if (response.data && Array.isArray(response.data.messages)) {
      return response.data.messages;
    }
    return [];
  },
};
