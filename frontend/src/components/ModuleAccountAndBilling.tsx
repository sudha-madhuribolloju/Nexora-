import React, { useState } from "react";
import {
  User,
  Settings,
  Bell,
  CreditCard,
  Key,
  Lock,
  Check,
  Download,
  FileText,
  ShieldCheck,
  Mail,
  RefreshCw,
  Sliders,
  DollarSign
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

export default function ModuleAccountAndBilling() {
  const [activeSubTab, setActiveSubTab] = useState<"profile" | "settings" | "notifications" | "billing">("profile");

  // Profile Form State
  const [name, setName] = useState("Prof. Sudha Madhuri.");
  const [email, setEmail] = useState("srinivasb.mwa@gmail.com");
  const [bio, setBio] = useState("Course Instructor of Theoretical Quantum Physics and molecular genetics. Passionate about teaching with Gemini LLM models.");
  const [isSaved, setIsSaved] = useState(false);

  // Billing states
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [activeTier, setActiveTier] = useState("pro");

  // Settings states
  const [geminiApiKey, setGeminiApiKey] = useState("••••••••••••••••••••");
  const [pinState, setPinState] = useState("4912");

  const saveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const invoiceHistory = [
    { id: "inv-2026-06", date: "June 15, 2026", amount: "$89.00", status: "Paid" },
    { id: "inv-2026-05", date: "May 15, 2026", amount: "$89.00", status: "Paid" },
    { id: "inv-2026-04", date: "April 15, 2026", amount: "$89.00", status: "Paid" }
  ];

  return (
    <div className="space-y-6">

      {/* Sub tabs selectors */}
      <div className="flex border-b border-gray-100 overflow-x-auto no-scrollbar">
        <button
          onClick={() => setActiveSubTab("profile")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 shrink-0 ${activeSubTab === "profile" ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500"
            }`}
        >
          <User className="w-4 h-4" /> User Profile
        </button>
        <button
          onClick={() => setActiveSubTab("settings")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 shrink-0 ${activeSubTab === "settings" ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500"
            }`}
        >
          <Settings className="w-4 h-4" /> Classroom Settings
        </button>
        <button
          onClick={() => setActiveSubTab("notifications")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 shrink-0 ${activeSubTab === "notifications" ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500"
            }`}
        >
          <Bell className="w-4 h-4" /> Notification Preferences
        </button>
        <button
          onClick={() => setActiveSubTab("billing")}
          className={`px-6 py-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 shrink-0 ${activeSubTab === "billing" ? "border-blue-600 text-blue-600 font-bold" : "border-transparent text-gray-500"
            }`}
        >
          <CreditCard className="w-4 h-4" /> Billing &amp; Subscription
        </button>
      </div>

      <AnimatePresence mode="wait">

        {/* --- PROFILE PAGE --- */}
        {activeSubTab === "profile" && (
          <motion.div key="profile" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Identity card */}
            <div className="bento-card bg-white p-6 flex flex-col items-center justify-between text-center min-h-[300px]">
              <div className="space-y-4 w-full">
                <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-purple-500 to-indigo-500 text-white font-bold text-2xl flex items-center justify-center shadow-lg shadow-purple-100 mx-auto">
                  NB
                </div>
                <div>
                  <h3 className="font-display font-semibold text-gray-900 text-lg">{name}</h3>
                  <span className="text-[10px] uppercase font-mono font-bold text-purple-600 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-100 block w-max mx-auto mt-1.5">
                    Course Instructor
                  </span>
                </div>
                <p className="text-gray-400 text-xs font-mono">{email}</p>
              </div>

              <div className="w-full border-t border-gray-50 pt-5 mt-5">
                <button className="w-full py-2.5 rounded-xl border border-gray-100 hover:bg-gray-50 transition-colors text-xs font-semibold text-gray-600">
                  Upload Profile Avatar
                </button>
              </div>
            </div>

            {/* Editing form card */}
            <div className="lg:col-span-2 bento-card bg-white p-6">
              <h4 className="font-display font-semibold text-gray-900 text-sm mb-4">Edit Personal Records</h4>

              <form onSubmit={saveProfile} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="font-semibold text-gray-600">Full Name</label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-gray-600">Primary Contact Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-gray-600">Academic Biography</label>
                  <textarea
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    rows={4}
                    className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600 resize-none"
                  ></textarea>
                </div>

                <div className="flex items-center justify-between border-t border-gray-50 pt-4">
                  <AnimatePresence>
                    {isSaved && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="text-xs text-emerald-600 font-semibold"
                      >
                        Profile update committed successfully!
                      </motion.span>
                    )}
                  </AnimatePresence>

                  <button type="submit" className="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-semibold text-xs hover:bg-blue-700 transition-colors">
                    Commit Changes
                  </button>
                </div>
              </form>
            </div>

          </motion.div>
        )}

        {/* --- SETTINGS PAGE --- */}
        {activeSubTab === "settings" && (
          <motion.div key="settings" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
            <div className="bento-card p-6 bg-white space-y-4">
              <div className="flex items-center gap-2 border-b border-gray-50 pb-3">
                <Key className="w-5 h-5 text-blue-600" />
                <h4 className="font-semibold text-gray-900 text-sm">LLM API Key Credentials</h4>
              </div>

              <div className="space-y-4 text-xs">
                <p className="text-gray-500 leading-relaxed">
                  Provide custom Google Gemini API secrets here. This is mapped inside the server-side proxy route to securely dispatch prompts without browser leaks.
                </p>

                <div className="space-y-1.5 max-w-lg">
                  <label className="font-semibold text-gray-600 block">Gemini Secret API Key</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={geminiApiKey}
                      onChange={(e) => setGeminiApiKey(e.target.value)}
                      className="flex-1 p-3 rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600 font-mono"
                    />
                    <button className="px-4 py-2.5 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors">
                      Update Key
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="bento-card p-6 bg-white space-y-4">
              <div className="flex items-center gap-2 border-b border-gray-50 pb-3">
                <Lock className="w-5 h-5 text-purple-600" />
                <h4 className="font-semibold text-gray-900 text-sm">Administrative PIN Authorization</h4>
              </div>

              <div className="space-y-1.5 max-w-sm text-xs">
                <label className="font-semibold text-gray-600 block">NEXORA Secure Local Pin</label>
                <input
                  type="password"
                  value={pinState}
                  onChange={(e) => setPinState(e.target.value)}
                  className="w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600 font-mono"
                />
              </div>
            </div>
          </motion.div>
        )}

        {/* --- NOTIFICATIONS --- */}
        {activeSubTab === "notifications" && (
          <motion.div key="notifications" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="bento-card p-6 bg-white space-y-5">
            <div className="border-b border-gray-50 pb-3">
              <h4 className="font-semibold text-gray-900 text-sm">Configure Classroom Signals</h4>
            </div>

            <div className="space-y-4 text-xs text-gray-600">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100/50">
                <div>
                  <span className="font-semibold text-gray-900 block">Inattention Spike Detection</span>
                  <span className="text-gray-400 block mt-0.5">Alert if classroom focus averages drop below 80%</span>
                </div>
                <input type="checkbox" defaultChecked className="w-5 h-5 text-blue-600 accent-blue-600" />
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100/50">
                <div>
                  <span className="font-semibold text-gray-900 block">AI Lecture Summary Complete</span>
                  <span className="text-gray-400 block mt-0.5">Receive system notification when Gemini finishes segmenting class notes</span>
                </div>
                <input type="checkbox" defaultChecked className="w-5 h-5 text-blue-600 accent-blue-600" />
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100/50">
                <div>
                  <span className="font-semibold text-gray-900 block">Email Reports Weekly digest</span>
                  <span className="text-gray-400 block mt-0.5">Receive signed transcripts summaries on Friday afternoon</span>
                </div>
                <input type="checkbox" className="w-5 h-5 text-blue-600 accent-blue-600" />
              </div>
            </div>
          </motion.div>
        )}

        {/* --- BILLING & SUBSCRIPTIONS --- */}
        {activeSubTab === "billing" && (
          <motion.div key="billing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">

            {/* Toggle Billing Period */}
            <div className="flex items-center justify-center gap-3">
              <span className={`text-xs font-semibold ${billingCycle === "monthly" ? "text-blue-600 font-bold" : "text-gray-400"}`}>Billed Monthly</span>
              <button
                onClick={() => setBillingCycle(prev => prev === "monthly" ? "yearly" : "monthly")}
                className="w-12 h-6 bg-blue-100 rounded-full p-1 relative transition-all"
              >
                <div className={`w-4 h-4 bg-blue-600 rounded-full transition-transform ${billingCycle === "yearly" ? "translate-x-6" : ""}`}></div>
              </button>
              <span className={`text-xs font-semibold ${billingCycle === "yearly" ? "text-blue-600 font-bold" : "text-gray-400"}`}>Billed Yearly (Save 20%)</span>
            </div>

            {/* Pricing cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

              {/* Free Sandbox */}
              <div className={`bento-card p-6 flex flex-col justify-between min-h-[350px] ${activeTier === "free" ? "border-2 border-blue-600" : "bg-white"}`}>
                <div className="space-y-4">
                  <span className="text-[10px] font-mono uppercase font-bold text-gray-400">Sandbox Trial</span>
                  <h4 className="font-display font-bold text-gray-900 text-lg">Developer Free</h4>
                  <div className="font-display text-2xl font-bold text-gray-900">$0 <span className="text-xs text-gray-400">/ forever</span></div>

                  <ul className="space-y-2 text-xs text-gray-500">
                    <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600" /> 1 Live Classroom Instance</li>
                    <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600" /> Basic AI Notes summaries</li>
                    <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600" /> 5 enrolled students roster</li>
                  </ul>
                </div>

                <button
                  onClick={() => setActiveTier("free")}
                  className="w-full py-2.5 rounded-xl border border-gray-100 hover:bg-gray-50 text-xs font-bold transition-colors mt-6 text-gray-600"
                >
                  {activeTier === "free" ? "Active Selected Tier" : "Select Plan"}
                </button>
              </div>

              {/* Professional Campus */}
              <div className={`bento-card p-6 flex flex-col justify-between min-h-[350px] relative overflow-hidden ${activeTier === "pro" ? "border-2 border-blue-600 bg-blue-50/10" : "bg-white"}`}>
                <div className="absolute top-0 right-0 bg-blue-600 text-white font-semibold text-[9px] uppercase tracking-wider px-3 py-1 rounded-bl-xl">
                  Popular Plan
                </div>

                <div className="space-y-4">
                  <span className="text-[10px] font-mono uppercase font-bold text-blue-600">Unlimited Classes</span>
                  <h4 className="font-display font-bold text-gray-900 text-lg">Professional Campus</h4>
                  <div className="font-display text-2xl font-bold text-gray-900">
                    {billingCycle === "monthly" ? "$89.00" : "$71.20"} <span className="text-xs text-gray-400">/ month</span>
                  </div>

                  <ul className="space-y-2 text-xs text-gray-500">
                    <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600" /> 10 Live Classroom Streams</li>
                    <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600" /> Pro active speech vector summary</li>
                    <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600" /> 100 enrolled students database</li>
                  </ul>
                </div>

                <button
                  onClick={() => setActiveTier("pro")}
                  className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors mt-6"
                >
                  {activeTier === "pro" ? "Active Selected Tier" : "Select Plan"}
                </button>
              </div>

              {/* Enterprise Authority */}
              <div className={`bento-card p-6 flex flex-col justify-between min-h-[350px] ${activeTier === "enterprise" ? "border-2 border-blue-600" : "bg-white"}`}>
                <div className="space-y-4">
                  <span className="text-[10px] font-mono uppercase font-bold text-purple-600">Custom Cloud</span>
                  <h4 className="font-display font-bold text-gray-900 text-lg">Enterprise Institution</h4>
                  <div className="font-display text-2xl font-bold text-gray-900">Contact Sales</div>

                  <ul className="space-y-2 text-xs text-gray-500">
                    <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600" /> Dedicated Google Cloud VM</li>
                    <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600" /> Offline PostgreSQL pgvector Store</li>
                    <li className="flex items-center gap-2"><Check className="w-3.5 h-3.5 text-blue-600" /> Custom private OAuth server</li>
                  </ul>
                </div>

                <button
                  onClick={() => setActiveTier("enterprise")}
                  className="w-full py-2.5 rounded-xl border border-gray-100 hover:bg-gray-50 text-xs font-bold transition-colors mt-6 text-gray-600"
                >
                  {activeTier === "enterprise" ? "Active Selected Tier" : "Select Plan"}
                </button>
              </div>

            </div>

            {/* Invoices */}
            <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm mt-8">
              <div className="p-5 border-b border-gray-50 flex items-center justify-between">
                <span className="font-display font-semibold text-sm text-gray-900">Sandbox Billing Invoices</span>
              </div>

              <div className="divide-y divide-gray-100 text-xs">
                {invoiceHistory.map((inv) => (
                  <div key={inv.id} className="p-4 flex items-center justify-between hover:bg-gray-50/30 transition-colors">
                    <div>
                      <span className="font-semibold text-gray-800">{inv.id}</span>
                      <span className="text-[10px] text-gray-400 block mt-0.5">{inv.date}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="font-mono text-gray-700 font-semibold">{inv.amount}</span>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 text-[10px] font-bold">{inv.status}</span>
                      <button className="p-1 rounded hover:bg-gray-50">
                        <Download className="w-4 h-4 text-gray-400 hover:text-gray-600" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </motion.div>
        )}

      </AnimatePresence>

    </div>
  );
}
