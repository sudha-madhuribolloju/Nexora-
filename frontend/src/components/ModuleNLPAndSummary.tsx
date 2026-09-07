import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { 
  Sparkles, 
  FileText, 
  BookOpen, 
  Cpu, 
  CheckCircle, 
  ChevronRight, 
  ArrowRight,
  Bookmark,
  TrendingUp,
  RotateCcw,
  BookMarked,
  Radio,
  Download,
  AlertCircle
} from "lucide-react";
import { NLPAnalysis } from "../types";
import { motion } from "motion/react";
import { summaryService } from "../services/summary";
import { useClassroomSession } from "../contexts/ClassroomContext";

export default function ModuleNLPAndSummary() {
  const { sessionId: routeSessionId } = useParams<{ sessionId?: string }>();
  const { activeSession, updateSession } = useClassroomSession();
  const [activeTab, setActiveTab] = useState<"summary" | "nlp">("summary");
  const [transcriptText, setTranscriptText] = useState("");
  const [transcriptStatus, setTranscriptStatus] = useState<"LOADING" | "READY" | "NO_TRANSCRIPT" | "ERROR">("LOADING");
  const [customPrompt, setCustomPrompt] = useState("");
  const [summaryResult, setSummaryResult] = useState<string>("");
  const [nlpResult, setNlpResult] = useState<NLPAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Auto-sync active or finalized session transcript, summary, and NLP data from PostgreSQL
  const loadSessionData = async () => {
    const targetSessionId = routeSessionId || activeSession?.id;
    if (!targetSessionId) {
      setTranscriptText("");
      setSummaryResult("");
      setNlpResult(null);
      setTranscriptStatus("NO_TRANSCRIPT");
      return;
    }

    console.log(`[SESSION] ACTIVE_SESSION_ID=${targetSessionId}`);
    console.log(`[NLP] FETCHING TRANSCRIPT`);
    console.log(`[NLP] session_id=${targetSessionId}`);
    console.log(`[TRANSCRIPT] FETCH_SESSION_ID=${targetSessionId}`);
    console.log(`[SUMMARY] SOURCE_SESSION_ID=${targetSessionId}`);
    console.log(`[NLP] Selected session: ${targetSessionId}`);

    // Clear stale states immediately before fetching so old lecture data is never displayed
    setTranscriptText("");
    setSummaryResult("");
    setNlpResult(null);
    setTranscriptStatus("LOADING");
    setFetchError(null);

    // 1. Initial sync from activeSession context ONLY if session IDs strictly match
    if (activeSession && activeSession.id === targetSessionId) {
      if (activeSession.transcript && activeSession.transcript.trim()) {
        setTranscriptText(activeSession.transcript);
        setTranscriptStatus("READY");
      }
      if (activeSession.summary) {
        const summaryStr = typeof activeSession.summary === "string" 
          ? activeSession.summary 
          : activeSession.summary.summary || "";
        setSummaryResult(summaryStr);
      }
      if (activeSession.nlp) {
        setNlpResult(activeSession.nlp);
      }
    }

    // 2. Fetch authoritative session data from backend PostgreSQL API
    try {
      const backendData = await summaryService.getSessionData(targetSessionId);
      console.log(`[NLP] Transcript API status: 200`);

      // Data Integrity Check: verify returned session matches requested session
      if (backendData && backendData.session_id && backendData.session_id !== targetSessionId) {
        console.error(`[DATA_INTEGRITY_ERROR] expected_session=${targetSessionId} received_session=${backendData.session_id}`);
        setTranscriptStatus("ERROR");
        setFetchError("Transcript session mismatch. Please reload the current lecture.");
        return;
      }
      console.log("[DATA_INTEGRITY] PASS");

      if (backendData && backendData.status === "success") {
        if (backendData.transcript && backendData.transcript.trim()) {
          const lines = backendData.transcript.split("\n").filter((l: string) => l.trim());
          console.log(`[NLP] Transcript records returned: ${lines.length}`);
          console.log(`[NLP] Transcript loaded successfully`);
          setTranscriptText(backendData.transcript);
          setTranscriptStatus("READY");
          
          if (updateSession) {
            updateSession({ transcript: backendData.transcript });
          }
        } else if (activeSession && activeSession.id === targetSessionId && activeSession.transcript && activeSession.transcript.trim()) {
          setTranscriptText(activeSession.transcript);
          setTranscriptStatus("READY");
          console.log(`[NLP] Transcript loaded from active session state`);
        } else {
          console.log(`[NLP] No transcript available for session: ${targetSessionId}`);
          setTranscriptText("");
          setTranscriptStatus("NO_TRANSCRIPT");
        }

        if (backendData.summary) {
          const bSum = typeof backendData.summary === "string" 
            ? backendData.summary 
            : backendData.summary.summary || "";
          setSummaryResult(bSum);
        }

        if (backendData.nlp && backendData.nlp.topics && backendData.nlp.topics.length > 0) {
          setNlpResult(backendData.nlp);
        }
      } else if (backendData && backendData.status === "not_found") {
        if (activeSession && activeSession.id === targetSessionId && activeSession.transcript && activeSession.transcript.trim()) {
          setTranscriptText(activeSession.transcript);
          setTranscriptStatus("READY");
        } else {
          setTranscriptText("");
          setTranscriptStatus("NO_TRANSCRIPT");
        }
      }
    } catch (e: any) {
      console.error("[ModuleNLPAndSummary] Session sync error:", e);
      if (activeSession && activeSession.id === targetSessionId && activeSession.transcript && activeSession.transcript.trim()) {
        setTranscriptText(activeSession.transcript);
        setTranscriptStatus("READY");
      } else {
        setTranscriptStatus("ERROR");
        setFetchError(e.message || "Unable to load lecture transcript. Please verify connection and retry.");
      }
    }
  };

  useEffect(() => {
    let isMounted = true;
    loadSessionData();
    return () => {
      isMounted = false;
    };
  }, [routeSessionId, activeSession?.id]);

  const handleImportSessionTranscript = () => {
    if (activeSession?.transcript) {
      setTranscriptText(activeSession.transcript);
      setTranscriptStatus("READY");
      if (activeSession.summary) {
        const summaryStr = typeof activeSession.summary === "string" 
          ? activeSession.summary 
          : activeSession.summary.summary || "";
        setSummaryResult(summaryStr);
      }
      if (activeSession.nlp) {
        setNlpResult(activeSession.nlp);
      }
      setApiError(null);
      setFetchError(null);
    }
  };

  const handleClear = () => {
    setTranscriptText("");
    setSummaryResult("");
    setNlpResult(null);
    setApiError(null);
    setFetchError(null);
    setTranscriptStatus("NO_TRANSCRIPT");
  };

  const handleGenerateSummary = async () => {
    if (!transcriptText.trim()) return;
    const targetSessionId = routeSessionId || activeSession?.id || "unknown";
    console.log(`[SUMMARY] SOURCE_SESSION_ID=${targetSessionId}`);
    setLoading(true);
    setSummaryResult("");
    setApiError(null);
    try {
      const data = await summaryService.generateSummary(transcriptText, customPrompt);
      console.log(`[SUMMARY] GENERATED session_id=${targetSessionId}`);
      setSummaryResult(data.summary);
      if (updateSession) {
        updateSession({ summary: { summary: data.summary, status: "completed" } });
      }
    } catch (err: any) {
      const errorMsg = err.message || "Failed to generate summary from transcript.";
      setApiError(errorMsg);
      setSummaryResult(`Error generating summary: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateNLP = async () => {
    if (!transcriptText.trim()) return;
    setLoading(true);
    setNlpResult(null);
    setApiError(null);
    try {
      const data = await summaryService.analyzeNLP(transcriptText);
      setNlpResult(data);
      if (updateSession) {
        updateSession({ nlp: data });
      }
    } catch (err: any) {
      const errorMsg = err.message || "Failed to analyze NLP data.";
      setApiError(errorMsg);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="space-y-8">
      
      {/* Title block */}
      <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-2 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-purple-50 rounded-full filter blur-2xl opacity-50"></div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
            <Sparkles className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-purple-600 uppercase">Module 3 &amp; 6</span>
            <h1 className="font-display text-2xl font-bold text-gray-900">NLP Engine &amp; Lecture Summaries</h1>
          </div>
        </div>
        <p className="text-gray-500 text-sm max-w-3xl">
          NEXORA parses real classroom lecture transcripts, structures technical principles into Markdown study sheets, captures vocabulary, maps homework guidelines, and measures student engagement.
        </p>
      </div>

      {/* Active Live Classroom Session Link Banner (Real Data Flow) */}
      {activeSession && (
        <div className="p-5 rounded-2xl bg-purple-50/70 border border-purple-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-600 text-white flex items-center justify-center shrink-0">
              <Radio className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${activeSession.status === "LIVE" ? "bg-emerald-500 animate-pulse" : "bg-purple-500"}`}></span>
                <span className="text-[10px] font-mono font-bold text-purple-700 uppercase tracking-wider">
                  {activeSession.status === "LIVE" ? "Live Classroom Session Active" : "Finalized Lecture Session"}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white text-purple-700 border border-purple-200">
                  #{activeSession.id}
                </span>
              </div>
              <h4 className="text-sm font-bold text-gray-900 mt-0.5">{activeSession.title}{activeSession.subject ? ` (${activeSession.subject})` : ""}</h4>
            </div>
          </div>

          {activeSession.transcript && activeSession.transcript !== transcriptText && (
            <button
              onClick={handleImportSessionTranscript}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm shrink-0"
            >
              <Download className="w-3.5 h-3.5" /> Import Session Transcript
            </button>
          )}
        </div>
      )}


      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left column: Transcript input */}
        <div className="lg:col-span-6 bg-white p-6 lg:p-8 rounded-3xl border border-gray-100 shadow-sm space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h3 className="font-display font-bold text-lg text-gray-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-purple-600" /> Lecture Transcript
                </h3>
                {transcriptStatus === "READY" && transcriptText && (
                  <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-emerald-50 text-emerald-700 rounded-full border border-emerald-100">
                    Live Verified
                  </span>
                )}
              </div>
              {transcriptText && (
                <button 
                  onClick={handleClear}
                  className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1.5 transition-colors font-mono"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Clear
                </button>
              )}
            </div>

            {transcriptStatus === "LOADING" ? (
              <div className="w-full h-72 rounded-2xl bg-purple-50/30 border border-purple-100 flex flex-col items-center justify-center space-y-3 text-center p-6">
                <Cpu className="w-7 h-7 text-purple-500 animate-spin" />
                <span className="text-sm font-semibold text-gray-700">Loading lecture transcript...</span>
                <p className="text-xs text-gray-400 max-w-xs">Retrieving speech-to-text transcript records from PostgreSQL database.</p>
              </div>
            ) : transcriptStatus === "ERROR" ? (
              <div className="w-full h-72 rounded-2xl bg-red-50/50 border border-red-200 flex flex-col items-center justify-center space-y-3 text-center p-6">
                <AlertCircle className="w-8 h-8 text-red-500" />
                <span className="text-sm font-bold text-red-800">Unable to load lecture transcript.</span>
                <p className="text-xs text-red-600 max-w-xs">{fetchError || "An error occurred querying the database."}</p>
                <button
                  onClick={() => loadSessionData()}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-sm"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Retry
                </button>
              </div>
            ) : (
              <textarea
                value={transcriptText}
                onChange={(e) => {
                  setTranscriptText(e.target.value);
                  if (e.target.value.trim()) {
                    setTranscriptStatus("READY");
                  } else {
                    setTranscriptStatus("NO_TRANSCRIPT");
                  }
                }}
                placeholder={
                  transcriptStatus === "NO_TRANSCRIPT"
                    ? "No transcript available for this session. Real transcripts will stream from the Live Classroom speech-to-text recording, or you can paste a lecture transcript here..."
                    : "Lecture transcript..."
                }
                className="w-full h-72 p-4 rounded-2xl glass-input text-sm leading-relaxed font-sans"
              />
            )}

            {activeTab === "summary" && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-600">Custom Summary Instructions (Optional)</label>
                <input
                  type="text"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="e.g. Focus specifically on formulas and definitions..."
                  className="w-full p-3 rounded-xl glass-input text-xs"
                />
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-gray-50 flex items-center justify-end gap-3">
            {activeTab === "summary" ? (
              <button
                onClick={handleGenerateSummary}
                disabled={loading || !transcriptText.trim()}
                className="px-6 py-3.5 rounded-2xl bg-purple-600 hover:bg-purple-700 disabled:bg-gray-200 disabled:cursor-not-allowed text-white text-sm font-semibold transition-all shadow-md shadow-purple-100 flex items-center gap-2"
              >
                {loading ? "Generating..." : "Compile Study Guide"} <Sparkles className="w-4.5 h-4.5" />
              </button>
            ) : (
              <button
                onClick={handleGenerateNLP}
                disabled={loading || !transcriptText.trim()}
                className="px-6 py-3.5 rounded-2xl bg-purple-600 hover:bg-purple-700 disabled:bg-gray-200 disabled:cursor-not-allowed text-white text-sm font-semibold transition-all shadow-md shadow-purple-100 flex items-center gap-2"
              >
                {loading ? "Analyzing..." : "Execute NLP Analysis"} <Cpu className="w-4.5 h-4.5" />
              </button>
            )}
          </div>
        </div>

        {/* Right column: Tab outputs */}
        <div className="lg:col-span-6 flex flex-col bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
          
          {/* Header Switcher */}
          <div className="flex border-b border-gray-100 bg-gray-50/50 p-2 gap-2 shrink-0">
            <button
              onClick={() => setActiveTab("summary")}
              className={`flex-1 py-3.5 rounded-2xl text-xs font-semibold tracking-tight transition-all flex items-center justify-center gap-2 ${
                activeTab === "summary"
                  ? "bg-white text-purple-600 shadow-sm border border-gray-100"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              <FileText className="w-4 h-4" /> Comprehensive Summary
            </button>
            <button
              onClick={() => setActiveTab("nlp")}
              className={`flex-1 py-3.5 rounded-2xl text-xs font-semibold tracking-tight transition-all flex items-center justify-center gap-2 ${
                activeTab === "nlp"
                  ? "bg-white text-purple-600 shadow-sm border border-gray-100"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              <Cpu className="w-4 h-4" /> Real-time NLP Insights
            </button>
          </div>

          {/* Results frame */}
          <div className="flex-1 p-6 lg:p-8 overflow-y-auto min-h-[450px] max-h-[600px]">
            {loading && (
              <div className="h-full flex flex-col items-center justify-center space-y-3 text-center">
                <Cpu className="w-8 h-8 text-purple-500 animate-spin" />
                <span className="text-sm font-semibold text-gray-600">Processing Transcript with AI Engine...</span>
                <p className="text-xs text-gray-400 max-w-xs">Restructuring knowledge base and formulating semantic takeaways.</p>
              </div>
            )}

            {apiError && !loading && (
              <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-3 mb-4">
                <AlertCircle className="w-5 h-5 shrink-0 text-red-500" />
                <div>
                  <p className="font-bold">AI Processing Notice</p>
                  <p className="text-[11px] text-red-600 mt-0.5">{apiError}</p>
                </div>
              </div>
            )}

            {!loading && activeTab === "summary" && (
              <div className="space-y-4">
                {summaryResult && !apiError ? (
                  <div className="prose prose-sm prose-purple select-text leading-relaxed text-gray-700 font-sans break-words whitespace-pre-wrap">
                    {summaryResult}
                  </div>
                ) : !apiError && (
                  <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 py-16 space-y-2">
                    <BookMarked className="w-10 h-10 text-gray-300" />
                    <span className="font-semibold text-sm">No summary generated yet</span>
                    <p className="text-xs text-gray-400 max-w-xs">Enter or import a real lecture transcript and click "Compile Study Guide" to generate an academically detailed Markdown study sheet.</p>
                  </div>
                )}
              </div>
            )}

            {!loading && activeTab === "nlp" && (
              <div className="space-y-6">
                {nlpResult ? (
                  <div className="space-y-6 select-text">
                    
                    {/* General Sentiment */}
                    <div className="p-4 bg-purple-50/50 rounded-2xl border border-purple-100 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] text-gray-400 font-bold block uppercase tracking-wider">Estimated Sentiment &amp; Tone</span>
                        <span className="text-sm font-bold text-purple-900">{nlpResult.sentiment}</span>
                      </div>
                      <TrendingUp className="w-5 h-5 text-purple-600" />
                    </div>

                    {/* Topics extracted */}
                    <div className="space-y-2.5">
                      <span className="text-xs font-bold text-gray-400 block uppercase tracking-wider">Extracted Topics</span>
                      <div className="flex flex-wrap gap-2">
                        {nlpResult.topics.map((topic, i) => (
                          <span key={i} className="px-3 py-1.5 rounded-xl bg-purple-50 text-purple-700 font-semibold text-xs border border-purple-100">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Definitions */}
                    <div className="space-y-2.5">
                      <span className="text-xs font-bold text-gray-400 block uppercase tracking-wider">Academic Vocabulary Defined</span>
                      <div className="space-y-2">
                        {nlpResult.definitions.map((def, i) => (
                          <div key={i} className="p-4 rounded-xl border border-gray-100 bg-white shadow-sm space-y-1">
                            <span className="font-bold text-sm text-gray-900">{def.term}</span>
                            <p className="text-xs text-gray-500 leading-normal">{def.explanation}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Items */}
                    <div className="space-y-2.5">
                      <span className="text-xs font-bold text-gray-400 block uppercase tracking-wider">Action Items &amp; Deadlines</span>
                      <ul className="space-y-2">
                        {nlpResult.actionItems.map((item, i) => (
                          <li key={i} className="flex gap-3 text-xs text-gray-600 leading-relaxed font-medium">
                            <CheckCircle className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 py-16 space-y-2">
                    <Cpu className="w-10 h-10 text-gray-300" />
                    <span className="font-semibold text-sm">No NLP analysis triggered yet</span>
                    <p className="text-xs text-gray-400 max-w-xs">Run the NLP analysis to automatically extract dictionary parameters, timeline highlights, and engagement levels from lecture transcripts.</p>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
