import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { 
  Bell, 
  CheckCheck, 
  Trash2, 
  Clock, 
  Sparkles, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight,
  Tv
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/Card";

interface NotificationItem {
  id: string;
  title: string;
  time: string;
  type: "success" | "warning" | "info" | "classroom";
  read: boolean;
  message: string;
}

export default function NotificationsPage() {
  const { triggerToast } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([
    { 
      id: "1", 
      title: "Live Classroom Speech Recognition Ready", 
      message: "Whisper STT speech recognition engine and Gemini AI NLP pipeline are initialized.",
      time: "Just Now", 
      type: "classroom", 
      read: false 
    },
    { 
      id: "2", 
      title: "AI Knowledge Base & Document Chat Online", 
      message: "Upload course textbooks and notes to generate study guides, summaries, and quizzes.",
      time: "System", 
      type: "success", 
      read: false 
    },
    { 
      id: "3", 
      title: "PostgreSQL Vector Database Connected", 
      message: "pgvector semantic search is active for academic research papers and study documents.",
      time: "System", 
      type: "info", 
      read: true 
    },
  ]);

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    triggerToast("All alerts marked as read", "success");
  };

  const clearAll = () => {
    setNotifications([]);
    triggerToast("Notification cache cleared", "info");
  };

  const toggleRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: !n.read } : n))
    );
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bell className="w-6 h-6 text-blue-600" />
            <span>Alerts &amp; Notifications</span>
          </h1>
          <p className="text-xs text-gray-500 mt-1">Review live notifications, system health status, and lecture session markers.</p>
        </div>

        {notifications.length > 0 && (
          <div className="flex items-center gap-3">
            <button
              onClick={markAllAsRead}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors cursor-pointer"
            >
              <CheckCheck className="w-4 h-4" />
              <span>Mark Read</span>
            </button>
            <button
              onClick={clearAll}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-red-600 bg-red-50 hover:bg-red-100 rounded-xl transition-colors cursor-pointer"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear Cache</span>
            </button>
          </div>
        )}
      </div>

      {notifications.length === 0 ? (
        <Card className="p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-gray-50 text-gray-400 flex items-center justify-center mx-auto border border-gray-100">
            <Bell className="w-5 h-5" />
          </div>
          <p className="text-xs text-gray-500 font-semibold">You have no active alerts in this session.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {notifications.map((n) => (
            <Card
              key={n.id}
              className={`p-6 transition-all duration-300 ${
                n.read ? "bg-white opacity-85" : "bg-white border-l-4 border-l-blue-600 shadow-md"
              }`}
            >
              <div className="flex items-start gap-4">
                {/* Visual Icon indicators based on alert types */}
                <div className="mt-0.5">
                  {n.type === "classroom" && (
                    <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                      <Tv className="w-4.5 h-4.5" />
                    </div>
                  )}
                  {n.type === "success" && (
                    <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                      <CheckCircle2 className="w-4.5 h-4.5" />
                    </div>
                  )}
                  {n.type === "warning" && (
                    <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
                      <AlertTriangle className="w-4.5 h-4.5" />
                    </div>
                  )}
                  {n.type === "info" && (
                    <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                      <Sparkles className="w-4.5 h-4.5" />
                    </div>
                  )}
                </div>

                {/* Text logs content */}
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between gap-4">
                    <span className={`text-xs font-bold text-gray-900 ${!n.read && "font-extrabold"}`}>
                      {n.title}
                    </span>
                    <span className="text-[10px] text-gray-400 font-medium flex items-center gap-1 shrink-0">
                      <Clock className="w-3 h-3" />
                      {n.time}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed font-sans pt-0.5">{n.message}</p>
                </div>

                {/* Mark read button toggle */}
                <button
                  onClick={() => toggleRead(n.id)}
                  className={`p-1.5 rounded-lg border text-[10px] font-bold transition-all shrink-0 cursor-pointer ${
                    n.read 
                      ? "border-gray-100 bg-gray-50/50 text-gray-400 hover:bg-gray-50" 
                      : "border-blue-100 bg-blue-50/50 text-blue-600 hover:bg-blue-50"
                  }`}
                >
                  {n.read ? "Mark Unread" : "Mark Read"}
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
