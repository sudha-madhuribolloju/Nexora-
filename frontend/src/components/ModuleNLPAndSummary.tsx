import React, { useState } from "react";
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
  BookMarked
} from "lucide-react";
import { NLPAnalysis } from "../types";
import { motion } from "motion/react";
import { summaryService } from "../services/summary";

export default function ModuleNLPAndSummary() {
  const [activeTab, setActiveTab] = useState<"summary" | "nlp">("summary");
  const [transcriptText, setTranscriptText] = useState("");
  const [customPrompt, setCustomPrompt] = useState("");
  const [summaryResult, setSummaryResult] = useState<string>("");
  const [nlpResult, setNlpResult] = useState<NLPAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  const samples = [
    {
      title: "Lecture: Quantum Mechanics & Entanglement",
      text: "Alright class, today we are delving into quantum mechanics. Let's start with Einstein's famous phrase 'spooky action at a distance', which describes quantum entanglement. When two particles are entangled, their spin states are tied together. If you measure one entangled electron to have spin up, the other instantly collapses into spin down, regardless of whether they are separated by one millimeter or ten light years. This is the bedrock of quantum computing. Your assignment due next Wednesday is to solve the tensor calculations on quantum state vectors in Chapter 4."
    },
    {
      title: "Lecture: Biology & CRISPR Gene Editing",
      text: "Today we will analyze CRISPR-Cas9, which revolutionized molecular biology. Cas9 is essentially an enzyme that act as molecular scissors, capable of cutting strands of DNA. But how does it know where to cut? It relies on a guide RNA, or gRNA, which is a pre-designed sequence of RNA that matches the targeted genome section exactly. Once matched, Cas9 snipps the DNA, enabling cellular repair mechanisms to insert or disable genes. The major action item is to read the 2012 landmark paper by Doudna and Charpentier before Friday's lab session."
    },
    {
      title: "Lecture: Economics & Inflation Theory",
      text: "In macroeconomics today, we focus on demand-pull inflation versus cost-push inflation. Demand-pull inflation occurs when aggregate demand for goods and services outstrips aggregate supply—classic 'too much money chasing too few goods'. Cost-push inflation, on the other hand, is driven by an aggregate decrease in supply, usually caused by rising costs of raw materials or wages. Remember, the Consumer Price Index (CPI) tracks this basket of goods over time. Please review the Federal Reserve's recent meeting minutes for next week's discussion."
    }
  ];

  const handleApplySample = (text: string) => {
    setTranscriptText(text);
    setSummaryResult("");
    setNlpResult(null);
  };

  const handleGenerateSummary = async () => {
    if (!transcriptText.trim()) return;
    setLoading(true);
    setSummaryResult("");
    try {
      const data = await summaryService.generateSummary(transcriptText, customPrompt);
      setSummaryResult(data.summary);
    } catch (err: any) {
      setSummaryResult(`Error generating summary: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateNLP = async () => {
    if (!transcriptText.trim()) return;
    setLoading(true);
    setNlpResult(null);
    try {
      const data = await summaryService.analyzeNLP(transcriptText);
      setNlpResult(data);
    } catch (err: any) {
      alert(`Error analyzing NLP data: ${err.message}`);
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
          NEXORA parses transcript text, structures the underlying technical principles into Markdown study sheets, captures vocabulary, maps homework guidelines, and measures student engagement.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left column: Transcript input */}
        <div className="lg:col-span-6 bg-white p-6 lg:p-8 rounded-3xl border border-gray-100 shadow-sm space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display font-bold text-lg text-gray-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-purple-600" /> Lecture Transcript
              </h3>
              <button 
                onClick={() => setTranscriptText("")}
                className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1.5 transition-colors font-mono"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Clear
              </button>
            </div>

            {/* Quick pre-sets */}
            <div className="space-y-2">
              <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-gray-400 block">Apply Academic Samples</span>
              <div className="flex flex-col gap-2">
                {samples.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleApplySample(s.text)}
                    className="w-full text-left p-3 rounded-xl border border-gray-100 hover:border-purple-200 hover:bg-purple-50/20 text-xs font-medium text-gray-700 transition-all flex items-center justify-between group"
                  >
                    <span>{s.title}</span>
                    <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 text-purple-600 transition-all" />
                  </button>
                ))}
              </div>
            </div>

            <textarea
              value={transcriptText}
              onChange={(e) => setTranscriptText(e.target.value)}
              placeholder="Paste a classroom transcript or select a pre-made sample from above to begin summary & NLP processing..."
              className="w-full h-64 p-4 rounded-2xl glass-input text-sm leading-relaxed"
            />

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
                <span className="text-sm font-semibold text-gray-600">Engaging Gemini 3.5 Flash Model...</span>
                <p className="text-xs text-gray-400 max-w-xs">Restructuring knowledge base and formulating semantic takeaways.</p>
              </div>
            )}

            {!loading && activeTab === "summary" && (
              <div className="space-y-4">
                {summaryResult ? (
                  <div className="prose prose-sm prose-purple select-text leading-relaxed text-gray-700 font-sans break-words whitespace-pre-wrap">
                    {summaryResult}
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 py-16 space-y-2">
                    <BookMarked className="w-10 h-10 text-gray-300" />
                    <span className="font-semibold text-sm">No summary generated yet</span>
                    <p className="text-xs text-gray-400 max-w-xs">Pasting a transcript and clicking "Compile Study Guide" will generate an academically detailed, Markdown-formatted notes sheet.</p>
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
