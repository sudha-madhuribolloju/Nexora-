import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import {
  Bot,
  Sparkles,
  Mic,
  FileText,
  Search,
  Award,
  Brush,
  LineChart,
  ShieldCheck,
  ArrowRight,
  ChevronRight,
  UserCheck,
  Activity
} from "lucide-react";
import { motion } from "motion/react";
import { Card } from "../components/Card";
import { ROLES } from "../utils/rbac";


export default function OverviewPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const currentRole = user?.role || "Student";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="space-y-8"
    >
      {/* Visual Greeting Card */}
      <Card className="p-8 lg:p-10 border-l-4 border-l-blue-600 flex flex-col md:flex-row md:items-center justify-between gap-6 hover:border-blue-300">
        <div className="absolute top-0 right-0 w-80 h-80 bg-blue-50/40 rounded-full filter blur-3xl -z-10"></div>
        <div className="space-y-2 relative z-10 max-w-2xl text-left">
          <span className="text-[10px] font-mono tracking-widest text-blue-600 font-bold uppercase">Workspace Hub</span>
          <h1 className="font-display text-2xl lg:text-3xl font-bold text-gray-900">Welcome back, {user?.fullName || "Prof.Sudha Madhuri ."}</h1>
          <p className="text-gray-500 text-xs leading-relaxed">
            NEXORA classroom client is active. The NLP transcription pipelines are running, connected to the Google Gemini 3.5 Flash server layer.
          </p>
        </div>

        {/* Active focus display */}
        <div className="p-5 rounded-2xl bg-blue-50/50 border border-blue-100 shrink-0 text-center space-y-1 relative z-10">
          <span className="text-[10px] text-blue-600 font-mono font-bold uppercase block">Average Student Focus</span>
          <span className="text-2xl font-bold text-blue-700 block">88.4%</span>
          <span className="text-[9px] text-emerald-600 font-semibold block">Highly Engaged</span>
        </div>
      </Card>

      {/* Role-Specific Overview widget panel */}
      <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-4">
        <div className="flex items-center gap-2 border-b border-gray-50 pb-3">
          <UserCheck className="w-5 h-5 text-blue-600" />
          <span className="text-sm font-bold text-gray-800">Perspective Dashboard: {currentRole} View</span>
        </div>

        {/* Student View Overview widgets */}
        {currentRole === ROLES.STUDENT && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-xs text-gray-600 leading-normal text-left">
            <div className="bento-card bento-card-blue p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Interactive Quizzes</span>
              <p className="font-bold text-gray-900 text-sm">Self-Paced Practice &amp; Review</p>
              <span className="text-blue-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/quizzes")}>Take preparatory quiz &gt;</span>
            </div>
            <div className="bento-card bento-card-purple p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Course Notes &amp; Whiteboard</span>
              <p className="font-bold text-gray-900 text-sm">AI Study Manuals &amp; Diagrams</p>
              <span className="text-blue-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/whiteboard")}>Open notes folder &gt;</span>
            </div>
            <div className="bento-card bento-card-emerald p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">AI Student Agent</span>
              <p className="font-bold text-gray-900 text-sm">PDF &amp; Textbook Assistant</p>
              <span className="text-blue-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/ai-chat")}>Ask a question &gt;</span>
            </div>
          </div>
        )}

        {/* Teacher View Overview widgets */}
        {currentRole === ROLES.TEACHER && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-xs text-gray-600 leading-normal text-left">
            <div className="bento-card bento-card-purple p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Classroom Engagement</span>
              <p className="font-bold text-gray-900 text-sm">Live Lecture NLP Analytics</p>
              <span className="text-purple-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/nlp-summary")}>Open NLP graphs &gt;</span>
            </div>
            <div className="bento-card bento-card-blue p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Staged Exam Builder</span>
              <p className="font-bold text-gray-900 text-sm">Interactive Quiz Generator</p>
              <span className="text-purple-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/quizzes")}>Generate new test &gt;</span>
            </div>
            <div className="bento-card bento-card-emerald p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Attendance &amp; Performance</span>
              <p className="font-bold text-gray-900 text-sm">Student Analytics &amp; Roster</p>
              <span className="text-purple-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/analytics")}>Inspect enrollment &gt;</span>
            </div>
          </div>
        )}

        {/* Super Admin & Support Perspectives */}
        {(currentRole === ROLES.SUPER_ADMIN || currentRole === ROLES.INSTITUTE_ADMIN || currentRole === ROLES.SUPPORT_ENGINEER) && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-xs text-gray-600 leading-normal text-left">
            <div className="bento-card bento-card-blue p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Database Index Metrics</span>
              <p className="font-bold text-gray-900 text-sm">PostgreSQL pgvector: 4,912 Vector Chunks</p>
              <span className="text-indigo-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/analytics")}>Review indexes &gt;</span>
            </div>
            <div className="bento-card bento-card-purple p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Global API Quota throughput</span>
              <p className="font-bold text-gray-900 text-sm">Gemini model: 142k/1M tokens</p>
              <span className="text-indigo-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/analytics")}>View analytics &gt;</span>
            </div>
            <div className="bento-card bento-card-emerald p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Credentials status</span>
              <p className="font-bold text-gray-900 text-sm">Gemini Server: Operational</p>
              <span className="text-indigo-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/analytics")}>Adjust credentials &gt;</span>
            </div>
          </div>
        )}

        {/* Principal & Parent Perspective */}
        {(currentRole === ROLES.PRINCIPAL || currentRole === ROLES.PARENT) && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-xs text-gray-600 leading-normal text-left">
            <div className="bento-card bento-card-emerald p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Academic Performance report</span>
              <p className="font-bold text-gray-900 text-sm">Classroom Grades: 88.4% average</p>
              <span className="text-amber-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/analytics")}>View progress reports &gt;</span>
            </div>
            <div className="bento-card bento-card-blue p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Enrollment Logs</span>
              <p className="font-bold text-gray-900 text-sm">Average attendance: 94.2%</p>
              <span className="text-amber-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/analytics")}>Track attendance &gt;</span>
            </div>
            <div className="bento-card bento-card-purple p-5 space-y-2">
              <span className="text-[10px] uppercase font-mono text-gray-400 font-bold">Class Timeline Logs</span>
              <p className="font-bold text-gray-900 text-sm">Bohr model session processed</p>
              <span className="text-amber-600 font-semibold mt-1 block hover:underline cursor-pointer" onClick={() => navigate("/analytics")}>Inspect timelines &gt;</span>
            </div>
          </div>
        )}
      </div>

      {/* Quick Launch Bento list */}
      <div className="space-y-4 text-left">
        <h3 className="font-display font-bold text-base text-gray-900">NEXORA Quick Launch Shortcuts</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">

          <button
            onClick={() => navigate("/live-classroom")}
            className="bento-card bento-card-blue text-left hover:border-blue-300 hover:shadow-md transition-all group cursor-pointer space-y-4"
          >
            <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center transition-transform group-hover:scale-105 duration-200">
              <Mic className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-gray-800 block">Record Lectures</span>
              <span className="text-[10px] text-gray-400 mt-1 block">Live Classroom microphone capture &amp; STT</span>
            </div>
          </button>

          <button
            onClick={() => navigate("/nlp-summary")}
            className="bento-card bento-card-purple text-left hover:border-purple-300 hover:shadow-md transition-all group cursor-pointer space-y-4"
          >
            <div className="w-10 h-10 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center transition-transform group-hover:scale-105 duration-200">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-gray-800 block">Summarize Lectures</span>
              <span className="text-[10px] text-gray-400 mt-1 block">Extract NLP metrics &amp; definitions</span>
            </div>
          </button>

          <button
            onClick={() => navigate("/research")}
            className="bento-card bento-card-pink text-left hover:border-pink-300 hover:shadow-md transition-all group cursor-pointer space-y-4"
          >
            <div className="w-10 h-10 rounded-2xl bg-pink-50 text-pink-600 flex items-center justify-center transition-transform group-hover:scale-105 duration-200">
              <Search className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-gray-800 block">Academic Search</span>
              <span className="text-[10px] text-gray-400 mt-1 block">Gather grounded web citations</span>
            </div>
          </button>

          <button
            onClick={() => navigate("/whiteboard")}
            className="bento-card bento-card-emerald text-left hover:border-emerald-300 hover:shadow-md transition-all group cursor-pointer space-y-4"
          >
            <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center transition-transform group-hover:scale-105 duration-200">
              <Brush className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-gray-800 block">AI Blackboard Solver</span>
              <span className="text-[10px] text-gray-400 mt-1 block">Reposition visual nodes and prove equations</span>
            </div>
          </button>

        </div>
      </div>
    </motion.div>
  );
}
