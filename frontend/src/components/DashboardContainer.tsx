import React, { useState } from "react";
import {
  Bot,
  ChevronRight,
  Menu,
  Bell,
  Search,
  Settings,
  Users,
  Sparkles,
  UserCheck,
  LogOut,
  ShieldAlert,
  Database,
  Briefcase,
  Layers,
  HelpCircle,
  Activity,
  User,
  CheckCircle,
  Clock,
  BookOpen,
  Tv,
  Video,
  Award,
  CreditCard

} from "lucide-react";
import { UserRole } from "../types";
import { ROLES } from "../utils/rbac";
import { motion, AnimatePresence } from "motion/react";


interface DashboardContainerProps {
  onLogout: () => void;
  currentRole: UserRole;
  onChangeRole: (role: UserRole) => void;
  activeModuleTab: string;
  onChangeTab: (tab: string) => void;
  children: React.ReactNode;
}

export default function DashboardContainer({
  onLogout,
  currentRole,
  onChangeRole,
  activeModuleTab,
  onChangeTab,
  children
}: DashboardContainerProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  const rolesList: UserRole[] = [
    ROLES.STUDENT,
    ROLES.TEACHER,
    ROLES.PRINCIPAL,
    ROLES.PARENT,
    ROLES.SUPER_ADMIN,
    ROLES.INSTITUTE_ADMIN,
    ROLES.SUPPORT_ENGINEER
  ];

  const sidebarItems = [
    { id: "overview", label: "Overview", icon: Layers },
    { id: "live-classroom", label: "Live Classroom", icon: Tv },
    { id: "recorded-lectures", label: "Recorded Lectures", icon: Video },
    { id: "audio-voice", label: "Audio & Voice", icon: Bot },

    { id: "nlp-summary", label: "NLP & Lecture Summaries", icon: Sparkles },
    { id: "ai-chat", label: "AI Chat & PDF Files", icon: BookOpen },
    { id: "research", label: "Academic AI Research", icon: Search },
    { id: "quizzes", label: "Quiz & Exercises", icon: UserCheck },
    { id: "whiteboard", label: "Notes & AI Whiteboard", icon: Activity },
    { id: "progress", label: "Academic Progress", icon: Award },
    { id: "directory", label: "Campus Directory", icon: Users },
    { id: "analytics", label: "Analytics & Performance", icon: Settings },
    { id: "account-billing", label: "Account & Billing", icon: CreditCard },
  ];

  const notifications = [
    { id: "1", title: "Live Classroom Speech Recognition Ready", time: "Active", type: "success" },
    { id: "2", title: "AI Academic Assistants Online", time: "Ready", type: "info" },
    { id: "3", title: "PostgreSQL Database Connected", time: "System", type: "success" },
  ];

  // Map roles to descriptions & specific color badges
  const roleStyles: Record<UserRole, { label: string; bg: string; text: string; border: string }> = {
    [ROLES.STUDENT]: { label: "Student Agent Peer", bg: "bg-blue-50", text: "text-blue-600", border: "border-blue-100" },
    [ROLES.TEACHER]: { label: "Course Instructor", bg: "bg-purple-50", text: "text-purple-600", border: "border-purple-100" },
    [ROLES.PRINCIPAL]: { label: "Campus Director", bg: "bg-amber-50", text: "text-amber-600", border: "border-amber-100" },
    [ROLES.PARENT]: { label: "Student Guardian", bg: "bg-pink-50", text: "text-pink-600", border: "border-pink-100" },
    [ROLES.SUPER_ADMIN]: { label: "Global Systems", bg: "bg-rose-50", text: "text-rose-600", border: "border-rose-100" },
    [ROLES.INSTITUTE_ADMIN]: { label: "College Administrator", bg: "bg-emerald-50", text: "text-emerald-600", border: "border-emerald-100" },
    [ROLES.SUPPORT_ENGINEER]: { label: "DevOps & Infrastructure", bg: "bg-teal-50", text: "text-teal-600", border: "border-teal-100" },
  };

  const activeStyle = roleStyles[currentRole];

  return (
    <div className="min-h-screen bg-gray-50/50 flex flex-col md:flex-row text-gray-800 font-sans antialiased overflow-x-hidden">

      {/* Sidebar navigation */}
      <aside
        className={`bg-white border-r border-gray-100 shrink-0 transition-all duration-300 relative z-30 flex flex-col ${sidebarOpen ? "w-72" : "w-20"
          }`}
      >
        {/* Brand Header */}
        <div className="p-6 flex items-center justify-between border-b border-gray-50">
          <div className="flex items-center gap-3 overflow-hidden">
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
            const isSelected = activeModuleTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onChangeTab(item.id)}
                className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-2xl transition-all font-medium text-sm group relative ${isSelected
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-100"
                    : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                  }`}
              >
                <Icon className={`w-5 h-5 shrink-0 transition-transform group-hover:scale-105 duration-200 ${isSelected ? "text-white" : "text-gray-400 group-hover:text-gray-700"
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
              <div className="text-xs font-semibold text-gray-800 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Node-Sandbox C12
              </div>
            </div>
          )}

          <button
            onClick={onLogout}
            className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-2xl text-red-600 hover:bg-red-50 hover:text-red-700 transition-all font-medium text-sm ${!sidebarOpen && "justify-center"
              }`}
          >
            <LogOut className="w-5 h-5 shrink-0" />
            {sidebarOpen && <span>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Global Dark Glass Header */}
        <header className="h-20 bg-white border-b border-gray-100 px-6 lg:px-10 flex items-center justify-between relative z-20">

          {/* Welcome Banner */}
          <div className="flex items-center gap-4">
            <div className="hidden lg:block">
              <h2 className="text-lg font-display font-bold text-gray-900 leading-none">Classroom Portal</h2>
              <span className="text-xs text-gray-400">Interactive Student Workspace</span>
            </div>
          </div>

          {/* Role selector dropdown panel */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <button
                onClick={() => setShowRoleMenu(!showRoleMenu)}
                className={`px-4 py-2 rounded-2xl border ${activeStyle.border} ${activeStyle.bg} ${activeStyle.text} text-xs font-semibold flex items-center gap-2 shadow-sm transition-all hover:brightness-95`}
              >
                <UserCheck className="w-4 h-4" />
                <span className="hidden sm:inline">Role:</span> {currentRole}
                <ChevronRight className="w-3.5 h-3.5 rotate-90" />
              </button>

              <AnimatePresence>
                {showRoleMenu && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShowRoleMenu(false)}></div>
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      className="absolute right-0 mt-2 w-56 bg-white border border-gray-100 rounded-2xl shadow-xl p-2 z-50"
                    >
                      <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-gray-400 font-semibold border-b border-gray-50 mb-1">
                        Select Sandbox Role
                      </div>
                      {rolesList.map((r) => (
                        <button
                          key={r}
                          onClick={() => {
                            onChangeRole(r);
                            setShowRoleMenu(false);
                          }}
                          className={`w-full text-left px-3 py-2 rounded-xl text-xs font-medium transition-colors flex items-center justify-between ${currentRole === r
                              ? "bg-blue-50 text-blue-600 font-semibold"
                              : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                            }`}
                        >
                          {r}
                          {currentRole === r && <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>}
                        </button>
                      ))}
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>

            {/* Notification triggers */}
            <div className="relative">
              <button
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="p-2.5 rounded-xl border border-gray-100 hover:border-gray-200 hover:bg-gray-50 text-gray-500 transition-all relative"
              >
                <Bell className="w-4.5 h-4.5" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-600 border border-white"></span>
              </button>

              <AnimatePresence>
                {notificationsOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setNotificationsOpen(false)}></div>
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      className="absolute right-0 mt-2.5 w-80 sm:w-96 bg-white border border-gray-100 rounded-3xl shadow-2xl p-4 z-50 space-y-3"
                    >
                      <div className="flex items-center justify-between border-b border-gray-50 pb-2.5">
                        <span className="font-display font-bold text-sm text-gray-900">Notifications</span>
                        <span className="text-[10px] font-mono text-blue-600 font-semibold cursor-pointer hover:underline">Mark all as read</span>
                      </div>
                      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                        {notifications.map((n) => (
                          <div key={n.id} className="p-3 bg-gray-50 rounded-xl border border-gray-100/50 flex gap-3 text-xs leading-normal">
                            <div className="mt-0.5">
                              {n.type === "success" && <div className="w-2 h-2 rounded-full bg-emerald-500"></div>}
                              {n.type === "warning" && <div className="w-2 h-2 rounded-full bg-amber-500"></div>}
                              {n.type === "info" && <div className="w-2 h-2 rounded-full bg-blue-500"></div>}
                            </div>
                            <div className="flex-1">
                              <p className="font-medium text-gray-700">{n.title}</p>
                              <span className="text-[10px] text-gray-400 block mt-1">{n.time}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>

            {/* Premium user identity */}
            <div className="flex items-center gap-3 border-l border-gray-100 pl-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-500 to-indigo-500 text-white flex items-center justify-center font-bold text-sm shadow-sm">
                NB
              </div>
              <div className="hidden xl:block">
                <span className="text-xs font-semibold block text-gray-800 leading-none">Prof. Sudha Madhuri</span>
                <span className="text-[10px] text-gray-400 mt-1 block">{activeStyle.label}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic Inner Tab Rendering */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeModuleTab + currentRole}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
