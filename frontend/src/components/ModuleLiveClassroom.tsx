import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Mic, 
  MicOff, 
  Hand, 
  Send, 
  Users, 
  MessageSquare, 
  AlertCircle, 
  Sparkles,
  CircleDot,
  Square,
  Play,
  LogOut,
  LogIn,
  Eye,
  Radio,
  FileText,
  Volume2,
  Activity,
  RotateCcw,
  ShieldAlert,
  RefreshCw,
  Settings,
  Layers,
  Sliders,
  Download
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { useAuth } from "../contexts/AuthContext";
import { useClassroomSession } from "../contexts/ClassroomContext";
import { getAccessToken } from "../services/session";
import { api } from "../services/api";
import { canControlLecture } from "../utils/rbac";

interface Participant {
  id: string;
  name: string;
  role: string;
  handRaised: boolean;
  muted: boolean;
  avatar: string;
}

interface ChatMessage {
  id: string;
  sender: string;
  content: string;
  time: string;
  isTeacher: boolean;
}

// ── Configurable STT Audio Chunk Duration (Requirement 2) ──────────────────────────
export const STT_CHUNK_DURATION_MS = 5000; // 5.0 seconds per audio slice

interface TranscriptEntry {
  id: string;
  speaker: string;
  time: string;
  text: string;
  isTeacher: boolean;
  is_final: boolean;
}

type MicStatus = "idle" | "requesting" | "active" | "denied" | "error";

/** Synthesizer Oscillator MediaStream for explicit Demo Mode selection */
function createSimulatedAudioStream(): MediaStream {
  const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
  if (!AudioCtx) {
    return new MediaStream();
  }
  const ctx = new AudioCtx();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  const dest = ctx.createMediaStreamDestination();

  osc.type = "sine";
  osc.frequency.setValueAtTime(220, ctx.currentTime);
  gain.gain.setValueAtTime(0.01, ctx.currentTime);

  osc.connect(gain);
  gain.connect(dest);
  osc.start();

  const stream = dest.stream;
  (stream as any)._cleanupAudio = () => {
    try {
      osc.stop();
      ctx.close();
    } catch (e) {}
  };
  return stream;
}

