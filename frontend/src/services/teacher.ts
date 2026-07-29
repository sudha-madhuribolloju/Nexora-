import { api } from "./api";

export interface Teacher {
  id: string;
  user_id: string;
  employee_id?: string;
  department?: string;
  qualification?: string;
  name?: string;
  email?: string;
  phone?: string;
  avatar?: string;
  joinedDate?: string;
  status?: string;
}

export interface TeacherResponseWrapper {
  status: string;
  message: string;
  data: {
    teachers: Teacher[];
  };
}

export const teacherService = {
  /**
   * List all teachers.
   */
  listTeachers: async (skip: number = 0, limit: number = 100): Promise<TeacherResponseWrapper> => {
    return api.get<TeacherResponseWrapper>(`/teachers/?skip=${skip}&limit=${limit}`);
  },

  /**
   * Get teacher details by ID.
   */
  getTeacher: async (teacherId: string): Promise<any> => {
    return api.get<any>(`/teachers/${teacherId}`);
  },

  /**
   * Create a new teacher entry.
   */
  createTeacher: async (teacherData: any): Promise<any> => {
    return api.post<any>("/teachers/", teacherData);
  },

  /**
   * Update teacher details by ID.
   */
  updateTeacher: async (teacherId: string, teacherData: any): Promise<any> => {
    return api.put<any>(`/teachers/${teacherId}`, teacherData);
  },

  /**
   * Delete teacher entry by ID.
   */
  deleteTeacher: async (teacherId: string): Promise<any> => {
    return api.del<any>(`/teachers/${teacherId}`);
  },
};
export type { Teacher as TeacherType };
