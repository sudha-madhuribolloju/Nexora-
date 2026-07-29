import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { 
  Bot, 
  Menu, 
  Layers, 
  Tv, 
  Sparkles, 
  BookOpen, 
  Search, 
  UserCheck, 
  Activity, 
  Award, 
  Users, 
  Settings, 
  CreditCard, 
  LogOut,
  User,
  Bell
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export default function Sidebar({ sidebarOpen, setSidebarOpen }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, user } = useAuth();

  const sidebarItems = [
    { id: "overview", label: "Overview", icon: Layers, path: "/" },
    { id: "live-classroom", label: "Live Classroom", icon: Tv, path: "/live-classroom" },
    { id: "audio-voice", label: "Audio & Voice", icon: Bot, path: "/audio-voice" },
    { id: "nlp-summary", label: "NLP & Lecture Summaries", icon: Sparkles, path: "/nlp-summary" },
    { id: "ai-chat", label: "AI Chat & PDF Files", icon: BookOpen, path: "/ai-chat" },
    { id: "research", label: "Academic AI Research", icon: Search, path: "/research" },
    { id: "quizzes", label: "Quiz & Exercises", icon: UserCheck, path: "/quizzes" },
    { id: "whiteboard", label: "Notes & AI Whiteboard", icon: Activity, path: "/whiteboard" },
    { id: "progress", label: "Academic Progress", icon: Award, path: "/progress" },
    { id: "directory", label: "Campus Directory", icon: Users, path: "/directory" },
    { id: "analytics", label: "Analytics & Performance", icon: Settings, path: "/analytics" },
    { id: "account-billing", label: "Account & Billing", icon: CreditCard, path: "/account-billing" },
  ];

  return (
    <aside 
      className={`bg-white border-r border-gray-100 shrink-0 transition-all duration-300 relative z-30 flex flex-col ${
        sidebarOpen ? "w-72" : "w-20"
      }`}
    >
      {/* Brand Header */}
      <div className="p-6 flex items-center justify-between border-b border-gray-50">
        <div className="flex items-center gap-3 overflow-hidden cursor-pointer" onClick={() => navigate("/")}>
          <div className="w-9 h-9 shrink-0 rounded-xl bg-gradient-to-tr from-blue-600 to-sky-400 flex items-center justify-center text-white shadow-md shadow-blue-200">
            <Bot className="w-5 h-5" />
          </div>
          {sidebarOpen && (
            <div className="flex flex-col">
              <span className="font-display font-bold text-base tracking-tight text-gray-900 leading-none">NEXORA</span>
              <span className="text-[8px] text-blue-600 font-mono font-semibold tracking-wider mt-1">CLASSROOM AGENT</span>
            </div>
          )}
        </div>
        <button 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-1.5 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-all"
        >
          <Menu className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {/* Sidebar Menu Items */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          const isSelected = location.pathname === item.path;
          return (
            <button
              key={item.id}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-2xl transition-all font-medium text-sm group relative cursor-pointer ${
                isSelected 
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-100" 
                  : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
              }`}
            >
              <Icon className={`w-5 h-5 shrink-0 transition-transform group-hover:scale-105 duration-200 ${
                isSelected ? "text-white" : "text-gray-400 group-hover:text-gray-700"
              }`} />
              {sidebarOpen && <span className="truncate">{item.label}</span>}
              {isSelected && !sidebarOpen && (
                <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-white rounded-r-full"></div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Sidebar bottom role selector & Logout */}
      <div className="p-4 border-t border-gray-50 space-y-2.5">
        {sidebarOpen && (
          <div className="p-3 bg-gray-50 rounded-2xl border border-gray-100 space-y-1">
            <div className="text-[10px] uppercase font-mono tracking-wider font-semibold text-gray-400">Environment Active</div>
            <div className="text-xs font-semibold text-gray-800 flex items-center gap-1.5 font-sans">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Node-Sandbox C12
            </div>
          </div>
        )}

        <button 
          onClick={logout}
          className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-2xl text-red-600 hover:bg-red-50 hover:text-red-700 transition-all font-medium text-sm cursor-pointer ${
            !sidebarOpen && "justify-center"
          }`}
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {sidebarOpen && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
}
