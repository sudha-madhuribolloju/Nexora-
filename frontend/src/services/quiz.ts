import { api } from "./api";
import { QuizQuestion } from "../types";

export interface Quiz {
  id: string;
  title: string;
  description?: string;
  course_id?: string;
  max_attempts: number;
  pass_score?: number;
  status: "DRAFT" | "PUBLISHED" | "ARCHIVED";
}

export interface QuizListResponse {
  total: number;
  skip: number;
  limit: number;
  data: Quiz[];
}

export interface QuizAttemptResponse {
  id: string;
  quiz_id: string;
  student_id: string;
  score?: number;
  total_marks?: number;
  passed?: boolean;
  submitted_at?: string;
}

export interface Assignment {
  id: string;
  title: string;
  description?: string;
  course_id?: string;
  due_date?: string;
  max_marks: number;
}

export interface AssignmentListResponse {
  total: number;
  skip: number;
  limit: number;
  data: Assignment[];
}

export const quizService = {
  /**
   * List all quizzes.
   */
  listQuizzes: async (skip: number = 0, limit: number = 20): Promise<QuizListResponse> => {
    return api.get<QuizListResponse>(`/quizzes/?skip=${skip}&limit=${limit}`);
  },

  /**
   * Get specific quiz by ID.
   */
  getQuiz: async (quizId: string): Promise<Quiz> => {
    return api.get<Quiz>(`/quizzes/${quizId}`);
  },

  /**
   * Generate an interactive MCQ quiz via the FastAPI backend (which orchestrates CrewAI/Gemini).
   */
  generateQuiz: async (topic: string, difficulty: string, questionCount: number = 5): Promise<{ quiz: QuizQuestion[] }> => {
    return api.post<{ quiz: QuizQuestion[] }>("/quizzes/generate", {
      topic,
      difficulty,
      questionCount,
    });
  },

  /**
   * Submit student answers for a quiz attempt.
   */
  submitAttempt: async (quizId: string, attemptId: string, answers: Record<string, string>): Promise<QuizAttemptResponse> => {
    return api.put<QuizAttemptResponse>(`/quizzes/${quizId}/attempt/${attemptId}/submit`, {
      answers,
    });
  },

  /**
   * Start a new quiz attempt.
   */
  startAttempt: async (quizId: string): Promise<QuizAttemptResponse> => {
    return api.post<QuizAttemptResponse>(`/quizzes/${quizId}/attempt`, {});
  },

  /**
   * List all assignments.
   */
  listAssignments: async (skip: number = 0, limit: number = 20): Promise<AssignmentListResponse> => {
    return api.get<AssignmentListResponse>(`/assignments/?skip=${skip}&limit=${limit}`);
  },

  /**
   * Generate a structured academic homework assignment via backend AI orchestration.
   */
  generateAssignment: async (topic: string): Promise<{ reply: string }> => {
    return api.post<{ reply: string }>("/assignments/generate", {
      topic,
    });
  },
};
