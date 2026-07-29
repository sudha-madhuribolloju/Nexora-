import React, { useState } from "react";
import {
  FileText,
  Calendar,
  CheckCircle,
  Clock,
  Plus,
  Search,
  Download,
  Award,
  Percent,
  QrCode,
  Filter,
  Upload,
  AlertCircle,
  FileDown,
  UserCheck,
  TrendingUp,
  X,
  BookOpen
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface Assignment {
  id: string;
  title: string;
  subject: string;
  dueDate: string;
  status: "Pending" | "Submitted" | "Graded";
  grade?: string;
  points: number;
}

interface AttendanceRecord {
  id: string;
  studentName: string;
  rollNumber: string;
  avatar: string;
  status: "Present" | "Absent" | "Late";
  lastCheckIn: string;
}

export default function ModuleAcademicProgress() {
  const [activeSubTab, setActiveSubTab] = useState<"assignments" | "attendance" | "reports">("assignments");
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // --- Assignments State ---
  const [assignments, setAssignments] = useState<Assignment[]>([
    { id: "asg-1", title: "Schrödinger Cat Probability Matrices", subject: "Quantum Physics", dueDate: "2026-06-30", status: "Pending", points: 100 },
    { id: "asg-2", title: "CRISPR-Cas9 Base Pairing Exercises", subject: "Genetics & Biology", dueDate: "2026-06-25", status: "Submitted", points: 50 },
    { id: "asg-3", title: "Keynesian VS Classical Equilibrium Essay", subject: "Macroeconomics", dueDate: "2026-06-18", status: "Graded", grade: "A+", points: 150 },
    { id: "asg-4", title: "Algorithmic Complexity & Big-O Proofs", subject: "Computer Science", dueDate: "2026-07-05", status: "Pending", points: 100 }
  ]);

  // Form State
  const [newTitle, setNewTitle] = useState("");
  const [newSubject, setNewSubject] = useState("Quantum Physics");
  const [newDueDate, setNewDueDate] = useState("2026-07-01");
  const [newPoints, setNewPoints] = useState(100);

  // --- Attendance State ---
  const [attendance, setAttendance] = useState<AttendanceRecord[]>([
    { id: "att-1", studentName: "Alice Vance", rollNumber: "NEX-2026-04", avatar: "AV", status: "Present", lastCheckIn: "08:52 AM" },
    { id: "att-2", studentName: "Bob Miller", rollNumber: "NEX-2026-11", avatar: "BM", status: "Late", lastCheckIn: "09:12 AM" },
    { id: "att-3", studentName: "Charlie Diaz", rollNumber: "NEX-2026-18", avatar: "CD", status: "Present", lastCheckIn: "08:45 AM" },
    { id: "att-4", studentName: "Diana Prince", rollNumber: "NEX-2026-25", avatar: "DP", status: "Absent", lastCheckIn: "—" },
    { id: "att-5", studentName: "Evan Wright", rollNumber: "NEX-2026-32", avatar: "EW", status: "Present", lastCheckIn: "08:58 AM" }
  ]);

  // Handle Add Assignment
  const handleAddAssignment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const newAsg: Assignment = {
      id: "asg-" + Date.now(),
      title: newTitle,
      subject: newSubject,
      dueDate: newDueDate,
      status: "Pending",
      points: Number(newPoints)
    };

    setAssignments([newAsg, ...assignments]);
    setNewTitle("");
    setShowAddModal(false);
  };

  const toggleAttendance = (id: string, nextStatus: "Present" | "Absent" | "Late") => {
    setAttendance(prev => prev.map(a => {
      if (a.id === id) {
        return {
          ...a,
          status: nextStatus,
          lastCheckIn: nextStatus === "Present" ? "08:55 AM" : nextStatus === "Late" ? "09:15 AM" : "—"
        };
      }
      return a;
    }));
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-6">

      {/* Sub-tab navigation selection */}
      <div className="flex border-b border-gray-100">
        <button
          onClick={() => setActiveSubTab("assignments")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 ${activeSubTab === "assignments"
            ? "border-blue-600 text-blue-600 font-bold"
            : "border-transparent text-gray-500 hover:text-gray-900"
            }`}
        >
          <BookOpen className="w-4 h-4" /> Assignments Manager
        </button>
        <button
          onClick={() => setActiveSubTab("attendance")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 ${activeSubTab === "attendance"
            ? "border-blue-600 text-blue-600 font-bold"
            : "border-transparent text-gray-500 hover:text-gray-900"
            }`}
        >
          <UserCheck className="w-4 h-4" /> Attendance Tracker
        </button>
        <button
          onClick={() => setActiveSubTab("reports")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 ${activeSubTab === "reports"
            ? "border-blue-600 text-blue-600 font-bold"
            : "border-transparent text-gray-500 hover:text-gray-900"
            }`}
        >
          <Award className="w-4 h-4" /> Report Cards &amp; Transcripts
        </button>
      </div>

      {/* Dynamic Content view switcher */}
      <AnimatePresence mode="wait">

        {/* --- ASSIGNMENTS VIEW --- */}
        {activeSubTab === "assignments" && (
          <motion.div
            key="assignments"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3.5 w-4 h-4 text-gray-400 top-3.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search homework &amp; exam submissions..."
                  className="w-full pl-10 pr-4 py-3 text-xs rounded-xl border border-gray-100 focus:outline-none focus:border-blue-600 bg-white"
                />
              </div>

              <button
                onClick={() => setShowAddModal(true)}
                className="px-4 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-md transition-all self-stretch sm:self-auto"
              >
                <Plus className="w-4 h-4" /> Assign New Lecture Task
              </button>
            </div>

            {/* Assignments Bento Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {assignments
                .filter(asg => asg.title.toLowerCase().includes(searchQuery.toLowerCase()) || asg.subject.toLowerCase().includes(searchQuery.toLowerCase()))
                .map((asg) => (
                  <div key={asg.id} className="bento-card bg-white p-5 flex flex-col justify-between min-h-[190px]">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-mono tracking-wider font-bold text-gray-400">{asg.subject}</span>
                        <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold ${asg.status === "Graded" ? "bg-emerald-50 text-emerald-600" :
                          asg.status === "Submitted" ? "bg-blue-50 text-blue-600" : "bg-amber-50 text-amber-600"
                          }`}>
                          {asg.status}
                        </span>
                      </div>
                      <h4 className="font-display font-semibold text-gray-900 text-sm line-clamp-2">{asg.title}</h4>
                    </div>

                    <div className="border-t border-gray-50 pt-4 mt-4 flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-gray-400" />
                        <span>Due: {asg.dueDate}</span>
                      </div>
                      <div className="font-mono text-[10px] font-bold">
                        {asg.status === "Graded" ? (
                          <span className="text-emerald-600">Grade: {asg.grade} ({asg.points}pts)</span>
                        ) : (
                          <span>{asg.points} Max Points</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
            </div>

            {/* File Submission Area mock for student */}
            <div className="p-8 rounded-3xl bg-white border border-gray-100/80 space-y-5 text-center max-w-2xl mx-auto mt-6">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                <Upload className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h4 className="font-display font-semibold text-gray-900 text-sm">Submit Completed Homework PDF</h4>
                <p className="text-gray-400 text-xs">Drag and drop file, or select files directly to upload to teacher</p>
              </div>

              {/* Drag Area */}
              <div
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                className={`p-10 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center gap-2 transition-all ${dragActive ? "border-blue-600 bg-blue-50/40" : "border-gray-200 hover:border-blue-300"
                  }`}
              >
                {selectedFile ? (
                  <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600">
                    <CheckCircle className="w-4 h-4" /> Selected File: {selectedFile.name}
                  </div>
                ) : (
                  <span className="text-xs text-gray-400 font-medium">Drop PDF files here</span>
                )}
              </div>

              <button className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-colors">
                Upload to Sandbox Server
              </button>
            </div>
          </motion.div>
        )}

        {/* --- ATTENDANCE TRACKER --- */}
        {activeSubTab === "attendance" && (
          <motion.div
            key="attendance"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Quick Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="bento-card p-5 bg-white flex flex-col justify-between">
                <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 font-semibold">Today's Presence</span>
                <span className="font-display text-2xl font-bold text-blue-600 mt-2">94.2%</span>
              </div>
              <div className="bento-card p-5 bg-white flex flex-col justify-between">
                <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 font-semibold">Excused Absences</span>
                <span className="font-display text-2xl font-bold text-amber-600 mt-2">1 Student</span>
              </div>
              <div className="bento-card p-5 bg-white flex flex-col justify-between">
                <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 font-semibold">QR Check-in Portal</span>
                <div className="flex items-center gap-1.5 text-blue-600 hover:underline cursor-pointer font-bold text-xs mt-2">
                  <QrCode className="w-4 h-4" /> Show Classroom QR Code
                </div>
              </div>
            </div>

            {/* Attendance Roster Table */}
            <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm">
              <div className="p-5 border-b border-gray-50 flex items-center justify-between">
                <span className="font-display font-semibold text-sm text-gray-900">Student Roll Call</span>
                <span className="text-[10px] font-mono font-bold text-gray-400 uppercase">Interactive Sheet</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-gray-50/50 text-gray-400 font-mono font-bold uppercase border-b border-gray-100">
                      <th className="p-4">Student</th>
                      <th className="p-4">Roll Number</th>
                      <th className="p-4">Daily Status</th>
                      <th className="p-4">Check-In Time</th>
                      <th className="p-4 text-right">Quick Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {attendance.map((rec) => (
                      <tr key={rec.id} className="hover:bg-gray-50/40 transition-colors">
                        <td className="p-4 flex items-center gap-3 font-semibold text-gray-900">
                          <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-[10px]">
                            {rec.avatar}
                          </div>
                          <span>{rec.studentName}</span>
                        </td>
                        <td className="p-4 text-gray-500 font-mono">{rec.rollNumber}</td>
                        <td className="p-4">
                          <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold ${rec.status === "Present" ? "bg-emerald-50 text-emerald-600" :
                            rec.status === "Late" ? "bg-amber-50 text-amber-600" : "bg-red-50 text-red-600"
                            }`}>
                            {rec.status}
                          </span>
                        </td>
                        <td className="p-4 text-gray-400 font-medium">{rec.lastCheckIn}</td>
                        <td className="p-4 text-right space-x-1.5">
                          <button
                            onClick={() => toggleAttendance(rec.id, "Present")}
                            className="px-2.5 py-1 bg-emerald-50 text-emerald-600 border border-transparent hover:border-emerald-200 rounded-lg text-[10px] font-semibold"
                          >
                            Present
                          </button>
                          <button
                            onClick={() => toggleAttendance(rec.id, "Late")}
                            className="px-2.5 py-1 bg-amber-50 text-amber-600 border border-transparent hover:border-amber-200 rounded-lg text-[10px] font-semibold"
                          >
                            Late
                          </button>
                          <button
                            onClick={() => toggleAttendance(rec.id, "Absent")}
                            className="px-2.5 py-1 bg-red-50 text-red-600 border border-transparent hover:border-red-200 rounded-lg text-[10px] font-semibold"
                          >
                            Absent
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

        {/* --- REPORTS & TRANSCRIPTS --- */}
        {activeSubTab === "reports" && (
          <motion.div
            key="reports"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            <div className="bento-card p-6 bg-white space-y-4">
              <div className="flex items-center justify-between border-b border-gray-50 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
                    <Award className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 text-sm">Official Academic Transcript</h3>
                    <p className="text-[10px] text-gray-400">Student ID: #NEX-2026-9011 • Spring Term 2026</p>
                  </div>
                </div>

                <button className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-semibold hover:bg-blue-700 transition-colors flex items-center gap-1.5">
                  <FileDown className="w-4 h-4" /> Export Signed PDF
                </button>
              </div>

              <div className="space-y-4 pt-2">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                    <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 block font-semibold">Cumulative GPA</span>
                    <span className="text-xl font-bold text-gray-900 mt-1 block">3.94 / 4.0</span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                    <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 block font-semibold">Rank percentile</span>
                    <span className="text-xl font-bold text-gray-900 mt-1 block">Top 2.5%</span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                    <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 block font-semibold">Completed Credits</span>
                    <span className="text-xl font-bold text-gray-900 mt-1 block">42 Units</span>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                    <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 block font-semibold">AI Assistant Peerage</span>
                    <span className="text-xl font-bold text-blue-600 mt-1 block">Elite Status</span>
                  </div>
                </div>

                <div className="bg-gray-50/50 p-4 rounded-2xl border border-gray-100 text-xs text-gray-600 leading-relaxed">
                  <span className="font-semibold text-gray-900 block mb-1">Teacher Counselor Remarks:</span>
                  "Prof. Sudha Madhuri has demonstrated outstanding intellectual rigor across advanced theoretical mechanics and genetics labs. His homework matrices showcase pristine adherence to scientific models."
                </div>
              </div>
            </div>
          </motion.div>
        )}

      </AnimatePresence>

      {/* Add Assignment Modal Frame popup simulation */}
      <AnimatePresence>
        {showAddModal && (
          <>
            <div className="fixed inset-0 bg-black/40 z-40" onClick={() => setShowAddModal(false)}></div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="fixed inset-x-6 top-20 max-w-md mx-auto bg-white border border-gray-100 rounded-3xl p-6 z-50 shadow-2xl space-y-4"
            >
              <div className="flex items-center justify-between border-b border-gray-50 pb-3">
                <span className="font-display font-semibold text-sm text-gray-900">Add New Lesson Homework</span>
                <button onClick={() => setShowAddModal(false)} className="p-1 rounded-lg hover:bg-gray-50">
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>

              <form onSubmit={handleAddAssignment} className="space-y-3.5 text-xs">
                <div className="space-y-1">
                  <label className="font-semibold text-gray-600">Task Title</label>
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. Wave Function Integration Proofs"
                    className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-gray-600">Assigned Course / Subject</label>
                  <select
                    value={newSubject}
                    onChange={(e) => setNewSubject(e.target.value)}
                    className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600 font-medium bg-white"
                  >
                    <option value="Quantum Physics">Quantum Physics</option>
                    <option value="Genetics & Biology">Genetics &amp; Biology</option>
                    <option value="Macroeconomics">Macroeconomics</option>
                    <option value="Computer Science">Computer Science</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="font-semibold text-gray-600">Due Date</label>
                    <input
                      type="date"
                      value={newDueDate}
                      onChange={(e) => setNewDueDate(e.target.value)}
                      className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-gray-600">Total Points</label>
                    <input
                      type="number"
                      value={newPoints}
                      onChange={(e) => setNewPoints(Number(e.target.value))}
                      className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none"
                    />
                  </div>
                </div>

                <button type="submit" className="w-full py-3 bg-blue-600 text-white font-bold rounded-xl text-xs hover:bg-blue-700 transition-colors">
                  Issue Assignment
                </button>
              </form>
            </motion.div>
          </>
        )}
      </AnimatePresence>

    </div>
  );
}
