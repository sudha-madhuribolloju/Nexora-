import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { 
  User, 
  Mail, 
  Smartphone, 
  FileText, 
  Award, 
  Save, 
  Loader2, 
  ShieldCheck 
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/Card";

export default function ProfilePage() {
  const { user, completeProfile, triggerToast } = useAuth();
  const [fullName, setFullName] = useState(user?.fullName || "");
  const [phone, setPhone] = useState(user?.phone || "");
  const [bio, setBio] = useState(user?.bio || "");
  const [isSaving, setIsSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      if (user) {
        await completeProfile(fullName, user.role, phone, bio);
      }
    } catch (err) {
      triggerToast("Error updating profile properties", "error");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Page Title */}
      <div>
        <h1 className="font-display text-2xl font-bold text-gray-900">User Profile</h1>
        <p className="text-xs text-gray-500 mt-1">Manage your active academic credentials and workspace metadata.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left column: Avatar and Info badges */}
        <div className="space-y-6 md:col-span-1">
          <Card className="text-center p-8 space-y-4">
            <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 text-white flex items-center justify-center font-extrabold text-3xl shadow-lg mx-auto relative">
              {fullName.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() || "NB"}
              <div className="absolute bottom-0 right-0 p-1.5 rounded-full bg-emerald-500 text-white border-2 border-white">
                <ShieldCheck className="w-3.5 h-3.5" />
              </div>
            </div>

            <div className="space-y-1">
              <h2 className="font-display font-bold text-base text-gray-900">{fullName}</h2>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-blue-600 bg-blue-50 border border-blue-100 px-2.5 py-1 rounded-full inline-block">
                {user?.role || "Student"}
              </span>
            </div>

            <div className="pt-4 border-t border-gray-50 text-xs text-left text-gray-500 space-y-2 leading-relaxed">
              <p className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-gray-400 shrink-0" />
                <span className="truncate">{user?.email || ""}</span>
              </p>
              <p className="flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-gray-400 shrink-0" />
                <span>{phone || "Not set"}</span>
              </p>
            </div>
          </Card>
        </div>

        {/* Right column: Edit forms */}
        <div className="md:col-span-2">
          <Card className="p-8">
            <CardHeader className="mb-6">
              <CardTitle className="text-base flex items-center gap-2">
                <User className="w-5 h-5 text-blue-600" />
                <span>Personal Profile Settings</span>
              </CardTitle>
            </CardHeader>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                
                {/* Full name */}
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-700">Full Academic Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    className="w-full p-3 text-xs rounded-xl border border-gray-200 bg-white focus:outline-none focus:border-blue-600 font-medium text-gray-800"
                  />
                </div>

                {/* Email address (readonly) */}
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500">Email Address (Primary)</label>
                  <input
                    type="email"
                    value={user?.email || ""}
                    disabled
                    className="w-full p-3 text-xs rounded-xl border border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed font-medium"
                  />
                </div>

                {/* Contact phone */}
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-700">Phone Connection</label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+1 (555) 019-2231"
                    className="w-full p-3 text-xs rounded-xl border border-gray-200 bg-white focus:outline-none focus:border-blue-600 font-medium text-gray-800"
                  />
                </div>

                {/* Sandbox Role (static display) */}
                <div className="space-y-1">
                  <label className="text-xs font-bold text-gray-500">Workspace Role Context</label>
                  <input
                    type="text"
                    value={user?.role || "Student"}
                    disabled
                    className="w-full p-3 text-xs rounded-xl border border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed font-medium font-mono"
                  />
                </div>

              </div>

              {/* Bio/Description */}
              <div className="space-y-1">
                <label className="text-xs font-bold text-gray-700">Academic Bio / Description</label>
                <div className="relative">
                  <textarea
                    rows={4}
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    placeholder="Provide a description of your courses, active transcript research folders, or scholarly projects..."
                    className="w-full p-3 text-xs rounded-xl border border-gray-200 bg-white focus:outline-none focus:border-blue-600 font-medium text-gray-800 leading-relaxed resize-none"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 border-t border-gray-50 flex justify-end gap-3">
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-5 py-3 rounded-xl bg-blue-900 hover:bg-blue-950 text-white text-xs font-bold flex items-center gap-2 transition-colors cursor-pointer disabled:opacity-75"
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Saving Profile...</span>
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4" />
                      <span>Save Changes</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </Card>
        </div>

      </div>
    </div>
  );
}
