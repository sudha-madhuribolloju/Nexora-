import React, { useState, useEffect, useRef } from "react";
import { 
  Mic, 
  Square, 
  Volume2, 
  ShieldCheck, 
  Sparkles, 
  Activity, 
  User, 
  CheckCircle, 
  Cpu, 
  Clock,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { motion } from "motion/react";
import { classroomService } from "../services/classroom";

export default function ModuleAudioVoice() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordTime, setRecordTime] = useState(0);
  const [selectedTeacher, setSelectedTeacher] = useState("Dr. Sarah Jenkins");
  const [noiseFilter, setNoiseFilter] = useState(true);
  const [echoCancellation, setEchoCancellation] = useState(true);
  const [decibels, setDecibels] = useState(-45);
  const [voiceLogs, setVoiceLogs] = useState<string[]>([
    "System standby. Audio pipeline loaded at 16000Hz (16-bit PCM).",
    "Acoustic feedback loop checked: Clear."
  ]);
  const [backendResult, setBackendResult] = useState<{
    speaker: string;
    confidence: number;
    voicePrintId: string;
    clarityScore: string;
    noiseReducedTranscript: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  // Simulated visual waveform nodes
  const [waveHeights, setWaveHeights] = useState<number[]>(Array(30).fill(10));

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isRecording) {
      timer = setInterval(() => {
        setRecordTime(prev => prev + 1);
        // Random fluctuate decibels & waveform heights
        setDecibels(Math.floor(Math.random() * 25) - 30);
        setWaveHeights(Array(30).fill(0).map(() => Math.floor(Math.random() * 50) + 10));
      }, 1000);
    } else {
      setRecordTime(0);
      setDecibels(-52);
      setWaveHeights(Array(30).fill(8));
    }
    return () => clearInterval(timer);
  }, [isRecording]);

  const addLog = (msg: string) => {
    setVoiceLogs(prev => [ `[${new Date().toLocaleTimeString()}] ${msg}`, ...prev]);
  };

  const handleStartRecording = () => {
    setIsRecording(true);
    addLog("Mic input started. Captured PCM Little Endian channel.");
    addLog(`Applying Active Noise Cancellation (ANC: ${noiseFilter ? "ON" : "OFF"}).`);
  };

  const handleStopRecording = async () => {
    setIsRecording(false);
    setLoading(true);
    addLog("Mic input suspended. Sending buffer to server `/api/voice-processing`...");
    
    try {
      const data = await classroomService.processVoice(selectedTeacher);
      
      setBackendResult(data);
      addLog(`Voice print verified: Match found for '${data.speaker}' (ID: ${data.voicePrintId})`);
      addLog(`Confidence score: ${Math.floor(data.confidence * 100)}%`);
    } catch (error: any) {
      addLog(`Processing Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const teachers = [
    { name: "Dr. Sarah Jenkins", subject: "Quantum Computing & Dynamics", printId: "VP_SCH_99812" },
    { name: "Prof. Robert Chen", subject: "Artificial Neural Architectures", printId: "VP_SCH_11048" },
    { name: "Dr. Maria Rodriguez", subject: "Bioinformatics & Systems", printId: "VP_SCH_77402" },
  ];

  return (
    <div className="space-y-8">
      
      {/* Module Title Card */}
      <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-2 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-blue-50 rounded-full filter blur-2xl opacity-50"></div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
            <Mic className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-blue-600 uppercase">Module 1 &amp; 2</span>
            <h1 className="font-display text-2xl font-bold text-gray-900">Audio Processing &amp; Voice Recognition</h1>
          </div>
        </div>
        <p className="text-gray-500 text-sm max-w-3xl">
          NEXORA registers academic lectures, normalizes sound vectors, suppresses classroom echoes, and uses vocal biometric voiceprints to index lectures by respective teachers.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Recording Console */}
        <div className="lg:col-span-7 bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-8">
          <div className="flex items-center justify-between">
            <h3 className="font-display font-bold text-lg text-gray-900 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600" /> Live Recording Console
            </h3>
            <span className="text-xs font-mono px-3 py-1 rounded-full bg-gray-50 border border-gray-100 font-semibold text-gray-500">
              STATUS: {isRecording ? "RECORDING" : "STANDBY"}
            </span>
          </div>

          {/* Interactive Recording Area */}
          <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-2xl border border-dashed border-gray-200 space-y-6">
            
            {/* Spectrogram / Waveform Nodes */}
            <div className="flex items-center justify-center gap-1 h-24 w-full px-4">
              {waveHeights.map((h, idx) => (
                <motion.div 
                  key={idx}
                  animate={{ height: isRecording ? h : 6 }}
                  className={`w-1.5 rounded-full transition-all duration-150 ${
                    isRecording ? "bg-gradient-to-t from-blue-600 to-sky-400" : "bg-gray-300"
                  }`}
                  style={{ minHeight: "6px" }}
                />
              ))}
            </div>

            {/* Timer & Decibels */}
            <div className="flex items-center gap-6 text-sm font-mono text-gray-600">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-gray-400" />
                Time: {Math.floor(recordTime / 60).toString().padStart(2, "0")}:
                {(recordTime % 60).toString().padStart(2, "0")}s
              </span>
              <span className="flex items-center gap-1.5">
                <Volume2 className="w-4 h-4 text-gray-400" />
                Gain: {decibels} dB
              </span>
            </div>

            {/* Rec Buttons */}
            <div className="flex items-center gap-4">
              {!isRecording ? (
                <button
                  onClick={handleStartRecording}
                  className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center gap-2 transition-all shadow-md shadow-blue-100 text-sm"
                >
                  <Mic className="w-4.5 h-4.5 animate-pulse" /> Start Mic Capture
                </button>
              ) : (
                <button
                  onClick={handleStopRecording}
                  className="px-6 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-semibold flex items-center gap-2 transition-all shadow-md shadow-red-100 text-sm"
                >
                  <Square className="w-4.5 h-4.5" /> Stop &amp; Analyze Voice
                </button>
              )}
            </div>
          </div>

          {/* Controls & Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50/50 rounded-2xl border border-gray-100 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold block text-gray-700">Acoustic Noise Reduction</span>
                <span className="text-[10px] text-gray-400">Filter classroom ambient noise</span>
              </div>
              <input 
                type="checkbox" 
                checked={noiseFilter} 
                onChange={(e) => {
                  setNoiseFilter(e.target.checked);
                  addLog(`Noise reduction toggle changed to ${e.target.checked ? "ON" : "OFF"}`);
                }}
                className="w-4 h-4 text-blue-600 accent-blue-600" 
              />
            </div>

            <div className="p-4 bg-gray-50/50 rounded-2xl border border-gray-100 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold block text-gray-700">Echo Cancellation</span>
                <span className="text-[10px] text-gray-400">Cancel speaker-feedback loop</span>
              </div>
              <input 
                type="checkbox" 
                checked={echoCancellation} 
                onChange={(e) => {
                  setEchoCancellation(e.target.checked);
                  addLog(`Echo cancellation toggle changed to ${e.target.checked ? "ON" : "OFF"}`);
                }}
                className="w-4 h-4 text-blue-600 accent-blue-600" 
              />
            </div>
          </div>

          {/* Display Voice recognition results */}
          {loading && (
            <div className="p-6 bg-blue-50/40 rounded-2xl border border-blue-100 animate-pulse flex items-center gap-3 text-sm text-blue-700 font-semibold">
              <Cpu className="w-5 h-5 animate-spin" /> Analyzing voiceprint features and retrieving verified lectures from Gemini model...
            </div>
          )}

          {backendResult && !loading && (
            <div className="p-6 bg-emerald-50/50 rounded-2xl border border-emerald-100 space-y-4">
              <div className="flex items-center justify-between border-b border-emerald-100/40 pb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <span className="text-sm font-bold text-emerald-800">Voice Print Authenticated</span>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">
                  MATCH: {Math.floor(backendResult.confidence * 100)}%
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-gray-400 block font-medium uppercase text-[9px]">Teacher Matching Name</span>
                  <span className="text-gray-800 font-bold text-sm block mt-0.5">{backendResult.speaker}</span>
                </div>
                <div>
                  <span className="text-gray-400 block font-medium uppercase text-[9px]">VoicePrint Database ID</span>
                  <span className="text-gray-800 font-mono font-bold mt-0.5 block">{backendResult.voicePrintId}</span>
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-emerald-100/50">
                <span className="text-[10px] text-gray-400 block font-semibold mb-1 uppercase tracking-wider">Clean Speech Transcript</span>
                <p className="text-sm text-gray-700 leading-relaxed font-sans">{backendResult.noiseReducedTranscript}</p>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar logs / matched Directory */}
        <div className="lg:col-span-5 space-y-8">
          
          {/* Active Voiceprint Directory */}
          <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-5">
            <h3 className="font-display font-bold text-base text-gray-900 flex items-center gap-2">
              <User className="w-4.5 h-4.5 text-blue-600" /> Vocal print Registry
            </h3>
            
            <div className="space-y-3">
              {teachers.map((t) => {
                const isActive = selectedTeacher === t.name;
                return (
                  <button
                    key={t.printId}
                    onClick={() => {
                      setSelectedTeacher(t.name);
                      addLog(`Vocal print target focus shifted to ${t.name}`);
                    }}
                    className={`w-full p-4 rounded-2xl text-left border transition-all flex items-center justify-between ${
                      isActive 
                        ? "bg-blue-50/50 border-blue-200 shadow-sm" 
                        : "bg-white border-gray-100 hover:bg-gray-50"
                    }`}
                  >
                    <div>
                      <span className="text-xs font-bold block text-gray-800">{t.name}</span>
                      <span className="text-[10px] text-gray-400 mt-0.5 block">{t.subject}</span>
                    </div>
                    <span className="text-[10px] font-mono font-semibold text-gray-500 bg-gray-50 border border-gray-100 px-2 py-1 rounded-lg">
                      {t.printId}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Console Pipelines Audit Log */}
          <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-4">
            <h3 className="font-display font-bold text-base text-gray-900 flex items-center gap-2">
              <Cpu className="w-4.5 h-4.5 text-blue-600" /> Audio Pipeline Logs
            </h3>
            
            <div className="bg-gray-950 p-4 rounded-2xl font-mono text-[10px] text-gray-300 space-y-2 h-48 overflow-y-auto border border-gray-900 select-text leading-relaxed">
              {voiceLogs.map((log, i) => (
                <div key={i} className="text-emerald-400 truncate">
                  <span className="text-gray-500">&gt;</span> {log}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
