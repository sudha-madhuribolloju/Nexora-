import React from "react";
import { useNavigate } from "react-router-dom";
import { Bot, HelpCircle, ArrowRight } from "lucide-react";

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-6 relative overflow-hidden select-none">
      
      {/* Visual background lights */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-100 rounded-full mix-blend-multiply filter blur-3xl opacity-40 -z-10 animate-pulse"></div>
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-indigo-100 rounded-full mix-blend-multiply filter blur-3xl opacity-30 -z-10"></div>

      <div className="max-w-md w-full text-center space-y-6 bg-white p-10 rounded-3xl border border-gray-100 shadow-2xl relative z-10">
        
        {/* Brand logo */}
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-sky-400 flex items-center justify-center text-white shadow-lg shadow-blue-200 mx-auto">
          <Bot className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <span className="text-[10px] font-mono font-extrabold uppercase tracking-widest text-blue-600 bg-blue-50 border border-blue-100 px-3 py-1 rounded-full">
            ERROR CODE 404
          </span>
          <h1 className="font-display text-2xl font-bold text-gray-900 pt-1">Workspace Route Missing</h1>
          <p className="text-xs text-gray-500 leading-relaxed font-sans px-2">
            The requested folder or pathway could not be located. The link may have expired or been moved to another administrative perspective.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={() => navigate("/")}
          className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer shadow-md shadow-blue-900/5 active:scale-[0.99]"
        >
          <span>Return to Safety Dashboard</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <div className="text-[10px] font-mono text-gray-400 mt-6 flex items-center gap-1.5">
        <HelpCircle className="w-3.5 h-3.5" />
        <span>Contact St. Mary IT support if this persists</span>
      </div>
    </div>
  );
}
