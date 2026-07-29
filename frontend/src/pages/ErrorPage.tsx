import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

export default function ErrorPage() {
  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-6 relative">
      <div className="max-w-md w-full text-center space-y-6 bg-white p-10 rounded-3xl border border-red-100 shadow-2xl relative z-10">
        
        {/* Error icon */}
        <div className="w-16 h-16 rounded-2xl bg-red-50 border border-red-100 text-red-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <span className="text-[10px] font-mono font-extrabold uppercase tracking-widest text-red-600 bg-red-50 border border-red-100 px-3 py-1 rounded-full">
            SYSTEM FATAL EXCEPTION
          </span>
          <h1 className="font-display text-2xl font-bold text-gray-900 pt-1">Something went wrong</h1>
          <p className="text-xs text-gray-500 leading-relaxed font-sans px-2">
            An unexpected error occurred in your current session. The reactive state engine was interrupted.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={handleReload}
          className="w-full py-3.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer shadow-md shadow-red-600/10 active:scale-[0.99]"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reload Active Session</span>
        </button>
      </div>
    </div>
  );
}
