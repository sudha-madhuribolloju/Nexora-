/**
 * Frontend Role-Based Access Control (RBAC) Constants and Utilities
 */

import { UserRole } from "../types";

export const ROLES = {
  SUPER_ADMIN: "Super Admin",
  INSTITUTE_ADMIN: "Institute Admin",
  PRINCIPAL: "Principal",
  TEACHER: "Teacher",
  STUDENT: "Student",
  PARENT: "Parent",
  SUPPORT_ENGINEER: "Support Engineer",
} as const;

/**
 * List of roles allowed to perform lecture control actions:
 * Start Lecture, Stop Lecture, Start Recording, Stop Recording.
 */
export const ALLOWED_LECTURE_CONTROL_ROLES: readonly string[] = [
  ROLES.TEACHER,
  ROLES.INSTITUTE_ADMIN,
  ROLES.SUPER_ADMIN,
  "teacher",
  "course instructor",
  "institute admin",
  "institute_admin",
  "school admin",
  "school_admin",
  "super admin",
  "super_admin",
];

/**
 * Reusable helper to check if a user role has permission to start/stop lectures and recordings.
 * Never trust frontend validation alone; backend enforces JWT authorization on all endpoints.
 */
export const canControlLecture = (role?: string | null): boolean => {
  if (!role) return false;
  const normalized = role.trim().toLowerCase();
  return ALLOWED_LECTURE_CONTROL_ROLES.some(
    (allowedRole) => allowedRole.toLowerCase() === normalized
  );
};

/**
 * Helper to check if user role can join live lectures.
 * Students, Teachers, Principals, Institute Admins, and Super Admins can join.
 */
export const canJoinLecture = (role?: string | null): boolean => {
  if (!role) return false;
  const normalized = role.trim().toLowerCase();
  // Parents may optional join if configured, default allow view/join for principal/student/teacher/admin
  return (
    normalized !== "guest"
  );
};

/**
 * Helper to check if user role can view lecture recordings.
 */
export const canViewRecording = (role?: string | null): boolean => {
  if (!role) return false;
  return true;
};
