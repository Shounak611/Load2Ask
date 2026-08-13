import { apiClient } from './client';
import type { QueryResponsePayload, Citation, RetrievalDebugInfo } from '../types';


export const queryApi = {
  sendQuery: async (
    query: string,
    sessionId?: string,
    documentId?: string
  ): Promise<QueryResponsePayload> => {
    const response = await apiClient.post<QueryResponsePayload>('/chat', {
      query,
      session_id: sessionId,
      document_id: documentId,
    });
    return response.data;
  },

  streamQuery: (
    query: string,
    sessionId: string | undefined,
    documentId: string | undefined,
    onMeta: (meta: { session_id: string; rewritten_query: string; sources: Citation[]; debug: RetrievalDebugInfo }) => void,
    onToken: (token: string) => void,
    onError: (err: Error) => void,
    onDone: () => void
  ) => {
    const controller = new AbortController();

    fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        session_id: sessionId,
        document_id: documentId,
      }),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || `Streaming request failed with status ${response.status}`);
        }
        if (!response.body) {
          throw new Error('Response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data: ')) continue;
            const dataStr = trimmed.slice(6);
            if (dataStr === '[DONE]') {
              onDone();
              return;
            }

            try {
              const data = JSON.parse(dataStr);
              if (data.type === 'meta') {
                onMeta({
                  session_id: data.session_id,
                  rewritten_query: data.rewritten_query,
                  sources: data.sources || [],
                  debug: data.retrieval_debug,
                });
              } else if (data.type === 'token') {
                onToken(data.token);
              }
            } catch (e) {
              console.warn('Failed to parse SSE line:', dataStr);
            }
          }
        }
        onDone();
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          onError(err instanceof Error ? err : new Error(String(err)));
        }
      });

    return () => controller.abort();
  },
};
