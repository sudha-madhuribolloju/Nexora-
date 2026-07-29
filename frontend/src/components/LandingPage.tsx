import React, { useState, useEffect } from "react";
import { 
  Bot, 
  Cpu, 
  Sparkles, 
  Mic, 
  FileText, 
  ShieldCheck, 
  Search, 
  Calendar, 
  LineChart, 
  BookOpen, 
  Users, 
  Layers, 
  HelpCircle, 
  ChevronDown, 
  ArrowRight,
  Zap,
  Volume2,
  CheckCircle2,
  Bookmark
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface LandingPageProps {
  onEnterApp: () => void;
}

export default function LandingPage({ onEnterApp }: LandingPageProps) {
  const [activeTab, setActiveTab] = useState<"features" | "tech" | "compliance">("features");
  const [typedText, setTypedText] = useState("");
  const [faqOpen, setFaqOpen] = useState<number | null>(null);

  const fullText = "Intelligent AI Student Agent & Classroom Assistant.";

  useEffect(() => {
    let index = 0;
    const interval = setInterval(() => {
      setTypedText(fullText.slice(0, index));
      index++;
      if (index > fullText.length) {
        clearInterval(interval);
      }
    }, 50);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { value: "142,890+", label: "Active Student Agents" },
    { value: "12.4M mins", label: "Lectures Transcribed" },
    { value: "98.7%", label: "Voice Recognition Accuracy" },
    { value: "8.9B+", label: "Knowledge Embeddings" },
  ];

  const modules = [
    { id: 1, title: "Intelligent Audio Processing", desc: "Filters noise, normalizes speech, and generates crisp transcripts.", icon: Mic, color: "text-blue-600 bg-blue-50" },
    { id: 2, title: "Teacher Voice Recognition", desc: "Recognizes teachers' voiceprints and matches personalized instruction contexts.", icon: Volume2, color: "text-indigo-600 bg-indigo-50" },
    { id: 3, title: "Real-Time NLP Engine", desc: "Extracts topics, maps key classroom terms, and reads student engagement sentiments.", icon: Cpu, color: "text-purple-600 bg-purple-50" },
    { id: 4, title: "AI Student Interaction", desc: "Answers doubts, raises creative questions, and works as an automated peer.", icon: Bot, color: "text-sky-600 bg-sky-50" },
    { id: 5, title: "Smart Academic Research", desc: "Conducts deep web-grounded research with standard Harvard/IEEE citations.", icon: Search, color: "text-pink-600 bg-pink-50" },
    { id: 6, title: "Lecture Summary Engine", desc: "Condenses lecture sessions into concise key takeaways and custom study guides.", icon: FileText, color: "text-emerald-600 bg-emerald-50" },
  ];

  const faqs = [
    {
      q: "What is NEXORA and how does it assist the classroom?",
      a: "NEXORA is a high-fidelity enterprise AI Student Agent designed to run seamlessly in modern school/college environments. It records, analyzes, transcribes, and extracts knowledge from lectures, serving as an advanced personalized study peer for students and an assistant for teachers."
    },
    {
      q: "Does it work in real-time?",
      a: "Yes. NEXORA uses real-time speech analytics and NLP engines to produce instant summaries, index terminology, map action items, and suggest relevant research topics during a live lecture."
    },
    {
      q: "How does the Citation Engine work in the Research Module?",
      a: "Our AI Research module uses Google Search grounding. When a query is analyzed, Gemini fetches verified research papers, web databases, and articles, generating citations linked to original URLs."
    },
    {
      q: "Can teachers use NEXORA for grading and assignments?",
      a: "Absolutely! Teacher dashboards contain fully automated Quiz, Note, and Assignment Generators. These can instantly build structured academic materials corresponding to the recorded lecture transcript."
    }
  ];

  return (
    <div className="min-h-screen bg-white text-gray-900 select-none selection:bg-blue-100 relative">
      {/* Background soft gradients */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-100 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse-slow"></div>
      <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-100 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse-slow"></div>

      {/* Sticky Premium Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-gray-100 px-6 lg:px-16 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-sky-400 flex items-center justify-center text-white shadow-md shadow-blue-200">
            <Bot className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="font-display font-bold text-xl tracking-tight text-gray-900">NEXORA</span>
            <span className="text-[9px] block text-blue-600 font-mono tracking-wider font-semibold uppercase">AI CLASSROOM STUDENT</span>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-600">
          <a href="#features" className="hover:text-blue-600 transition-colors">Features</a>
          <a href="#why-nexora" className="hover:text-blue-600 transition-colors">Why Nexora</a>
          <a href="#modules" className="hover:text-blue-600 transition-colors">Modules</a>
          <a href="#pricing" className="hover:text-blue-600 transition-colors">Pricing</a>
          <a href="#faq" className="hover:text-blue-600 transition-colors">FAQ</a>
        </nav>

        <div className="flex items-center gap-3">
          <button 
            onClick={onEnterApp}
            className="px-5 py-2.5 rounded-xl bg-gray-900 text-white text-sm font-semibold hover:bg-gray-800 transition-all flex items-center gap-2 shadow-sm"
          >
            Launch Workspace <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-6 lg:px-16 pt-16 pb-24 max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-7 space-y-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-100 text-blue-600 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" /> Enterprise AI Student Agent
          </div>
          
          <h1 className="font-display text-4xl sm:text-6xl font-bold tracking-tight text-gray-900 leading-[1.1]">
            Unlocking Smarter <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-sky-500 to-purple-600">
              Classroom Agency
            </span>
          </h1>

          <p className="text-lg text-gray-600 font-mono leading-relaxed h-12">
            {typedText}
            <span className="animate-pulse font-bold text-blue-600">|</span>
          </p>

          <p className="text-gray-500 leading-relaxed max-w-xl text-base">
            NEXORA is an advanced AI Student Agent that listens, learns, interacts, assists, and summarizes live lectures. It supports real-time transcription, automated academic research, custom quizzes, and beautiful interactive whiteboards.
          </p>

          <div className="flex flex-col sm:flex-row gap-4">
            <button 
              onClick={onEnterApp}
              className="px-8 py-4 rounded-2xl bg-gradient-to-tr from-blue-600 to-blue-500 text-white font-semibold shadow-lg shadow-blue-200 hover:brightness-105 transition-all flex items-center justify-center gap-2 text-base"
            >
              Get Started for Free <ArrowRight className="w-5 h-5" />
            </button>
            <a 
              href="#modules"
              className="px-8 py-4 rounded-2xl border border-gray-200 bg-white text-gray-700 font-semibold hover:bg-gray-50 transition-all flex items-center justify-center gap-2 text-base"
            >
              Explore Modules
            </a>
          </div>

          {/* Stats widgets */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6">
            {stats.map((stat, i) => (
              <div key={i} className="bento-card p-5 rounded-2xl bg-white border border-gray-100 flex flex-col justify-between hover:border-blue-300">
                <span className="text-[10px] uppercase font-mono tracking-wider text-gray-400 font-bold block">{stat.label}</span>
                <span className="font-display text-2xl lg:text-3xl font-bold text-blue-600 mt-2 block">{stat.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Floating AI Robot Graphic */}
        <div className="lg:col-span-5 flex justify-center relative">
          <div className="w-72 h-72 md:w-96 md:h-96 relative flex items-center justify-center animate-float">
            {/* Ambient shadow ring */}
            <div className="absolute -bottom-6 w-48 h-6 bg-blue-100 rounded-full filter blur-xl opacity-60"></div>

            {/* Premium Custom SVG Robot */}
            <svg viewBox="0 0 400 400" className="w-full h-full drop-shadow-2xl">
              <defs>
                <linearGradient id="robotGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#FFFFFF" />
                  <stop offset="100%" stopColor="#EFF6FF" />
                </linearGradient>
                <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#2563EB" />
                  <stop offset="50%" stopColor="#38BDF8" />
                  <stop offset="100%" stopColor="#7C3AED" />
                </linearGradient>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="8" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Background circular glowing rings */}
              <circle cx="200" cy="200" r="160" fill="none" stroke="url(#accentGrad)" strokeWidth="1" strokeDasharray="5 10" opacity="0.3" />
              <circle cx="200" cy="200" r="130" fill="none" stroke="#38BDF8" strokeWidth="1.5" strokeDasharray="120 40" opacity="0.4" className="animate-spin" style={{ transformOrigin: "200px 200px", animationDuration: "12s" }} />

              {/* Robot Body Torso */}
              <rect x="130" y="210" width="140" height="110" rx="30" fill="url(#robotGrad)" stroke="#E2E8F0" strokeWidth="2" />
              <rect x="150" y="230" width="100" height="70" rx="20" fill="#0F172A" />
              {/* Inner screen graphics */}
              <path d="M 160,265 Q 200,285 240,265" fill="none" stroke="#38BDF8" strokeWidth="3" opacity="0.8" />
              <circle cx="170" cy="250" r="3" fill="#10B981" />
              <circle cx="230" cy="250" r="3" fill="#10B981" />
              <circle cx="200" cy="250" r="2" fill="#7C3AED" />

              {/* Robot Neck */}
              <rect x="180" y="185" width="40" height="30" rx="5" fill="#CBD5E1" stroke="#94A3B8" strokeWidth="1" />

              {/* Robot Head */}
              <rect x="110" y="70" width="180" height="120" rx="40" fill="url(#robotGrad)" stroke="#E2E8F0" strokeWidth="3" />
              {/* Visor Area */}
              <rect x="125" y="85" width="150" height="80" rx="30" fill="#030712" />
              {/* Intelligent Glowing Blue Eyes */}
              <ellipse cx="165" cy="125" rx="18" ry="12" fill="#38BDF8" filter="url(#glow)" />
              <ellipse cx="165" cy="125" rx="6" ry="6" fill="#FFFFFF" />

              <ellipse cx="235" cy="125" rx="18" ry="12" fill="#38BDF8" filter="url(#glow)" />
              <ellipse cx="235" cy="125" rx="6" ry="6" fill="#FFFFFF" />

              {/* Subtle visual lines */}
              <line x1="150" y1="150" x2="250" y2="150" stroke="#38BDF8" strokeWidth="2" strokeDasharray="4 4" opacity="0.6" />

              {/* Antennas */}
              <line x1="200" y1="70" x2="200" y2="40" stroke="#94A3B8" strokeWidth="4" />
              <circle cx="200" cy="35" r="10" fill="url(#accentGrad)" filter="url(#glow)" />

              {/* Hands/Arms */}
              <path d="M 130,230 Q 80,250 100,280" fill="none" stroke="#E2E8F0" strokeWidth="8" strokeLinecap="round" />
              <path d="M 270,230 Q 320,250 300,280" fill="none" stroke="#E2E8F0" strokeWidth="8" strokeLinecap="round" />
            </svg>
          </div>
        </div>
      </section>

      {/* Why NEXORA Grid */}
      <section id="why-nexora" className="px-6 lg:px-16 py-24 bg-white border-y border-gray-100">
        <div className="max-w-7xl mx-auto space-y-16">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-gray-900">
              Why Choose NEXORA?
            </h2>
            <p className="text-gray-500">
              Traditional classrooms are limited by memory and passive attention. NEXORA acts as an automated intellectual catalyst, capturing and restructuring core content.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bento-card bento-card-blue space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600">
                <Mic className="w-6 h-6" />
              </div>
              <h3 className="font-display font-semibold text-xl">Intelligent Transcription</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                NEXORA isolates the teacher's voice, cancels white noise, and logs precise transcripts with semantic timestamps in real time.
              </p>
            </div>

            <div className="bento-card bento-card-purple space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-purple-50 flex items-center justify-center text-purple-600">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="font-display font-semibold text-xl">Real-Time NLP Analysis</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                Extracts key definitions, categorizes topics, captures student sentiment, and lists actionable tasks as soon as they are mentioned.
              </p>
            </div>

            <div className="bento-card bento-card-emerald space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="font-display font-semibold text-xl">Active Knowledge Graph</h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                Turns verbal material into real-time interactive quizzes, structured markdown notes, and collaborative whiteboards instantly.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Modules Bento Grid */}
      <section id="modules" className="px-6 lg:px-16 py-24 max-w-7xl mx-auto space-y-16">
        <div className="text-center max-w-2xl mx-auto space-y-4">
          <span className="text-sm font-semibold tracking-wider uppercase text-blue-600 font-mono">22 Key Modules Included</span>
          <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-gray-900">
            Engineered For Academic Mastery
          </h2>
          <p className="text-gray-500">
            A comprehensive curriculum and suite of operational components built for administrators, teachers, parents, and students alike.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules.map((m) => {
            const Icon = m.icon;
            // Let's vary border types slightly based on id to create an asymmetric, custom look
            const borderClass = m.id % 3 === 0 ? "bento-card-blue" : m.id % 3 === 1 ? "bento-card-purple" : "bento-card-emerald";
            return (
              <div 
                key={m.id} 
                className={`bento-card ${borderClass} group flex flex-col justify-between space-y-5`}
              >
                <div>
                  <div className={`w-12 h-12 rounded-2xl ${m.color} flex items-center justify-center transition-transform group-hover:scale-105 duration-300 mb-5`}>
                    <Icon className="w-5.5 h-5.5" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-blue-600">0{m.id}</span>
                      <h3 className="font-display font-semibold text-lg text-gray-900 group-hover:text-blue-600 transition-colors">{m.title}</h3>
                    </div>
                    <p className="text-gray-500 text-sm leading-relaxed">{m.desc}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Course details outline banner */}
        <div className="p-8 lg:p-12 rounded-3xl bg-gradient-to-tr from-gray-950 to-gray-900 text-white relative overflow-hidden shadow-xl">
          <div className="absolute top-0 right-0 w-80 h-80 bg-blue-600/10 rounded-full filter blur-3xl"></div>
          <div className="relative z-10 max-w-4xl space-y-6">
            <span className="text-xs font-semibold tracking-wider uppercase text-blue-400 font-mono">Comprehensive Path To Agency</span>
            <h3 className="font-display text-2xl lg:text-3xl font-bold">NEXORA Course Details &amp; Technology Stack</h3>
            <p className="text-gray-400 text-sm leading-relaxed max-w-3xl">
              NEXORA is built on an enterprise architecture featuring Next.js, React 19, Tailwind CSS, FastAPI, Supabase Realtime/Postgres/Auth, and a secure Gemini-powered semantic indexing pipeline for PDF, Word, PPT, Audio, and Video files.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-6">
              <div className="space-y-1">
                <div className="text-xs text-gray-400 uppercase font-semibold">Frontend</div>
                <div className="text-sm font-semibold text-white">React 19, Tailwind</div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-gray-400 uppercase font-semibold">Backend</div>
                <div className="text-sm font-semibold text-white">Express / Node.js</div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-gray-400 uppercase font-semibold">AI Models</div>
                <div className="text-sm font-semibold text-white">Gemini 3.5 Flash</div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-gray-400 uppercase font-semibold">Security</div>
                <div className="text-sm font-semibold text-white">AES-256 / RLS</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="px-6 lg:px-16 py-24 bg-gray-50 border-t border-gray-100">
        <div className="max-w-7xl mx-auto space-y-16">
          <div className="text-center max-w-2xl mx-auto space-y-4">
            <span className="text-sm font-semibold uppercase tracking-wider text-blue-600 font-mono">Simple Transparent Pricing</span>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-gray-900">
              One Plan. Complete Empowerment.
            </h2>
            <p className="text-gray-500">
              Unlock enterprise-grade AI Student Agent capability for your entire educational institution.
            </p>
          </div>

          <div className="max-w-lg mx-auto bg-white rounded-3xl border border-gray-100 shadow-xl overflow-hidden relative">
            <div className="p-8 lg:p-12 space-y-8">
              <div className="space-y-2">
                <h3 className="font-display text-2xl font-bold text-gray-900">Enterprise AI Campus</h3>
                <p className="text-sm text-gray-500">Complete suite of 22 modules for unlimited users, students, and teachers.</p>
              </div>

              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold tracking-tight text-gray-900">$499</span>
                <span className="text-sm text-gray-500 font-medium">/ month per institute</span>
              </div>

              <button 
                onClick={onEnterApp}
                className="w-full py-4 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-all shadow-md shadow-blue-100 flex items-center justify-center gap-2"
              >
                Launch Live Interactive Sandbox <ArrowRight className="w-5 h-5" />
              </button>

              <div className="space-y-4 pt-6 border-t border-gray-100 text-sm">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <span>All 22 Advanced Classroom Modules</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <span>Real-time Gemini 3.5 Flash Integration</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <span>Multi-role dashboards for all 7 major roles</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  <span>Secure Local Database Encryption &amp; Memory</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="px-6 lg:px-16 py-24 max-w-4xl mx-auto space-y-16">
        <div className="text-center space-y-4">
          <h2 className="font-display text-3xl font-bold text-gray-900">Frequently Asked Questions</h2>
          <p className="text-gray-500">Have questions about the NEXORA classroom system? Let us clarify.</p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, idx) => (
            <div key={idx} className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
              <button 
                onClick={() => setFaqOpen(faqOpen === idx ? null : idx)}
                className="w-full p-6 text-left flex items-center justify-between font-semibold text-gray-800 hover:text-blue-600 transition-colors"
              >
                <span>{faq.q}</span>
                <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform duration-300 ${faqOpen === idx ? "rotate-180 text-blue-600" : ""}`} />
              </button>
              
              <AnimatePresence>
                {faqOpen === idx && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="p-6 pt-0 text-sm text-gray-500 leading-relaxed border-t border-gray-50">
                      {faq.a}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </section>

      {/* Footer Section */}
      <footer className="border-t border-gray-100 px-6 lg:px-16 py-12 bg-white text-gray-500 text-sm">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold">
              <Bot className="w-4.5 h-4.5" />
            </div>
            <span className="font-display font-bold text-gray-900 text-base">NEXORA</span>
          </div>

          <div className="flex items-center gap-6">
            <a href="#features" className="hover:text-blue-600 transition-colors">Privacy Policy</a>
            <a href="#why-nexora" className="hover:text-blue-600 transition-colors">Terms of Service</a>
            <a href="#faq" className="hover:text-blue-600 transition-colors">Contact Support</a>
          </div>

          <div className="font-mono text-xs">
            &copy; {new Date().getFullYear()} NEXORA. Crafted with enterprise integrity.
          </div>
        </div>
      </footer>
    </div>
  );
}
