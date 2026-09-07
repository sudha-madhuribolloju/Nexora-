import React, { useState, useEffect, useRef } from "react";
import { 
  Bot, 
  Send, 
  Upload, 
  FileText, 
  ArrowRight, 
  Sparkles, 
  Trash2, 
  ChevronRight, 
  Loader2,
  FileUp,
  XCircle,
  HelpCircle
} from "lucide-react";
import { ChatMessage } from "../types";
import { motion, AnimatePresence } from "motion/react";

import { summaryService } from "../services/summary";
import { documentService } from "../services/document";

export default function ModuleAIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I am NEXORA, your AI Student Agent. You can upload textbook PDFs, lecture slides, or documents here, and chat with me about them. What shall we learn today?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Real user uploaded documents list
  const [documents, setDocuments] = useState<Array<{ id: string; name: string; size: string; pages: number; uploadedAt: string }>>([]);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);

  const messageEndRef = useRef<HTMLDivElement>(null);

  // Load real documents from API on mount
  useEffect(() => {
    loadUserDocuments();
  }, []);

  const loadUserDocuments = async () => {
    try {
      const res = await documentService.listDocuments(0, 50);
      if (res && res.data && res.data.length > 0) {
        const mapped = res.data.map((d: any) => ({
          id: d.id,
          name: d.title || d.file_url?.split("/").pop() || "Document.pdf",
          size: d.file_size ? `${(d.file_size / (1024 * 1024)).toFixed(1)} MB` : "PDF Document",
          pages: d.page_count || 1,
          uploadedAt: new Date(d.created_at || Date.now()).toLocaleDateString()
        }));
        setDocuments(mapped);
        if (!activeDocId && mapped.length > 0) {
          setActiveDocId(mapped[0].id);
        }
      } else {
        setDocuments([]);
        setActiveDocId(null);
      }
    } catch (err) {
      console.warn("[AIChat] Could not load documents from API:", err);
      setDocuments([]);
      setActiveDocId(null);
    }
  };

  const activeDoc = documents.find(d => d.id === activeDocId);

  const suggestionPills = activeDoc ? [
    { label: "Summarize this document", prompt: `Summarize the core takeaways and main arguments presented in ${activeDoc.name}.` },
    { label: "Explain key concepts", prompt: `Identify and explain the key technical concepts and definitions from ${activeDoc.name}.` },
    { label: "Generate study questions", prompt: `Generate 3 comprehensive study questions based on the key points in ${activeDoc.name}.` }
  ] : [
    { label: "How to use NEXORA AI", prompt: "How can you help me study, summarize lecture transcripts, and analyze documents?" },
    { label: "Effective Study Strategies", prompt: "What are effective study and note-taking techniques for complex academic topics?" },
    { label: "Academic Topic Overview", prompt: "I'd like to explore a new academic subject. Can you give me an overview?" }
  ];

  // Auto-scroll chat to bottom
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSendMessage = async (customPrompt?: string) => {
    const textToSend = customPrompt || inputText;
    if (!textToSend.trim()) return;

    // Construct the user message
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText("");
    setLoading(true);

    try {
      // Include document context if available
      const contextualQuery = activeDoc 
        ? `[Referring to document: ${activeDoc.name}]\n\n${textToSend}`
        : textToSend;

      // Extract last 6 messages for history to avoid overloading token context
      const history = messages.slice(-6).map(m => ({
        role: m.role,
        content: m.content
      }));

      const data = await summaryService.chat(contextualQuery, history, activeDocId);

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (error: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Sorry, I encountered an error during transmission: ${error.message}. Please ensure the FastAPI backend is running and try again.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file) return;
    try {
      setLoading(true);
      const res = await documentService.uploadDocumentFile(file);
      const newDoc = {
        id: "doc-" + Date.now(),
        name: res.title || file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        pages: 1,
        uploadedAt: "Just Now"
      };
      setDocuments(prev => [newDoc, ...prev]);
      setActiveDocId(newDoc.id);
    } catch (err: any) {
      console.warn("Upload error:", err);
      // Fallback local registration
      const newDoc = {
        id: "doc-" + Date.now(),
        name: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        pages: 1,
        uploadedAt: "Just Now"
      };
      setDocuments(prev => [newDoc, ...prev]);
      setActiveDocId(newDoc.id);
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFileUpload(e.target.files[0]);
    }
  };

  const handleDeleteDoc = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await documentService.deleteDocument(id);
    } catch (err) {
      console.warn("Delete document note:", err);
    }
    setDocuments(prev => prev.filter(d => d.id !== id));
    if (activeDocId === id) {
      setActiveDocId(null);
    }
  };


  return (
    <div className="space-y-8 h-full flex flex-col justify-between">
      
      {/* Title section */}
      <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-2 relative overflow-hidden shrink-0">
        <div className="absolute top-0 right-0 w-48 h-48 bg-sky-50 rounded-full filter blur-2xl opacity-50"></div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-50 flex items-center justify-center text-sky-600">
            <Bot className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-sky-600 uppercase">Module 4, 12 &amp; 14</span>
            <h1 className="font-display text-2xl font-bold text-gray-900">AI Student Interaction &amp; PDF Chat</h1>
          </div>
        </div>
        <p className="text-gray-500 text-sm max-w-3xl">
          Upload reference textbooks or notes, select any active course files, and query NEXORA live to summarize definitions, run code snippets, or explain equations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1 min-h-[500px]">
        
        {/* Left Side: Document Library & File Upload */}
        <div className="lg:col-span-4 bg-white p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col space-y-6">
          <div className="space-y-2">
            <h3 className="font-display font-bold text-base text-gray-900">Document Library</h3>
            <p className="text-xs text-gray-400">Select which context textbook is active for the AI Agent.</p>
          </div>

          {/* Drag & Drop uploader */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileInputChange}
            className="hidden"
            accept=".pdf,.doc,.docx,.pptx,.txt"
          />
          <div 
            onClick={() => fileInputRef.current?.click()}
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            className={`p-6 rounded-2xl border-2 border-dashed text-center flex flex-col items-center justify-center gap-3 transition-all cursor-pointer ${
              dragActive 
                ? "border-sky-500 bg-sky-50/50" 
                : "border-gray-200 hover:border-sky-300 bg-gray-50/50"
            }`}
          >
            <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-sky-600 shadow-sm">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-semibold block text-gray-700">Upload Textbook or Drag &amp; Drop</span>
              <span className="text-[10px] text-gray-400 mt-1 block">Supports PDF, Word, PowerPoint (Max 50MB)</span>
            </div>
          </div>

          {/* List of active documents */}
          <div className="space-y-2.5 flex-1 overflow-y-auto max-h-72">
            {documents.length > 0 ? (
              documents.map((doc) => {
                const isActive = activeDocId === doc.id;
                return (
                  <div
                    key={doc.id}
                    onClick={() => setActiveDocId(doc.id)}
                    className={`p-4 rounded-2xl border text-left transition-all flex items-center justify-between cursor-pointer ${
                      isActive 
                        ? "bg-sky-50/40 border-sky-200 shadow-sm" 
                        : "bg-white border-gray-100 hover:bg-gray-50/50"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                        isActive ? "bg-sky-100 text-sky-600" : "bg-gray-100 text-gray-500"
                      }`}>
                        <FileText className="w-4.5 h-4.5" />
                      </div>
                      <div className="min-w-0">
                        <span className="text-xs font-bold block text-gray-800 truncate">{doc.name}</span>
                        <span className="text-[9px] text-gray-400 block mt-0.5">{doc.size} • {doc.pages} pages</span>
                      </div>
                    </div>
                    
                    <button 
                      onClick={(e) => handleDeleteDoc(doc.id, e)}
                      className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-10 text-gray-400 space-y-2">
                <FileText className="w-8 h-8 mx-auto text-gray-300" />
                <p className="text-xs font-semibold text-gray-500">No documents uploaded yet</p>
                <p className="text-[11px] text-gray-400 max-w-[200px] mx-auto">Upload a PDF, Word document, or PowerPoint to begin.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Conversation Frame */}
        <div className="lg:col-span-8 bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden flex flex-col h-[550px]">
          
          {/* Active document context banner */}
          <div className="px-6 py-3 bg-gray-50/50 border-b border-gray-50 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sky-500"></span>
              <span className="text-xs font-semibold text-gray-600">
                {activeDocId 
                  ? `Active Context: ${documents.find(d => d.id === activeDocId)?.name}` 
                  : "No document attached (Standard AI Mode)"}
              </span>
            </div>
            <span className="text-[10px] font-mono text-gray-400">Memory Active</span>
          </div>

          {/* Thread messages block */}
          <div className="flex-1 p-6 overflow-y-auto space-y-4">
            <AnimatePresence initial={false}>
              {messages.map((m) => {
                const isAI = m.role === "assistant";
                return (
                  <motion.div
                    key={m.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`flex gap-3 max-w-[85%] ${isAI ? "mr-auto" : "ml-auto flex-row-reverse"}`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-sm text-sm font-bold ${
                      isAI ? "bg-sky-500 text-white" : "bg-purple-600 text-white"
                    }`}>
                      {isAI ? <Bot className="w-4 h-4" /> : "ME"}
                    </div>
                    <div className="space-y-1">
                      <div className={`p-4 rounded-2xl text-xs leading-relaxed select-text ${
                        isAI 
                          ? "bg-gray-50 border border-gray-100 text-gray-800" 
                          : "bg-blue-600 text-white"
                      }`}>
                        <p className="whitespace-pre-wrap font-sans">{m.content}</p>
                      </div>
                      <span className="text-[9px] text-gray-400 block mt-0.5 text-right px-1">{m.timestamp}</span>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
            
            {loading && (
              <div className="flex gap-3 mr-auto max-w-[85%]">
                <div className="w-8 h-8 rounded-lg bg-sky-500 text-white flex items-center justify-center shrink-0 animate-spin">
                  <Loader2 className="w-4 h-4" />
                </div>
                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs text-gray-500 italic animate-pulse">
                  NEXORA is compiling answers from academic vectors...
                </div>
              </div>
            )}
            <div ref={messageEndRef} />
          </div>

          {/* Thread Bottom triggers: Suggestions */}
          <div className="px-6 py-3 border-t border-gray-50 bg-gray-50/20 overflow-x-auto whitespace-nowrap scrollbar-none flex gap-2 shrink-0">
            {suggestionPills.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(p.prompt)}
                className="px-3.5 py-1.5 rounded-full border border-gray-200 bg-white hover:border-sky-300 hover:text-sky-600 text-xs text-gray-500 transition-all font-medium cursor-pointer"
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Input Block */}
          <div className="p-4 border-t border-gray-100 shrink-0 bg-white flex items-center gap-3">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading) handleSendMessage();
              }}
              placeholder="Query NEXORA or analyze connected textbook..."
              className="flex-1 p-3.5 rounded-2xl glass-input text-xs"
              disabled={loading}
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={loading || !inputText.trim()}
              className="p-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition-all disabled:bg-gray-100 disabled:text-gray-400 shadow-md shadow-blue-100 cursor-pointer flex items-center justify-center shrink-0"
            >
              <Send className="w-4.5 h-4.5" />
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}
