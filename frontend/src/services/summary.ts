import { api } from "./api";
import { NLPAnalysis } from "../types";

export interface ChatHistoryItem {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
}

export interface SummaryResponse {
  summary: string;
}

export interface NotesResponse {
  notes: string;
}

export interface ResearchResponse {
  findings: string;
  citations: { title: string; uri: string }[];
}

export const summaryService = {
  /**
   * Interact with NEXORA AI Student Agent, supporting document context or general chat.
   */
  chat: async (
    message: string,
    history: ChatHistoryItem[] = [],
    documentId?: string | null
  ): Promise<ChatResponse> => {
    return api.post<ChatResponse>("/ai/chat", {
      message,
      history,
      document_id: documentId,
    });
  },

  /**
   * Compile a comprehensive study guide/summary from transcript text.
   */
  generateSummary: async (transcript: string, customPrompt?: string): Promise<SummaryResponse> => {
    return api.post<SummaryResponse>("/ai/summarize", {
      transcript,
      custom_prompt: customPrompt,
    });
  },

  /**
   * Run real-time NLP analysis on classroom transcripts.
   */
  analyzeNLP: async (transcript: string): Promise<NLPAnalysis> => {
    return api.post<NLPAnalysis>("/ai/nlp", {
      transcript,
    });
  },

  /**
   * Execute academic research using Google Search grounding.
   */
  research: async (query: string): Promise<ResearchResponse> => {
    return api.post<ResearchResponse>("/ai/research", {
      query,
    });
  },

  /**
   * Generate comprehensive study notes for a given topic and subject.
   * AI orchestration (CrewAI / Gemini) runs exclusively in the FastAPI backend.
   */
  generateNotes: async (topic: string, subject: string): Promise<NotesResponse> => {
    return api.post<NotesResponse>("/ai/notes", {
      topic,
      subject,
    });
  },

  /**
   * Get all session data (transcript, summary, nlp) for a specific lecture session.
   */
  getSessionData: async (sessionId: string): Promise<any> => {
    return api.get<any>(`/lecture/sessions/${sessionId}`);
  },

  /**
   * Get transcript for a specific lecture session.
   */
  getSessionTranscript: async (sessionId: string): Promise<{ session_id: string; transcript: string; status: string }> => {
    return api.get<{ session_id: string; transcript: string; status: string }>(`/lecture/sessions/${sessionId}/transcript`);
  },

  /**
   * Get summary for a specific lecture session.
   */
  getSessionSummary: async (sessionId: string): Promise<{ session_id: string; summary: string; status: string }> => {
    return api.get<{ session_id: string; summary: string; status: string }>(`/lecture/sessions/${sessionId}/summary`);
  },

  /**
   * Get NLP insights for a specific lecture session.
   */
  getSessionNLP: async (sessionId: string): Promise<NLPAnalysis & { session_id: string; status: string }> => {
    return api.get<NLPAnalysis & { session_id: string; status: string }>(`/lecture/sessions/${sessionId}/nlp`);
  },
};

