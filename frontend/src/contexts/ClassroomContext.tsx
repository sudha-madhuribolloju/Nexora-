import React, { createContext, useContext, useState, useEffect, useRef } from "react";
import { calculateRMSAndDb } from "../utils/audioProcessor";

export interface ActiveClassroomSession {
  id: string;
  title: string;
  subject: string;
  teacherName: string;
  teacherId?: string;
  status: "LIVE" | "ENDED";
  startedAt: string;
  recordingId?: string | null;
  transcript?: string;
  summary?: any;
  nlp?: any;
}

export interface AudioTelemetry {
  isRecording: boolean;
  micStatus: "idle" | "requesting" | "active" | "denied" | "error";
  micMode: "hardware" | "simulated" | "standby";
  hardwareSampleRate: number;
  processingRate: number;
  outputRate: number;
  inputFormat: string;
  outputFormat: string;
  chunkDuration: number;
  chunksGenerated: number;
  chunksSent: number;
  wsStatus: "connected" | "connecting" | "disconnected";
  sttStatus: "active" | "idle" | "error" | "receiving";
  audioLevel: number;
  decibels: number;
  waveHeights: number[];
  noiseFilter: boolean;
  echoCancellation: boolean;
}

interface ClassroomContextType {
  activeSession: ActiveClassroomSession | null;
  mediaStream: MediaStream | null;
  audioContext: AudioContext | null;
  analyserNode: AnalyserNode | null;
  audioTelemetry: AudioTelemetry;
  startSession: (sessionData: Partial<ActiveClassroomSession>) => ActiveClassroomSession;
  loadSession: (sessionData: ActiveClassroomSession) => void;
  updateSession: (partialData: Partial<ActiveClassroomSession>) => void;
  endSession: (finalData?: Partial<ActiveClassroomSession>) => void;
  clearSession: () => void;
  initMicrophone: (deviceId?: string) => Promise<MediaStream | null>;
  attachMediaStream: (stream: MediaStream, audioCtx?: AudioContext, analyser?: AnalyserNode) => void;
  stopMicrophone: () => void;
  updateAudioTelemetry: (partial: Partial<AudioTelemetry>) => void;
  incrementChunks: (sent?: boolean) => void;
}

const ClassroomContext = createContext<ClassroomContextType | undefined>(undefined);

function generateLectureSessionId(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const time = String(now.getHours()).padStart(2, "0") + String(now.getMinutes()).padStart(2, "0");
  const randNum = String(Math.floor(100 + Math.random() * 900));
  return `LC-${year}${month}${day}-${time}-${randNum}`;
}

