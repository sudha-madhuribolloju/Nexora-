import { api } from "./api";

export interface Student {
  id: string;
  user_id: string;
  roll_number?: string;
  grade_level?: string;
  enrollment_status?: string;
  guardian_name?: string;
  guardian_phone?: string;
  name?: string;
  email?: string;
  phone?: string;
  avatar?: string;
  joinedDate?: string;
  status?: string;
}

export interface StudentResponseWrapper {
  status: string;
  message: string;
  data: {
    students: Student[];
  };
}

export const studentService = {
  /**
   * List all students.
   */
  listStudents: async (skip: number = 0, limit: number = 100): Promise<StudentResponseWrapper> => {
    return api.get<StudentResponseWrapper>(`/students/?skip=${skip}&limit=${limit}`);
  },

  /**
   * Get student details by ID.
   */
  getStudent: async (studentId: string): Promise<any> => {
    return api.get<any>(`/students/${studentId}`);
  },

  /**
   * Create a new student entry.
   */
  createStudent: async (studentData: any): Promise<any> => {
    return api.post<any>("/students/", studentData);
  },

  /**
   * Update student details by ID.
   */
  updateStudent: async (studentId: string, studentData: any): Promise<any> => {
    return api.put<any>(`/students/${studentId}`, studentData);
  },

  /**
   * Delete student entry by ID.
   */
  deleteStudent: async (studentId: string): Promise<any> => {
    return api.del<any>(`/students/${studentId}`);
  },
};
export type { Student as StudentType };
