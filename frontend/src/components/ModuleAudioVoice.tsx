import React, { useState, useEffect } from "react";
import { 
  Mic, 
  MicOff,
  Volume2, 
  ShieldCheck, 
  Sparkles, 
  Activity, 
  User, 
  CheckCircle2, 
  Cpu, 
  Clock,
  AlertCircle,
  Radio,
  Sliders,
  FileText,
  ArrowRight,
  Layers
} from "lucide-react";
import { motion } from "motion/react";
import { useNavigate } from "react-router-dom";
import { useClassroomSession } from "../contexts/ClassroomContext";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";

interface VoicePrintItem {
  id: string;
  name: string;
  subject: string;
  printId: string;
  role: string;
}

export default function ModuleAudioVoice() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { 
    activeSession, 
    mediaStream, 
    audioTelemetry, 
    updateAudioTelemetry 
  } = useClassroomSession();

  const currentSpeakerName = user?.fullName || user?.email?.split("@")[0] || "Instructor";
  const [selectedSpeaker, setSelectedSpeaker] = useState(currentSpeakerName);
  
  const [voiceLogs, setVoiceLogs] = useState<string[]>([
    `[${new Date().toLocaleTimeString()}] Audio configuration initialized. Single recording controller: Live Classroom.`,
    `[${new Date().toLocaleTimeString()}] Acoustic Noise Reduction: ${audioTelemetry.noiseFilter ? "ON" : "OFF"} | Echo Cancellation: ${audioTelemetry.echoCancellation ? "ON" : "OFF"}.`
  ]);

  // Voice Print Directory State (Fetched from PostgreSQL users/teachers)
  const [voicePrintRegistry, setVoicePrintRegistry] = useState<VoicePrintItem[]>([]);
  const [loadingRegistry, setLoadingRegistry] = useState(false);

  const isLiveLectureActive = activeSession && activeSession.status === "LIVE";
  const isRecording = audioTelemetry.isRecording;
  const micStatus = audioTelemetry.micStatus;
  const micMode = audioTelemetry.micMode;
  const hardwareSampleRate = audioTelemetry.hardwareSampleRate || 48000;
  const decibels = audioTelemetry.decibels;
  const waveHeights = audioTelemetry.waveHeights;
  const noiseFilter = audioTelemetry.noiseFilter;
  const echoCancellation = audioTelemetry.echoCancellation;

  // Add Timestamped Log
  const addLog = (msg: string) => {
    setVoiceLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev.slice(0, 49)]);
  };

  // Fetch Real Users / Teachers from PostgreSQL Database
  useEffect(() => {
    const fetchRegisteredTeachers = async () => {
      setLoadingRegistry(true);
      try {
        const res = await api.get<any>("/users/teachers").catch(() => null);
        if (res && res.data && Array.isArray(res.data) && res.data.length > 0) {
          const mapped: VoicePrintItem[] = res.data.map((u: any) => ({
            id: u.id,
            name: u.fullName || `${u.first_name || ""} ${u.last_name || ""}`.trim() || u.email || "Teacher",
            subject: u.department || activeSession?.subject || "Subject not assigned",
            printId: u.voice_print_id || "Not registered",
            role: u.role || "Teacher"
          }));
          setVoicePrintRegistry(mapped);
        } else if (user) {
          setVoicePrintRegistry([
            {
              id: user.id || "current-user",
              name: user.fullName || user.email?.split("@")[0] || "Authenticated User",
              subject: activeSession?.subject || "Subject not assigned",
              printId: "Not registered",
              role: user.role || "Teacher"
            }
          ]);
        }
      } catch (err) {
        if (user) {
          setVoicePrintRegistry([
            {
              id: user.id || "current-user",
              name: user.fullName || user.email?.split("@")[0] || "Authenticated User",
              subject: activeSession?.subject || "Subject not assigned",
              printId: "Not registered",
              role: user.role || "Teacher"
            }
          ]);
        }
      } finally {
        setLoadingRegistry(false);
      }
    };

    fetchRegisteredTeachers();
  }, [user, activeSession]);

  // Log live classroom session telemetry events
  useEffect(() => {
    if (isLiveLectureActive) {
      addLog(`[LivePipeline] Linked with Live Classroom session '${activeSession?.id}'. Recording: ${isRecording ? "ON" : "OFF"}.`);
    }
  }, [isLiveLectureActive, activeSession?.id, isRecording]);

  const handleToggleNoiseFilter = (checked: boolean) => {
    updateAudioTelemetry({ noiseFilter: checked });
    addLog(`Acoustic Noise Reduction updated: ${checked ? "ON" : "OFF"}`);
  };

  const handleToggleEchoCancellation = (checked: boolean) => {
    updateAudioTelemetry({ echoCancellation: checked });
    addLog(`Echo Cancellation updated: ${checked ? "ON" : "OFF"}`);
  };

  return (
    <div className="space-y-8">
      
      {/* Active Live Classroom Context Banner (Single Microphone Pipeline Owner) */}
      {isLiveLectureActive ? (
        <div className="p-6 rounded-3xl bg-blue-900 text-white space-y-4 shadow-lg border border-blue-800 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500 rounded-full filter blur-3xl opacity-20"></div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-blue-800/80 pb-4 z-10 relative">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl bg-blue-600/40 border border-blue-400/30 flex items-center justify-center text-blue-300">
                <Sparkles className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <span className="text-[10px] font-mono font-semibold text-blue-300 uppercase tracking-wider block">PIPELINE ATTACHED: Live Classroom</span>
                <h2 className="font-display text-xl font-bold text-white">{activeSession.title}</h2>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className={`px-3.5 py-1.5 rounded-full text-xs font-mono font-bold flex items-center gap-1.5 border ${
                isRecording 
                  ? "bg-red-500/20 border-red-500/40 text-red-300 animate-pulse" 
                  : "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
              }`}>
                <span className={`w-2 h-2 rounded-full ${isRecording ? "bg-red-400 animate-pulse" : "bg-emerald-400"}`}></span>
                {isRecording ? "● RECORDING CAPTURE ACTIVE" : "● AUDIO PIPELINE READY"}
              </span>
              <button 
                onClick={() => navigate("/live-classroom")}
                className="px-3.5 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-mono font-semibold border border-white/20 transition-colors flex items-center gap-1.5"
              >
                Session #{activeSession.id} <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-xs z-10 relative pt-1">
            <div className="p-2.5 rounded-xl bg-blue-950/60 border border-blue-800/60">
              <span className="text-blue-300/80 block uppercase text-[9px] font-bold">Source</span>
              <span className="font-semibold text-white mt-0.5 block">Live Classroom</span>
            </div>
            <div className="p-2.5 rounded-xl bg-blue-950/60 border border-blue-800/60">
              <span className="text-blue-300/80 block uppercase text-[9px] font-bold">Lecture Session</span>
              <span className="font-semibold text-white mt-0.5 block font-mono truncate">{activeSession.id}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-blue-950/60 border border-blue-800/60">
              <span className="text-blue-300/80 block uppercase text-[9px] font-bold">Microphone</span>
              <span className="font-semibold text-emerald-400 mt-0.5 block flex items-center gap-1">
                {micStatus === "active" ? "✓ Connected" : micStatus === "requesting" ? "Connecting..." : "Standby"}
              </span>
            </div>
            <div className="p-2.5 rounded-xl bg-blue-950/60 border border-blue-800/60">
              <span className="text-blue-300/80 block uppercase text-[9px] font-bold">Input / Output</span>
              <span className="font-semibold text-white mt-0.5 block text-[10px]">48kHz F32 → 16kHz PCM</span>
            </div>
            <div className="p-2.5 rounded-xl bg-blue-950/60 border border-blue-800/60">
              <span className="text-blue-300/80 block uppercase text-[9px] font-bold">Chunks Generated / Sent</span>
              <span className="font-semibold text-sky-300 mt-0.5 block font-mono">{audioTelemetry.chunksGenerated} / {audioTelemetry.chunksSent}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-blue-950/60 border border-blue-800/60">
              <span className="text-blue-300/80 block uppercase text-[9px] font-bold">STT &amp; Transcript</span>
              <span className="font-semibold text-emerald-300 mt-0.5 block">
                {isRecording ? "Receiving" : activeSession.transcript ? "Live" : "Ready"}
              </span>
            </div>
          </div>
        </div>
      ) : (
        /* Module Title Card */
        <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-2 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-48 h-48 bg-blue-50 rounded-full filter blur-2xl opacity-50"></div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
              <Sliders className="w-5.5 h-5.5" />
            </div>
            <div>
              <span className="text-xs font-mono font-bold text-blue-600 uppercase">Module 1 &amp; 2 • Audio Configuration &amp; Diagnostics</span>
              <h1 className="font-display text-2xl font-bold text-gray-900">Audio Processing &amp; Voice Diagnostics</h1>
            </div>
          </div>
          <p className="text-gray-500 text-sm max-w-3xl">
            Live Classroom is the single owner of microphone capture and audio recording. This console configures acoustic processing parameters, monitors hardware sample rates, and reviews teacher vocal print telemetry.
          </p>
        </div>
      )}

      {/* Notice Banner explaining the Single Recording Mechanism */}
      <div className="p-4 bg-sky-50 border border-sky-200 rounded-2xl flex items-center justify-between text-xs text-sky-900 shadow-2xs">
        <div className="flex items-center gap-3">
          <ShieldCheck className="w-5 h-5 text-sky-600 shrink-0" />
          <span>
            <strong>Single Recording Pipeline:</strong> Microphone capture, chunk generation, and Speech-to-Text streaming are exclusively managed by <strong>Live Classroom</strong> to eliminate duplicate streams.
          </span>
        </div>
        <button
          onClick={() => navigate("/live-classroom")}
          className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shrink-0 ml-4 shadow-sm"
        >
          Open Live Classroom <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Audio Configuration & Diagnostics Console */}
        <div className="lg:col-span-7 bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-8">
          <div className="flex items-center justify-between">
            <h3 className="font-display font-bold text-lg text-gray-900 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600" /> Audio Pipeline Telemetry
            </h3>
            <span className={`text-xs font-mono px-3 py-1 rounded-full border font-semibold flex items-center gap-1.5 ${
              isRecording 
                ? "bg-red-50 border-red-200 text-red-700 animate-pulse" 
                : micStatus === "active" 
                  ? "bg-emerald-50 border-emerald-200 text-emerald-700" 
                  : "bg-gray-50 border-gray-100 text-gray-500"
            }`}>
              <span className={`w-2 h-2 rounded-full ${
                isRecording 
                  ? "bg-red-500 animate-pulse"
                  : micStatus === "active" 
                    ? "bg-emerald-500 animate-pulse" 
                    : "bg-gray-400"
              }`}></span>
              STATUS: {
                isRecording 
                  ? "RECORDING (LIVE CLASSROOM ACTIVE)"
                  : micStatus === "active"
                    ? "HARDWARE MIC CONNECTED"
                    : "STANDBY"
              }
            </span>
          </div>

          {/* Soundwave Spectrum Driven by Shared Classroom Telemetry */}
          <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-2xl border border-dashed border-gray-200 space-y-6">
            
            <div className="flex items-center justify-center gap-1 h-24 w-full px-4">
              {waveHeights.map((h, idx) => (
                <motion.div 
                  key={idx}
                  animate={{ height: isRecording || micStatus === "active" ? h : 6 }}
                  className={`w-1.5 rounded-full transition-all duration-150 ${
                    isRecording 
                      ? "bg-gradient-to-t from-red-600 to-amber-400" 
                      : micStatus === "active"
                        ? "bg-gradient-to-t from-blue-600 to-sky-400" 
                        : "bg-gray-300"
                  }`}
                  style={{ minHeight: "6px" }}
                />
              ))}
            </div>

            {/* Real Audio Diagnostics */}
            <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-mono text-gray-600">
              <span className="flex items-center gap-1.5">
                <Volume2 className="w-4 h-4 text-gray-400" />
                Gain Level: {decibels} dB
              </span>
              <span className="flex items-center gap-1.5 text-slate-500">
                <Sliders className="w-4 h-4 text-gray-400" />
                Hardware Rate: {hardwareSampleRate ? `${hardwareSampleRate} Hz` : "Not initialized"}
              </span>
              <span className="flex items-center gap-1.5 text-slate-500">
                <Layers className="w-4 h-4 text-gray-400" />
                Chunks: {audioTelemetry.chunksGenerated} / {audioTelemetry.chunksSent}
              </span>
            </div>

            {/* Audio Quality Validation Diagnostics */}
            <div className="w-full grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono text-gray-600 bg-white p-3.5 rounded-2xl border border-gray-200 shadow-2xs">
              <div>
                <span className="text-[9px] text-gray-400 block uppercase font-bold">Hardware Rate</span>
                <span className="font-bold text-gray-800">{hardwareSampleRate ? `${hardwareSampleRate} Hz` : "Detecting..."}</span>
              </div>
              <div>
                <span className="text-[9px] text-gray-400 block uppercase font-bold">Processing Rate</span>
                <span className="font-bold text-gray-800">{hardwareSampleRate ? `${hardwareSampleRate} Hz` : "Detecting..."}</span>
              </div>
              <div>
                <span className="text-[9px] text-gray-400 block uppercase font-bold">Output Rate</span>
                <span className="font-bold text-blue-600">16000 Hz</span>
              </div>
              <div>
                <span className="text-[9px] text-gray-400 block uppercase font-bold">Output Format</span>
                <span className="font-bold text-emerald-600">16-bit PCM Mono</span>
              </div>
              <div>
                <span className="text-[9px] text-gray-400 block uppercase font-bold">Input Format</span>
                <span className="font-bold text-gray-800">Float32</span>
              </div>
              <div>
                <span className="text-[9px] text-gray-400 block uppercase font-bold">Channels</span>
                <span className="font-bold text-gray-800">1 (Mono)</span>
              </div>
              <div>
                <span className="text-[9px] text-gray-400 block uppercase font-bold">Chunk Duration</span>
                <span className="font-bold text-gray-800">2.5s - 3.0s</span>
              </div>
              <div>
                <span className="text-[9px] text-gray-400 block uppercase font-bold">STT Pipeline</span>
                <span className={`font-bold ${isRecording ? "text-emerald-600" : "text-gray-400"}`}>
                  {isRecording ? "Receiving" : "Standby"}
                </span>
              </div>
            </div>

            {/* Read-Only Microphone Capturing Status Indicator (Requirement 4 & 5) */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              {isRecording ? (
                <div className="flex items-center gap-3">
                  <span className="px-5 py-2.5 rounded-xl bg-red-50 border border-red-200 text-red-700 font-semibold flex items-center gap-2 text-sm shadow-sm">
                    <Mic className="w-4.5 h-4.5 text-red-600 animate-pulse" />
                    🎤 Microphone Capturing (Live Classroom Active)
                  </span>
                  <button
                    onClick={() => navigate("/live-classroom")}
                    className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-black text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-sm"
                  >
                    Go to Live Classroom <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : micStatus === "active" ? (
                <div className="flex items-center gap-3">
                  <span className="px-5 py-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 font-semibold flex items-center gap-2 text-sm">
                    <Mic className="w-4.5 h-4.5 text-emerald-600" />
                    🎤 Microphone Connected
                  </span>
                  <button
                    onClick={() => navigate("/live-classroom")}
                    className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-sm"
                  >
                    Start Recording in Live Classroom <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <span className="px-5 py-2.5 rounded-xl bg-gray-50 border border-gray-200 text-gray-600 font-semibold flex items-center gap-2 text-sm">
                    <MicOff className="w-4.5 h-4.5 text-gray-400" />
                    🎤 Microphone Standby
                  </span>
                  <button
                    onClick={() => navigate("/live-classroom")}
                    className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-sm"
                  >
                    Go to Live Classroom <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Audio Processing Configuration Controls */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-bold text-gray-700 uppercase tracking-wider">Audio Hardware Configuration</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50/70 rounded-2xl border border-gray-100 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold block text-gray-800">Acoustic Noise Reduction</span>
                  <span className="text-[10px] text-gray-400">Filter classroom ambient noise</span>
                </div>
                <input 
                  type="checkbox" 
                  checked={noiseFilter} 
                  onChange={(e) => handleToggleNoiseFilter(e.target.checked)}
                  className="w-4 h-4 text-blue-600 accent-blue-600 cursor-pointer" 
                />
              </div>

              <div className="p-4 bg-gray-50/70 rounded-2xl border border-gray-100 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold block text-gray-800">Echo Cancellation</span>
                  <span className="text-[10px] text-gray-400">Cancel speaker-feedback loop</span>
                </div>
                <input 
                  type="checkbox" 
                  checked={echoCancellation} 
                  onChange={(e) => handleToggleEchoCancellation(e.target.checked)}
                  className="w-4 h-4 text-blue-600 accent-blue-600 cursor-pointer" 
                />
              </div>
            </div>
          </div>

          {/* Session Transcript Status Card if available */}
          {activeSession?.transcript && (
            <div className="p-6 bg-emerald-50/50 rounded-2xl border border-emerald-100 space-y-3">
              <div className="flex items-center justify-between border-b border-emerald-100/40 pb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <span className="text-sm font-bold text-emerald-800">Live Transcript Synchronized</span>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">
                  SESSION #{activeSession.id}
                </span>
              </div>
              <div className="bg-white p-4 rounded-xl border border-emerald-100/50 space-y-1">
                <span className="text-[10px] text-gray-400 block font-semibold uppercase tracking-wider">Latest Lecture Transcript</span>
                <p className="text-sm text-gray-700 leading-relaxed font-sans line-clamp-3">{activeSession.transcript}</p>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar: Vocal Print Registry & Pipeline Logs */}
        <div className="lg:col-span-5 space-y-8">
          
          {/* Active Voiceprint Directory */}
          <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="font-display font-bold text-base text-gray-900 flex items-center gap-2">
                <User className="w-4.5 h-4.5 text-blue-600" /> Vocal Print Registry
              </h3>
              <span className="text-[10px] font-mono text-gray-400 bg-gray-50 border border-gray-100 px-2 py-0.5 rounded-md">
                PostgreSQL Table: users
              </span>
            </div>
            
            <div className="space-y-3">
              {loadingRegistry ? (
                <div className="p-4 text-center text-xs text-gray-400 bg-gray-50 rounded-2xl">
                  Loading registered teachers from database...
                </div>
              ) : voicePrintRegistry.length === 0 ? (
                <div className="p-6 text-center text-xs text-gray-400 bg-gray-50 rounded-2xl border border-gray-100 space-y-1">
                  <User className="w-5 h-5 mx-auto text-gray-300" />
                  <p className="font-semibold text-gray-600">No voice prints registered.</p>
                  <p className="text-[11px] text-gray-400">Authenticated instructors can register voiceprints in profile settings.</p>
                </div>
              ) : (
                voicePrintRegistry.map((t) => {
                  const isActive = selectedSpeaker === t.name;
                  return (
                    <button
                      key={t.id}
                      onClick={() => {
                        setSelectedSpeaker(t.name);
                        addLog(`Speaker selection target set to '${t.name}'`);
                      }}
                      className={`w-full p-4 rounded-2xl text-left border transition-all flex items-center justify-between ${
                        isActive 
                          ? "bg-blue-50/50 border-blue-200 shadow-sm" 
                          : "bg-white border-gray-100 hover:bg-gray-50"
                      }`}
                    >
                      <div>
                        <span className="text-xs font-bold block text-gray-800">{t.name}</span>
                        <span className="text-[10px] text-gray-400 mt-0.5 block">{t.subject} • ({t.role})</span>
                      </div>
                      <span className={`text-[10px] font-mono font-semibold px-2 py-1 rounded-lg border ${
                        t.printId === "Not registered" 
                          ? "bg-gray-50 text-gray-500 border-gray-200" 
                          : "bg-blue-50 text-blue-700 border-blue-200"
                      }`}>
                        {t.printId}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Console Pipelines Audit Log */}
          <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-4">
            <h3 className="font-display font-bold text-base text-gray-900 flex items-center gap-2">
              <Cpu className="w-4.5 h-4.5 text-blue-600" /> Audio Pipeline Logs
            </h3>
            
            <div className="bg-gray-950 p-4 rounded-2xl font-mono text-[10px] text-gray-300 space-y-2 h-56 overflow-y-auto border border-gray-900 select-text leading-relaxed">
              {voiceLogs.length === 0 ? (
                <div className="text-gray-500 text-center py-4">Audio pipeline standby. Live Classroom controls recording.</div>
              ) : (
                voiceLogs.map((log, i) => (
                  <div key={i} className="text-emerald-400 truncate">
                    <span className="text-gray-500">&gt;</span> {log}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