export const ClassroomProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeSession, setActiveSession] = useState<ActiveClassroomSession | null>(() => {
    try {
      const savedRaw = localStorage.getItem("nexora_active_classroom_session");
      if (!savedRaw) return null;
      const saved = JSON.parse(savedRaw);
      
      // Cleanse any legacy placeholder strings stored during past test runs
      if (saved.transcript && (
        saved.transcript.includes("Standard live audio") ||
        saved.transcript.includes("Standard lecture transcript")
      )) {
        saved.transcript = "";
      }
      if (saved.summary && (
        JSON.stringify(saved.summary).includes("Whisper STT speech recognition, and real-time audio NLP analysis") ||
        JSON.stringify(saved.summary).includes("Standard lecture")
      )) {
        saved.summary = null;
      }
      if (saved.subject && (
        saved.subject.includes("Quantum Physics & Computing") ||
        saved.subject.includes("General Lecture")
      )) {
        saved.subject = "";
      }
      if (saved.title && saved.title.includes("Quantum Physics & Computing")) {
        saved.title = "Live Classroom Session";
      }
      return saved;
    } catch {
      return null;
    }
  });

  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const [audioTelemetry, setAudioTelemetry] = useState<AudioTelemetry>({
    isRecording: false,
    micStatus: "idle",
    micMode: "standby",
    hardwareSampleRate: 48000,
    processingRate: 48000,
    outputRate: 16000,
    inputFormat: "48 kHz Float32",
    outputFormat: "16 kHz 16-bit PCM Mono",
    chunkDuration: 3.0,
    chunksGenerated: 0,
    chunksSent: 0,
    wsStatus: "disconnected",
    sttStatus: "idle",
    audioLevel: 0,
    decibels: -60,
    waveHeights: new Array(30).fill(6),
    noiseFilter: true,
    echoCancellation: true,
  });

  useEffect(() => {
    if (activeSession) {
      localStorage.setItem("nexora_active_classroom_session", JSON.stringify(activeSession));
    } else {
      localStorage.removeItem("nexora_active_classroom_session");
    }
  }, [activeSession]);

  const updateAudioTelemetry = (partial: Partial<AudioTelemetry>) => {
    setAudioTelemetry(prev => ({ ...prev, ...partial }));
  };

  const incrementChunks = (sent?: boolean) => {
    setAudioTelemetry(prev => ({
      ...prev,
      chunksGenerated: prev.chunksGenerated + 1,
      chunksSent: sent ? prev.chunksSent + 1 : prev.chunksSent,
    }));
  };

  const startWaveformLoop = (analyser: AnalyserNode) => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    const updateLoop = () => {
      if (!analyserRef.current) return;
      const { db, rms } = calculateRMSAndDb(analyserRef.current);
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);

      const newHeights: number[] = [];
      const step = Math.floor(dataArray.length / 30) || 1;
      for (let i = 0; i < 30; i++) {
        const val = dataArray[(i * step) % dataArray.length] || 0;
        newHeights.push(Math.max(6, Math.round((val / 255) * 55)));
      }

      setAudioTelemetry(prev => ({
        ...prev,
        decibels: db,
        audioLevel: Math.round(rms * 100),
        waveHeights: newHeights,
      }));

      animationFrameRef.current = requestAnimationFrame(updateLoop);
    };

    animationFrameRef.current = requestAnimationFrame(updateLoop);
  };

  const attachMediaStream = (stream: MediaStream, audioCtx?: AudioContext, analyser?: AnalyserNode) => {
    mediaStreamRef.current = stream;
    setMediaStream(stream);

    if (audioCtx) {
      audioContextRef.current = audioCtx;
      setAudioContext(audioCtx);
      setAudioTelemetry(prev => ({
        ...prev,
        hardwareSampleRate: audioCtx.sampleRate || 48000,
        processingRate: audioCtx.sampleRate || 48000,
        micStatus: "active",
        micMode: "hardware",
      }));
    }

    if (analyser) {
      analyserRef.current = analyser;
      setAnalyserNode(analyser);
      startWaveformLoop(analyser);
    }
  };

  const initMicrophone = async (_deviceId?: string): Promise<MediaStream | null> => {
    if (mediaStreamRef.current && mediaStreamRef.current.active && mediaStreamRef.current.getAudioTracks().some(t => t.readyState === "live")) {
      console.log("[Audio] Returning active Live Classroom microphone stream from context.");
      return mediaStreamRef.current;
    }
    console.warn("[Audio] Live Classroom is the single owner of microphone capture. Please initialize from Live Classroom.");
    return null;
  };

  const stopMicrophone = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => {
        try { t.stop(); } catch (e) {}
      });
      mediaStreamRef.current = null;
      setMediaStream(null);
    }
    if (audioContextRef.current) {
      try { audioContextRef.current.close(); } catch (e) {}
      audioContextRef.current = null;
      setAudioContext(null);
    }
    analyserRef.current = null;
    setAnalyserNode(null);
    setAudioTelemetry(prev => ({
      ...prev,
      isRecording: false,
      micStatus: "idle",
      micMode: "standby",
      decibels: -60,
      audioLevel: 0,
      waveHeights: new Array(30).fill(6),
      sttStatus: "idle",
      wsStatus: "disconnected",
    }));
  };

  const loadSession = (sessionData: ActiveClassroomSession) => {
    setActiveSession(sessionData);
  };

  const startSession = (sessionData: Partial<ActiveClassroomSession>): ActiveClassroomSession => {
    // If the provided id is empty or matches an ended session, generate a fresh ID
    const shouldGenerateNewId = !sessionData.id || (activeSession && activeSession.id === sessionData.id && activeSession.status === "ENDED");
    const resolvedId = shouldGenerateNewId ? generateLectureSessionId() : sessionData.id!;

    const newSession: ActiveClassroomSession = {
      id: resolvedId,
      title: sessionData.title || "Live Audio Classroom Session",
      subject: sessionData.subject || "",
      teacherName: sessionData.teacherName || "Instructor",
      teacherId: sessionData.teacherId,
      status: "LIVE",
      startedAt: sessionData.startedAt || new Date().toISOString(),
      recordingId: sessionData.recordingId || null,
      transcript: sessionData.transcript || "",
      summary: sessionData.summary || null,
      nlp: sessionData.nlp || null,
    };
    console.log(`[SESSION] CREATED id=${newSession.id}`);
    console.log(`[SESSION] ACTIVE id=${newSession.id}`);
    console.log(`[SESSION] ACTIVE_SESSION_ID=${newSession.id}`);
    setActiveSession(newSession);
    return newSession;
  };

  const updateSession = (partialData: Partial<ActiveClassroomSession>) => {
    setActiveSession(prev => {
      if (!prev) {
        if (partialData.id) {
          return {
            id: partialData.id,
            title: partialData.title || "Live Classroom Session",
            subject: partialData.subject || "General Lecture",
            teacherName: partialData.teacherName || "Instructor",
            status: partialData.status || "LIVE",
            startedAt: partialData.startedAt || new Date().toISOString(),
            ...partialData,
          };
        }
        return null;
      }
      return {
        ...prev,
        ...partialData,
      };
    });
  };

  const endSession = (finalData?: Partial<ActiveClassroomSession>) => {
    stopMicrophone();
    setActiveSession(prev => {
      if (!prev) return null;
      return {
        ...prev,
        status: "ENDED",
        transcript: finalData?.transcript !== undefined ? finalData.transcript : prev.transcript,
        summary: finalData?.summary !== undefined ? finalData.summary : prev.summary,
        nlp: finalData?.nlp !== undefined ? finalData.nlp : prev.nlp,
      };
    });
  };

  const clearSession = () => {
    stopMicrophone();
    setActiveSession(null);
  };

  return (
    <ClassroomContext.Provider value={{
      activeSession,
      mediaStream,
      audioContext,
      analyserNode,
      audioTelemetry,
      startSession,
      loadSession,
      updateSession,
      endSession,
      clearSession,
      initMicrophone,
      attachMediaStream,
      stopMicrophone,
      updateAudioTelemetry,
      incrementChunks,
    }}>
      {children}
    </ClassroomContext.Provider>
  );
};

export const useClassroomSession = (): ClassroomContextType => {
  const context = useContext(ClassroomContext);
  if (!context) {
    throw new Error("useClassroomSession must be used within a ClassroomProvider");
  }
  return context;
};
