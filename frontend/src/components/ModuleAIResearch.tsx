import React, { useState, useEffect } from "react";
import { 
  Search, 
  BookOpen, 
  Sparkles, 
  ExternalLink, 
  Bookmark, 
  BookmarkCheck,
  Cpu, 
  FileText, 
  ArrowRight,
  BookmarkX,
  Plus
} from "lucide-react";
import { Citation } from "../types";
import { motion, AnimatePresence } from "motion/react";
import { summaryService } from "../services/summary";

interface SavedPaper {
  id: string;
  query: string;
  findings: string;
  citations: Citation[];
  timestamp: string;
}

export default function ModuleAIResearch() {
  const [researchQuery, setResearchQuery] = useState("");
  const [findings, setFindings] = useState<string>("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Knowledge Base Saved list
  const [savedPapers, setSavedPapers] = useState<SavedPaper[]>([]);
  const [selectedSavedId, setSelectedSavedId] = useState<string | null>(null);

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("nexora_research_papers");
    if (saved) {
      try {
        setSavedPapers(JSON.parse(saved));
      } catch (err) {
        console.error(err);
      }
    }
  }, []);

  const handleResearch = async () => {
    if (!researchQuery.trim()) return;
    setLoading(true);
    setFindings("");
    setCitations([]);
    setSelectedSavedId(null);

    try {
      const data = await summaryService.research(researchQuery);

      setFindings(data.findings);
      setCitations(data.citations || []);
    } catch (err: any) {
      setFindings(`Failed to compile academic research findings: ${err.message}. Please ensure the FastAPI backend is running.`);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveToKB = () => {
    if (!findings) return;
    const newPaper: SavedPaper = {
      id: "paper-" + Date.now(),
      query: researchQuery || "General Inquiry",
      findings: findings,
      citations: citations,
      timestamp: new Date().toLocaleDateString()
    };
    
    const updated = [newPaper, ...savedPapers];
    setSavedPapers(updated);
    localStorage.setItem("nexora_research_papers", JSON.stringify(updated));
    setSelectedSavedId(newPaper.id);
  };

  const handleDeletePaper = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = savedPapers.filter(p => p.id !== id);
    setSavedPapers(updated);
    localStorage.setItem("nexora_research_papers", JSON.stringify(updated));
    if (selectedSavedId === id) {
      setSelectedSavedId(null);
    }
  };

  const handleSelectPaper = (paper: SavedPaper) => {
    setSelectedSavedId(paper.id);
    setResearchQuery(paper.query);
    setFindings(paper.findings);
    setCitations(paper.citations);
  };

  const isCurrentPaperSaved = savedPapers.some(p => p.query.toLowerCase() === researchQuery.toLowerCase() && findings);

  const presetQueries = [
    "CRISPR gene drive ecology risks",
    "Latest milestones in Room-Temperature Superconductors",
    "Compare GPT-4o vs Claude 3.5 Sonnet on mathematical reasoning"
  ];

  return (
    <div className="space-y-8">
      
      {/* Title */}
      <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-2 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-blue-50 rounded-full filter blur-2xl opacity-50"></div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
            <Search className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-blue-600 uppercase">Module 5 &amp; 21</span>
            <h1 className="font-display text-2xl font-bold text-gray-900">Academic AI Research &amp; Knowledge Base</h1>
          </div>
        </div>
        <p className="text-gray-500 text-sm max-w-3xl">
          NEXORA connects directly to web search grounding, gathering real-time academic literature, news, and technical data, citing original reference links into the Knowledge Base.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left column: Research portal */}
        <div className="lg:col-span-8 bg-white p-6 lg:p-8 rounded-3xl border border-gray-100 shadow-sm space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="font-display font-bold text-lg text-gray-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" /> Academic Search Portal
            </h3>

            {/* Input query and search button */}
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={researchQuery}
                onChange={(e) => setResearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !loading) handleResearch();
                }}
                placeholder="Submit inquiry (e.g., compare solid state batteries with lithium-ion...)"
                className="flex-1 p-3.5 rounded-2xl glass-input text-xs"
                disabled={loading}
              />
              <button
                onClick={handleResearch}
                disabled={loading || !researchQuery.trim()}
                className="px-6 py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:cursor-not-allowed text-white text-xs font-semibold transition-all shadow-md shadow-blue-100 shrink-0 flex items-center justify-center gap-2 cursor-pointer"
              >
                {loading ? "Searching..." : "Launch Research"} <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Quick Presets */}
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-gray-400 block">Preset Inquiries</span>
              <div className="flex flex-col sm:flex-row gap-2">
                {presetQueries.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setResearchQuery(q);
                      setFindings("");
                      setCitations([]);
                      setSelectedSavedId(null);
                    }}
                    className="flex-1 text-left p-2.5 rounded-xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50/20 text-[11px] font-medium text-gray-600 transition-all truncate"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {/* Citations references display */}
            {citations.length > 0 && (
              <div className="p-4 bg-gray-50 rounded-2xl border border-gray-100 space-y-2">
                <span className="text-[10px] uppercase font-mono font-bold text-gray-400 block">Google Search Grounding Citations</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {citations.map((cite, i) => (
                    <a
                      key={i}
                      href={cite.uri}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 bg-white rounded-xl border border-gray-100 hover:border-blue-300 hover:text-blue-600 transition-all flex items-center justify-between gap-2 min-w-0"
                    >
                      <span className="truncate font-semibold text-gray-700">{cite.title}</span>
                      <ExternalLink className="w-3.5 h-3.5 shrink-0 text-gray-400" />
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Findings Display Area */}
            {loading && (
              <div className="py-20 flex flex-col items-center justify-center space-y-3">
                <Cpu className="w-8 h-8 text-blue-500 animate-spin" />
                <span className="text-sm font-semibold text-gray-600">Executing Deep Academic Web Search...</span>
                <p className="text-xs text-gray-400 max-w-xs text-center">Formulating citations, aggregating scholarly literature, and evaluating context windows with Gemini.</p>
              </div>
            )}

            {!loading && findings && (
              <div className="p-6 bg-gray-50/50 rounded-3xl border border-gray-100 space-y-4 max-h-[400px] overflow-y-auto">
                <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Research Findings</span>
                  {isCurrentPaperSaved ? (
                    <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                      <BookmarkCheck className="w-4 h-4" /> Saved in KB
                    </span>
                  ) : (
                    <button
                      onClick={handleSaveToKB}
                      className="text-xs text-blue-600 font-semibold flex items-center gap-1 hover:text-blue-700 transition-colors"
                    >
                      <Plus className="w-4 h-4" /> Save to Knowledge Base
                    </button>
                  )}
                </div>
                <div className="prose prose-sm prose-blue select-text leading-relaxed text-gray-700 whitespace-pre-wrap text-xs font-sans">
                  {findings}
                </div>
              </div>
            )}

            {!loading && !findings && (
              <div className="py-20 text-center text-gray-400 flex flex-col items-center justify-center space-y-2">
                <BookOpen className="w-10 h-10 text-gray-300" />
                <span className="font-semibold text-sm">No Active Research</span>
                <p className="text-xs text-gray-400 max-w-xs">Submit a technical query above. We will fetch literature, ground it in Google Search, and structure the result in Harvard citation formats.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right column: KB index list */}
        <div className="lg:col-span-4 bg-white p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col space-y-5">
          <div className="space-y-1">
            <h3 className="font-display font-bold text-base text-gray-900">Knowledge Base</h3>
            <p className="text-xs text-gray-400">Review saved scientific papers and class guidelines here.</p>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto max-h-96 pr-1">
            {savedPapers.length > 0 ? (
              savedPapers.map((paper) => {
                const isSelected = selectedSavedId === paper.id;
                return (
                  <div
                    key={paper.id}
                    onClick={() => handleSelectPaper(paper)}
                    className={`p-4 rounded-2xl border text-left transition-all flex flex-col justify-between cursor-pointer ${
                      isSelected 
                        ? "bg-blue-50/50 border-blue-200 shadow-sm" 
                        : "bg-white border-gray-100 hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3 min-w-0">
                      <div className="flex gap-2.5 min-w-0">
                        <FileText className="w-4.5 h-4.5 text-blue-500 mt-0.5 shrink-0" />
                        <div className="min-w-0">
                          <span className="text-xs font-bold text-gray-800 block truncate">{paper.query}</span>
                          <span className="text-[10px] text-gray-400 mt-0.5 block">{paper.timestamp} • {paper.citations.length} sources</span>
                        </div>
                      </div>
                      
                      <button 
                        onClick={(e) => handleDeletePaper(paper.id, e)}
                        className="p-1 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors shrink-0"
                      >
                        <BookmarkX className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center text-xs text-gray-400 py-16 space-y-2">
                <Bookmark className="w-8 h-8 mx-auto text-gray-300" />
                <span className="font-semibold block">Knowledge Base is Empty</span>
                <p className="text-[11px] text-gray-400">Conduct research and click "Save to Knowledge Base" to preserve summaries.</p>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
