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
   * Calls Whisper / Vocal biometrics via FastAPI backend with optional classroom_session_id link.
   */
  processVoice: async (speakerName?: string, classroomSessionId?: string, audioBlob?: Blob): Promise<VoiceProcessingResult> => {
    if (audioBlob && audioBlob.size > 0) {
      const formData = new FormData();
      formData.append("file", audioBlob, "voice_recording.webm");
      if (speakerName) {
        formData.append("speakerName", speakerName);
        formData.append("speaker", speakerName);
      }
      if (classroomSessionId) {
        formData.append("classroom_session_id", classroomSessionId);
      }
      return api.postForm<VoiceProcessingResult>("/ai/voice-processing", formData);
    }

    return api.post<VoiceProcessingResult>("/ai/voice-processing", {
      speakerName: speakerName || "Instructor",
      speaker: speakerName || "Instructor",
      classroom_session_id: classroomSessionId,
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
