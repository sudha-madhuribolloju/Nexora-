import React, { useState } from "react";
import {
  Users,
  BookOpen,
  Search,
  Plus,
  Mail,
  Phone,
  BookMarked,
  GraduationCap,
  FolderPlus,
  Compass,
  FileText,
  Clock,
  Filter,
  UserCheck,
  X,
  Database,
  Building
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface UserProfile {
  id: string;
  name: string;
  role: "Student" | "Teacher" | "Principal" | "Support";
  email: string;
  phone: string;
  status: "Active" | "Pending" | "Suspended";
  avatar: string;
  joinedDate: string;
}

interface Course {
  id: string;
  code: string;
  title: string;
  department: string;
  instructor: string;
  subjectsCount: number;
  studentsCount: number;
}

export default function ModuleCampusDirectory() {
  const [activeSubTab, setActiveSubTab] = useState<"users" | "courses" | "students" | "teachers" | "kb">("users");
  const [searchQuery, setSearchQuery] = useState("");
  const [showInviteModal, setShowInviteModal] = useState(false);

  // Users Database
  const [users, setUsers] = useState<UserProfile[]>([
    { id: "u-1", name: "Prof. Sudha Madhuri", role: "Teacher", email: "sudha.madhuri@stmary.edu", phone: "+1 (555) 019-2231", status: "Active", avatar: "SB", joinedDate: "2024-09-01" },
    { id: "u-2", name: "Alice Vance", role: "Student", email: "alice.vance@stmary.edu", phone: "+1 (555) 012-9988", status: "Active", avatar: "AV", joinedDate: "2025-01-15" },
    { id: "u-3", name: "Bob Miller", role: "Student", email: "bob.miller@stmary.edu", phone: "+1 (555) 017-4455", status: "Active", avatar: "BM", joinedDate: "2025-01-15" },
    { id: "u-4", name: "Dr. Sarah Jenkins", role: "Teacher", email: "sarah.jenkins@stmary.edu", phone: "+1 (555) 013-1122", status: "Active", avatar: "SJ", joinedDate: "2023-08-20" },
    { id: "u-5", name: "Dean Thomas Moore", role: "Principal", email: "thomas.moore@stmary.edu", phone: "+1 (555) 011-0011", status: "Active", avatar: "TM", joinedDate: "2022-06-10" },
    { id: "u-6", name: "Charlie Diaz", role: "Student", email: "charlie.diaz@stmary.edu", phone: "+1 (555) 018-8833", status: "Pending", avatar: "CD", joinedDate: "2026-06-01" }
  ]);

  // Courses Database
  const [courses, setCourses] = useState<Course[]>([
    { id: "c-1", code: "PHY-401", title: "Advanced Quantum Superposition", department: "Physics", instructor: "Prof. Sudha Madhuri", subjectsCount: 4, studentsCount: 24 },
    { id: "c-2", code: "BIO-305", title: "Genetics Lab & CRISPR Splicing", department: "Biology", instructor: "Dr. Sarah Jenkins", subjectsCount: 3, studentsCount: 18 },
    { id: "c-3", code: "ECO-201", title: "Microeconomics Equilibrium Models", department: "Economics", instructor: "Prof. Arthur Pendelton", subjectsCount: 5, studentsCount: 40 },
    { id: "c-4", code: "CS-502", title: "Algorithmic Complexity & Graph Systems", department: "Computer Science", instructor: "Dr. Alan Turing", subjectsCount: 6, studentsCount: 32 }
  ]);

  // Form states for Invite User
  const [inviteName, setInviteName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"Student" | "Teacher" | "Principal" | "Support">("Student");

  const handleInviteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteName.trim() || !inviteEmail.trim()) return;

    const newUser: UserProfile = {
      id: "u-" + Date.now(),
      name: inviteName,
      email: inviteEmail,
      role: inviteRole,
      phone: "+1 (555) 010-0000",
      status: "Pending",
      avatar: inviteName.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2),
      joinedDate: new Date().toISOString().split("T")[0]
    };

    setUsers([newUser, ...users]);
    setInviteName("");
    setInviteEmail("");
    setShowInviteModal(false);
  };

  const deleteUser = (id: string) => {
    setUsers(prev => prev.filter(u => u.id !== id));
  };

  const toggleUserStatus = (id: string) => {
    setUsers(prev => prev.map(u => {
      if (u.id === id) {
        return {
          ...u,
          status: u.status === "Active" ? "Suspended" : "Active"
        };
      }
      return u;
    }));
  };

  return (
    <div className="space-y-6">

      {/* Tab Selectors */}
      <div className="flex overflow-x-auto border-b border-gray-100 no-scrollbar">
        <button
          onClick={() => setActiveSubTab("users")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 shrink-0 ${activeSubTab === "users" ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500"
            }`}
        >
          <Users className="w-4 h-4" /> User Management
        </button>
        <button
          onClick={() => setActiveSubTab("courses")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 shrink-0 ${activeSubTab === "courses" ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500"
            }`}
        >
          <BookOpen className="w-4 h-4" /> Courses &amp; Subjects
        </button>
        <button
          onClick={() => setActiveSubTab("students")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 shrink-0 ${activeSubTab === "students" ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500"
            }`}
        >
          <GraduationCap className="w-4 h-4" /> Student Directory
        </button>
        <button
          onClick={() => setActiveSubTab("teachers")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 shrink-0 ${activeSubTab === "teachers" ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500"
            }`}
        >
          <UserCheck className="w-4 h-4" /> Teacher Directory
        </button>
        <button
          onClick={() => setActiveSubTab("kb")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 shrink-0 ${activeSubTab === "kb" ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500"
            }`}
        >
          <Compass className="w-4 h-4" /> AI Knowledge Base
        </button>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 w-4 h-4 text-gray-400 top-3.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search directory logs..."
            className="w-full pl-10 pr-4 py-3 text-xs rounded-xl border border-gray-100 bg-white focus:outline-none focus:border-blue-600"
          />
        </div>

        {activeSubTab === "users" && (
          <button
            onClick={() => setShowInviteModal(true)}
            className="px-4 py-3 rounded-xl bg-blue-600 text-white font-semibold text-xs flex items-center justify-center gap-2 hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" /> Invite New Campus User
          </button>
        )}
      </div>

      <AnimatePresence mode="wait">

        {/* --- USER MANAGEMENT --- */}
        {activeSubTab === "users" && (
          <motion.div key="users" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-gray-50 text-gray-400 font-mono font-bold uppercase border-b border-gray-100">
                      <th className="p-4">User</th>
                      <th className="p-4">Role</th>
                      <th className="p-4">Email Address</th>
                      <th className="p-4">Joined Date</th>
                      <th className="p-4">Status</th>
                      <th className="p-4 text-right">Administrative Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {users
                      .filter(u => u.name.toLowerCase().includes(searchQuery.toLowerCase()) || u.email.toLowerCase().includes(searchQuery.toLowerCase()))
                      .map((u) => (
                        <tr key={u.id} className="hover:bg-gray-50/40">
                          <td className="p-4 flex items-center gap-3 font-semibold text-gray-900">
                            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-[10px]">
                              {u.avatar}
                            </div>
                            <span>{u.name}</span>
                          </td>
                          <td className="p-4 font-semibold text-gray-600">{u.role}</td>
                          <td className="p-4 text-gray-500 font-mono">{u.email}</td>
                          <td className="p-4 text-gray-400">{u.joinedDate}</td>
                          <td className="p-4">
                            <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold ${u.status === "Active" ? "bg-emerald-50 text-emerald-600" :
                              u.status === "Pending" ? "bg-amber-50 text-amber-600" : "bg-red-50 text-red-600"
                              }`}>
                              {u.status}
                            </span>
                          </td>
                          <td className="p-4 text-right space-x-1.5">
                            <button
                              onClick={() => toggleUserStatus(u.id)}
                              className="px-2 py-1 border border-gray-200 hover:bg-gray-50 rounded-lg text-[10px] font-semibold text-gray-600"
                            >
                              Toggle Lock
                            </button>
                            <button
                              onClick={() => deleteUser(u.id)}
                              className="px-2 py-1 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg text-[10px] font-semibold"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>
        )}

        {/* --- COURSES --- */}
        {activeSubTab === "courses" && (
          <motion.div key="courses" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {courses
              .filter(c => c.title.toLowerCase().includes(searchQuery.toLowerCase()) || c.code.toLowerCase().includes(searchQuery.toLowerCase()))
              .map((c) => (
                <div key={c.id} className="bento-card bg-white p-6 space-y-4">
                  <div className="flex items-center justify-between border-b border-gray-50 pb-3">
                    <div>
                      <span className="text-[10px] uppercase font-mono text-blue-600 font-bold">{c.code}</span>
                      <h4 className="font-display font-semibold text-gray-900 text-base mt-1">{c.title}</h4>
                    </div>
                    <span className="text-xs text-gray-400 font-semibold">{c.department}</span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <div>
                      <span className="block text-[10px] text-gray-400 uppercase font-mono font-bold">INSTRUCTOR</span>
                      <span className="font-semibold text-gray-800">{c.instructor}</span>
                    </div>
                    <div className="text-right">
                      <span className="block text-[10px] text-gray-400 uppercase font-mono font-bold">ROSTER</span>
                      <span className="font-semibold text-gray-800">{c.studentsCount} Students • {c.subjectsCount} Subjects</span>
                    </div>
                  </div>
                </div>
              ))}
          </motion.div>
        )}

        {/* --- STUDENTS DIRECTORY --- */}
        {activeSubTab === "students" && (
          <motion.div key="students" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {users
              .filter(u => u.role === "Student" && u.name.toLowerCase().includes(searchQuery.toLowerCase()))
              .map((u) => (
                <div key={u.id} className="bento-card bg-white p-5 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 font-bold flex items-center justify-center">
                      {u.avatar}
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 text-sm">{u.name}</h4>
                      <p className="text-[10px] text-gray-400 font-mono">Roll: #NEX-2026-00{u.id.split("-")[1] || "34"}</p>
                    </div>
                  </div>

                  <div className="border-t border-gray-50 pt-3 mt-3 text-xs space-y-1.5 text-gray-500">
                    <div className="flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-gray-400" />
                      <span className="font-mono">{u.email}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-gray-400" />
                      <span>{u.phone}</span>
                    </div>
                  </div>
                </div>
              ))}
          </motion.div>
        )}

        {/* --- TEACHERS DIRECTORY --- */}
        {activeSubTab === "teachers" && (
          <motion.div key="teachers" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {users
              .filter(u => u.role === "Teacher" && u.name.toLowerCase().includes(searchQuery.toLowerCase()))
              .map((u) => (
                <div key={u.id} className="bento-card bg-white p-6 space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 font-bold flex items-center justify-center text-sm shadow-sm">
                      {u.avatar}
                    </div>
                    <div>
                      <h4 className="font-display font-semibold text-gray-900 text-base">{u.name}</h4>
                      <p className="text-xs text-purple-600 font-semibold">Course Instructor &amp; Lead Researcher</p>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 leading-relaxed">
                    Lead supervisor overseeing the local experimental physics &amp; biology labs connected to the Google Gemini cloud servers.
                  </p>

                  <div className="border-t border-gray-50 pt-4 mt-4 grid grid-cols-2 gap-2 text-xs text-gray-500">
                    <div className="flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-gray-400" />
                      <span className="font-mono truncate">{u.email}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-gray-400" />
                      <span>{u.phone}</span>
                    </div>
                  </div>
                </div>
              ))}
          </motion.div>
        )}

        {/* --- KNOWLEDGE BASE --- */}
        {activeSubTab === "kb" && (
          <motion.div key="kb" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
            <div className="bento-card p-6 bg-white space-y-4 border-l-4 border-l-blue-600">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-blue-600" />
                <h4 className="font-semibold text-gray-900 text-sm">Active Vector Database Indexes</h4>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">
                NEXORA automatically segments text contents from classroom recordings, notes, and uploaded files into 512-dimension vector embeddings. These are stored locally to allow the AI Chat companion to answer grounded textbook queries with precise citations.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bento-card p-5 bg-white space-y-3">
                <span className="text-[10px] font-mono uppercase text-gray-400 font-bold">WIKI MANUAL</span>
                <h4 className="font-semibold text-gray-900 text-sm">How Quantum Computing Superposition Works</h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Unlike traditional bits that store static 0s and 1s, quantum qubits employ state vectors allowing simultaneous superposition calculated as linear combinations.
                </p>
              </div>

              <div className="bento-card p-5 bg-white space-y-3">
                <span className="text-[10px] font-mono uppercase text-gray-400 font-bold">BIOLOGY LAB NOTES</span>
                <h4 className="font-semibold text-gray-900 text-sm">Introduction to CRISPR-Cas9 Cell Edits</h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  CRISPR uses targeted synthetic guide RNAs that latch precisely onto complementary genomic segments. The Cas9 endonuclease acts as a biological molecular scissors to cut.
                </p>
              </div>
            </div>
          </motion.div>
        )}

      </AnimatePresence>

      {/* Invite Modal Frame */}
      <AnimatePresence>
        {showInviteModal && (
          <>
            <div className="fixed inset-0 bg-black/40 z-40" onClick={() => setShowInviteModal(false)}></div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-x-6 top-20 max-w-md mx-auto bg-white border border-gray-100 rounded-3xl p-6 z-50 shadow-2xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-gray-50 pb-3">
                <span className="font-display font-semibold text-sm text-gray-900">Invite Campus Member</span>
                <button onClick={() => setShowInviteModal(false)} className="p-1 rounded-lg hover:bg-gray-50">
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>

              <form onSubmit={handleInviteSubmit} className="space-y-4 text-xs">
                <div className="space-y-1">
                  <label className="font-semibold text-gray-600">Full Name</label>
                  <input
                    type="text"
                    value={inviteName}
                    onChange={(e) => setInviteName(e.target.value)}
                    placeholder="e.g. Professor John Doe"
                    className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-gray-600">Email Address</label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="e.g. john@university.edu"
                    className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-gray-600">Role Perspective Assignment</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as any)}
                    className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none font-medium bg-white"
                  >
                    <option value="Student">Student Perspective</option>
                    <option value="Teacher">Teacher Perspective</option>
                    <option value="Principal">Principal Perspective</option>
                    <option value="Support">Support Engineer</option>
                  </select>
                </div>

                <button type="submit" className="w-full py-3 bg-blue-600 text-white font-bold rounded-xl text-xs hover:bg-blue-700 transition-colors">
                  Send Campus Invite
                </button>
              </form>
            </motion.div>
          </>
        )}
      </AnimatePresence>

    </div>
  );
}
