import { api } from "./api";

export interface ClassroomSession {
  id: string;
  course_id?: string;
  teacher_id?: string;
  title: string;
  scheduled_start?: string;
  scheduled_end?: string;
  status: "SCHEDULED" | "ACTIVE" | "COMPLETED";
}

export interface SessionListResponse {
  total: number;
  skip: number;
  limit: number;
  data: ClassroomSession[];
}

export interface VoiceProcessingResult {
  speaker: string;
  confidence: number;
  voicePrintId: string;
  clarityScore: string;
  noiseReducedTranscript: string;
}

export const classroomService = {
  /**
   * List all classroom sessions.
   */
  listSessions: async (skip: number = 0, limit: number = 20, status?: string): Promise<SessionListResponse> => {
    let path = `/sessions/?skip=${skip}&limit=${limit}`;
    if (status) {
      path += `&status=${status}`;
    }
    return api.get<SessionListResponse>(path);
  },

  /**
   * Get specific classroom session by ID.
   */
  getSession: async (sessionId: string): Promise<ClassroomSession> => {
    return api.get<ClassroomSession>(`/sessions/${sessionId}`);
  },

  /**
   * Create a new classroom session.
   */
  createSession: async (sessionData: {
    title: string;
    course_id?: string;
    scheduled_start?: string;
    scheduled_end?: string;
  }): Promise<ClassroomSession> => {
    return api.post<ClassroomSession>("/sessions/", sessionData);
  },

  /**
   * Start a scheduled session.
   */
  startSession: async (sessionId: string): Promise<ClassroomSession> => {
    return api.post<ClassroomSession>(`/sessions/${sessionId}/start`, {});
  },

  /**
   * End an active session.
   */
  endSession: async (sessionId: string): Promise<ClassroomSession> => {
    return api.post<ClassroomSession>(`/sessions/${sessionId}/end`, {});
  },

  /**
   * Process a teacher's recorded audio input to recognize their voiceprint and return transcription.
   * Calls Whisper / Vocal biometrics via FastAPI backend.
   */
  processVoice: async (speakerName: string): Promise<VoiceProcessingResult> => {
    return api.post<VoiceProcessingResult>("/ai/voice-processing", {
      speakerName,
    });
  },

  /**
   * Send a chat message in the live classroom feed.
   */
  sendChatMessage: async (sessionId: string, content: string): Promise<any> => {
    return api.post<any>(`/sessions/${sessionId}/messages`, {
      content,
    });
  },
};