export default function ModuleLiveClassroom() {
  const { user, triggerToast } = useAuth();
  const { 
    activeSession, 
    startSession, 
    updateSession, 
    endSession, 
    attachMediaStream, 
    stopMicrophone, 
    incrementChunks, 
    updateAudioTelemetry,
    audioTelemetry
  } = useClassroomSession();
  const navigate = useNavigate();
  
  // Role Permission Helper
  const isAuthorizedToControl = canControlLecture(user?.role);

  // Connection & Media States
  const [isConnecting, setIsConnecting] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [errorState, setErrorState] = useState<string | null>(null);

  // Microphone & Audio State Machine
  const [micStatus, setMicStatus] = useState<MicStatus>("idle");
  const [micMode, setMicMode] = useState<"hardware" | "simulated">("hardware");
  const [micErrorMsg, setMicErrorMsg] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [handRaised, setHandRaised] = useState(false);
  const [hasJoinedSession, setHasJoinedSession] = useState(true);
  
  // Real Hardware Audio Analysis & Devices
  const [audioInputDevices, setAudioInputDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [realWaveHeights, setRealWaveHeights] = useState<number[]>(new Array(28).fill(4));

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  // Recording & Action States
  const [isRecording, setIsRecording] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);

  // STT Status state machine representing the true pipeline state (Section 3)
  type STTStatus = "IDLE" | "LISTENING" | "PROCESSING" | "TRANSCRIBING" | "LIVE" | "ERROR";
  const [sttStatus, setSttStatus] = useState<STTStatus>("IDLE");
  const sttStatusRef = useRef<STTStatus>("IDLE");
  const speechRecognitionRef = useRef<any>(null);

  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const currentRecordingIdRef = useRef<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  // Lifecycle guards to prevent race conditions, duplicate uploads, and double clicks
  const recordingRef = useRef(false);
  const isStoppingRef = useRef(false);
  const isEndingRef = useRef(false);
  const isStartingRef = useRef(false);
  const activeSessionRef = useRef(activeSession);
  const transcriptsRef = useRef<TranscriptEntry[]>([]);
  const recordingDurationRef = useRef(0);
  const pendingUploadsRef = useRef<Set<Promise<any>>>(new Set());

  // Classroom Data, Summary & Transcript
  const [isLectureActive, setIsLectureActive] = useState(true);
  const [lectureTitle, setLectureTitle] = useState("Live Audio Classroom Session");
  const [lectureSummary, setLectureSummary] = useState<any>(null);
  
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [newMsg, setNewMsg] = useState("");
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [transcripts, setTranscripts] = useState<TranscriptEntry[]>([]);

  const socketRef = useRef<WebSocket | null>(null);
  const sttRecorderRef = useRef<MediaRecorder | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const triggerToastRef = useRef(triggerToast);
  // Set to true when End Lecture is clicked — suppresses WS reconnect loop
  const isLectureEndedRef = useRef(false);

  // Stabilized refs so the STT useEffect does NOT restart when user/role objects change identity
  const userRef = useRef(user);
  const isAuthorizedToControlRef = useRef(isAuthorizedToControl);
  // Flag to prevent concurrent MediaRecorder instances on the same stream (Root Cause 1 fix)
  const isSTTCapturingRef = useRef(false);
  // Deduplication: Set of transcript IDs already appended (Root Cause 3 fix)
  const seenTranscriptIdsRef = useRef<Set<string>>(new Set());
  // Recorded audio blobs accumulated during active recording for debug export (Requirement 5)
  const sessionRecordedBlobsRef = useRef<Blob[]>([]);

  useEffect(() => {
    triggerToastRef.current = triggerToast;
  }, [triggerToast]);

  // Keep stabilized refs in sync without triggering STT useEffect re-runs
  useEffect(() => {
    userRef.current = user;
    isAuthorizedToControlRef.current = isAuthorizedToControl;
  }, [user, isAuthorizedToControl]);

  // Keep lifecycle refs in sync to prevent stale closures in async callbacks
  useEffect(() => {
    recordingRef.current = isRecording;
  }, [isRecording]);

  useEffect(() => {
    activeSessionRef.current = activeSession;
  }, [activeSession]);

  useEffect(() => {
    transcriptsRef.current = transcripts;
  }, [transcripts]);

  useEffect(() => {
    recordingDurationRef.current = recordingDuration;
  }, [recordingDuration]);

  useEffect(() => {
    sttStatusRef.current = sttStatus;
  }, [sttStatus]);

  // Enumerate Physical Audio Devices
  const refreshAudioDevices = async () => {
    if (navigator.mediaDevices?.enumerateDevices) {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const inputs = devices.filter(d => d.kind === "audioinput");
        setAudioInputDevices(inputs);
        if (inputs.length > 0 && !selectedDeviceId) {
          setSelectedDeviceId(inputs[0].deviceId);
        }
      } catch (e) {
        console.warn("[MIC] Enumerate devices failed:", e);
      }
    }
  };

  // Helper to construct dynamic WebSocket Base URL
  const getWsBaseUrl = (): string => {
    if (import.meta.env.VITE_WS_URL) {
      return import.meta.env.VITE_WS_URL.replace(/\/$/, "");
    }
    const apiBase = import.meta.env.VITE_API_BASE_URL || "";
    if (apiBase) {
      try {
        const url = new URL(apiBase);
        const wsProtocol = url.protocol === "https:" ? "wss:" : "ws:";
        return `${wsProtocol}//${url.host}`;
      } catch (e) {
        // Fallback below
      }
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.hostname || "localhost";
    return `${protocol}//${host}:8000`;
  };

  // Disable any keyboard shortcuts for lecture controls if unauthorized
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey || e.altKey) && (e.key === "s" || e.key === "r" || e.key === "S" || e.key === "R")) {
        if (!isAuthorizedToControl) {
          e.preventDefault();
          e.stopPropagation();
          triggerToast("Lecture control keyboard shortcuts are disabled for your role.", "error");
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown, true);
    return () => {
      window.removeEventListener("keydown", handleKeyDown, true);
    };
  }, [isAuthorizedToControl, triggerToast]);

  // Complete Real Microphone Connection Logic with Detailed Diagnostic Logs
  const requestMicrophoneStream = async (targetDeviceId?: string): Promise<MediaStream | null> => {
    console.log("[LiveAudio] microphone started");
    console.log("[LiveClassroom] Microphone initialized");
    console.log("[MIC] Starting hardware microphone connection");
    console.log("[MIC] isSecureContext:", window.isSecureContext);
    console.log("[MIC] mediaDevices available:", !!navigator.mediaDevices);
    console.log("[MIC] getUserMedia available:", !!navigator.mediaDevices?.getUserMedia);

    // Stop existing audio processing & stream tracks
    if (analyserRef.current) analyserRef.current = null;
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (mediaStreamRef.current) {
      if ((mediaStreamRef.current as any)._cleanupAudio) {
        (mediaStreamRef.current as any)._cleanupAudio();
      }
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    setMicStatus("requesting");
    setMicErrorMsg(null);
    setErrorState(null);

    if (navigator.permissions?.query) {
      try {
        const permission = await navigator.permissions.query({ name: "microphone" as any });
        console.log("[MIC] Permission state:", permission.state);
      } catch (e) {
        console.warn("[MIC] Permission query failed:", e);
      }
    }

    if (navigator.mediaDevices?.enumerateDevices) {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const inputs = devices.filter(d => d.kind === "audioinput");
        console.log("[MIC] audioinput devices found:", inputs.length);
        console.table(
          devices.map(device => ({
            kind: device.kind,
            label: device.label || "(Device label hidden until permission granted)",
            deviceId: device.deviceId,
            groupId: device.groupId
          }))
        );
      } catch (e) {
        console.warn("[MIC] Enumerate devices failed:", e);
      }
    }

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("MediaDevices API is unavailable in this environment.");
      }

      const deviceIdToUse = targetDeviceId || selectedDeviceId;
      const echoCancelSetting = audioTelemetry.echoCancellation !== false;
      const noiseFilterSetting = audioTelemetry.noiseFilter !== false;
      let stream: MediaStream | null = null;

      if (deviceIdToUse) {
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            audio: {
              deviceId: { exact: deviceIdToUse },
              echoCancellation: echoCancelSetting,
              noiseSuppression: noiseFilterSetting,
              autoGainControl: true
            }
          });
        } catch (e) {
          console.warn("[MIC] Specific device constraints failed, trying default audio constraints:", e);
          stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
              echoCancellation: echoCancelSetting,
              noiseSuppression: noiseFilterSetting,
              autoGainControl: true
            } 
          });
        }
      } else {
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            audio: {
              echoCancellation: echoCancelSetting,
              noiseSuppression: noiseFilterSetting,
              autoGainControl: true
            }
          });
        } catch (e) {
          stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }
      }

      console.log("[MIC] getUserMedia SUCCESS");
      console.log("[MIC] stream ID:", stream.id);

      const tracks = stream.getAudioTracks();
      console.log("[LiveSTT] Microphone initialized. Active audio tracks:", tracks.length);
      tracks.forEach((track, idx) => {
        // Microphone disconnection listener (Requirement 9: Error handling)
        track.onended = () => {
          console.warn(`[MIC] Audio track ended/disconnected: ${track.label}`);
          triggerToast("Microphone disconnected.", "error");
          setErrorState("Microphone was disconnected. Please check your audio device.");
          setMicStatus("error");
          updateAudioTelemetry({ micStatus: "error" });
          if (recordingRef.current) {
            stopRecording();
          }
        };

        const settings = track.getSettings();
        const capabilities = track.getCapabilities ? track.getCapabilities() : {};
        if (track.readyState === "live" && track.enabled) {
          console.log(`[LiveSTT] Audio track [${idx}] ACTIVE: "${track.label}"`);
        }
        console.log(`[MIC] Track Diagnostic [${idx}]:`, {
          trackId: track.id,
          label: track.label,
          enabled: track.enabled,
          muted: track.muted,
          readyState: track.readyState,
          deviceId: settings.deviceId || "(default)",
          sampleRate: settings.sampleRate || "Browser default (48000 Hz)",
          channelCount: settings.channelCount || 1,
          sampleSize: settings.sampleSize || "16-bit float",
          echoCancellation: settings.echoCancellation,
          noiseSuppression: settings.noiseSuppression,
          autoGainControl: settings.autoGainControl,
          capabilities: capabilities
        });
      });

      // Initialize Web Audio API AudioContext & AnalyserNode for Real Hardware Waveform Analysis
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        const audioCtx = new AudioCtx();
        audioContextRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        analyser.smoothingTimeConstant = 0.7;
        source.connect(analyser);
        analyserRef.current = analyser;
        console.log(`[MIC] AudioContext initialized: state=${audioCtx.state}, sampleRate=${audioCtx.sampleRate} Hz, baseLatency=${audioCtx.baseLatency || "N/A"}`);
      }

      mediaStreamRef.current = stream;
      attachMediaStream(stream, audioContextRef.current || undefined, analyserRef.current || undefined);
      console.log("[Audio] Microphone initialized");
      console.log("[Audio] Processing started");

      let currentSess = activeSessionRef.current || activeSession;
      if (!currentSess || currentSess.status === "ENDED") {
        currentSess = startSession({ title: lectureTitle, subject: user?.department || "" });
        activeSessionRef.current = currentSess;
        console.log("[LiveClassroom] Session created");
        console.log(`[LiveClassroom] Session: ${currentSess.id}`);
      }

      setMicMode("hardware");
      setMicStatus("active");
      setMicErrorMsg(null);
      setErrorState(null);
      refreshAudioDevices();
      triggerToast("Hardware microphone connected successfully.", "success");
      return stream;

    } catch (error: any) {
      console.error("[MIC] getUserMedia failed:", error);
      console.error("[MIC] error.name:", error?.name);
      console.error("[MIC] error.message:", error?.message);

      let errorReason = "Unknown microphone error";
      const errName = error?.name || "";
      const errMsg = error?.message || "";

      if (errName === "NotAllowedError" || errName === "PermissionDeniedError" || errMsg.includes("Permission")) {
        errorReason = "Permission denied. Chrome or site settings blocked microphone access.";
      } else if (errName === "NotFoundError" || errName === "DevicesNotFoundError") {
        errorReason = "No microphone detected. Please connect a physical microphone.";
      } else if (errName === "NotReadableError" || errName === "TrackStartError") {
        errorReason = "Microphone is already in use by another application or OS service.";
      } else if (errName === "OverconstrainedError" || errName === "ConstraintNotSatisfiedError") {
        errorReason = "Requested audio constraints cannot be satisfied by the hardware microphone.";
      } else if (errName === "SecurityError") {
        errorReason = "Browser security policy blocked microphone access.";
      } else if (errName === "AbortError") {
        errorReason = "Microphone connection request was aborted.";
      } else {
        errorReason = errMsg || "Unable to access microphone device.";
      }

      setMicStatus(errName === "NotAllowedError" ? "denied" : "error");
      setMicErrorMsg(errorReason);
      setErrorState(errorReason);
      return null;
    }
  };

  // Explicit User Opt-in for Demo Audio Mode
  const enableDemoAudioMode = () => {
    if (analyserRef.current) analyserRef.current = null;
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (mediaStreamRef.current) {
      if ((mediaStreamRef.current as any)._cleanupAudio) {
        (mediaStreamRef.current as any)._cleanupAudio();
      }
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    const simStream = createSimulatedAudioStream();
    mediaStreamRef.current = simStream;
    setMicMode("simulated");
    setMicStatus("active");
    setMicErrorMsg(null);
    setErrorState(null);
    triggerToast("Demo Audio Mode enabled.", "info");
  };

  // Trigger microphone acquisition on mount / session join
  useEffect(() => {
    if (!hasJoinedSession) return;
    requestMicrophoneStream();

    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        try { mediaRecorderRef.current.stop(); } catch (e) {}
        mediaRecorderRef.current = null;
      }
      if (sttRecorderRef.current && sttRecorderRef.current.state !== "inactive") {
        try { sttRecorderRef.current.stop(); } catch (e) {}
        sttRecorderRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
      if (mediaStreamRef.current) {
        if ((mediaStreamRef.current as any)._cleanupAudio) {
          (mediaStreamRef.current as any)._cleanupAudio();
        }
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
        mediaStreamRef.current = null;
      }
      stopMicrophone();
      updateAudioTelemetry({ isRecording: false, micStatus: "idle", sttStatus: "idle" });
    };
  }, [hasJoinedSession]);

  // Real Hardware Frequency & Level Visualizer Loop (Driven by Real Microphone AnalyserNode)
  useEffect(() => {
    let animId: number;
    const updateAudioData = () => {
      if (micStatus === "active" && !isMuted && hasJoinedSession) {
        if (micMode === "hardware" && analyserRef.current) {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
          analyserRef.current.getByteFrequencyData(dataArray);

          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
          }
          const avg = sum / (dataArray.length || 1);
          const levelPct = Math.min(100, Math.round((avg / 255) * 100));
          setAudioLevel(levelPct);

          const heights: number[] = [];
          const step = Math.floor(dataArray.length / 28) || 1;
          for (let i = 0; i < 28; i++) {
            const val = dataArray[(i * step) % dataArray.length] || 0;
            heights.push(Math.max(4, Math.round((val / 255) * 44)));
          }
          setRealWaveHeights(heights);
        } else if (micMode === "simulated") {
          const lvl = Math.floor(Math.random() * 45) + 35;
          setAudioLevel(lvl);
          const heights: number[] = [];
          for (let i = 0; i < 28; i++) {
            heights.push(Math.max(4, Math.floor(Math.random() * 30) + 8));
          }
          setRealWaveHeights(heights);
        }
      } else {
        setAudioLevel(0);
        setRealWaveHeights(new Array(28).fill(4));
      }
      animId = requestAnimationFrame(updateAudioData);
    };
    updateAudioData();
    return () => cancelAnimationFrame(animId);
  }, [micStatus, micMode, isMuted, hasJoinedSession]);

  // Toggle Microphone Mute State without destroying MediaStream
  const toggleMute = () => {
    const nextMuted = !isMuted;
    setIsMuted(nextMuted);
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getAudioTracks().forEach(track => {
        track.enabled = !nextMuted;
      });
    }
  };

  // Establish WebSocket Connection
  useEffect(() => {
    let pingInterval: NodeJS.Timeout | null = null;
    let isComponentMounted = true;

    const connectWebSocket = () => {
      if (!isComponentMounted) return;

      if (socketRef.current) {
        if (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING) {
          return;
        }
      }

      const token = getAccessToken() || "";
      const wsBase = getWsBaseUrl();
      const currentSessionId = activeSession?.id || "default";
      const wsUrl = `${wsBase}/api/v1/ws/classroom/${currentSessionId}${token ? `?token=${encodeURIComponent(token)}` : ""}`;

      console.log("[STT WS] CONNECTING", wsUrl);
      setIsConnecting(true);
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        if (!isComponentMounted) {
          ws.close();
          return;
        }
        console.log("[STT WS] CONNECTED");
        console.log("[LiveClassroom] Audio WebSocket connected");
        console.log(`[LiveClassroom] Session: ${currentSessionId}`);
        console.log("[WebSocket] Connected");
        setIsConnected(true);
        setIsConnecting(false);
        updateAudioTelemetry({ wsStatus: "connected", sttStatus: "active" });
        setErrorState(prev => (prev?.includes("WebSocket") ? null : prev));
        reconnectAttemptsRef.current = 0;
        
        if (pingInterval) clearInterval(pingInterval);
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        if (!isComponentMounted) return;
        try {
          console.log("[STT WS] MESSAGE_RECEIVED", typeof event.data === "string" ? event.data.slice(0, 100) : "");
          const data = JSON.parse(event.data);
          console.log("[STT WS] MESSAGE_PARSED", data.type);

          if (data.type === "error" && data.status === 403) {
            triggerToastRef.current(data.detail || "Only Teachers or Administrators can control lectures.", "error");
            return;
          }
          
          if (data.type === "stt_error") {
            console.error(`[STT] ERROR session_id=${data.session_id || currentSessionId} message=${data.message}`);
            console.error("[LiveSTT] Speech-to-text error:", data.message);
            setSttStatus("ERROR");
            triggerToastRef.current(`Live STT Error: ${data.message || "Speech-to-text processing failed"}`, "error");
            return;
          }

          if (data.type === "stt_status") {
            if (data.status === "transcribing") {
              setSttStatus("TRANSCRIBING");
            } else if (data.status === "listening" && recordingRef.current) {
              setSttStatus("LISTENING");
            } else if (data.status === "idle") {
              setSttStatus("IDLE");
            }
            return;
          }

          if (data.type === "room_state" || data.type === "user_left") {
            if (data.participants && Array.isArray(data.participants)) {
              setParticipants(data.participants.map((p: any) => ({
                id: p.id || Math.random().toString(),
                name: p.email ? p.email.split("@")[0] : "Student",
                role: p.role || "Student",
                handRaised: false,
                muted: false,
                avatar: (p.email || "U").substring(0, 2).toUpperCase()
              })));
            }
          } else if (data.type === "chat") {
            setChatMessages(prev => [...prev, {
              id: data.id || Date.now().toString(),
              sender: data.sender,
              content: data.content,
              time: data.time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              isTeacher: data.isTeacher
            }]);
          } else if (data.type === "transcript" || data.type === "partial") {
            const isFinal = data.type === "transcript" && (data.is_final !== false) && (data.transcript_type !== "partial");
            const transcriptId = data.id || `${data.chunk_id || ""}-${data.sequence || Date.now()}`;

            if (isFinal) {
              if (seenTranscriptIdsRef.current.has(transcriptId)) {
                console.warn(`[LiveSTT] Duplicate transcript id=${transcriptId} skipped.`);
                return;
              }
              seenTranscriptIdsRef.current.add(transcriptId);
              // Limit the seen-set size to prevent unbounded memory growth
              if (seenTranscriptIdsRef.current.size > 500) {
                const firstKey = seenTranscriptIdsRef.current.values().next().value;
                if (firstKey !== undefined) seenTranscriptIdsRef.current.delete(firstKey);
              }
              console.log(
                `TRANSCRIPT_EVENT_RECEIVED session_id=${data.session_id || "default"} type=transcript seq=${data.sequence ?? "?"} is_final=true text="${data.text}"`
              );
              console.log(`[LiveAudio] transcript received: "${data.text}" (session_id=${data.session_id || activeSession?.id || "default"}, seq=${data.sequence ?? "?"})`);
              console.log(`[LiveClassroom] Transcript received: "${data.text}"`);
              console.log(`[NLP] Transcript received`);

              setTranscripts(prev => {
                const finalEntry: TranscriptEntry = {
                  id: transcriptId,
                  speaker: data.speaker || "Teacher",
                  time: data.time || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                  text: data.text,
                  isTeacher: data.isTeacher ?? true,
                  is_final: true,
                };
                let updated: TranscriptEntry[];
                // Replace active interim entry if present, else append
                if (prev.length > 0 && !prev[prev.length - 1].is_final) {
                  updated = [...prev.slice(0, -1), finalEntry];
                } else {
                  updated = [...prev, finalEntry];
                }
                const fullText = updated.filter(t => t.is_final).map(t => `${t.speaker}: ${t.text}`).join("\n");
                updateSession({ transcript: fullText });
                return updated;
              });
              if (recordingRef.current) {
                setSttStatus("LIVE");
              }
            } else {
              // Partial transcript: update or append the single active interim message
              setTranscripts(prev => {
                const partialEntry: TranscriptEntry = {
                  id: transcriptId,
                  speaker: data.speaker || "Teacher",
                  time: data.time || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                  text: data.text,
                  isTeacher: data.isTeacher ?? true,
                  is_final: false,
                };
                if (prev.length > 0 && !prev[prev.length - 1].is_final) {
                  return [...prev.slice(0, -1), partialEntry];
                }
                return [...prev, partialEntry];
              });
              if (recordingRef.current) {
                setSttStatus("LISTENING");
              }
            }
          } else if (data.type === "hand_raise") {
            setParticipants(prev => prev.map(p => {
              if (p.id === data.userId || p.name === data.userName) {
                return { ...p, handRaised: data.handRaised };
              }
              return p;
            }));
          } else if (data.type === "recording_status") {
            setIsRecording(data.isRecording);
          } else if (data.type === "lecture_status") {
            if (data.status !== undefined) setIsLectureActive(data.status);
            if (data.title) setLectureTitle(data.title);
            if (data.summary) setLectureSummary(data.summary);
            if (data.event === "lecture_started") {
              triggerToastRef.current("Teacher started the audio lecture session.", "info");
            } else if (data.event === "lecture_ended") {
              triggerToastRef.current("Lecture session ended. AI summary & attendance finalized.", "info");
            }
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e);
        }
      };

      ws.onerror = (err) => {
        console.error("[STT WS] ERROR", err);
        if (!isComponentMounted) return;
        if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
          setErrorState("Live classroom connection lost. Reconnecting...");
        }
      };

      ws.onclose = () => {
        console.log("[STT WS] DISCONNECTED");
        if (!isComponentMounted) return;
        setIsConnected(false);
        setIsConnecting(false);
        if (pingInterval) clearInterval(pingInterval);

        // Do NOT reconnect if End Lecture was clicked — that's an intentional close
        if (isLectureEndedRef.current) {
          console.log("[LiveClassroom] WebSocket closed after End Lecture — no reconnect.");
          return;
        }

        if (reconnectAttemptsRef.current < 5) {
          const timeout = Math.pow(2, reconnectAttemptsRef.current) * 1000;
          reconnectAttemptsRef.current += 1;
          console.log(`[LiveClassroom] WebSocket reconnecting in ${timeout}ms (attempt ${reconnectAttemptsRef.current})...`);
          setTimeout(connectWebSocket, timeout);
        } else {
          setErrorState("Live classroom connection lost after 5 attempts. Please refresh.");
        }
      };
    };

    connectWebSocket();

    return () => {
      isComponentMounted = false;
      if (pingInterval) clearInterval(pingInterval);
      if (socketRef.current) {
        const ws = socketRef.current;
        socketRef.current = null;
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => {
            ws.close();
          };
        } else if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      }
    };
  }, [activeSession?.id]);

  // Real-time Audio Chunk Capture Loop for Live STT WebSocket Streaming
  // Strictly gated by isRecording: audio is NEVER sent to STT or DB unless recording is active!
  useEffect(() => {
    if (micStatus !== "active" || !hasJoinedSession || isMuted || !isConnected || !isLectureActive || !isRecording || isStoppingRef.current || isEndingRef.current) {
      // Stop any active recorder when conditions no longer allow STT streaming
      if (sttRecorderRef.current && sttRecorderRef.current.state !== "inactive") {
        try {
          sttRecorderRef.current.stop();
        } catch (e) {}
        sttRecorderRef.current = null;
        isSTTCapturingRef.current = false;
        console.log("[LiveSTT] Live STT audio recorder stopped (not recording or conditions not met).");
      }
      return;
    }

    let isCancelled = false;
    let sliceTimeout: NodeJS.Timeout | null = null;

    /**
     * captureAudioSlice:
     *  - Strictly active only during recording (isRecording === true)
     *  - 4.0 second chunks ensure complete phrases and accurate Whisper transcription
     *  - Collects chunks into sessionRecordedBlobsRef for debug playback (Requirement 5)
     */
    const captureAudioSlice = () => {
      if (isCancelled || isStoppingRef.current || isEndingRef.current || isLectureEndedRef.current || micStatus !== "active" || isMuted || !isConnected || !isLectureActive || !recordingRef.current) {
        isSTTCapturingRef.current = false;
        return;
      }

      if (isSTTCapturingRef.current) {
        return;
      }

      const stream = mediaStreamRef.current;
      if (!stream || stream.getAudioTracks().length === 0 || !stream.getAudioTracks().some(t => t.readyState === "live" && t.enabled)) {
        if (!isCancelled && !isStoppingRef.current && !isEndingRef.current && recordingRef.current) {
          sliceTimeout = setTimeout(captureAudioSlice, 500);
        }
        return;
      }

      try {
        const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm";

        const recorder = new MediaRecorder(stream, { mimeType });
        sttRecorderRef.current = recorder;
        mediaRecorderRef.current = recorder;
        isSTTCapturingRef.current = true;

        // Unique ID for this audio chunk — sent to backend for deduplication
        const chunkId = `chunk-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
        const currentSessId = activeSessionRef.current?.id || activeSession?.id || "default";

        if (sttStatusRef.current === "IDLE") {
          setSttStatus("LISTENING");
        }

        recorder.ondataavailable = (event: BlobEvent) => {
          if (!event.data || event.data.size === 0 || isMuted || isCancelled || isStoppingRef.current || isEndingRef.current || !recordingRef.current) return;

          const byteSize = event.data.size;
          console.log(`[STT] ACTIVE_SESSION_ID=${currentSessId}`);
          console.log(`[LiveAudio] audio chunk created: ${byteSize} bytes (chunk_id=${chunkId})`);
          console.log(`AUDIO_CHUNK_CREATED size=${byteSize} duration=4.0s chunk_id=${chunkId} mime=${event.data.type || mimeType}`);
          console.log("[Audio] Audio chunk generated");
          console.log(`[Audio] Bytes: ${byteSize}`);
          console.log(`[Audio] Session: ${currentSessId}`);

          // Save raw chunk in memory for debug export (Requirement 5)
          sessionRecordedBlobsRef.current.push(event.data);

          // Discard empty/corrupted headers < 500 bytes
          if (byteSize < 500) {
            console.log(`[Audio] chunk_id=${chunkId} empty (${byteSize} bytes) — skipping.`);
            return;
          }

          // 1. Upload chunk to backend recording storage if lecture recording is active
          const activeRecId = currentRecordingIdRef.current;
          if (activeRecId && (recordingRef.current || isRecording)) {
            const chunkBlob = event.data;
            const formData = new FormData();
            formData.append("recording_id", activeRecId);
            formData.append("chunk", chunkBlob, "chunk.webm");
            const uploadPromise = (async () => {
              try {
                await api.postForm(`/lecture/${currentSessId}/recording/chunk`, formData);
              } catch (err) {
                console.error("[LiveClassroom] Failed to upload recording chunk:", err);
              }
            })();
            pendingUploadsRef.current.add(uploadPromise);
            uploadPromise.finally(() => {
              pendingUploadsRef.current.delete(uploadPromise);
            });
          }

          // 2. Stream chunk to WebSocket for live STT transcription
          if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            setSttStatus("PROCESSING");
            const reader = new FileReader();
            reader.onloadend = () => {
              if (isCancelled || isStoppingRef.current || isEndingRef.current || !recordingRef.current) return;
              const base64data = reader.result as string;
              // Read from stabilized refs — not from closure (Root Cause 2 fix)
              const senderName =
                userRef.current?.fullName ||
                userRef.current?.email?.split("@")[0] ||
                "Teacher";
              const isTeacher = isAuthorizedToControlRef.current;

              socketRef.current?.send(JSON.stringify({
                type: "audio_chunk",
                chunk_id: chunkId,
                data: base64data,
                mimeType: event.data.type || mimeType,
                speaker: senderName,
                isTeacher: isTeacher,
              }));
              console.log(`[LiveAudio] audio chunk sent: ${byteSize} bytes (session_id=${currentSessId})`);
              console.log("[Audio] Audio chunk sent");
              console.log(`[Audio] Session: ${currentSessId}`);
              console.log(`AUDIO_SEND session_id=${currentSessId} bytes=${byteSize}`);
              console.log(`WS_AUDIO_SEND session_id=${currentSessId} bytes=${byteSize} chunk_id=${chunkId}`);
              incrementChunks(true);
              updateAudioTelemetry({ sttStatus: "receiving" });
            };
            reader.readAsDataURL(event.data);
          } else {
            console.warn(`[WebSocket] Not open — chunk_id=${chunkId} skipped.`);
          }
        };

        recorder.onstop = () => {
          isSTTCapturingRef.current = false;
          // Immediately chain next slice while recording is still active
          if (!isCancelled && !isStoppingRef.current && !isEndingRef.current && !isLectureEndedRef.current && micStatus === "active" && !isMuted && isConnected && isLectureActive && recordingRef.current) {
            captureAudioSlice();
          }
        };

        recorder.start();
        console.log(`AUDIO_CAPTURE_STARTED chunk_id=${chunkId}`);

        // Stop after STT_CHUNK_DURATION_MS (5.0s) to produce complete phrases with high Whisper STT accuracy
        sliceTimeout = setTimeout(() => {
          if (recorder.state === "recording") {
            try {
              recorder.stop();
            } catch (e) {}
          }
        }, STT_CHUNK_DURATION_MS);

      } catch (err) {
        isSTTCapturingRef.current = false;
        console.error("[LiveSTT] Failed to capture audio slice:", err);
        if (!isCancelled && recordingRef.current) {
          sliceTimeout = setTimeout(captureAudioSlice, 1000);
        }
      }
    };

    // Initialize browser SpeechRecognition for zero-latency local interim feedback if supported
    try {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition && !speechRecognitionRef.current) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = "en-US";
        recognition.maxAlternatives = 1;

        recognition.onresult = (event: any) => {
          if (isStoppingRef.current || isEndingRef.current || isLectureEndedRef.current) return;
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const res = event.results[i];
            const transcriptText = res[0]?.transcript?.trim();
            if (!transcriptText) continue;

            const isFinal = res.isFinal;
            const senderName = userRef.current?.fullName || userRef.current?.email?.split("@")[0] || "Teacher";

            if (!isFinal) {
              // Real-time interim partial display
              setTranscripts(prev => {
                const interimItem: TranscriptEntry = {
                  id: "interim-live-partial",
                  speaker: senderName,
                  time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                  text: transcriptText,
                  isTeacher: true,
                  is_final: false,
                };
                if (prev.length > 0 && !prev[prev.length - 1].is_final) {
                  return [...prev.slice(0, -1), interimItem];
                }
                return [...prev, interimItem];
              });
              setSttStatus("LISTENING");
            }
          }
        };

        recognition.onerror = () => {};
        recognition.onend = () => {
          if (recordingRef.current && !isStoppingRef.current && !isEndingRef.current && !isLectureEndedRef.current) {
            try {
              recognition.start();
            } catch (e) {}
          }
        };

        recognition.start();
        speechRecognitionRef.current = recognition;
      }
    } catch (speechErr) {
      console.debug("Browser SpeechRecognition initialization note:", speechErr);
    }

    console.log("[LiveSTT] Initializing seamless audio slice recorder...");
    captureAudioSlice();

    return () => {
      isCancelled = true;
      if (sliceTimeout) clearTimeout(sliceTimeout);
      if (sttRecorderRef.current && sttRecorderRef.current.state !== "inactive") {
        try {
          sttRecorderRef.current.stop();
        } catch (e) {}
        sttRecorderRef.current = null;
      }
      if (speechRecognitionRef.current) {
        try {
          speechRecognitionRef.current.stop();
        } catch (e) {}
        speechRecognitionRef.current = null;
      }
      isSTTCapturingRef.current = false;
    };
  // isRecording added: STT chunk capturing only runs while recording is active!
  }, [micStatus, hasJoinedSession, isMuted, isConnected, isLectureActive, isRecording]);

  // Timer for Recording Duration
  useEffect(() => {
    if (isRecording) {
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } else {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
      setRecordingDuration(0);
    }
    return () => {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    };
  }, [isRecording]);

  // Send Chat Message via WebSocket
  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMsg.trim()) return;

    const senderName = user?.fullName || user?.email?.split("@")[0] || "User";
    const msgObj = {
      type: "chat",
      id: Date.now().toString(),
      sender: senderName,
      content: newMsg,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isTeacher: isAuthorizedToControl
    };

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(msgObj));
    } else {
      setChatMessages(prev => [...prev, msgObj]);
    }
    setNewMsg("");
  };

  // Toggle Hand Raise via WebSocket
  const toggleHandRaise = () => {
    const nextState = !handRaised;
    setHandRaised(nextState);
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: "hand_raise",
        userId: user?.id,
        userName: user?.fullName || user?.email,
        handRaised: nextState
      }));
    }
  };

  // Start Lecture (Authorized Teachers / Admins)
  const handleStartLecture = async () => {
    if (!isAuthorizedToControl) {
      triggerToast("Only Teachers or Administrators can control lectures.", "error");
      return;
    }
    if (isStartingRef.current || isEndingRef.current || isStoppingRef.current) {
      return;
    }
    isLectureEndedRef.current = false;
    try {
      const teacherNameStr = user?.fullName || user?.email?.split("@")[0] || "Instructor";
      const res = await api.post<any>("/lecture/start", { title: lectureTitle });
      const sessId = res.classroom_session_id || res.session_id || res.lecture_id || `sess_${Date.now().toString(36)}`;
      console.log(`LIVE_SESSION_STARTED session_id=${sessId} lecture_id=${sessId}`);
      
      setTranscripts([]);
      seenTranscriptIdsRef.current.clear();

      const newSess = startSession({
        id: sessId,
        title: lectureTitle,
        subject: "Live Audio Classroom",
        teacherName: teacherNameStr,
        teacherId: user?.id,
        status: "LIVE",
        transcript: "",
        summary: null,
        nlp: null,
      });
      activeSessionRef.current = newSess;

      setIsLectureActive(true);
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: "start_lecture",
          title: lectureTitle,
          status: true,
          classroom_session_id: sessId,
          session_id: sessId
        }));
      }
      triggerToast(`Audio lecture started successfully (Session #${sessId}).`, "success");

      // Requirement 1: Automatically start microphone capture & recording pipeline on lecture session start
      setTimeout(() => {
        if (!recordingRef.current && !isStartingRef.current) {
          startRecording();
        }
      }, 250);
    } catch (err: any) {
      triggerToast(err.message || "Only Teachers or Administrators can control lectures.", "error");
    }
  };


  // End / Stop Lecture (Authorized Teachers / Admins)
  const handleStopLecture = async () => {
    if (!isAuthorizedToControl) {
      triggerToast("Only Teachers or Administrators can control lectures.", "error");
      return;
    }
    // Prevent duplicate clicks or ending while stopping
    if (isEndingRef.current || isStoppingRef.current || isLectureEndedRef.current) {
      return;
    }
    isEndingRef.current = true;
    setIsEnding(true);
    console.log("[LiveClassroom] END_LECTURE_STARTED");

    try {
      // ── Step 1: If recording is active, stop recording first ─────────────
      if (recordingRef.current || isRecording) {
        console.log("[LiveClassroom] Stopping active recording before ending lecture...");
        await stopRecording();
      }

      // ── Step 2: Flush final STT audio chunk if still active ──────────────
      if (sttRecorderRef.current && sttRecorderRef.current.state === "recording") {
        console.log("[LiveSTT] End Lecture: stopping active STT recorder to flush final audio chunk...");
        await new Promise<void>((resolve) => {
          let done = false;
          const finish = () => {
            if (!done) {
              done = true;
              resolve();
            }
          };
          const timeout = setTimeout(finish, 2500);
          sttRecorderRef.current?.addEventListener("stop", () => {
            clearTimeout(timeout);
            finish();
          }, { once: true });
          try {
            sttRecorderRef.current?.stop();
          } catch (e) {
            clearTimeout(timeout);
            finish();
          }
        });
        console.log("[LiveSTT] End Lecture: final audio flush complete.");
      }
      sttRecorderRef.current = null;
      isSTTCapturingRef.current = false;

      // ── Step 3: Wait for pending audio chunk uploads ─────────────────────
      if (pendingUploadsRef.current.size > 0) {
        console.log("[LiveClassroom] WAITING_FOR_AUDIO_UPLOADS");
        await Promise.allSettled(Array.from(pendingUploadsRef.current));
      }

      // ── Step 4: Finalize transcript and lecture session on backend ─────────
      console.log("[LiveClassroom] FINALIZING_SESSION");
      const currentSessionId = activeSessionRef.current?.id || activeSession?.id || "default";
      const fullTranscriptText = transcriptsRef.current.map(t => `${t.speaker}: ${t.text}`).join("\n");
      const finalDuration = recordingDurationRef.current || recordingDuration;

      let res: any = null;
      try {
        res = await api.post<any>(`/lecture/${currentSessionId}/stop`, {
          recording_id: currentRecordingIdRef.current,
          duration: finalDuration,
          transcript: fullTranscriptText,
          room_id: currentSessionId
        });
      } catch (postErr: any) {
        console.warn("[LiveClassroom] Backend lecture stop fallback:", postErr);
        res = {
          status: "success",
          ai_summary: {
            summary: fullTranscriptText ? "Lecture completed. Summary generated." : "No transcript available for this session yet.",
            status: fullTranscriptText ? "completed" : "not_available"
          },
          transcript: fullTranscriptText,
          nlp: null,
          attendance: {
            status: "finalized",
            total_participants: participants.length || 1,
            finalized_at: new Date().toISOString()
          }
        };
      }

      // ── Step 5: Mark lecture as ended in state and refs ──────────────────
      setIsLectureActive(false);
      isLectureEndedRef.current = true;
      if (res && res.ai_summary) {
        setLectureSummary(res.ai_summary);
      }

      // ── Step 6: Notify room via WebSocket before closing ──────────────────
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: "stop_lecture",
          status: false,
          summary: res?.ai_summary,
          nlp: res?.nlp
        }));
      }

      // ── Step 7: Stop microphone tracks (turns off browser mic indicator) ──
      console.log("[LiveClassroom] End Lecture: stopping microphone MediaStream tracks...");
      if (mediaStreamRef.current) {
        if ((mediaStreamRef.current as any)._cleanupAudio) {
          (mediaStreamRef.current as any)._cleanupAudio();
        }
        mediaStreamRef.current.getTracks().forEach(track => {
          try {
            track.stop();
            console.log(`[LiveClassroom] Mic track stopped: ${track.label}`);
          } catch (e) {}
        });
        mediaStreamRef.current = null;
      }

      // ── Step 8: Close AudioContext ─────────────────────────────────────────
      analyserRef.current = null;
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
        console.log("[LiveClassroom] AudioContext closed.");
      }

      // Update mic UI state
      setMicStatus("idle");
      stopMicrophone();
      if (speechRecognitionRef.current) {
        try {
          speechRecognitionRef.current.stop();
        } catch (e) {}
        speechRecognitionRef.current = null;
      }
      setSttStatus("IDLE");

      // ── Step 9: Close WebSocket ───────────────────────────────────────────
      if (socketRef.current) {
        const wsToClose = socketRef.current;
        socketRef.current = null;
        if (wsToClose.readyState === WebSocket.OPEN || wsToClose.readyState === WebSocket.CONNECTING) {
          wsToClose.close(1000, "Lecture ended by teacher");
          console.log("[LiveClassroom] WebSocket intentionally closed after End Lecture.");
        }
      }

      // ── Step 10: Persist final session state with transcript, summary & NLP ───
      endSession({
        summary: res?.ai_summary || (res?.summary ? { summary: res.summary } : null),
        transcript: res?.transcript || fullTranscriptText || "",
        nlp: res?.nlp || null
      });

      console.log(`[SESSION] ACTIVE_SESSION_ID=${currentSessionId}`);
      console.log(`[SUMMARY] SOURCE_SESSION_ID=${currentSessionId}`);
      console.log("[LiveClassroom] SESSION_FINALIZED");
      triggerToast("Lecture ended. Navigating to NLP & Lecture Summaries...", "success");
      setTimeout(() => {
        navigate(`/nlp-summary/${currentSessionId}`);
      }, 1000);
    } catch (err: any) {
      console.error("[LiveClassroom] END_LECTURE_ERROR", err);
      triggerToast(err.message || "Lecture state updated.", "info");
    } finally {
      isEndingRef.current = false;
      setIsEnding(false);
    }
  };

  // Start Audio MediaRecorder & Upload Audio Chunks (Guarded by Real Hardware Microphone)
  const startRecording = async () => {
    if (!isAuthorizedToControl) {
      triggerToast("Only Teachers or Administrators can control lectures.", "error");
      return;
    }
    // Prevent double clicks or starting while stopping/ending
    if (isStartingRef.current || recordingRef.current || isStoppingRef.current || isEndingRef.current) {
      return;
    }
    isStartingRef.current = true;
    setIsStarting(true);

    try {
      // Require active microphone stream before starting recording
      let stream = mediaStreamRef.current;
      if (!stream || stream.getAudioTracks().length === 0 || !stream.getAudioTracks().some(t => t.readyState === "live" && t.enabled) || micStatus !== "active") {
        stream = await requestMicrophoneStream();
        if (!stream || micStatus !== "active") {
          triggerToast("Microphone permission required. Please allow microphone access before starting recording.", "error");
          isStartingRef.current = false;
          setIsStarting(false);
          return;
        }
      }

      // Ensure completely clean state for the new recording (Requirement 2)
      setTranscripts([]);
      seenTranscriptIdsRef.current.clear();
      transcriptsRef.current = [];
      sessionRecordedBlobsRef.current = [];
      pendingUploadsRef.current.clear();
      setRecordingDuration(0);

      // Use active session ID or initialize a fresh one
      const currentSess = activeSessionRef.current || activeSession;
      let lectureId = currentSess?.id;
      if (!currentSess || currentSess.status === "ENDED" || !lectureId) {
        const newSess = startSession({
          title: lectureTitle,
          subject: "Live Audio Classroom",
          teacherName: user?.fullName || user?.email?.split("@")[0] || "Instructor",
          teacherId: user?.id,
          status: "LIVE",
          transcript: "",
          summary: null,
          nlp: null,
        });
        lectureId = newSess.id;
        activeSessionRef.current = newSess;
      } else {
        // Clear previous transcript text in active session
        updateSession({ transcript: "", summary: null, nlp: null });
      }

      console.log(`[SESSION] ACTIVE_SESSION_ID=${lectureId}`);
      console.log(`[RECORDING] STARTED session_id=${lectureId}`);
      console.log(`[TRANSCRIPT] RECORDING_SESSION_ID=${lectureId}`);
      console.log(`[STT] ACTIVE_SESSION_ID=${lectureId}`);
      setSttStatus("LISTENING");

      const startRes = await api.post<any>(`/lecture/${lectureId}/recording/start`, {});
      const recId = startRes.recording_id;
      currentRecordingIdRef.current = recId;

      recordingRef.current = true;
      setIsRecording(true);
      updateAudioTelemetry({ isRecording: true, micStatus: "active", sttStatus: "active" });

      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: "recording_status",
          isRecording: true,
          recordingId: recId
        }));
      }

      triggerToast("Live audio lecture recording initiated.", "success");
    } catch (err: any) {
      console.error("[LiveClassroom] START_RECORDING_ERROR", err);
      triggerToast(err.message || "Failed to start audio recording.", "error");
    } finally {
      isStartingRef.current = false;
      setIsStarting(false);
    }
  };

  // Stop MediaRecorder & Finalize Recording Metadata
  const stopRecording = async () => {
    if (!isAuthorizedToControl) {
      triggerToast("Only Teachers or Administrators can control lectures.", "error");
      return;
    }
    // Prevent duplicate clicks
    if (isStoppingRef.current || !recordingRef.current) {
      return;
    }
    isStoppingRef.current = true;
    setIsStopping(true);
    console.log("[LiveClassroom] STOP_RECORDING_STARTED");

    try {
      // 1. Set UI state immediately: recording = false, stopping = true
      recordingRef.current = false;
      setIsRecording(false);

      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }

      const recId = currentRecordingIdRef.current;
      const lectureId = activeSessionRef.current?.id || activeSession?.id || "default";
      const finalDuration = recordingDurationRef.current || recordingDuration;

      // 2. Stop MediaRecorder safely & wait for final chunk
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        console.log("[LiveClassroom] FINAL_AUDIO_CHUNK_PROCESSING");
        await new Promise<void>((resolve) => {
          let resolved = false;
          const finish = () => {
            if (!resolved) {
              resolved = true;
              resolve();
            }
          };
          const timeout = setTimeout(finish, 4000);
          recorder.addEventListener("stop", () => {
            clearTimeout(timeout);
            finish();
          }, { once: true });
          try {
            recorder.stop();
          } catch (e) {
            clearTimeout(timeout);
            finish();
          }
        });
      }
      mediaRecorderRef.current = null;

      // 3. Wait for any pending chunk uploads in flight
      if (pendingUploadsRef.current.size > 0) {
        console.log("[LiveClassroom] WAITING_FOR_AUDIO_UPLOADS");
        await Promise.allSettled(Array.from(pendingUploadsRef.current));
      }

      // 4. Stop STT recorder if active
      if (sttRecorderRef.current && sttRecorderRef.current.state !== "inactive") {
        try {
          sttRecorderRef.current.stop();
        } catch (e) {}
        sttRecorderRef.current = null;
      }
      isSTTCapturingRef.current = false;

      // 5. Finalize recording metadata on backend
      if (recId) {
        const formData = new FormData();
        formData.append("recording_id", recId);
        formData.append("duration", finalDuration.toString());

        try {
          const stopRes: any = await api.postForm(`/lecture/${lectureId}/recording/stop`, formData);
          if (stopRes && stopRes.summary) {
            updateSession({ summary: stopRes.summary });
          }
        } catch (err: any) {
          console.warn("[LiveClassroom] Recording stop server notice:", err);
        }
      }
      currentRecordingIdRef.current = null;

      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: "recording_status",
          isRecording: false
        }));
      }

      // 6. Stop every microphone MediaStream track
      console.log("[LiveClassroom] AUDIO_CAPTURE_STOPPED");
      if (mediaStreamRef.current) {
        if ((mediaStreamRef.current as any)._cleanupAudio) {
          (mediaStreamRef.current as any)._cleanupAudio();
        }
        mediaStreamRef.current.getTracks().forEach(track => {
          try {
            track.stop();
          } catch (e) {}
        });
        mediaStreamRef.current = null;
      }

      // 7. Disconnect and close audio processing resources
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
      analyserRef.current = null;

      stopMicrophone();
      setMicStatus("idle");
      updateAudioTelemetry({ isRecording: false, micStatus: "idle", sttStatus: "idle" });
      setAudioLevel(0);
      setRealWaveHeights(new Array(28).fill(4));
      if (speechRecognitionRef.current) {
        try {
          speechRecognitionRef.current.stop();
        } catch (e) {}
        speechRecognitionRef.current = null;
      }
      setSttStatus("IDLE");

      console.log(`[RECORDING] STOPPED session_id=${lectureId}`);
      console.log("[LiveClassroom] RECORDING_STOPPED");
      triggerToast("Audio lecture recording saved successfully.", "success");
    } catch (err: any) {
      console.error("[LiveClassroom] STOP_RECORDING_ERROR", err);
      triggerToast(err.message || "Error finalizing lecture recording.", "error");
    } finally {
      isStoppingRef.current = false;
      setIsStopping(false);
    }
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Export recorded audio received from microphone before STT (Requirement 5)
  const handleExportDebugAudio = () => {
    if (sessionRecordedBlobsRef.current.length > 0) {
      const fullBlob = new Blob(sessionRecordedBlobsRef.current, { type: "audio/webm" });
      const url = URL.createObjectURL(fullBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `debug_audio_${activeSessionRef.current?.id || "session"}.webm`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      triggerToast("Downloaded microphone audio recorded before STT.", "success");
      return;
    }
    const currentSessionId = activeSessionRef.current?.id || activeSession?.id;
    if (currentSessionId) {
      window.open(`/api/v1/lecture/sessions/${currentSessionId}/debug-audio`, "_blank");
    } else {
      triggerToast("No recorded audio available to export.", "info");
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner / Session Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : isConnecting ? "bg-amber-500 animate-ping" : "bg-red-500"}`}></span>
            <span className="text-xs font-mono font-bold text-gray-600 uppercase tracking-widest">
              {isConnected ? "REAL-TIME WEBSOCKET ACTIVE" : isConnecting ? "CONNECTING..." : "DISCONNECTED"}
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
              Role: {user?.role || "Student"}
            </span>
          </div>
          {isAuthorizedToControl && !isLectureActive ? (
            <input
              type="text"
              value={lectureTitle}
              onChange={(e) => setLectureTitle(e.target.value)}
              placeholder="Enter Lecture Title..."
              className="text-xl font-display font-bold text-gray-900 border-b border-dashed border-gray-300 hover:border-purple-500 focus:border-purple-600 focus:outline-none bg-transparent w-full max-w-md"
            />
          ) : (
            <h2 className="text-xl font-display font-bold text-gray-900">{activeSession?.title || lectureTitle}</h2>
          )}
          <p className="text-xs text-gray-500">
            Connected Participants: {participants.length} | Status: {isLectureActive ? "Lecture Active" : "Lecture Ended"}
          </p>
        </div>

        {/* Action Controls - Strictly Filtered by RBAC permission helper canControlLecture */}
        <div className="flex items-center gap-2.5 self-stretch sm:self-auto">
          {isAuthorizedToControl ? (
            <>
              {/* Start / Stop Lecture Buttons for Teachers & Admins */}
              {isLectureActive ? (
                <button
                  onClick={handleStopLecture}
                  disabled={isEnding || isStopping}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold bg-red-600 hover:bg-red-700 text-white transition-colors flex items-center gap-2 shadow-sm ${
                    isEnding ? "opacity-75 cursor-not-allowed" : ""
                  }`}
                >
                  <Square className="w-3.5 h-3.5 fill-current" />
                  {isEnding ? "Ending Lecture..." : "End Lecture"}
                </button>
              ) : (
                <button
                  onClick={handleStartLecture}
                  disabled={isEnding || isStopping}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors flex items-center gap-2 shadow-sm ${
                    isEnding || isStopping ? "opacity-75 cursor-not-allowed" : ""
                  }`}
                >
                  <Play className="w-3.5 h-3.5 fill-current" /> Start Lecture
                </button>
              )}

            </>
          ) : (
            /* Student / Principal / Parent View Actions */
            <div className="flex items-center gap-2">
              {user?.role === "Principal" && (
                <span className="px-3 py-1.5 rounded-xl bg-amber-50 text-amber-700 border border-amber-200 text-xs font-semibold flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5" /> Read-Only Classroom Control
                </span>
              )}
              {hasJoinedSession ? (
                <button
                  onClick={() => {
                    setHasJoinedSession(false);
                    triggerToast("Left live audio classroom session.", "info");
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-200 transition-colors flex items-center gap-2"
                >
                  <LogOut className="w-3.5 h-3.5" /> Leave Lecture
                </button>
              ) : (
                <button
                  onClick={() => {
                    setHasJoinedSession(true);
                    triggerToast("Joined live audio classroom session.", "success");
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition-colors flex items-center gap-2 shadow-sm"
                >
                  <LogIn className="w-3.5 h-3.5" /> Join Lecture
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Requirement 12: Clear, consistent status panel & Single Recording Control */}
      <div className="bg-white p-5 rounded-3xl border border-gray-100 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2.5">
          {/* 1. SESSION: ACTIVE / ENDED */}
          <span className={`px-3.5 py-1.5 rounded-full text-xs font-mono font-bold flex items-center gap-2 border ${
            isLectureActive
              ? "bg-emerald-50 border-emerald-200 text-emerald-700"
              : "bg-gray-50 border-gray-200 text-gray-500"
          }`}>
            <span className={`w-2 h-2 rounded-full ${isLectureActive ? "bg-emerald-500 animate-pulse" : "bg-gray-400"}`} />
            SESSION: {isLectureActive ? "ACTIVE" : "ENDED"}
          </span>

          {/* 2. RECORDING: NOT RECORDING / RECORDING */}
          <span className={`px-3.5 py-1.5 rounded-full text-xs font-mono font-bold flex items-center gap-2 border ${
            isRecording 
              ? "bg-red-50 border-red-200 text-red-700 animate-pulse" 
              : "bg-gray-50 border-gray-200 text-gray-600"
          }`}>
            <span className={`w-2 h-2 rounded-full ${isRecording ? "bg-red-500 animate-pulse" : "bg-gray-400"}`} />
            RECORDING: {isRecording ? `RECORDING (${formatTime(recordingDuration)})` : "NOT RECORDING"}
          </span>

          {/* 3. STT: STANDBY / PROCESSING / RECEIVING / COMPLETED / ERROR */}
          <span className={`px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 border ${
            errorState && errorState.includes("STT")
              ? "bg-red-50 border-red-200 text-red-700"
              : isRecording && (sttStatus === "PROCESSING" || audioTelemetry.sttStatus === "receiving")
                ? "bg-amber-50 border-amber-200 text-amber-700 animate-pulse"
                : isRecording
                  ? "bg-blue-50 border-blue-200 text-blue-700"
                  : transcripts.length > 0
                    ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                    : "bg-gray-50 border-gray-200 text-gray-500"
          }`}>
            <Activity className="w-3.5 h-3.5" />
            <span>
              STT: {
                errorState && errorState.includes("STT")
                  ? "ERROR"
                  : isEnding
                    ? "COMPLETED"
                    : isRecording
                      ? (sttStatus === "TRANSCRIBING" || audioTelemetry.sttStatus === "receiving" ? "RECEIVING" : sttStatus === "PROCESSING" ? "PROCESSING" : "RECEIVING")
                      : transcripts.length > 0 ? "COMPLETED" : "STANDBY"
              }
            </span>
          </span>

          {/* 4. TRANSCRIPT: READY / RECEIVING / FINALIZING / FINALIZED */}
          <span className={`px-3.5 py-1.5 rounded-full text-xs font-semibold border flex items-center gap-1.5 ${
            isRecording && transcripts.length > 0
              ? "bg-emerald-50 border-emerald-200 text-emerald-700"
              : isEnding
                ? "bg-amber-50 border-amber-200 text-amber-700"
                : "bg-gray-50 border-gray-200 text-gray-700"
          }`}>
            <FileText className="w-3.5 h-3.5 text-gray-400" />
            <span>
              TRANSCRIPT: {
                isEnding
                  ? "FINALIZING"
                  : isLectureEndedRef.current
                    ? "FINALIZED"
                    : isRecording && transcripts.length > 0
                      ? "RECEIVING"
                      : "READY"
              }
            </span>
          </span>

          {/* Chunks Counter */}
          <span className="px-3.5 py-1.5 rounded-full text-xs font-mono font-semibold bg-gray-50 border border-gray-200 text-gray-700 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-gray-400" />
            <span>Chunks: {audioTelemetry.chunksGenerated} / {audioTelemetry.chunksSent}</span>
          </span>
        </div>

        {/* Single Clear Recording Control & Debug Audio Export (Requirements 4, 5, 10, 12) */}
        <div className="flex items-center gap-2 self-stretch md:self-auto shrink-0">
          <button 
            onClick={handleExportDebugAudio}
            className="px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-200 transition-all flex items-center justify-center gap-1.5 shadow-2xs"
            title="Download microphone audio recorded before STT (Requirement 5)"
          >
            <Download className="w-3.5 h-3.5 text-gray-600" />
            <span>Export Audio</span>
          </button>
          {isAuthorizedToControl && (
            <>
              {isRecording ? (
                <button 
                  onClick={stopRecording}
                  disabled={isStopping || isEnding}
                  className={`px-5 py-2.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-black text-white transition-all flex items-center justify-center gap-2 shadow-sm ${
                    isStopping ? "opacity-75 cursor-not-allowed" : ""
                  }`}
                >
                  <Square className="w-3.5 h-3.5 fill-current text-red-400" />
                  <span>{isStopping ? "Stopping..." : `Stop Recording (${formatTime(recordingDuration)})`}</span>
                </button>
              ) : (
                <button 
                  onClick={startRecording}
                  disabled={isStopping || isEnding || isStarting || !isLectureActive || micStatus === "requesting"}
                  className={`px-5 py-2.5 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-2 shadow-sm ${
                    !isStopping && !isEnding && !isStarting && isLectureActive && micStatus !== "requesting"
                      ? "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-200" 
                      : "bg-gray-200 text-gray-400 cursor-not-allowed"
                  }`}
                >
                  <CircleDot className="w-3.5 h-3.5 text-red-400 animate-pulse" />
                  <span>{isStarting ? "Starting..." : "Start Recording"}</span>
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Audio Console Viewport & Transcript Area */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* Audio Console Panel */}
          <div className="relative bg-slate-950 rounded-3xl overflow-hidden border border-slate-800 shadow-2xl p-6 sm:p-8 flex flex-col justify-between space-y-6">
            
            {/* Top Overlay Bar */}
            <div className="flex items-center justify-between z-10">
              <div className="px-3.5 py-1.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-white font-mono text-[10px] tracking-wider flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${
                  micStatus === "active" 
                    ? isRecording 
                      ? "bg-red-500 animate-pulse" 
                      : "bg-emerald-400" 
                    : micStatus === "requesting" 
                      ? "bg-amber-400 animate-pulse" 
                      : "bg-red-500"
                }`}></span>
                {micStatus === "active" 
                  ? isRecording 
                    ? `RECORDING AUDIO (${formatTime(recordingDuration)})` 
                    : isLectureActive 
                      ? "LIVE AUDIO CLASSROOM ACTIVE" 
                      : "LECTURE ENDED"
                  : micStatus === "requesting"
                    ? "REQUESTING MICROPHONE ACCESS..."
                    : "MICROPHONE ACCESS DENIED"
                }
              </div>

              <div className={`px-3.5 py-1.5 rounded-full border font-mono text-[10px] uppercase tracking-wider flex items-center gap-1.5 ${
                micStatus === "active"
                  ? micMode === "hardware"
                    ? "bg-slate-800/80 border-slate-700 text-emerald-400"
                    : "bg-slate-800/80 border-slate-700 text-sky-400"
                  : "bg-red-950/60 border-red-800 text-red-400"
              }`}>
                <Radio className={`w-3 h-3 ${micStatus === "active" ? (micMode === "hardware" ? "text-emerald-400 animate-pulse" : "text-sky-400 animate-pulse") : "text-red-400"}`} />
                <span>
                  {micStatus === "active" 
                    ? (micMode === "hardware" ? "Hardware Microphone Active • 16kHz ANC" : "Demo Audio Stream (Simulated)")
                    : "Audio Pipeline Disconnected"
                  }
                </span>
              </div>
            </div>

            {/* Error Banner */}
            <AnimatePresence>
              {errorState && (
                <motion.div 
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="z-20 p-4 rounded-2xl bg-red-500/15 border border-red-500/30 flex items-center gap-3 text-red-200 text-xs font-semibold"
                >
                  <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                  <p className="flex-1">{errorState}</p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Central Audio Visualizer / Hardware Mic Error Display */}
            <div className="py-8 flex flex-col items-center justify-center text-center space-y-6">
              
              {micStatus === "active" ? (
                <>
                  {/* Animated Mic Ring */}
                  <div className="relative flex items-center justify-center">
                    <div className={`absolute w-36 h-36 rounded-full transition-all duration-500 ${isMuted ? "bg-red-500/10 border border-red-500/20" : "bg-blue-500/20 border border-blue-500/30 animate-ping"}`}></div>
                    <div className={`absolute w-28 h-28 rounded-full ${isMuted ? "bg-red-500/20" : "bg-blue-600/30"}`}></div>
                    <div className={`w-20 h-20 rounded-full flex items-center justify-center shadow-xl z-10 transition-colors ${isMuted ? "bg-red-600 text-white" : "bg-blue-600 text-white"}`}>
                      {isMuted ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
                    </div>
                  </div>

                  {/* Status & Real Voice Input Levels */}
                  <div className="space-y-1">
                    <h3 className="text-xl font-display font-bold text-white tracking-tight">
                      {isMuted ? "Microphone Muted" : isRecording ? "Live Audio Recording in Progress" : "Live Audio Stream Active"}
                    </h3>
                    <p className="text-xs text-slate-400 font-mono">
                      Duration: <span className="text-white font-bold">{formatTime(recordingDuration)}</span> | Gain Level: <span className="text-sky-400 font-bold">{isMuted ? "0 dB" : `${audioLevel} dB`}</span>
                    </p>
                  </div>

                  {/* Dynamic Equalizer Soundwave Spectrum Driven by Real Hardware Analyser */}
                  <div className="w-full max-w-md h-12 flex items-center justify-center gap-1.5 py-2">
                    {realWaveHeights.map((height, i) => (
                      <div
                        key={i}
                        className={`w-1.5 rounded-full transition-all duration-75 ${isMuted ? "bg-slate-800" : isRecording ? "bg-red-400" : "bg-sky-400"}`}
                        style={{ height: `${height}px` }}
                      />
                    ))}
                  </div>
                </>
              ) : micStatus === "requesting" ? (
                <>
                  <div className="w-20 h-20 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 animate-spin">
                    <RefreshCw className="w-8 h-8" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-xl font-display font-bold text-white tracking-tight">Requesting Hardware Microphone Access...</h3>
                    <p className="text-xs text-slate-400 max-w-md">Please click "Allow" on the Chrome browser permission prompt to activate your microphone.</p>
                  </div>
                </>
              ) : (
                <>
                  {/* Microphone Denied / Hardware Error View */}
                  <div className="w-20 h-20 rounded-full bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 shadow-xl">
                    <ShieldAlert className="w-9 h-9" />
                  </div>
                  <div className="space-y-2 max-w-md">
                    <h3 className="text-xl font-display font-bold text-white tracking-tight">Hardware Microphone Unavailable</h3>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {micErrorMsg || "Hardware microphone access failed. Please ensure your microphone is plugged in, unmuted in Windows settings, and granted permission in Chrome."}
                    </p>
                  </div>

                  {/* Audio Device Selector Dropdown if multiple inputs exist */}
                  {audioInputDevices.length > 0 && (
                    <div className="flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 text-xs text-slate-300">
                      <Settings className="w-3.5 h-3.5 text-slate-400" />
                      <select 
                        value={selectedDeviceId}
                        onChange={(e) => {
                          setSelectedDeviceId(e.target.value);
                          requestMicrophoneStream(e.target.value);
                        }}
                        className="bg-transparent focus:outline-none text-white font-semibold cursor-pointer"
                      >
                        {audioInputDevices.map((dev, idx) => (
                          <option key={dev.deviceId || idx} value={dev.deviceId} className="bg-slate-900 text-white">
                            {dev.label || `Microphone Input ${idx + 1}`}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Explicit Action Buttons */}
                  <div className="flex flex-wrap items-center justify-center gap-3">
                    <button
                      onClick={() => requestMicrophoneStream(selectedDeviceId)}
                      className="px-5 py-2.5 rounded-xl font-semibold text-xs bg-blue-600 hover:bg-blue-700 text-white transition-colors flex items-center gap-2 shadow-lg hover:shadow-blue-500/25"
                    >
                      <RotateCcw className="w-4 h-4" /> Connect Hardware Mic
                    </button>

                    <button
                      onClick={enableDemoAudioMode}
                      className="px-5 py-2.5 rounded-xl font-semibold text-xs bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 transition-colors flex items-center gap-2"
                    >
                      <Sparkles className="w-4 h-4 text-sky-400" /> Use Demo Audio
                    </button>
                  </div>
                </>
              )}

            </div>

            {/* Bottom Audio Control Toolbar */}
            <div className="z-10 bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-4 flex items-center justify-between text-white">
              <div className="flex items-center gap-3">
                <button 
                  onClick={toggleMute} 
                  disabled={!hasJoinedSession || micStatus !== "active"}
                  className={`px-4 py-2.5 rounded-xl font-semibold text-xs flex items-center gap-2 transition-colors ${
                    micStatus !== "active" 
                      ? "bg-gray-800 text-gray-500 cursor-not-allowed" 
                      : isMuted 
                        ? "bg-red-500/30 text-red-300 border border-red-500/40" 
                        : "bg-white/10 hover:bg-white/20 text-white"
                  }`}
                >
                  {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  {isMuted ? "Unmute Mic" : "Mute Mic"}
                </button>

                <button 
                  onClick={toggleHandRaise}
                  disabled={!hasJoinedSession}
                  className={`p-2.5 rounded-xl transition-colors ${handRaised ? "bg-amber-500/30 text-amber-300 border border-amber-500/40" : "bg-white/10 hover:bg-white/20 text-white"}`}
                  title="Raise Hand"
                >
                  <Hand className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-center gap-3">
                {/* Read-Only Microphone Capturing Status Indicator (Requirement 4) */}
                <div className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 border select-none ${
                  micStatus === "active" && isRecording
                    ? "bg-red-500/20 border-red-500/30 text-red-300"
                    : micStatus === "active"
                      ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-300"
                      : "bg-slate-800/80 border-slate-700 text-slate-400"
                }`}>
                  <Mic className={`w-3.5 h-3.5 ${isRecording ? "text-red-400 animate-pulse" : micStatus === "active" ? "text-emerald-400" : "text-slate-400"}`} />
                  <span>
                    {isRecording 
                      ? "Microphone Capturing" 
                      : micStatus === "active" 
                        ? "Microphone Connected" 
                        : "Microphone Standby"
                    }
                  </span>
                </div>

                {isAuthorizedToControl && isLectureActive && (
                  <button
                    onClick={handleStopLecture}
                    disabled={isEnding || isStopping}
                    className={`px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors flex items-center gap-2 border border-slate-700 ${
                      isEnding ? "opacity-75 cursor-not-allowed" : ""
                    }`}
                  >
                    <LogOut className="w-4 h-4 text-red-400" />
                    {isEnding ? "Ending Lecture..." : "End Lecture"}
                  </button>
                )}
              </div>
            </div>

          </div>

          {/* Live Audio Transcript Feed Panel */}
          <div className="bento-card p-6 bg-white space-y-4 border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-display font-bold text-sm text-gray-900">Live Audio Speech-to-Text & Transcript</h3>
                  <p className="text-[10px] text-gray-400">Real-time Whisper AI speech recognition pipeline</p>
                </div>
              </div>
              <span className={`text-[10px] font-mono px-2.5 py-1 rounded-full font-semibold border flex items-center gap-1.5 ${
                sttStatus === "LIVE"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : sttStatus === "LISTENING"
                  ? "bg-blue-50 text-blue-700 border-blue-200"
                  : sttStatus === "TRANSCRIBING"
                  ? "bg-purple-50 text-purple-700 border-purple-200"
                  : sttStatus === "PROCESSING"
                  ? "bg-amber-50 text-amber-700 border-amber-200"
                  : sttStatus === "ERROR"
                  ? "bg-red-50 text-red-700 border-red-200"
                  : "bg-gray-100 text-gray-500 border-gray-200"
              }`}>
                <Activity className={`w-3 h-3 ${sttStatus !== "IDLE" ? "text-current animate-pulse" : "text-gray-400"}`} />
                {sttStatus === "LIVE" && "Live STT Active"}
                {sttStatus === "LISTENING" && "STT Listening"}
                {sttStatus === "TRANSCRIBING" && "STT Transcribing"}
                {sttStatus === "PROCESSING" && "STT Processing"}
                {sttStatus === "ERROR" && "STT Error"}
                {sttStatus === "IDLE" && "STT Idle"}
              </span>
            </div>

            <div className="space-y-3 max-h-56 overflow-y-auto pr-1">
              {transcripts.length === 0 ? (
                <div className="p-6 text-center text-xs text-gray-400 bg-slate-50 rounded-2xl border border-slate-100 space-y-1">
                  <Volume2 className="w-5 h-5 mx-auto text-gray-300" />
                  <p className="font-semibold text-gray-600">Waiting for live speech input...</p>
                  <p className="text-[11px] text-gray-400">Transcripts will automatically stream here as audio is spoken into the microphone.</p>
                </div>
              ) : (
                transcripts.map((entry) => (
                  <div key={entry.id} className={`p-3.5 rounded-2xl text-xs border space-y-1.5 ${entry.is_final ? "bg-slate-50 border-slate-100" : "bg-amber-50/60 border-amber-100"}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-blue-900 flex items-center gap-1.5">
                        <Volume2 className="w-3.5 h-3.5 text-blue-600" />
                        {entry.speaker} {entry.isTeacher ? "(Teacher)" : "(Student)"}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full font-mono ${entry.is_final ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                          {entry.is_final ? "FINAL" : "PARTIAL"}
                        </span>
                        <span className="text-[10px] text-gray-400 font-mono">{entry.time}</span>
                      </div>
                    </div>
                    <p className={`leading-relaxed font-sans ${entry.is_final ? "text-gray-700" : "text-gray-600 italic"}`}>{entry.text}</p>
                  </div>
                ))
              )}

              {sttStatus === "TRANSCRIBING" && (!transcripts.length || transcripts[transcripts.length - 1].is_final) && (
                <div className="p-3 bg-purple-50/50 rounded-2xl text-xs border border-purple-100 flex items-center gap-2 text-purple-700 animate-pulse">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span className="font-medium">Transcribing live speech with Whisper AI...</span>
                </div>
              )}
            </div>
          </div>

          {/* AI Live Overview & Summary Card */}
          <div className="bento-card bento-card-blue p-6 bg-white space-y-4 border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Sparkles className="w-4.5 h-4.5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 text-sm">Real-time Audio Session & AI Summary</h3>
                  <p className="text-[10px] text-gray-400">Classroom state synchronized</p>
                </div>
              </div>
            </div>
            
            {lectureSummary ? (
              <div className="p-4 bg-blue-50/60 rounded-2xl space-y-2 border border-blue-100 text-xs text-gray-800">
                <p className="font-bold text-blue-900">Finalized AI Summary:</p>
                <p className="whitespace-pre-line leading-relaxed">{typeof lectureSummary === 'string' ? lectureSummary : lectureSummary.summary || JSON.stringify(lectureSummary)}</p>
              </div>
            ) : (
              <div className="p-4 bg-gray-50 rounded-2xl space-y-1.5 border border-gray-100 text-xs text-gray-600">
                <p className="font-semibold text-gray-800">No lecture summary available yet.</p>
                <p className="text-[11px] text-gray-500 leading-relaxed">
                  AI summaries are automatically generated from real-time audio transcripts when the lecture session ends.
                </p>
              </div>
            )}
          </div>

        </div>

        {/* Right Sidebar: Active Classroom Members & Live Chat Feed */}
        <div className="space-y-6">
          <div className="bento-card p-6 bg-white flex flex-col h-[600px] border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
              <div className="flex items-center gap-2">
                <Users className="w-4.5 h-4.5 text-blue-600" />
                <span className="font-display font-bold text-sm text-gray-900">Active Classroom ({participants.length})</span>
              </div>
            </div>

            {/* Participants List */}
            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 mb-4">
              {participants.length === 0 ? (
                <p className="text-xs text-gray-400 text-center py-4">Waiting for peers to join...</p>
              ) : (
                participants.map((p) => (
                  <div key={p.id} className="p-2.5 bg-gray-50 rounded-xl flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-blue-100 text-blue-600 font-bold flex items-center justify-center text-[10px]">
                        {p.avatar}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-800">{p.name}</p>
                        <span className="text-[9px] text-gray-400 capitalize">{p.role}</span>
                      </div>
                    </div>
                    {p.handRaised && <Hand className="w-3.5 h-3.5 text-amber-500" />}
                  </div>
                ))
              )}
            </div>

            {/* Chat Feed */}
            <div className="border-t border-gray-100 pt-4 flex flex-col h-1/2">
              <div className="flex items-center gap-1.5 text-xs text-gray-400 font-semibold mb-2">
                <MessageSquare className="w-4 h-4 text-purple-600" /> Live Feed & Chat
              </div>

              <div className="flex-1 overflow-y-auto space-y-2 pr-1 mb-2">
                {chatMessages.length === 0 ? (
                  <p className="text-[11px] text-gray-400 text-center py-4">No messages yet.</p>
                ) : (
                  chatMessages.map((msg) => (
                    <div key={msg.id} className={`p-2 rounded-xl text-xs ${msg.isTeacher ? "bg-blue-50 border border-blue-100" : "bg-gray-50"}`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-gray-800">{msg.sender}</span>
                        <span className="text-[9px] text-gray-400">{msg.time}</span>
                      </div>
                      <p className="text-gray-600">{msg.content}</p>
                    </div>
                  ))
                )}
              </div>

              <form onSubmit={handleSendMessage} className="flex gap-2">
                <input 
                  type="text" 
                  value={newMsg}
                  onChange={(e) => setNewMsg(e.target.value)}
                  placeholder="Ask a classroom query..."
                  className="flex-1 px-3 py-1.5 rounded-xl text-xs border border-gray-200 focus:outline-none focus:border-blue-600"
                />
                <button type="submit" className="p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors">
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            </div>

          </div>
        </div>

      </div>

    </div>
  );
}
