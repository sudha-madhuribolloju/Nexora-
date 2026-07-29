import React, { useState } from "react";
import { 
  LineChart, 
  Settings, 
  Users, 
  Clock, 
  TrendingUp, 
  ShieldCheck, 
  Cpu, 
  Database, 
  CheckCircle,
  AlertTriangle,
  FileText,
  UserCheck,
  MemoryStick,
  Save,
  Trash2
} from "lucide-react";
import { StudentPerformance, LiveActivity } from "../types";
import { motion } from "motion/react";

export default function ModuleAnalyticsPerformance() {
  const [activeSubTab, setActiveSubTab] = useState<"performance" | "timeline" | "memory">("performance");
  
  // Simulated State: API keys configuration
  const [geminiKeySet, setGeminiKeySet] = useState(true);
  const [pgvectorStatus, setPgvectorStatus] = useState("Connected");
  const [whisperKey, setWhisperKey] = useState("••••••••••••••••");
  const [isSaved, setIsSaved] = useState(false);

  // Student directory
  const students: StudentPerformance[] = [
    { id: "1", name: "Alex Mercer", attendance: 96, grade: "A", engagement: 95, recentQuizScore: 100, avatar: "AM" },
    { id: "2", name: "Elara Sterling", attendance: 92, grade: "B+", engagement: 88, recentQuizScore: 80, avatar: "ES" },
    { id: "3", name: "Jonathan Crane", attendance: 85, grade: "B", engagement: 74, recentQuizScore: 80, avatar: "JC" },
    { id: "4", name: "Mia Wong", attendance: 98, grade: "A+", engagement: 98, recentQuizScore: 100, avatar: "MW" },
    { id: "5", name: "Marcus Brody", attendance: 78, grade: "C+", engagement: 62, recentQuizScore: 60, avatar: "MB" }
  ];

  // Classroom events timeline
  const timeline: LiveActivity[] = [
    { id: "1", time: "09:00 AM", event: "Classroom transcription started (Acoustic Noise Floor: -52dB)", type: "info", user: "Dr. Sarah Jenkins" },
    { id: "2", time: "09:12 AM", event: "NEXORA detected Topic focus: 'Quantum Superposition'", type: "success", user: "NEXORA Agent" },
    { id: "3", time: "09:28 AM", event: "Generated Entanglement Quiz (MCQ) for students", type: "success", user: "NEXORA Agent" },
    { id: "4", time: "09:35 AM", event: "Student engagement dip detected (Average Focus level: 74%)", type: "warning", user: "NLP Engine" },
    { id: "5", time: "09:48 AM", event: "Compiled Lecture Summary study sheet", type: "success", user: "NEXORA Agent" }
  ];

  const handleSaveAPIKeys = () => {
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  return (
    <div className="space-y-8">
      
      {/* Title */}
      <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-2 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-blue-50 rounded-full filter blur-2xl opacity-50"></div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
            <LineChart className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-blue-600 uppercase">Module 10, 16, 17, 18 &amp; 20</span>
            <h1 className="font-display text-2xl font-bold text-gray-900">Analytics, Performance &amp; AI Memory</h1>
          </div>
        </div>
        <p className="text-gray-500 text-sm max-w-3xl">
          Observe attendance percentages, engagement ratios, and review live classroom timeline sequences. Adjust core LLM memory scopes and credentials here.
        </p>
      </div>

      {/* Main Stats metrics widget */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-2">
          <span className="text-xs text-gray-400 font-bold uppercase tracking-wider block">Average Attendance</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-gray-900">94.2%</span>
            <span className="text-xs text-emerald-600 font-semibold">+1.2% this week</span>
          </div>
          <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden mt-2">
            <div className="bg-blue-600 h-full w-[94.2%] rounded-full"></div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-2">
          <span className="text-xs text-gray-400 font-bold uppercase tracking-wider block">Student Focus index</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-gray-900">88.4%</span>
            <span className="text-xs text-emerald-600 font-semibold">Highly Engaged</span>
          </div>
          <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden mt-2">
            <div className="bg-emerald-500 h-full w-[88.4%] rounded-full"></div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-2">
          <span className="text-xs text-gray-400 font-bold uppercase tracking-wider block">AI Token Quota</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-gray-900">142k / 1M</span>
            <span className="text-xs text-gray-400 font-medium">14.2% Consumed</span>
          </div>
          <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden mt-2">
            <div className="bg-indigo-500 h-full w-[14.2%] rounded-full"></div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-2">
          <span className="text-xs text-gray-400 font-bold uppercase tracking-wider block">Memory Nodes Index</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-gray-900">4,912</span>
            <span className="text-xs text-emerald-600 font-semibold">Active Vectors</span>
          </div>
          <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden mt-2">
            <div className="bg-purple-500 h-full w-[65%] rounded-full"></div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left column Content panels */}
        <div className="lg:col-span-8 flex flex-col bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden min-h-[420px]">
          
          {/* Menu sub header tabs */}
          <div className="flex border-b border-gray-100 bg-gray-50/50 p-2 gap-2 shrink-0">
            <button
              onClick={() => setActiveSubTab("performance")}
              className={`flex-1 py-3.5 rounded-2xl text-xs font-semibold tracking-tight transition-all flex items-center justify-center gap-2 ${
                activeSubTab === "performance"
                  ? "bg-white text-blue-600 shadow-sm border border-gray-100"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              <Users className="w-4 h-4" /> Student Performance
            </button>
            <button
              onClick={() => setActiveSubTab("timeline")}
              className={`flex-1 py-3.5 rounded-2xl text-xs font-semibold tracking-tight transition-all flex items-center justify-center gap-2 ${
                activeSubTab === "timeline"
                  ? "bg-white text-blue-600 shadow-sm border border-gray-100"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              <Clock className="w-4 h-4" /> Classroom Timeline
            </button>
            <button
              onClick={() => setActiveSubTab("memory")}
              className={`flex-1 py-3.5 rounded-2xl text-xs font-semibold tracking-tight transition-all flex items-center justify-center gap-2 ${
                activeSubTab === "memory"
                  ? "bg-white text-blue-600 shadow-sm border border-gray-100"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              <MemoryStick className="w-4 h-4" /> System credentials
            </button>
          </div>

          <div className="flex-1 p-6 lg:p-8">
            
            {/* Performance table directory */}
            {activeSubTab === "performance" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-gray-50 pb-3">
                  <h3 className="text-sm font-bold text-gray-800">Student Enrollment Ledger</h3>
                  <span className="text-[10px] font-mono text-gray-400">Total Enrolled: {students.length}</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-gray-600 leading-normal">
                    <thead>
                      <tr className="border-b border-gray-100 text-gray-400 font-bold uppercase text-[9px]">
                        <th className="py-3 px-2">Student Name</th>
                        <th className="py-3 px-2">Attendance %</th>
                        <th className="py-3 px-2">Grade</th>
                        <th className="py-3 px-2">Focus Level</th>
                        <th className="py-3 px-2">Recent MCQ Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {students.map((st) => (
                        <tr key={st.id} className="hover:bg-gray-50/50">
                          <td className="py-3.5 px-2 flex items-center gap-2.5 font-semibold text-gray-900">
                            <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-[10px] font-bold">
                              {st.avatar}
                            </div>
                            {st.name}
                          </td>
                          <td className="py-3.5 px-2 font-semibold">{st.attendance}%</td>
                          <td className="py-3.5 px-2 font-bold text-blue-600">{st.grade}</td>
                          <td className="py-3.5 px-2">
                            <span className={`px-2 py-1 rounded-full text-[10px] font-bold ${
                              st.engagement > 80 ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
                            }`}>
                              {st.engagement}% Focus
                            </span>
                          </td>
                          <td className="py-3.5 px-2 font-mono font-bold text-gray-700">{st.recentQuizScore}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Timeline component log */}
            {activeSubTab === "timeline" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-gray-50 pb-3">
                  <h3 className="text-sm font-bold text-gray-800">Lesson Timeline Sequences</h3>
                  <span className="text-[10px] font-mono text-gray-400">Chronological Order</span>
                </div>

                <div className="space-y-4 relative pl-4 border-l border-gray-100 mt-2">
                  {timeline.map((act) => (
                    <div key={act.id} className="relative space-y-1">
                      {/* Circle bullet point */}
                      <span className={`absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full border border-white ${
                        act.type === "success" ? "bg-emerald-500" : (act.type === "warning" ? "bg-amber-500" : "bg-blue-500")
                      }`}></span>
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] font-mono font-bold text-blue-600">{act.time}</span>
                        <span className="text-[10px] font-semibold text-gray-400">• {act.user}</span>
                      </div>
                      <p className="text-xs text-gray-700 font-semibold">{act.event}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* API settings system panel */}
            {activeSubTab === "memory" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-gray-50 pb-3">
                  <h3 className="text-sm font-bold text-gray-800">LLM Credentials Control</h3>
                  <span className="text-[10px] font-mono text-gray-400">Secrets status</span>
                </div>

                <div className="space-y-4 text-xs">
                  <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-center justify-between">
                    <div>
                      <span className="font-bold text-emerald-800 block text-xs">Gemini 3.5 Flash API Key</span>
                      <p className="text-[11px] text-emerald-600 mt-0.5">Injecting automatically from your settings secrets panel.</p>
                    </div>
                    <span className="text-[10px] font-mono font-bold bg-emerald-200 text-emerald-800 px-2.5 py-1 rounded-full uppercase">
                      CONNECTED
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-gray-600">PostgreSQL pgvector Vector Store</label>
                      <input
                        type="text"
                        readOnly
                        value={pgvectorStatus}
                        className="w-full p-3 rounded-xl glass-input text-xs font-bold text-emerald-600 bg-emerald-50/50"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-gray-600">Whisper Audio Transcription API Key</label>
                      <input
                        type="password"
                        value={whisperKey}
                        onChange={(e) => setWhisperKey(e.target.value)}
                        className="w-full p-3 rounded-xl glass-input text-xs"
                      />
                    </div>
                  </div>

                  <div className="pt-4 border-t border-gray-50 flex items-center justify-end">
                    <button
                      onClick={handleSaveAPIKeys}
                      className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-2 transition-all shadow-md shadow-blue-100"
                    >
                      <Save className="w-4 h-4" /> {isSaved ? "Credentials Saved!" : "Save Credentials"}
                    </button>
                  </div>
                </div>
              </div>
            )}

          </div>

        </div>

        {/* Right column system details */}
        <div className="lg:col-span-4 space-y-8">
          
          {/* Diagnostic Vector search details */}
          <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-4">
            <h3 className="font-display font-bold text-base text-gray-900 flex items-center gap-2">
              <Database className="w-4.5 h-4.5 text-blue-600" /> Database diagnostics
            </h3>
            
            <div className="space-y-3.5 text-xs">
              <div className="flex justify-between items-center border-b border-gray-50 pb-2">
                <span className="text-gray-400">Supabase Connection</span>
                <span className="font-bold text-emerald-600 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Normal
                </span>
              </div>
              <div className="flex justify-between items-center border-b border-gray-50 pb-2">
                <span className="text-gray-400">PostgreSQL Status</span>
                <span className="font-bold text-emerald-600 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Connected
                </span>
              </div>
              <div className="flex justify-between items-center border-b border-gray-50 pb-2">
                <span className="text-gray-400">PostgreSQL pgvector Index</span>
                <span className="font-bold text-emerald-600 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Synced
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Websockets Channels</span>
                <span className="font-bold text-emerald-600 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> Active
                </span>
              </div>
            </div>
          </div>

          {/* AI Student agent instructions */}
          <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-4">
            <h3 className="font-display font-bold text-base text-gray-900 flex items-center gap-2">
              <Cpu className="w-4.5 h-4.5 text-blue-600" /> Agent Instructions
            </h3>
            <p className="text-xs text-gray-500 leading-normal">
              NEXORA's core reasoning system leverages Gemini models to guide context retrievals, match student definitions with actual citations, and compile interactive materials. Ensure API key holds proper quotas.
            </p>
          </div>

        </div>

      </div>
    </div>
  );
}
