import { apiClient } from './client';
import type { ChatSession, ChatMessage } from '../types';


export const sessionApi = {
  getSessions: async (): Promise<ChatSession[]> => {
    const response = await apiClient.get<ChatSession[]>('/sessions');
    return response.data;
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
    const response = await apiClient.get<ChatMessage[]>(`/sessions/${sessionId}/messages`);
    return response.data;
  },
};
