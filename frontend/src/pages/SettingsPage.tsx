import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { 
  Settings, 
  Eye, 
  EyeOff, 
  Shield, 
  Cpu, 
  Database, 
  CheckCircle, 
  Save, 
  HelpCircle,
  Bell,
  Sliders,
  Sparkles
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/Card";

export default function SettingsPage() {
  const { user, triggerToast } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [apiKey, setApiKey] = useState("••••••••••••••••••••••••••••••••");
  const [showApiKey, setShowApiKey] = useState(false);
  const [modelType, setModelType] = useState("gemini-3.5-flash");
  const [nlpConfidence, setNlpConfidence] = useState(90);

  const handleSaveSettings = () => {
    triggerToast("Workspace settings preserved successfully", "success");
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Title */}
      <div>
        <h1 className="font-display text-2xl font-bold text-gray-900">System Settings</h1>
        <p className="text-xs text-gray-500 mt-1">Configure active classroom modules, model settings, and integration keys.</p>
      </div>

      <div className="space-y-6">
        {/* Core System Properties */}
        <Card className="p-8">
          <CardHeader className="mb-6">
            <CardTitle className="text-base flex items-center gap-2">
              <Sliders className="w-5 h-5 text-blue-600" />
              <span>Workspace Preferences</span>
            </CardTitle>
          </CardHeader>

          <div className="space-y-6">
            {/* Visual theme */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-50 pb-4">
              <div>
                <span className="text-xs font-bold text-gray-800 block">Workspace Display Mode</span>
                <span className="text-[11px] text-gray-400 mt-0.5 block leading-normal">Switch between a clean, paper-white theme and cosmic slate dark layouts.</span>
              </div>
              <button
                onClick={toggleTheme}
                className="px-4 py-2 text-xs font-bold rounded-xl bg-gray-50 border border-gray-200 hover:border-gray-300 text-gray-700 transition-colors cursor-pointer self-start sm:self-auto"
              >
                Current Theme: {theme.toUpperCase()}
              </button>
            </div>

            {/* Transcription volume */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-50 pb-4">
              <div>
                <span className="text-xs font-bold text-gray-800 block">AI NLP Processing Confidence Threshold</span>
                <span className="text-[11px] text-gray-400 mt-0.5 block leading-normal">Filter speech inputs failing to meet confidence parameters.</span>
              </div>
              <div className="flex items-center gap-3 self-start sm:self-auto">
                <input
                  type="range"
                  min="50"
                  max="99"
                  value={nlpConfidence}
                  onChange={(e) => setNlpConfidence(Number(e.target.value))}
                  className="w-32 accent-blue-600 cursor-pointer h-1.5 bg-gray-100 rounded-lg"
                />
                <span className="text-xs font-bold text-gray-700 font-mono w-8 text-right">{nlpConfidence}%</span>
              </div>
            </div>

            {/* Model preference Selection */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-1">
              <div>
                <span className="text-xs font-bold text-gray-800 block">Primary Intelligence Model Selection</span>
                <span className="text-[11px] text-gray-400 mt-0.5 block leading-normal">Route transcription summarizers through specialized models.</span>
              </div>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                className="p-2 text-xs rounded-xl border border-gray-200 bg-white font-medium text-gray-700 focus:outline-none focus:border-blue-600"
              >
                <option value="gemini-3.5-flash">Gemini 3.5 Flash (Recommended)</option>
                <option value="gemini-3.5-pro">Gemini 3.5 Pro (Deep Research)</option>
                <option value="custom-rag">PostgreSQL pgvector RAG Layer</option>
              </select>
            </div>
          </div>
        </Card>

        {/* FastAPI Backend Configurations Card */}
        <Card className="p-8">
          <CardHeader className="mb-6">
            <CardTitle className="text-base flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-600" />
              <span>Backend API Configurations (FastAPI)</span>
            </CardTitle>
          </CardHeader>

          <div className="space-y-5">
            {/* FastAPI status banner */}
            <div className="space-y-4 p-4 rounded-2xl bg-emerald-50/40 border border-emerald-100/50">
              <div className="flex items-center gap-1.5 text-emerald-700">
                <Sparkles className="w-4.5 h-4.5 animate-pulse" />
                <span className="text-[11px] uppercase font-mono font-extrabold tracking-wider">FastAPI Backend Active</span>
              </div>
              <p className="text-[11px] text-gray-500 leading-relaxed">
                NEXORA frontend is connected to the FastAPI REST backend at <span className="font-mono text-indigo-600">localhost:8000/api/v1</span>. Authentication tokens are managed locally via JWT. Supabase is used exclusively server-side for auth delegation.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* API Key placeholder */}
              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700">Gemini Key Token</label>
                <div className="relative">
                  <input
                    type={showApiKey ? "text" : "password"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full p-2.5 pl-3 pr-10 text-xs font-mono rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600 bg-white"
                  />
                  <button
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-3 text-gray-400 hover:text-gray-600 cursor-pointer"
                  >
                    {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Server connection endpoint */}
              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700">Active API Base Endpoint</label>
                <input
                  type="text"
                  disabled
                  value="http://localhost:8000/api/v1"
                  className="w-full p-2.5 text-xs font-mono rounded-xl border border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Global Save Button */}
        <div className="flex justify-end pt-2">
          <button
            onClick={handleSaveSettings}
            className="px-6 py-3 rounded-xl bg-blue-900 hover:bg-blue-950 text-white text-xs font-bold flex items-center gap-2 transition-colors cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>Preserve All Configurations</span>
          </button>
        </div>
      </div>
    </div>
  );
}
