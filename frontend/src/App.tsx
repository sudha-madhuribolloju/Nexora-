import React from "react";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { ClassroomProvider } from "./contexts/ClassroomContext";
import AppRoutes from "./routes";
import { CheckCircle, AlertCircle, Info } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

function AppContent() {
  const { toasts, dismissToast } = useAuth();

  return (
    <div className="min-h-screen bg-white text-gray-900 font-sans select-none selection:bg-blue-100">
      
      {/* Central App Routing */}
      <AppRoutes />

      {/* Floating global notifications toasts */}
      <div className="fixed bottom-6 right-6 z-50 space-y-2 pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 15, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onClick={() => dismissToast(toast.id)}
              className="px-5 py-3.5 rounded-2xl bg-gray-900 border border-gray-800 text-white shadow-xl flex items-center gap-3 pointer-events-auto min-w-[300px] cursor-pointer hover:bg-slate-950 transition-colors"
            >
              {toast.type === "success" && <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />}
              {toast.type === "error" && <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />}
              {toast.type === "info" && <Info className="w-5 h-5 text-blue-400 shrink-0" />}
              <span className="text-xs font-semibold leading-relaxed font-sans">{toast.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ClassroomProvider>
          <BrowserRouter>
            <AppContent />
          </BrowserRouter>
        </ClassroomProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

