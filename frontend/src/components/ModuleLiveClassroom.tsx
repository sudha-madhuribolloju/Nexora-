import React, { useState, useEffect, useRef } from "react";
import { 
  Video, 
  VideoOff, 
  Mic, 
  MicOff, 
  Hand, 
  Send, 
  Users, 
  MessageSquare, 
  Monitor, 
  AlertCircle, 
  Sparkles,
  CircleDot,
  Square,
  Play,
  LogOut,
  LogIn,
  Eye,
  ShieldAlert
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { useAuth } from "../contexts/AuthContext";
import { getAccessToken } from "../services/session";
import { api } from "../services/api";
import { canControlLecture } from "../utils/rbac";

interface Participant {
  id: string;
  name: string;
  role: string;
  handRaised: boolean;
  muted: boolean;
  videoOn: boolean;
  avatar: string;
}

interface ChatMessage {
  id: string;
  sender: string;
  content: string;
  time: string;
  isTeacher: boolean;
}

export default function ModuleLiveClassroom() {
  const { user, triggerToast } = useAuth();
  
  // Role Permission Helper
  const isAuthorizedToControl = canControlLecture(user?.role);

  // Connection & Media States
  const [isConnecting, setIsConnecting] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [errorState, setErrorState] = useState<string | null>(null);

  // Hardware Controls & MediaRecorder
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [handRaised, setHandRaised] = useState(false);
  const [hasJoinedSession, setHasJoinedSession] = useState(true);
  
  // Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const currentRecordingIdRef = useRef<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Classroom Data & Summary
  const [isLectureActive, setIsLectureActive] = useState(true);
  const [lectureTitle, setLectureTitle] = useState("Live Classroom Session");
  const [lectureSummary, setLectureSummary] = useState<any>(null);
  
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [newMsg, setNewMsg] = useState("");
  const [participants, setParticipants] = useState<Participant[]>([]);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // Disable any keyboard shortcuts for lecture controls if unauthorized
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Intercept common control hotkeys (Ctrl+Alt+S, Ctrl+Alt+R, Alt+S, Alt+R)
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

  // Initialize Media Stream for Video Preview
  useEffect(() => {
    let activeStream: MediaStream | null = null;

    const setupMedia = async () => {
      try {
        if (hasJoinedSession && (isVideoOn || !isMuted)) {
          activeStream = await navigator.mediaDevices.getUserMedia({
            video: isVideoOn,
            audio: !isMuted
          });
          mediaStreamRef.current = activeStream;
          if (videoRef.current && isVideoOn) {
            videoRef.current.srcObject = activeStream;
          }
        }
      } catch (err: any) {
        console.warn("Media device acquisition warning:", err);
      }
    };

    setupMedia();

    return () => {
      if (activeStream) {
        activeStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [isVideoOn, isMuted, hasJoinedSession]);

  // Establish WebSocket Connection
  useEffect(() => {
    let pingInterval: NodeJS.Timeout | null = null;
    let isComponentMounted = true;

    const connectWebSocket = () => {
      const token = getAccessToken() || "";
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = window.location.hostname || "localhost";
      const wsUrl = `${protocol}//${host}:8000/api/v1/ws/classroom/default?token=${token}`;

      setIsConnecting(true);
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        if (!isComponentMounted) return;
        setIsConnected(true);
        setIsConnecting(false);
        setErrorState(null);
        reconnectAttemptsRef.current = 0;
        
        // Heartbeat
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        if (!isComponentMounted) return;
        try {
          const data = JSON.parse(event.data);

          if (data.type === "error" && data.status === 403) {
            triggerToast(data.detail || "Only Teachers or Administrators can control lectures.", "error");
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
                videoOn: true,
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
              triggerToast("Teacher started the lecture session.", "info");
            } else if (data.event === "lecture_ended") {
              triggerToast("Lecture session ended. AI summary & attendance finalized.", "info");
            }
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e);
        }
      };

      ws.onerror = () => {
        if (!isComponentMounted) return;
        setErrorState("WebSocket connection error. Retrying connection...");
      };

      ws.onclose = () => {
        if (!isComponentMounted) return;
        setIsConnected(false);
        setIsConnecting(false);
        if (pingInterval) clearInterval(pingInterval);

        if (reconnectAttemptsRef.current < 5) {
          const timeout = Math.pow(2, reconnectAttemptsRef.current) * 1000;
          reconnectAttemptsRef.current += 1;
          setTimeout(connectWebSocket, timeout);
        }
      };
    };

    connectWebSocket();

    return () => {
      isComponentMounted = false;
      if (pingInterval) clearInterval(pingInterval);
      if (socketRef.current) socketRef.current.close();
    };
  }, [triggerToast]);

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
    try {
      await api.post("/lecture/start", { title: lectureTitle });
      setIsLectureActive(true);
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: "start_lecture",
          title: lectureTitle,
          status: true
        }));
      }
      triggerToast("Lecture started successfully.", "success");
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
    try {
      // 1. Stop recording if active
      if (isRecording) {
        await stopRecording();
      }

      // 2. Call stop lecture endpoint (triggers transcript, AI summary, attendance)
      const res = await api.post<any>("/lecture/stop", {
        recording_id: currentRecordingIdRef.current,
        duration: recordingDuration
      });

      setIsLectureActive(false);
      if (res && res.ai_summary) {
        setLectureSummary(res.ai_summary);
      }

      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: "stop_lecture",
          status: false,
          summary: res.ai_summary
        }));
      }

      triggerToast("Lecture ended. Transcript & AI summary generated, attendance finalized.", "success");
    } catch (err: any) {
      triggerToast(err.message || "Only Teachers or Administrators can control lectures.", "error");
    }
  };

  // Start MediaRecorder & Upload Chunks (Authorized Teachers / Admins)
  const startRecording = async () => {
    if (!isAuthorizedToControl) {
      triggerToast("Only Teachers or Administrators can control lectures.", "error");
      return;
    }
    try {
      const startRes = await api.post<any>("/lecture/default/recording/start", {});
      const recId = startRes.recording_id;
      currentRecordingIdRef.current = recId;

      let stream = mediaStreamRef.current;
      if (!stream || stream.getTracks().length === 0) {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
        mediaStreamRef.current = stream;
      }

      const options = MediaRecorder.isTypeSupported("video/webm;codecs=vp8,opus")
        ? { mimeType: "video/webm;codecs=vp8,opus" }
        : undefined;

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = async (event) => {
        if (event.data && event.data.size > 0 && currentRecordingIdRef.current) {
          const formData = new FormData();
          formData.append("recording_id", currentRecordingIdRef.current);
          formData.append("chunk", event.data, "chunk.webm");
          try {
            await api.postForm("/lecture/default/recording/chunk", formData);
          } catch (err) {
            console.error("Failed to upload recording chunk:", err);
          }
        }
      };

      mediaRecorder.start(3000);
      setIsRecording(true);

      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: "recording_status",
          isRecording: true,
          recordingId: recId
        }));
      }

      triggerToast("Lecture recording initiated.", "success");
    } catch (err: any) {
      triggerToast(err.message || "Failed to start MediaRecorder recording.", "error");
    }
  };

  // Stop MediaRecorder & Finalize Recording Metadata
  const stopRecording = async () => {
    if (!isAuthorizedToControl) {
      triggerToast("Only Teachers or Administrators can control lectures.", "error");
      return;
    }
    try {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }

      if (currentRecordingIdRef.current) {
        const formData = new FormData();
        formData.append("recording_id", currentRecordingIdRef.current);
        formData.append("duration", recordingDuration.toString());

        await api.postForm("/lecture/default/recording/stop", formData);
      }

      setIsRecording(false);
      currentRecordingIdRef.current = null;

      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: "recording_status",
          isRecording: false
        }));
      }

      triggerToast("Lecture recording saved to PostgreSQL database successfully.", "success");
    } catch (err: any) {
      triggerToast(err.message || "Error finalizing lecture recording.", "error");
    }
  };

  // Handle Screen Sharing
  const handleScreenShareToggle = async () => {
    try {
      if (!isScreenSharing) {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
        setIsScreenSharing(true);
        if (videoRef.current) {
          videoRef.current.srcObject = screenStream;
        }
        screenStream.getVideoTracks()[0].onended = () => {
          setIsScreenSharing(false);
          if (videoRef.current && mediaStreamRef.current) {
            videoRef.current.srcObject = mediaStreamRef.current;
          }
        };
      } else {
        setIsScreenSharing(false);
        if (videoRef.current && mediaStreamRef.current) {
          videoRef.current.srcObject = mediaStreamRef.current;
        }
      }
    } catch (err) {
      console.warn("Screen share cancelled or failed:", err);
      setIsScreenSharing(false);
    }
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      
      {/* Top Header & Role Permissions Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500 animate-ping"}`}></span>
            <span className="text-xs font-mono font-bold text-gray-600 uppercase tracking-widest">
              {isConnected ? "REAL-TIME WEBSOCKET ACTIVE" : isConnecting ? "CONNECTING..." : "DISCONNECTED"}
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
              Role: {user?.role || "Student"}
            </span>
          </div>
          <h2 className="text-xl font-display font-bold text-gray-900">{lectureTitle}</h2>
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
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-red-600 hover:bg-red-700 text-white transition-colors flex items-center gap-2 shadow-sm"
                >
                  <Square className="w-3.5 h-3.5 fill-current" /> End Lecture
                </button>
              ) : (
                <button
                  onClick={handleStartLecture}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-colors flex items-center gap-2 shadow-sm"
                >
                  <Play className="w-3.5 h-3.5 fill-current" /> Start Lecture
                </button>
              )}

              {/* Start / Stop Recording Buttons for Teachers & Admins */}
              {isRecording ? (
                <button 
                  onClick={stopRecording}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-900 text-white transition-colors flex items-center gap-2 shadow-sm"
                >
                  <Square className="w-3.5 h-3.5 fill-current" /> Stop Recording ({formatTime(recordingDuration)})
                </button>
              ) : (
                <button 
                  onClick={startRecording}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition-colors flex items-center gap-2 shadow-sm"
                >
                  <CircleDot className="w-3.5 h-3.5 text-red-400 animate-pulse" /> Start Recording
                </button>
              )}
            </>
          ) : (
            /* Student / Principal / Parent View Actions: Join / Leave Lecture & Status Badge */
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
                    triggerToast("Left live classroom session.", "info");
                  }}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-200 transition-colors flex items-center gap-2"
                >
                  <LogOut className="w-3.5 h-3.5" /> Leave Lecture
                </button>
              ) : (
                <button
                  onClick={() => {
                    setHasJoinedSession(true);
                    triggerToast("Joined live classroom session.", "success");
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

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Stream & Media Player Viewport */}
        <div className="xl:col-span-2 space-y-6">
          
          <div className="relative aspect-video bg-gray-950 rounded-3xl overflow-hidden border border-gray-800 shadow-xl flex flex-col justify-between p-6">
            
            {/* Top Overlay Bar */}
            <div className="flex items-center justify-between z-10">
              <div className="px-3.5 py-1.5 rounded-full bg-black/50 backdrop-blur-md border border-white/10 text-white font-mono text-[10px] tracking-wider flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${isRecording ? "bg-red-500 animate-pulse" : isLectureActive ? "bg-emerald-400" : "bg-gray-400"}`}></span>
                {isRecording ? `RECORDING IN PROGRESS (${formatTime(recordingDuration)})` : isLectureActive ? "LIVE CLASSROOM ACTIVE" : "LECTURE ENDED"}
              </div>

              <div className="px-3.5 py-1.5 rounded-full bg-blue-600 border border-blue-500 text-white font-semibold text-[10px] uppercase tracking-wider">
                {isScreenSharing ? "Shared Screen View" : "Webcam Feed"}
              </div>
            </div>

            {/* Error Banner */}
            <AnimatePresence>
              {errorState && (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 z-20 bg-gray-950/90 flex flex-col items-center justify-center text-center p-8 space-y-4"
                >
                  <AlertCircle className="w-10 h-10 text-amber-500" />
                  <p className="text-white text-xs font-semibold">{errorState}</p>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Main Video Viewport */}
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
              {hasJoinedSession ? (
                <>
                  <video 
                    ref={videoRef}
                    autoPlay 
                    playsInline 
                    muted
                    className={`w-full h-full object-cover ${isVideoOn || isScreenSharing ? "block" : "hidden"}`}
                  />
                  {!(isVideoOn || isScreenSharing) && (
                    <div className="text-center space-y-3">
                      <VideoOff className="w-12 h-12 text-gray-600 mx-auto" />
                      <p className="text-white font-medium text-sm">Camera Video Off</p>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center space-y-3">
                  <LogIn className="w-12 h-12 text-gray-500 mx-auto" />
                  <p className="text-white font-medium text-sm">You are currently disconnected from the live stream.</p>
                  <p className="text-xs text-gray-400">Click "Join Lecture" above to view stream feed and participate.</p>
                </div>
              )}
            </div>

            {/* Bottom Interactive Controls (Mic, Video, Hand Raise, Screen Share) */}
            <div className="z-10 bg-black/70 backdrop-blur-lg border border-white/10 rounded-2xl p-4 flex items-center justify-between text-white">
              <div className="flex items-center gap-3">
                <button 
                  onClick={() => setIsMuted(!isMuted)} 
                  disabled={!hasJoinedSession}
                  className={`p-3 rounded-xl transition-colors ${isMuted ? "bg-red-500/25 text-red-400 border border-red-500/30" : "bg-white/10 hover:bg-white/20 text-white"}`}
                  title={isMuted ? "Unmute Microphone" : "Mute Microphone"}
                >
                  {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
                <button 
                  onClick={() => setIsVideoOn(!isVideoOn)} 
                  disabled={!hasJoinedSession}
                  className={`p-3 rounded-xl transition-colors ${!isVideoOn ? "bg-red-500/25 text-red-400 border border-red-500/30" : "bg-white/10 hover:bg-white/20 text-white"}`}
                  title={isVideoOn ? "Turn Camera Off" : "Turn Camera On"}
                >
                  {isVideoOn ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
                </button>
                <button 
                  onClick={toggleHandRaise}
                  disabled={!hasJoinedSession}
                  className={`p-3 rounded-xl transition-colors ${handRaised ? "bg-amber-500/25 text-amber-400 border border-amber-500/30" : "bg-white/10 hover:bg-white/20 text-white"}`}
                  title="Raise Hand"
                >
                  <Hand className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button 
                  onClick={handleScreenShareToggle} 
                  disabled={!hasJoinedSession}
                  className={`p-3 rounded-xl transition-colors ${isScreenSharing ? "bg-blue-600 text-white" : "bg-white/10 hover:bg-white/20"}`}
                  title={isScreenSharing ? "Stop View Shared Screen" : "View / Share Screen"}
                >
                  <Monitor className="w-4 h-4" />
                </button>
              </div>
            </div>

          </div>

          {/* AI Live Overview & Summary Card */}
          <div className="bento-card bento-card-blue p-6 bg-white space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Sparkles className="w-4.5 h-4.5" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 text-sm">Real-time Session & AI Summary</h3>
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
              <div className="p-4 bg-gray-50 rounded-2xl space-y-2 border border-gray-100 text-xs text-gray-700">
                <p>• RBAC authorized stream active for role: <strong className="text-gray-900">{user?.role || "Student"}</strong></p>
                <p>• {isAuthorizedToControl ? "Full lecture start/stop and recording controls enabled." : "Read-only stream controls enabled (Start/Stop lecture buttons hidden)."}</p>
                <p>• Real-time WebSockets synchronization across peers with PostgreSQL backend persistence.</p>
              </div>
            )}
          </div>

        </div>

        {/* Right Sidebar: Active Classroom Members & Live Chat Feed */}
        <div className="space-y-6">
          <div className="bento-card p-6 bg-white flex flex-col h-[520px]">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
              <div className="flex items-center gap-2">
                <Users className="w-4.5 h-4.5 text-blue-600" />
                <span className="font-display font-bold text-sm text-gray-900">Active Classroom ({participants.length})</span>
              </div>
            </div>

            {/* Participants */}
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
