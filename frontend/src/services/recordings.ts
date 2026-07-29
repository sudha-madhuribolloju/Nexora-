import { Recording, RecordingAnalytics } from "../types";

const API_BASE = "/api/v1";

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("token") || localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export interface FetchRecordingsParams {
  skip?: number;
  limit?: number;
  search?: string;
  subject_id?: string;
  class_id?: string;
  recording_status?: string;
  include_deleted?: boolean;
}

export interface RecordingListResponse {
  total: number;
  skip: number;
  limit: number;
  data: Recording[];
}

export const recordingsService = {
  async fetchMyRecordings(params: FetchRecordingsParams = {}): Promise<RecordingListResponse> {
    const query = new URLSearchParams();
    if (params.skip !== undefined) query.set("skip", params.skip.toString());
    if (params.limit !== undefined) query.set("limit", params.limit.toString());
    if (params.search) query.set("search", params.search);
    if (params.subject_id) query.set("subject_id", params.subject_id);
    if (params.class_id) query.set("class_id", params.class_id);
    if (params.recording_status) query.set("recording_status", params.recording_status);

    const res = await fetch(`${API_BASE}/recordings/my?${query.toString()}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch teacher recordings");
    return res.json();
  },

  async fetchAccessibleRecordings(params: FetchRecordingsParams = {}): Promise<RecordingListResponse> {
    const query = new URLSearchParams();
    if (params.skip !== undefined) query.set("skip", params.skip.toString());
    if (params.limit !== undefined) query.set("limit", params.limit.toString());
    if (params.search) query.set("search", params.search);
    if (params.subject_id) query.set("subject_id", params.subject_id);

    const res = await fetch(`${API_BASE}/recordings?${query.toString()}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch accessible recordings");
    return res.json();
  },

  async fetchAdminAllRecordings(params: FetchRecordingsParams = {}): Promise<RecordingListResponse> {
    const query = new URLSearchParams();
    if (params.skip !== undefined) query.set("skip", params.skip.toString());
    if (params.limit !== undefined) query.set("limit", params.limit.toString());
    if (params.search) query.set("search", params.search);
    if (params.subject_id) query.set("subject_id", params.subject_id);
    if (params.class_id) query.set("class_id", params.class_id);
    if (params.recording_status) query.set("recording_status", params.recording_status);
    if (params.include_deleted) query.set("include_deleted", "true");

    const res = await fetch(`${API_BASE}/recordings/admin/all?${query.toString()}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch admin recordings");
    return res.json();
  },

  async fetchRecordingById(id: string): Promise<Recording> {
    const res = await fetch(`${API_BASE}/recordings/${id}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch recording details");
    return res.json();
  },

  async getRecordingStreamUrl(id: string): Promise<string> {
    return `${API_BASE}/recordings/${id}/stream`;
  },

  async downloadRecording(id: string, filename: string): Promise<void> {
    const res = await fetch(`${API_BASE}/recordings/${id}/download`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to download recording file");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  async deleteRecording(id: string): Promise<Recording> {
    const res = await fetch(`${API_BASE}/recordings/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to delete recording");
    return res.json();
  },

  async restoreRecording(id: string): Promise<Recording> {
    const res = await fetch(`${API_BASE}/recordings/admin/${id}/restore`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to restore recording");
    return res.json();
  },

  async processAI(id: string): Promise<Recording> {
    const res = await fetch(`${API_BASE}/recordings/${id}/ai-process`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to process AI summary");
    return res.json();
  },

  async fetchAnalytics(): Promise<RecordingAnalytics> {
    const res = await fetch(`${API_BASE}/recordings/analytics`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch recording analytics");
    return res.json();
  },
};
