import React, { useState } from "react";
import { 
  UserCheck, 
  Sparkles, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  ChevronRight, 
  RotateCcw, 
  Award, 
  Cpu, 
  BookOpen, 
  Briefcase,
  Layers,
  FileText
} from "lucide-react";
import { QuizQuestion } from "../types";
import { motion, AnimatePresence } from "motion/react";
import { quizService } from "../services/quiz";

export default function ModuleQuizAndAssignments() {
  const [activeTab, setActiveTab] = useState<"quiz" | "assignment">("quiz");
  
  // Quiz states
  const [quizTopic, setQuizTopic] = useState("Quantum Mechanics");
  const [difficulty, setDifficulty] = useState("Intermediate");
  const [loading, setLoading] = useState(false);
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([]);
  
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [score, setScore] = useState(0);
  const [quizCompleted, setQuizCompleted] = useState(false);

  // Assignment states
  const [assignmentTopic, setAssignmentTopic] = useState("Gene Editing Methods");
  const [assignmentResult, setAssignmentResult] = useState("");
  const [assignmentLoading, setAssignmentLoading] = useState(false);

  const handleGenerateQuiz = async () => {
    setLoading(true);
    setQuizQuestions([]);
    setCurrentQuestionIndex(0);
    setSelectedAnswers({});
    setScore(0);
    setQuizCompleted(false);

    try {
      const data = await quizService.generateQuiz(quizTopic, difficulty, 5);
      setQuizQuestions(data.quiz || []);
    } catch (err: any) {
      alert(`Failed to generate interactive quiz: ${err.message}. Please ensure the FastAPI backend is running.`);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (questionId: string, option: string) => {
    if (selectedAnswers[questionId]) return; // Answer locked once submitted
    
    const question = quizQuestions.find(q => q.id === questionId);
    const isCorrect = question?.correctAnswer === option;

    setSelectedAnswers(prev => ({ ...prev, [questionId]: option }));
    if (isCorrect) {
      setScore(prev => prev + 1);
    }
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < quizQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      setQuizCompleted(true);
    }
  };

  const handleResetQuiz = () => {
    setQuizQuestions([]);
    setQuizCompleted(false);
    setSelectedAnswers({});
    setScore(0);
    setCurrentQuestionIndex(0);
  };

  const handleGenerateAssignment = async () => {
    setAssignmentLoading(true);
    setAssignmentResult("");
    try {
      const data = await quizService.generateAssignment(assignmentTopic);
      setAssignmentResult(data.reply);
    } catch (err: any) {
      setAssignmentResult(`Failed to generate assignment instructions: ${err.message}`);
    } finally {
      setAssignmentLoading(false);
    }
  };

  const presetTopics = ["Quantum Superposition", "Artificial Neural Dynamics", "CRISPR-Cas9 Editing", "Macroeconomic Theories"];

  return (
    <div className="space-y-8">
      
      {/* Title banner */}
      <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm space-y-2 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-blue-50 rounded-full filter blur-2xl opacity-50"></div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
            <UserCheck className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-blue-600 uppercase">Module 7 &amp; 8</span>
            <h1 className="font-display text-2xl font-bold text-gray-900">Quiz &amp; Assignment Generator</h1>
          </div>
        </div>
        <p className="text-gray-500 text-sm max-w-3xl">
          NEXORA transforms verbal transcripts or textbooks into interactive staged quizzes, homework assignment tasks, and evaluation rubrics, scoring responses and offering deep scientific explanations in real-time.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Control Panel */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Section Selector */}
          <div className="bg-white p-3 rounded-2xl border border-gray-100 shadow-sm flex gap-2">
            <button
              onClick={() => setActiveTab("quiz")}
              className={`flex-1 py-3.5 rounded-xl text-xs font-semibold tracking-tight transition-all flex items-center justify-center gap-2 ${
                activeTab === "quiz"
                  ? "bg-blue-600 text-white shadow-md shadow-blue-100"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              <UserCheck className="w-4 h-4" /> Staged Quiz Generator
            </button>
            <button
              onClick={() => setActiveTab("assignment")}
              className={`flex-1 py-3.5 rounded-xl text-xs font-semibold tracking-tight transition-all flex items-center justify-center gap-2 ${
                activeTab === "assignment"
                  ? "bg-blue-600 text-white shadow-md shadow-blue-100"
                  : "text-gray-500 hover:text-gray-900"
              }`}
            >
              <Briefcase className="w-4 h-4" /> Assignment Builder
            </button>
          </div>

          {/* Form configuration card */}
          <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm space-y-5">
            <h4 className="font-display font-bold text-base text-gray-900">
              {activeTab === "quiz" ? "Quiz Configuration" : "Assignment Settings"}
            </h4>

            {activeTab === "quiz" ? (
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600">Topic or Subject</label>
                  <input
                    type="text"
                    value={quizTopic}
                    onChange={(e) => setQuizTopic(e.target.value)}
                    className="w-full p-3 rounded-xl glass-input text-xs"
                    placeholder="e.g., Photosynthesis, Trigonometry..."
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600">Difficulty Grade</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full p-3 rounded-xl glass-input text-xs font-medium"
                  >
                    <option value="Elementary">Elementary (Under 10)</option>
                    <option value="High School">High School (Grade 9-12)</option>
                    <option value="Intermediate">Intermediate Undergraduate</option>
                    <option value="PhD Research">PhD Academic Research</option>
                  </select>
                </div>

                {/* Preset Chips */}
                <div className="space-y-2">
                  <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-gray-400 block">Preset Topics</span>
                  <div className="flex flex-wrap gap-1.5">
                    {presetTopics.map((t) => (
                      <button
                        key={t}
                        onClick={() => setQuizTopic(t)}
                        className="px-2.5 py-1 rounded-lg border border-gray-100 hover:border-blue-200 text-[10px] text-gray-500 font-medium transition-colors"
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleGenerateQuiz}
                  disabled={loading || !quizTopic.trim()}
                  className="w-full py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:bg-gray-100 disabled:text-gray-400 text-white font-semibold text-xs transition-all shadow-md shadow-blue-100 flex items-center justify-center gap-2"
                >
                  {loading ? "Compiling Quiz..." : "Compile Interactive Test"} <Sparkles className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-600">Subject Core Topic</label>
                  <input
                    type="text"
                    value={assignmentTopic}
                    onChange={(e) => setAssignmentTopic(e.target.value)}
                    className="w-full p-3 rounded-xl glass-input text-xs"
                    placeholder="e.g. CRISPR vs TALEN..."
                  />
                </div>

                <button
                  onClick={handleGenerateAssignment}
                  disabled={assignmentLoading || !assignmentTopic.trim()}
                  className="w-full py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold text-xs transition-all shadow-md shadow-blue-100 flex items-center justify-center gap-2"
                >
                  {assignmentLoading ? "Compiling rubric..." : "Generate Assignment Outline"} <Sparkles className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Active Interactive Screen */}
        <div className="lg:col-span-8 bg-white p-6 lg:p-8 rounded-3xl border border-gray-100 shadow-sm flex flex-col justify-between min-h-[450px]">
          
          {activeTab === "quiz" && (
            <div className="space-y-6 h-full flex flex-col justify-between">
              
              {loading && (
                <div className="h-full flex flex-col items-center justify-center py-20 space-y-3 text-center">
                  <Cpu className="w-8 h-8 text-blue-500 animate-spin" />
                  <span className="text-sm font-semibold text-gray-600">Structuring Staged Questions...</span>
                  <p className="text-xs text-gray-400 max-w-xs">Connecting to Gemini to formulate multiple-choice questions with customized option arrays.</p>
                </div>
              )}

              {!loading && quizQuestions.length > 0 && !quizCompleted && (
                <div className="space-y-6">
                  {/* Progress Header */}
                  <div className="flex items-center justify-between border-b border-gray-50 pb-4">
                    <div>
                      <span className="text-xs font-mono font-bold text-blue-600">Question {currentQuestionIndex + 1} of {quizQuestions.length}</span>
                      <h4 className="text-sm font-bold text-gray-500 mt-0.5">Topic: {quizTopic}</h4>
                    </div>
                    <span className="text-xs font-mono bg-gray-50 border border-gray-100 px-3 py-1 rounded-full font-semibold text-gray-500 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-blue-500 animate-pulse" /> Live Session
                    </span>
                  </div>

                  {/* Active Question Title */}
                  <div className="space-y-4">
                    <h3 className="font-display font-bold text-lg text-gray-900 leading-normal">
                      {quizQuestions[currentQuestionIndex].question}
                    </h3>

                    {/* Options Grid */}
                    <div className="grid grid-cols-1 gap-3 pt-2">
                      {quizQuestions[currentQuestionIndex].options.map((option, idx) => {
                        const questionId = quizQuestions[currentQuestionIndex].id;
                        const selectedOption = selectedAnswers[questionId];
                        const isSelected = selectedOption === option;
                        const isCorrect = quizQuestions[currentQuestionIndex].correctAnswer === option;
                        const hasSubmitted = !!selectedOption;

                        // Calculate visual colors
                        let borderStyle = "border-gray-100 bg-white hover:border-blue-200";
                        let checkIcon = null;

                        if (hasSubmitted) {
                          if (isCorrect) {
                            borderStyle = "border-emerald-300 bg-emerald-50/40 text-emerald-800 font-semibold";
                            checkIcon = <CheckCircle2 className="w-4.5 h-4.5 text-emerald-600" />;
                          } else if (isSelected) {
                            borderStyle = "border-red-300 bg-red-50/40 text-red-800 font-semibold";
                            checkIcon = <XCircle className="w-4.5 h-4.5 text-red-600" />;
                          } else {
                            borderStyle = "border-gray-100 bg-white opacity-60";
                          }
                        } else if (isSelected) {
                          borderStyle = "border-blue-500 bg-blue-50/50";
                        }

                        return (
                          <button
                            key={idx}
                            disabled={hasSubmitted}
                            onClick={() => handleSelectOption(questionId, option)}
                            className={`p-4 rounded-2xl border text-left text-xs font-medium transition-all flex items-center justify-between gap-3 ${borderStyle}`}
                          >
                            <span>{option}</span>
                            {checkIcon}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Interactive Explanation Reveal */}
                  {selectedAnswers[quizQuestions[currentQuestionIndex].id] && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-5 bg-blue-50/30 rounded-2xl border border-blue-100/60 text-xs leading-relaxed space-y-1"
                    >
                      <span className="font-bold text-blue-800 uppercase text-[9px] tracking-wider block">Scientific Rationale</span>
                      <p className="text-gray-600 font-medium font-sans">{quizQuestions[currentQuestionIndex].explanation}</p>
                    </motion.div>
                  )}

                  {/* Actions to continue */}
                  <div className="pt-4 border-t border-gray-50 flex items-center justify-end">
                    {selectedAnswers[quizQuestions[currentQuestionIndex].id] && (
                      <button
                        onClick={handleNextQuestion}
                        className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-2 transition-all shadow-md shadow-blue-100 cursor-pointer"
                      >
                        {currentQuestionIndex === quizQuestions.length - 1 ? "Finish Quiz" : "Next Question"} <ChevronRight className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                </div>
              )}

              {/* Quiz Completed Certification Banner */}
              {!loading && quizCompleted && (
                <div className="h-full py-12 flex flex-col items-center justify-center text-center space-y-6">
                  <div className="w-16 h-16 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-500 shadow-md">
                    <Award className="w-8 h-8" />
                  </div>

                  <div className="space-y-2">
                    <h3 className="font-display font-bold text-2xl text-gray-900">Quiz Completed!</h3>
                    <p className="text-sm text-gray-400">Your student agent assessment score has been updated in the portal.</p>
                  </div>

                  {/* Score details */}
                  <div className="p-6 bg-gray-50 rounded-3xl border border-gray-100 grid grid-cols-2 gap-8 text-center min-w-[260px]">
                    <div>
                      <span className="text-[10px] text-gray-400 font-bold block uppercase">Score</span>
                      <span className="text-3xl font-bold text-gray-800 block mt-1">{score} / {quizQuestions.length}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-gray-400 font-bold block uppercase">Accuracy</span>
                      <span className="text-3xl font-bold text-gray-800 block mt-1">{Math.floor((score / quizQuestions.length) * 100)}%</span>
                    </div>
                  </div>

                  <button
                    onClick={handleResetQuiz}
                    className="px-6 py-3 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-gray-600 text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
                  >
                    <RotateCcw className="w-4 h-4" /> Try Another Quiz
                  </button>
                </div>
              )}

              {!loading && quizQuestions.length === 0 && (
                <div className="py-24 text-center text-gray-400 flex flex-col items-center justify-center space-y-2">
                  <BookOpen className="w-10 h-10 text-gray-300" />
                  <span className="font-semibold text-sm">No Active Assessment</span>
                  <p className="text-xs text-gray-400 max-w-xs">Configure your subject parameters in the left settings block and click Compile Interactive Test to start live evaluations.</p>
                </div>
              )}

            </div>
          )}

          {activeTab === "assignment" && (
            <div className="space-y-6 select-text">
              {assignmentLoading && (
                <div className="py-24 flex flex-col items-center justify-center space-y-3 text-center">
                  <Cpu className="w-8 h-8 text-blue-500 animate-spin" />
                  <span className="text-sm font-semibold text-gray-600">Compiling Evaluation Rubric...</span>
                  <p className="text-xs text-gray-400 max-w-xs">Formatting scientific questions and grading boundaries with Gemini.</p>
                </div>
              )}

              {!assignmentLoading && assignmentResult && (
                <div className="p-6 bg-gray-50/50 rounded-3xl border border-gray-100 space-y-4 max-h-[400px] overflow-y-auto">
                  <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Course Assignment Instructions</span>
                    <span className="text-xs text-blue-600 font-semibold flex items-center gap-1">
                      <FileText className="w-4 h-4" /> Ready for Students
                    </span>
                  </div>
                  <div className="prose prose-sm prose-blue select-text leading-relaxed text-gray-700 whitespace-pre-wrap text-xs font-sans">
                    {assignmentResult}
                  </div>
                </div>
              )}

              {!assignmentLoading && !assignmentResult && (
                <div className="py-24 text-center text-gray-400 flex flex-col items-center justify-center space-y-2">
                  <Briefcase className="w-10 h-10 text-gray-300" />
                  <span className="font-semibold text-sm">No Active Assignment</span>
                  <p className="text-xs text-gray-400 max-w-xs">Use our AI tool on the left to instantly build homework files, lab rubrics, and research topics matching any lesson.</p>
                </div>
              )}
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
