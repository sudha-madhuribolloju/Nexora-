import { UserRole } from "../types";

export const SYSTEM_VERSION = "v2.4";

export const ROLES_LIST: UserRole[] = [
  "Student", 
  "Teacher", 
  "Principal", 
  "Parent", 
  "Super Admin", 
  "Institute Admin", 
  "Support Engineer"
];

export interface RoleStyle {
  label: string;
  bg: string;
  text: string;
  border: string;
}

export const ROLE_STYLES: Record<UserRole, RoleStyle> = {
  "Student": { label: "Student Agent Peer", bg: "bg-blue-50/70", text: "text-blue-600", border: "border-blue-100/80" },
  "Teacher": { label: "Course Instructor", bg: "bg-purple-50/70", text: "text-purple-600", border: "border-purple-100/80" },
  "Principal": { label: "Campus Director", bg: "bg-amber-50/70", text: "text-amber-600", border: "border-amber-100/80" },
  "Parent": { label: "Student Guardian", bg: "bg-pink-50/70", text: "text-pink-600", border: "border-pink-100/80" },
  "Super Admin": { label: "Global Systems", bg: "bg-rose-50/70", text: "text-rose-600", border: "border-rose-100/80" },
  "Institute Admin": { label: "College Administrator", bg: "bg-emerald-50/70", text: "text-emerald-600", border: "border-emerald-100/80" },
  "Support Engineer": { label: "DevOps & Infrastructure", bg: "bg-teal-50/70", text: "text-teal-600", border: "border-teal-100/80" },
};
