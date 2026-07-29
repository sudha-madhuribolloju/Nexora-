import React from "react";
import { useNavigate } from "react-router-dom";
import { 
  Bot, 
  Cpu, 
  CheckSquare, 
  Laptop, 
  Award 
} from "lucide-react";
import { motion } from "motion/react";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex bg-slate-50 relative overflow-hidden select-none">
      
      {/* Decorative vector background */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-100/30 rounded-full filter blur-3xl -z-10"></div>
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-indigo-100/20 rounded-full filter blur-3xl -z-10"></div>

      {/* --- LEFT SIDE: HERO PORTAL & ILLUSTRATION --- */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 text-white p-12 flex-col justify-between relative overflow-hidden shadow-2xl">
        
        {/* Futuristic glowing particle effect */}
        <div className="absolute top-1/4 left-1/3 w-80 h-80 bg-blue-500/20 rounded-full mix-blend-screen filter blur-[100px] animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-indigo-500/15 rounded-full mix-blend-screen filter blur-[120px]"></div>

        {/* Brand Header */}
        <div className="flex items-center gap-3 relative z-10 cursor-pointer" onClick={() => navigate("/")}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-500 to-sky-400 flex items-center justify-center text-white shadow-lg shadow-blue-400/20">
            <Bot className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="font-display font-bold text-lg tracking-tight">NEXORA</span>
            <span className="text-[9px] block text-blue-400 font-mono tracking-wider font-semibold uppercase">AI Student Workspace</span>
          </div>
        </div>

        {/* Middle content: Illustration representation */}
        <div className="my-auto space-y-10 relative z-10 max-w-lg">
          <div className="space-y-4">
            <span className="text-[10px] uppercase font-mono tracking-widest text-blue-400 font-bold bg-blue-950/60 px-3 py-1.5 rounded-full border border-blue-900/40 w-max block">
              System Release v2.4
            </span>
            <h1 className="font-display text-4xl font-extrabold tracking-tight leading-[1.1]">
              The Ultimate Multi-Role <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-300">
                AI Classroom Workspace
              </span>
            </h1>
            <p className="text-slate-300 text-xs leading-relaxed font-sans">
              Enter your credential files to connect with the cloud-hosted Gemini transcription tunnels. Manage active student directories, run complex web-grounded research reports, and host interactive multi-user whiteboard canvases.
            </p>
          </div>

          {/* Interactive UI Mockup Card Representation */}
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-400" />
                <span className="text-xs font-mono font-bold text-slate-200">ACTIVE COGNITIVE AGENT</span>
              </div>
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
                <span className="text-[9px] text-emerald-400 font-bold font-mono">LIVE</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono">
                <span>LECTURE TRANSCRIPTION PATH</span>
                <span>98.7% CONFIDENCE</span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: "91%" }}
                  transition={{ duration: 2, repeat: Infinity, repeatType: "reverse" }}
                  className="h-full bg-gradient-to-r from-blue-500 to-indigo-400"
                ></motion.div>
              </div>
            </div>

            <div className="flex gap-4 pt-1">
              <div className="flex items-center gap-1.5 text-[10px] text-slate-300">
                <CheckSquare className="w-3.5 h-3.5 text-blue-400" />
                <span>Zod Validated</span>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] text-slate-300">
                <Laptop className="w-3.5 h-3.5 text-blue-400" />
                <span>OAuth 2.0 Secure</span>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] text-slate-300">
                <Award className="w-3.5 h-3.5 text-blue-400" />
                <span>React 19 Ready</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="flex items-center justify-between border-t border-white/5 pt-6 text-[10px] text-slate-400 font-mono relative z-10">
          <span>St. Mary’s Digital Hub Portal</span>
          <span>© 2026 NEXORA AI Inc.</span>
        </div>
      </div>

      {/* --- RIGHT SIDE: GLASSMORPHISM CARD FOR AUTHENTICATION FORM --- */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center p-6 sm:p-12 md:p-16 relative">
        
        {/* Soft light background element */}
        <div className="absolute top-10 left-10 w-40 h-40 bg-indigo-200/40 rounded-full filter blur-2xl -z-10"></div>
        <div className="absolute bottom-10 right-10 w-52 h-52 bg-sky-200/30 rounded-full filter blur-2xl -z-10"></div>

        {/* Responsive Brand Header on Mobile only */}
        <div className="flex lg:hidden items-center gap-2 mb-8 cursor-pointer" onClick={() => navigate("/")}>
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
            <Bot className="w-4 h-4" />
          </div>
          <span className="font-display font-bold text-lg text-gray-900 tracking-tight">NEXORA</span>
        </div>

        {/* Main Content Glass Card Frame */}
        <div className="w-full max-w-md bg-white/80 backdrop-blur-md border border-gray-100 rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 space-y-6">
          {children}
        </div>
      </div>
    </div>
  );
}
