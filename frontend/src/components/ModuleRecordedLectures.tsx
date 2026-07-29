import React, { useState, useEffect, useRef } from "react";
import {
  Video,
  Play,
  Download,
  Trash2,
  FileText,
  Sparkles,
  Search,
  Filter,
  Clock,
  HardDrive,
  User as UserIcon,
  BookOpen,
  Calendar,
  X,
  Volume2,
  VolumeX,
  Maximize,
  FastForward,
  RotateCcw,
  CheckCircle,
  BarChart2,
  RefreshCw,
} from "lucide-react";
import { Recording, RecordingAnalytics } from "../types";
import { recordingsService } from "../services/recordings";
import { canControlLecture } from "../utils/rbac";

interface ModuleRecordedLecturesProps {
  userRole?: string | null;
  userId?: string | null;
}

export const ModuleRecordedLectures: React.FC<ModuleRecordedLecturesProps> = ({
  userRole = "Student",
  userId = "",
}) => {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [analytics, setAnalytics] = useState<RecordingAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"list" | "analytics">(
    userRole === "Principal" ? "analytics" : "list"
  );

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [filterDeleted, setFilterDeleted] = useState(false);

  // Modals state
  const [playingRecording, setPlayingRecording] = useState<Recording | null>(null);
  const [aiSummaryRecording, setAiSummaryRecording] = useState<Recording | null>(null);
  const [transcriptRecording, setTranscriptRecording] = useState<Recording | null>(null);
  const [transcriptSearch, setTranscriptSearch] = useState("");
  const [deletingRecording, setDeletingRecording] = useState<Recording | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const isTeacher = userRole === "Teacher" || userRole === "teacher";
  const isPrincipal = userRole === "Principal" || userRole === "principal";
  const isAdmin = ["Super Admin", "Institute Admin", "super_admin", "school_admin"].includes(
    userRole || ""
  );

  useEffect(() => {
    loadData();
  }, [userRole, searchQuery, selectedSubject, selectedStatus, filterDeleted, activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === "analytics" || isPrincipal || isAdmin) {
        try {
          const analyticsData = await recordingsService.fetchAnalytics();
          setAnalytics(analyticsData);
        } catch (e) {
          console.warn("Analytics fetch note:", e);
        }
      }

      let res;
      if (isAdmin) {
        res = await recordingsService.fetchAdminAllRecordings({
          search: searchQuery,
          subject_id: selectedSubject || undefined,
          recording_status: selectedStatus || undefined,
          include_deleted: filterDeleted,
        });
      } else if (isTeacher) {
        res = await recordingsService.fetchMyRecordings({
          search: searchQuery,
          subject_id: selectedSubject || undefined,
          recording_status: selectedStatus || undefined,
        });
      } else {
        res = await recordingsService.fetchAccessibleRecordings({
          search: searchQuery,
          subject_id: selectedSubject || undefined,
        });
      }
      setRecordings(res.data || []);
    } catch (err: any) {
      console.error("Error loading recordings:", err);
      showToast(err.message || "Failed to load recorded lectures.");
    } finally {
      setLoading(false);
    }
  };

  const showToast = (msg: string) => {
    setActionMessage(msg);
    setTimeout(() => setActionMessage(null), 4000);
  };

  const handleDelete = async (rec: Recording) => {
    try {
      await recordingsService.deleteRecording(rec.id);
      showToast(`Recording "${rec.filename}" moved to Recycle Bin.`);
      setDeletingRecording(null);
      loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to delete recording.");
    }
  };

  const handleRestore = async (rec: Recording) => {
    try {
      await recordingsService.restoreRecording(rec.id);
      showToast(`Recording "${rec.filename}" restored.`);
      loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to restore recording.");
    }
  };

  const handleTriggerAI = async (rec: Recording) => {
    showToast("Generating AI transcript and summary using Gemini...");
    try {
      const updated = await recordingsService.processAI(rec.id);
      showToast("AI Summary and Transcript ready!");
      setAiSummaryRecording(updated);
      loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to process AI summary.");
    }
  };

  const formatDuration = (sec: number) => {
    if (!sec || sec <= 0) return "00:00";
    const mins = Math.floor(sec / 60);
    const remainingSecs = Math.floor(sec % 60);
    return `${mins.toString().padStart(2, "0")}:${remainingSecs.toString().padStart(2, "0")}`;
  };

  const formatBytes = (bytes: number) => {
    if (!bytes || bytes === 0) return "0 MB";
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {actionMessage && (
        <div className="fixed top-5 right-5 z-50 flex items-center gap-3 bg-indigo-950 text-indigo-100 border border-indigo-500/30 px-4 py-3 rounded-xl shadow-2xl backdrop-blur-md animate-fade-in">
          <Sparkles className="w-5 h-5 text-indigo-400 animate-spin-slow" />
          <span className="text-sm font-medium">{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="hover:opacity-75">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
              <Video className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100">Recorded Lectures Hub</h1>
              <p className="text-sm text-slate-400">
                Stream, review AI summaries, search transcripts, and manage lecture recordings.
              </p>
            </div>
          </div>
        </div>

        {/* View Mode Tabs */}
        {(isPrincipal || isAdmin) && (
          <div className="flex items-center bg-slate-800/80 p-1.5 rounded-xl border border-slate-700">
            <button
              onClick={() => setActiveTab("list")}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                activeTab === "list"
                  ? "bg-indigo-600 text-white shadow-lg"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Video className="w-4 h-4" /> Recordings List
            </button>
            <button
              onClick={() => setActiveTab("analytics")}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                activeTab === "analytics"
                  ? "bg-indigo-600 text-white shadow-lg"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <BarChart2 className="w-4 h-4" /> Principal Analytics
            </button>
          </div>
        )}
      </div>

      {/* Analytics Overview Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/40 p-5 rounded-2xl border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-sm">
              <span>Total Recordings</span>
              <Video className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {analytics.total_recordings}
            </div>
            <div className="text-xs text-indigo-400 mt-1">Available in portal</div>
          </div>

          <div className="bg-slate-900/40 p-5 rounded-2xl border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-sm">
              <span>Total Lecture Hours</span>
              <Clock className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {analytics.total_duration_hours} hrs
            </div>
            <div className="text-xs text-emerald-400 mt-1">
              {(analytics.total_duration_seconds / 60).toFixed(0)} total minutes
            </div>
          </div>

          <div className="bg-slate-900/40 p-5 rounded-2xl border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-sm">
              <span>Storage Used</span>
              <HardDrive className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-slate-100 mt-2">
              {analytics.total_storage_mb} MB
            </div>
            <div className="text-xs text-amber-400 mt-1">FastAPI Media Storage</div>
          </div>

          <div className="bg-slate-900/40 p-5 rounded-2xl border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-sm">
              <span>Top Contributor</span>
              <UserIcon className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-lg font-bold text-slate-100 mt-2 truncate">
              {analytics.top_teachers[0]?.name || "Active Teachers"}
            </div>
            <div className="text-xs text-cyan-400 mt-1">
              {analytics.top_teachers[0] ? `${analytics.top_teachers[0].count} lectures` : "No activity"}
            </div>
          </div>
        </div>
      )}

      {/* Main Recordings Tab Content */}
      {activeTab === "list" ? (
        <div className="space-y-6">
          {/* Search & Filter Toolbar */}
          <div className="flex flex-col md:flex-row gap-4 bg-slate-900/40 p-4 rounded-2xl border border-slate-800">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search by filename, subject, teacher, keyword, or transcript..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-all"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Statuses</option>
                <option value="ready">Ready</option>
                <option value="processing">Processing</option>
                <option value="deleted">Recycle Bin</option>
              </select>

              {isAdmin && (
                <label className="flex items-center gap-2 text-xs text-slate-400 bg-slate-950 px-3 py-2.5 rounded-xl border border-slate-800 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filterDeleted}
                    onChange={(e) => setFilterDeleted(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-600 focus:ring-0"
                  />
                  Show Deleted
                </label>
              )}

              <button
                onClick={loadData}
                className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition-all"
                title="Refresh List"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* Recordings Grid */}
          {loading ? (
            <div className="py-16 text-center text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-indigo-500 mb-3" />
              <p>Loading recorded lectures catalog...</p>
            </div>
          ) : recordings.length === 0 ? (
            <div className="py-16 text-center bg-slate-900/30 rounded-2xl border border-slate-800/60 p-8">
              <Video className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-slate-300">No Recorded Lectures Found</h3>
              <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
                No lecture recordings match your current role permissions or search query. Teachers will automatically populate this catalog when stopping live class sessions.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recordings.map((rec) => (
                <div
                  key={rec.id}
                  className="group bg-slate-900/50 hover:bg-slate-900/80 rounded-2xl border border-slate-800 hover:border-indigo-500/50 transition-all duration-300 overflow-hidden flex flex-col justify-between shadow-lg"
                >
                  {/* Card Header & Preview */}
                  <div>
                    <div className="relative aspect-video bg-slate-950 flex items-center justify-center border-b border-slate-800/60 overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent z-10" />
                      <Video className="w-12 h-12 text-slate-800 group-hover:scale-110 transition-transform duration-500" />

                      {/* Duration Tag */}
                      <div className="absolute bottom-3 right-3 z-20 bg-slate-900/90 text-slate-200 text-xs px-2.5 py-1 rounded-md font-mono border border-slate-700 flex items-center gap-1.5 backdrop-blur-md">
                        <Clock className="w-3 h-3 text-indigo-400" />
                        {formatDuration(rec.duration)}
                      </div>

                      {/* Status Tag */}
                      <div className="absolute top-3 left-3 z-20">
                        {rec.is_deleted ? (
                          <span className="bg-rose-950/80 text-rose-300 text-[10px] px-2 py-0.5 rounded-full border border-rose-800">
                            Deleted
                          </span>
                        ) : (
                          <span className="bg-emerald-950/80 text-emerald-300 text-[10px] px-2 py-0.5 rounded-full border border-emerald-800">
                            Ready
                          </span>
                        )}
                      </div>

                      {/* Quick Play Hover Button */}
                      <button
                        onClick={() => setPlayingRecording(rec)}
                        className="absolute inset-0 z-30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-slate-950/60 backdrop-blur-xs"
                      >
                        <div className="w-12 h-12 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-xl transform group-hover:scale-105 transition-transform">
                          <Play className="w-6 h-6 ml-1" />
                        </div>
                      </button>
                    </div>

                    {/* Card Meta Content */}
                    <div className="p-5 space-y-3">
                      <h3
                        className="font-semibold text-slate-100 text-base truncate group-hover:text-indigo-400 transition-colors"
                        title={rec.filename}
                      >
                        {rec.filename}
                      </h3>

                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                        {rec.subject_name && (
                          <span className="bg-indigo-950/50 text-indigo-300 px-2.5 py-1 rounded-md border border-indigo-800/50 flex items-center gap-1">
                            <BookOpen className="w-3 h-3" /> {rec.subject_name}
                          </span>
                        )}
                        {rec.teacher_name && (
                          <span className="bg-slate-800 text-slate-300 px-2.5 py-1 rounded-md border border-slate-700 flex items-center gap-1">
                            <UserIcon className="w-3 h-3" /> {rec.teacher_name}
                          </span>
                        )}
                        <span className="text-slate-500">{formatBytes(rec.file_size)}</span>
                      </div>

                      {/* AI Summary snippet */}
                      {rec.summary && (
                        <p className="text-xs text-slate-400 line-clamp-2 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/80">
                          {rec.summary.summary || "AI executive summary available for review."}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Card Actions Footer */}
                  <div className="p-4 bg-slate-950/40 border-t border-slate-800/80 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => setPlayingRecording(rec)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-all shadow-md"
                      >
                        <Play className="w-3.5 h-3.5" /> Play
                      </button>

                      <button
                        onClick={() => recordingsService.downloadRecording(rec.id, rec.filename)}
                        className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-all"
                        title="Download Video"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => {
                          if (!rec.summary) {
                            handleTriggerAI(rec);
                          } else {
                            setAiSummaryRecording(rec);
                          }
                        }}
                        className="p-1.5 bg-indigo-950/60 hover:bg-indigo-900/60 text-indigo-300 rounded-lg border border-indigo-800/50 transition-all"
                        title="View AI Summary"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => setTranscriptRecording(rec)}
                        className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-all"
                        title="View AI Transcript"
                      >
                        <FileText className="w-3.5 h-3.5" />
                      </button>

                      {/* Delete / Restore Actions */}
                      {rec.is_deleted ? (
                        isAdmin && (
                          <button
                            onClick={() => handleRestore(rec)}
                            className="p-1.5 bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 rounded-lg border border-emerald-800/50 transition-all"
                            title="Restore Recording"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                          </button>
                        )
                      ) : (
                        (isTeacher || isAdmin) && (
                          <button
                            onClick={() => setDeletingRecording(rec)}
                            className="p-1.5 bg-rose-950/40 hover:bg-rose-900/60 text-rose-400 rounded-lg border border-rose-900/50 transition-all"
                            title="Delete Recording"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Principal Analytics Tab */
        <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800 space-y-6">
          <h2 className="text-xl font-bold text-slate-100">School Recording Analytics & Metrics</h2>

          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
                <h3 className="text-sm font-semibold text-slate-300 mb-4">Top Teacher Contributors</h3>
                <div className="space-y-3">
                  {analytics.top_teachers.map((t, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <span className="text-slate-300">{t.name}</span>
                      <span className="bg-indigo-950 text-indigo-300 text-xs px-2.5 py-1 rounded-md border border-indigo-800">
                        {t.count} recordings
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-slate-950 p-5 rounded-xl border border-slate-800">
                <h3 className="text-sm font-semibold text-slate-300 mb-4">Recent School Activity</h3>
                <div className="space-y-3">
                  {analytics.latest_recordings.map((r) => (
                    <div key={r.id} className="flex items-center justify-between text-sm">
                      <span className="text-slate-300 truncate max-w-[200px]">{r.filename}</span>
                      <span className="text-xs text-slate-500 font-mono">
                        {formatDuration(r.duration)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Video Player Modal */}
      {playingRecording && (
        <VideoPlayerModal
          recording={playingRecording}
          onClose={() => setPlayingRecording(null)}
        />
      )}

      {/* AI Summary Modal */}
      {aiSummaryRecording && (
        <AISummaryModal
          recording={aiSummaryRecording}
          onClose={() => setAiSummaryRecording(null)}
        />
      )}

      {/* Transcript Modal */}
      {transcriptRecording && (
        <TranscriptModal
          recording={transcriptRecording}
          onClose={() => setTranscriptRecording(null)}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deletingRecording && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl max-w-md w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-rose-400">Confirm Recording Deletion</h3>
            <p className="text-sm text-slate-300">
              Are you sure you want to move <span className="font-semibold text-white">"{deletingRecording.filename}"</span> to the Recycle Bin?
            </p>
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setDeletingRecording(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deletingRecording)}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-sm font-medium rounded-xl shadow-lg"
              >
                Delete Recording
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


// ── Custom HTML5 Video Player Modal ──────────────────────────────────────────

const VideoPlayerModal: React.FC<{ recording: Recording; onClose: () => void }> = ({
  recording,
  onClose,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(recording.duration || 0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [volume, setVolume] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);

  const streamUrl = `/api/v1/recordings/${recording.id}/stream`;

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
  };

  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (videoRef.current.requestFullscreen) {
        videoRef.current.requestFullscreen();
      }
    }
  };

  const formatTime = (sec: number) => {
    if (!sec || isNaN(sec)) return "00:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-xl flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-4 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Video className="w-5 h-5 text-indigo-400" />
            <h3 className="font-semibold text-slate-100 text-sm truncate">{recording.filename}</h3>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-white rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Video Canvas */}
        <div className="relative bg-black aspect-video flex items-center justify-center">
          <video
            ref={videoRef}
            src={streamUrl}
            autoPlay
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={() => {
              if (videoRef.current) setDuration(videoRef.current.duration);
            }}
            className="w-full h-full object-contain"
          />
        </div>

        {/* Player Controls Bar */}
        <div className="p-4 bg-slate-950 space-y-3">
          {/* Seekbar */}
          <input
            type="range"
            min="0"
            max={duration || 100}
            value={currentTime}
            onChange={handleSeek}
            className="w-full accent-indigo-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />

          <div className="flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-3">
              <button
                onClick={togglePlay}
                className="p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg transition-all"
              >
                {isPlaying ? <span className="font-bold">❚❚</span> : <Play className="w-4 h-4 ml-0.5" />}
              </button>

              <span className="font-mono text-slate-200">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>

            {/* Playback Speed Controls */}
            <div className="flex items-center gap-2">
              <span className="text-slate-500">Speed:</span>
              {[0.75, 1.0, 1.25, 1.5, 2.0].map((s) => (
                <button
                  key={s}
                  onClick={() => handleSpeedChange(s)}
                  className={`px-2 py-1 rounded-md text-[11px] font-mono ${
                    playbackSpeed === s
                      ? "bg-indigo-600 text-white"
                      : "bg-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {s}x
                </button>
              ))}

              <button
                onClick={toggleFullscreen}
                className="p-1.5 bg-slate-800 text-slate-300 rounded-lg hover:text-white ml-2"
                title="Fullscreen"
              >
                <Maximize className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


// ── AI Summary Modal Component ────────────────────────────────────────────────

const AISummaryModal: React.FC<{ recording: Recording; onClose: () => void }> = ({
  recording,
  onClose,
}) => {
  const summary = recording.summary || {};

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-6 max-h-[85vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-slate-100 text-lg">Gemini AI Executive Summary</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">
              Lecture Summary
            </h4>
            <p className="text-sm text-slate-300 leading-relaxed bg-slate-950 p-4 rounded-xl border border-slate-800">
              {summary.summary || "Summary synthesized for this lecture session."}
            </p>
          </div>

          {summary.key_topics && summary.key_topics.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">
                Key Topics Covered
              </h4>
              <div className="flex flex-wrap gap-2">
                {summary.key_topics.map((t, idx) => (
                  <span
                    key={idx}
                    className="bg-emerald-950/60 text-emerald-300 text-xs px-3 py-1 rounded-full border border-emerald-800"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {summary.important_questions && summary.important_questions.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">
                Important Exam Questions
              </h4>
              <ul className="space-y-2">
                {summary.important_questions.map((q, idx) => (
                  <li
                    key={idx}
                    className="text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800/80 flex items-start gap-2"
                  >
                    <span className="text-amber-400 font-bold">•</span> {q}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {summary.homework_generated && summary.homework_generated.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">
                Suggested Homework & Practice
              </h4>
              <ul className="space-y-2">
                {summary.homework_generated.map((hw, idx) => (
                  <li
                    key={idx}
                    className="text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800/80 flex items-start gap-2"
                  >
                    <CheckCircle className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" /> {hw}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};


// ── Transcript Modal Component ────────────────────────────────────────────────

const TranscriptModal: React.FC<{ recording: Recording; onClose: () => void }> = ({
  recording,
  onClose,
}) => {
  const [filterText, setFilterText] = useState("");

  const rawTranscript = recording.transcript || "No transcript compiled yet for this recording.";
  const lines = rawTranscript.split("\n");

  const filteredLines = lines.filter((l) =>
    l.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full p-6 space-y-4 max-h-[85vh] flex flex-col shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <FileText className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-slate-100 text-lg">Full AI Lecture Transcript</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search transcript text..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex-1 bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-y-auto font-mono text-xs text-slate-300 space-y-2 leading-relaxed">
          {filteredLines.length > 0 ? (
            filteredLines.map((line, idx) => (
              <div key={idx} className="hover:bg-slate-900/60 p-1.5 rounded transition-colors">
                {line}
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-slate-500">No matching transcript lines found.</div>
          )}
        </div>
      </div>
    </div>
  );
};
