import React, { useState } from "react";
import { 
  FileText, 
  Sparkles, 
  Cpu, 
  Square, 
  Circle, 
  Type, 
  Trash2, 
  Play, 
  Award,
  ChevronRight,
  BookOpen,
  Brush,
  RefreshCw,
  Plus
} from "lucide-react";
import { WhiteboardElement } from "../types";
import { motion, AnimatePresence } from "motion/react";
import { summaryService } from "../services/summary";

export default function ModuleNotesAndWhiteboard() {
  const [activeTab, setActiveTab] = useState<"notes" | "whiteboard">("notes");
  
  // Notes generator state
  const [notesTopic, setNotesTopic] = useState("");
  const [subject, setSubject] = useState("");
  const [notesResult, setNotesResult] = useState("");
  const [notesLoading, setNotesLoading] = useState(false);

  // Whiteboard state
  const [elements, setElements] = useState<WhiteboardElement[]>([]);
  const [elementText, setElementText] = useState("");
  const [elementType, setElementType] = useState<"text" | "rect" | "circle">("circle");
  const [whiteboardAnalysis, setWhiteboardAnalysis] = useState("");
  const [whiteboardLoading, setWhiteboardLoading] = useState(false);

  const handleGenerateNotes = async () => {
    if (!notesTopic.trim()) return;
    setNotesLoading(true);
    setNotesResult("");
    try {
      // Routes through FastAPI /ai/notes — all AI orchestration is server-side
      const data = await summaryService.generateNotes(notesTopic, subject);
      setNotesResult(data.notes);
    } catch (err: any) {
      setNotesResult(
        `Failed to compile lecture notes: ${err.message}. Please ensure the FastAPI backend is running.`
      );
    } finally {
      setNotesLoading(false);
    }
  };

  const handleAddWhiteboardElement = () => {
    const textVal = elementText || (elementType === "text" ? "Equation: y = mx + c" : "New Block");
    const newEl: WhiteboardElement = {
      id: "el-" + Date.now(),
      type: elementType,
      x: Math.floor(Math.random() * 200) + 120,
      y: Math.floor(Math.random() * 100) + 80,
      width: elementType === "rect" ? 120 : undefined,
      height: elementType === "rect" ? 60 : undefined,
      color: elementType === "circle" ? "#2563EB" : (elementType === "rect" ? "#7C3AED" : "#111827"),
      text: textVal
    };
    setElements([...elements, newEl]);
    setElementText("");
  };

  const handleAnalyzeWhiteboard = async () => {
    setWhiteboardLoading(true);
    setWhiteboardAnalysis("");
    
    // Convert current whiteboard canvas elements into a clean textual representation for Gemini
    const canvasDesc = elements.map(el => {
      if (el.type === "circle") return `Circle Node containing "${el.text}" situated at coordinate (${el.x}, ${el.y})`;
      if (el.type === "rect") return `Rectangular Activation function block containing "${el.text}" with dims ${el.width}x${el.height} at coordinate (${el.x}, ${el.y})`;
      if (el.type === "text") return `Mathematical equation statement containing label "${el.text}" located at (${el.x}, ${el.y})`;
      return `Connective flow Vector link at (${el.x}, ${el.y})`;
    }).join(", ");

    try {
      // Routes through FastAPI /ai/chat — all AI orchestration is server-side
      const data = await summaryService.chat(
        `Observe the following whiteboard diagram components: [${canvasDesc}]. This represents a computer science or physics blackboard. Analyze this configuration, solve or expand on the underlying mathematical theory/concepts, and produce a brief step-by-step academic explainer for students. Use Markdown.`
      );
      setWhiteboardAnalysis(data.reply);
    } catch (err: any) {
      setWhiteboardAnalysis(
        `Whiteboard Analysis failed: ${err.message}. Please ensure the FastAPI backend is running.`
      );
    } finally {
      setWhiteboardLoading(false);
    }
  };

  const presetNotesTopics = [
    { topic: "Artificial Neural Networks", subject: "Computer Science" },
    { topic: "Cellular Mitosis & Meiosis", subject: "Biology" },
    { topic: "Newtonian Classical Mechanics", subject: "Physics" }
  ];

  return (
    <div className="space-y-8">
      
      {/* Title block */}
      <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-2 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-purple-50 rounded-full filter blur-2xl opacity-50"></div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
            <Brush className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-purple-600 uppercase">Module 9 &amp; 15</span>
            <h1 className="font-display text-2xl font-bold text-gray-900">Notes Generator &amp; AI Whiteboard</h1>
          </div>
        </div>
        <p className="text-gray-500 text-sm max-w-3xl">
          NEXORA provides printable lecture study sheets and features an interactive logical whiteboard where equations, neural layers, and flow paths can be mapped and parsed by the AI.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Control Column */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Tab selector */}
          <div className="bg-white p-3 rounded-2xl border border-gray-100 shadow-sm flex gap-2">
            <button
              onClick={() => setActiveTab("notes")}
              className={`flex-1 py-3.5 rounded-xl text-xs font-semibold tracking-tight transition-all flex items-center justify-center gap-2 ${
                activeTab === "notes"
                  ? "bg-purple-600 text-white shadow-md shadow-purple-100"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              <FileText className="w-4 h-4" /> Study Notes Gen
            </button>
            <button
              onClick={() => setActiveTab("whiteboard")}
              className={`flex-1 py-3.5 rounded-xl text-xs font-semibold tracking-tight transition-all flex items-center justify-center gap-2 ${
                activeTab === "whiteboard"
                  ? "bg-purple-600 text-white shadow-md shadow-purple-100"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              <Brush className="w-4 h-4" /> AI Logical Whiteboard
            </button>
          </div>

          {/* Configuration Parameters */}
          <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-5">
            <h4 className="font-display font-bold text-base text-gray-900">
              {activeTab === "notes" ? "Notes Parameters" : "Whiteboard Toolbox"}
            </h4>

            {activeTab === "notes" ? (
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600">Lecture Topic</label>
                  <input
                    type="text"
                    value={notesTopic}
                    onChange={(e) => setNotesTopic(e.target.value)}
                    className="w-full p-3 rounded-xl glass-input text-xs"
                    placeholder="e.g. Mitochondria ATP cycle..."
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600">Academic Field</label>
                  <input
                    type="text"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="w-full p-3 rounded-xl glass-input text-xs"
                    placeholder="e.g. Biochemistry..."
                  />
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-gray-400 block">Preset Topics</span>
                  <div className="flex flex-col gap-2">
                    {presetNotesTopics.map((pt, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setNotesTopic(pt.topic);
                          setSubject(pt.subject);
                        }}
                        className="w-full text-left p-3 rounded-xl border border-gray-100 hover:border-purple-200 hover:bg-purple-50/20 text-xs font-medium text-gray-700 transition-colors"
                      >
                        {pt.topic}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleGenerateNotes}
                  disabled={notesLoading || !notesTopic.trim()}
                  className="w-full py-3.5 rounded-2xl bg-purple-600 hover:bg-purple-700 disabled:bg-gray-100 disabled:text-gray-400 text-white font-semibold text-xs transition-all shadow-md shadow-purple-100 flex items-center justify-center gap-2"
                >
                  {notesLoading ? "Compiling Notes..." : "Compile Comprehensive Notes"} <Sparkles className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600">Component Shape</label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => setElementType("circle")}
                      className={`py-2 rounded-xl border text-xs font-semibold flex flex-col items-center justify-center gap-1.5 ${
                        elementType === "circle" ? "border-purple-500 bg-purple-50 text-purple-600" : "border-gray-100 hover:bg-gray-50 text-gray-500"
                      }`}
                    >
                      <Circle className="w-4.5 h-4.5" /> Circle Node
                    </button>
                    <button
                      onClick={() => setElementType("rect")}
                      className={`py-2 rounded-xl border text-xs font-semibold flex flex-col items-center justify-center gap-1.5 ${
                        elementType === "rect" ? "border-purple-500 bg-purple-50 text-purple-600" : "border-gray-100 hover:bg-gray-50 text-gray-500"
                      }`}
                    >
                      <Square className="w-4.5 h-4.5" /> Block Rect
                    </button>
                    <button
                      onClick={() => setElementType("text")}
                      className={`py-2 rounded-xl border text-xs font-semibold flex flex-col items-center justify-center gap-1.5 ${
                        elementType === "text" ? "border-purple-500 bg-purple-50 text-purple-600" : "border-gray-100 hover:bg-gray-50 text-gray-500"
                      }`}
                    >
                      <Type className="w-4.5 h-4.5" /> Text Line
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600">Label or Equation String</label>
                  <input
                    type="text"
                    value={elementText}
                    onChange={(e) => setElementText(e.target.value)}
                    placeholder="e.g. d/dx(e^x) = e^x..."
                    className="w-full p-3 rounded-xl glass-input text-xs"
                  />
                </div>

                <button
                  onClick={handleAddWhiteboardElement}
                  className="w-full py-3 rounded-xl border border-purple-200 bg-purple-50 text-purple-600 hover:bg-purple-100 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Plus className="w-4 h-4" /> Add Element to Board
                </button>

                <div className="pt-4 border-t border-gray-100 space-y-2">
                  <button
                    onClick={handleAnalyzeWhiteboard}
                    disabled={whiteboardLoading || elements.length === 0}
                    className="w-full py-3.5 rounded-2xl bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs transition-all shadow-md shadow-purple-100 flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {whiteboardLoading ? "NEXORA Solves..." : "Solve Blackboard Logic"} <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      setElements([]);
                      setWhiteboardAnalysis("");
                    }}
                    className="w-full py-2 rounded-xl text-gray-400 hover:text-red-500 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" /> Reset Board
                  </button>
                </div>

              </div>
            )}
          </div>
        </div>

        {/* Output Screen */}
        <div className="lg:col-span-8 bg-white p-6 lg:p-8 rounded-3xl border border-gray-100 shadow-sm flex flex-col justify-between min-h-[480px]">
          
          {activeTab === "notes" && (
            <div className="space-y-6 select-text h-full flex flex-col justify-between">
              {notesLoading && (
                <div className="py-24 flex flex-col items-center justify-center space-y-3 text-center">
                  <Cpu className="w-8 h-8 text-purple-500 animate-spin" />
                  <span className="text-sm font-semibold text-gray-600">Structuring Lesson Notes...</span>
                  <p className="text-xs text-gray-400 max-w-xs">Connecting to Gemini to structure definitions, bulleted paragraphs, and conceptual frameworks.</p>
                </div>
              )}

              {!notesLoading && notesResult && (
                <div className="p-6 bg-gray-50/50 rounded-3xl border border-gray-100 space-y-4 max-h-[420px] overflow-y-auto">
                  <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Lesson Notes Study Sheet</span>
                    <span className="text-xs text-purple-600 font-semibold flex items-center gap-1">
                      <FileText className="w-4 h-4" /> Printable PDF Available
                    </span>
                  </div>
                  <div className="prose prose-sm prose-purple select-text leading-relaxed text-gray-700 whitespace-pre-wrap text-xs font-sans">
                    {notesResult}
                  </div>
                </div>
              )}

              {!notesLoading && !notesResult && (
                <div className="py-24 text-center text-gray-400 flex flex-col items-center justify-center space-y-2">
                  <BookOpen className="w-10 h-10 text-gray-300" />
                  <span className="font-semibold text-sm">No Active Lesson Study Sheets</span>
                  <p className="text-xs text-gray-400 max-w-xs">Enter your topic, adjust the parameters on the left, and click Compile Lecture Notes to generate study manuals.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === "whiteboard" && (
            <div className="space-y-6 h-full flex flex-col justify-between">
              
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-full">
                
                {/* Board grid Canvas */}
                <div className="md:col-span-7 h-80 rounded-2xl bg-gray-950 border border-gray-900 relative overflow-hidden flex items-center justify-center p-2">
                  
                  {/* Grid overlay lines */}
                  <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-40"></div>

                  {elements.length > 0 ? (
                    elements.map((el) => {
                      if (el.type === "circle") {
                        return (
                          <div
                            key={el.id}
                            className="absolute w-20 h-20 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold text-center p-1 cursor-move shadow-md border-2 border-white/20"
                            style={{ left: `${el.x}px`, top: `${el.y}px` }}
                          >
                            {el.text}
                          </div>
                        );
                      }
                      if (el.type === "rect") {
                        return (
                          <div
                            key={el.id}
                            className="absolute bg-purple-600 text-white flex items-center justify-center text-[10px] font-bold text-center p-2 cursor-move rounded-xl shadow-md border-2 border-white/20"
                            style={{ left: `${el.x}px`, top: `${el.y}px`, width: `${el.width}px`, height: `${el.height}px` }}
                          >
                            {el.text}
                          </div>
                        );
                      }
                      if (el.type === "text") {
                        return (
                          <div
                            key={el.id}
                            className="absolute text-emerald-400 font-mono text-[11px] font-bold p-1 whitespace-nowrap"
                            style={{ left: `${el.x}px`, top: `${el.y}px` }}
                          >
                            {el.text}
                          </div>
                        );
                      }
                      return (
                        <div
                          key={el.id}
                          className="absolute w-24 h-0.5 bg-sky-400"
                          style={{ left: `${el.x}px`, top: `${el.y}px`, transform: "rotate(15deg)" }}
                        ></div>
                      );
                    })
                  ) : (
                    <div className="text-center font-mono text-xs text-gray-500 relative z-10 space-y-2">
                      <Brush className="w-8 h-8 mx-auto text-gray-600 animate-pulse" />
                      <span>Blackboard Canvas Empty</span>
                      <p className="text-[10px] text-gray-600">Use the left toolbox to add shapes &amp; formulas.</p>
                    </div>
                  )}

                  {/* Header labels */}
                  <div className="absolute top-3 left-3 px-3 py-1 rounded bg-black/50 border border-white/10 text-[9px] text-gray-400 font-mono">
                    logical_whiteboard.ts
                  </div>
                </div>

                {/* AI Solution Response */}
                <div className="md:col-span-5 flex flex-col justify-between h-80 bg-gray-50 rounded-2xl border border-gray-100 overflow-hidden">
                  
                  <div className="px-4 py-2.5 bg-gray-100 border-b border-gray-200 flex items-center justify-between">
                    <span className="text-[10px] font-bold text-gray-500 uppercase font-mono">NEXORA Solver</span>
                    <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                  </div>

                  <div className="flex-1 p-4 overflow-y-auto text-[11px] select-text font-sans leading-relaxed text-gray-600">
                    {whiteboardLoading && (
                      <div className="h-full flex flex-col items-center justify-center space-y-2 animate-pulse text-center">
                        <RefreshCw className="w-5 h-5 text-purple-500 animate-spin" />
                        <span className="font-semibold text-gray-500">Calculating logic proof...</span>
                      </div>
                    )}

                    {!whiteboardLoading && whiteboardAnalysis && (
                      <div className="whitespace-pre-wrap prose prose-sm prose-purple font-sans leading-relaxed">
                        {whiteboardAnalysis}
                      </div>
                    )}

                    {!whiteboardLoading && !whiteboardAnalysis && (
                      <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 space-y-1 py-10">
                        <Cpu className="w-6 h-6 text-gray-300" />
                        <span className="font-bold">Solver Standby</span>
                        <p className="text-[10px] text-gray-400">Map custom components on the blackboard and click "Solve Blackboard Logic" to trigger a proof.</p>
                      </div>
                    )}
                  </div>

                </div>

              </div>

            </div>
          )}

        </div>

      </div>
    </div>
  );
}
