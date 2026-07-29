/**
 * NEXORA Types & Interfaces
 */

export type UserRole = 
  | "Super Admin" 
  | "Institute Admin" 
  | "Principal" 
  | "Teacher" 
  | "Student" 
  | "Parent" 
  | "Support Engineer";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctAnswer: string;
  explanation: string;
}

export interface Citation {
  title: string;
  uri: string;
}

export interface AcademicResearchResult {
  findings: string;
  citations: Citation[];
}

export interface NLPAnalysis {
  topics: string[];
  sentiment: string;
  definitions: { term: string; explanation: string }[];
  actionItems: string[];
}

export interface LiveActivity {
  id: string;
  time: string;
  event: string;
  type: "info" | "success" | "warning" | "danger";
  user: string;
}

export interface StudentPerformance {
  id: string;
  name: string;
  attendance: number;
  grade: string;
  engagement: number;
  recentQuizScore: number;
  riskStatus?: "Optimal" | "Moderate Risk" | "High Risk";
  avatar?: string;
}



export interface RecordingSummary {
  summary?: string;
  key_topics?: string[];
  important_questions?: string[];
  homework_generated?: string[];
  keywords?: string[];
}

export interface Recording {
  id: string;
  lecture_id?: string | null;
  teacher_id?: string | null;
  class_id?: string | null;
  section_id?: string | null;
  subject_id?: string | null;
  filename: string;
  storage_path: string;
  file_size: number;
  duration: number;
  recording_status: "processing" | "ready" | "failed" | "deleted";
  transcript?: string | null;
  summary?: RecordingSummary | null;
  thumbnail?: string | null;
  is_deleted?: boolean;
  start_time?: string | null;
  end_time?: string | null;
  created_at?: string | null;
  teacher_name?: string | null;
  subject_name?: string | null;
  class_name?: string | null;
}

export interface RecordingAnalytics {
  total_recordings: number;
  total_duration_seconds: number;
  total_duration_hours: number;
  total_storage_bytes: number;
  total_storage_mb: number;
  top_teachers: { name: string; count: number }[];
  latest_recordings: Recording[];
}


export interface WhiteboardElement {
  id: string;
  type: "text" | "rect" | "circle" | "line";
  x: number;
  y: number;
  width?: number;
  height?: number;
  text?: string;
  color: string;
}
