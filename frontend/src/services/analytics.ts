import { api } from "./api";

export interface OverviewStats {
  total_students: number;
  total_teachers: number;
  total_courses: number;
  total_sessions: number;
  total_assignments: number;
  total_quizzes: number;
}

export interface AttendanceStats {
  present_count: number;
  absent_count: number;
  late_count: number;
  excused_count: number;
  attendance_rate: number;
}

export interface PerformanceStats {
  average_grade: string;
  average_quiz_score: number;
  average_assignment_score: number;
  engagement_rate: number;
  completion_rate: number;
}

export interface CourseAnalyticItem {
  course_id: string;
  course_code: string;
  course_name: string;
  enrolled_students: number;
  average_attendance: number;
  completed_sessions: number;
}

export interface TeacherAnalyticItem {
  teacher_id: string;
  teacher_name: string;
  courses_count: number;
  sessions_count: number;
}

export const analyticsService = {
  /**
   * Get dashboard overview counters and stats.
   */
  getOverviewStats: async (): Promise<OverviewStats> => {
    return api.get<OverviewStats>("/analytics/overview");
  },

  /**
   * Get system-wide attendance breakdown.
   */
  getAttendance: async (): Promise<AttendanceStats> => {
    return api.get<AttendanceStats>("/analytics/attendance");
  },

  /**
   * Get student performance metrics (grades, quiz scores, engagement index).
   */
  getPerformance: async (): Promise<PerformanceStats> => {
    return api.get<PerformanceStats>("/analytics/performance");
  },

  /**
   * Get per-course stats and roster analysis.
   */
  getCourseAnalytics: async (): Promise<CourseAnalyticItem[]> => {
    return api.get<CourseAnalyticItem[]>("/analytics/courses");
  },

  /**
   * Get per-teacher performance statistics.
   */
  getTeacherAnalytics: async (): Promise<TeacherAnalyticItem[]> => {
    return api.get<TeacherAnalyticItem[]>("/analytics/teachers");
  },
};
