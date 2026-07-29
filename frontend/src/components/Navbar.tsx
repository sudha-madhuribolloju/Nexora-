import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Bell, 
  ChevronRight, 
  UserCheck, 
  Settings, 
  User, 
  LogOut 
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { UserRole } from "../types";
import { motion, AnimatePresence } from "motion/react";
import { ROLES_LIST, ROLE_STYLES } from "../constants";

export default function Navbar() {
  const navigate = useNavigate();
  const { user, changeRole, logout } = useAuth();
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const notifications = [
    { id: "1", title: "Dr. Sarah Jenkins started Live Classroom", time: "Just Now", type: "success" },
    { id: "2", title: "New AI Note compiled for Quantum Dynamics", time: "10m ago", type: "info" },
    { id: "3", title: "NEXORA detected student distraction spike (15%)", time: "25m ago", type: "warning" },
    { id: "4", title: "PostgreSQL pgvector index synchronized", time: "1h ago", type: "success" },
  ];

  const currentRole = user?.role || "Student";
  const activeStyle = ROLE_STYLES[currentRole] || ROLE_STYLES["Student"];

  return (
    <header className="h-20 bg-white border-b border-gray-100 px-6 lg:px-10 flex items-center justify-between relative z-20">
      
      {/* Welcome Banner */}
      <div className="flex items-center gap-4">
        <div className="hidden lg:block">
          <h2 className="text-lg font-display font-bold text-gray-900 leading-none">Classroom Portal</h2>
          <span className="text-xs text-gray-400">Interactive Student Workspace</span>
        </div>
      </div>

      {/* Profile & Role Panel */}
      <div className="flex items-center gap-4">
        
        {/* Role Selector */}
        <div className="relative">
          <button 
            onClick={() => setShowRoleMenu(!showRoleMenu)}
            className={`px-4 py-2 rounded-2xl border ${activeStyle.border} ${activeStyle.bg} ${activeStyle.text} text-xs font-semibold flex items-center gap-2 shadow-sm transition-all hover:brightness-95 cursor-pointer`}
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
                  {ROLES_LIST.map((r) => (
                    <button
                      key={r}
                      onClick={() => {
                        changeRole(r);
                        setShowRoleMenu(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-xl text-xs font-medium transition-colors flex items-center justify-between cursor-pointer ${
                        currentRole === r 
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

        {/* Notifications Trigger */}
        <div className="relative">
          <button 
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="p-2.5 rounded-xl border border-gray-100 hover:border-gray-200 hover:bg-gray-50 text-gray-500 transition-all relative cursor-pointer"
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
                    <span 
                      onClick={() => {
                        setNotificationsOpen(false);
                        navigate("/notifications");
                      }} 
                      className="text-[10px] font-mono text-blue-600 font-semibold cursor-pointer hover:underline"
                    >
                      View all alerts
                    </span>
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

        {/* User Identity */}
        <div className="flex items-center gap-3 border-l border-gray-100 pl-4 relative group">
          <div 
            onClick={() => navigate("/profile")}
            className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-500 to-indigo-500 text-white flex items-center justify-center font-bold text-sm shadow-sm cursor-pointer hover:brightness-105"
          >
            {user?.fullName.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() || "NB"}
          </div>
          <div className="hidden xl:block text-left cursor-pointer" onClick={() => navigate("/profile")}>
            <span className="text-xs font-semibold block text-gray-800 leading-none hover:text-blue-600 transition-colors">
              {user?.fullName || "Prof. Srinivas B."}
            </span>
            <span className="text-[10px] text-gray-400 mt-1 block">{activeStyle.label}</span>
          </div>
          <button
            onClick={() => navigate("/settings")}
            className="p-1.5 rounded-lg border border-transparent hover:border-gray-200 hover:bg-gray-50 text-gray-400 hover:text-gray-700 transition-all cursor-pointer"
            title="Workspace Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>

      </div>
    </header>
  );
}
