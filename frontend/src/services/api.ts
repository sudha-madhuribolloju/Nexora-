/**
 * NEXORA — FastAPI REST Client Core
 *
 * All frontend services communicate through this module to route requests to
 * the FastAPI backend. Automatic JWT token injection, multipart form support,
 * and standard helper methods (get, post, put, del) are provided.
 */

import { getAccessToken, getRefreshToken, setTokens, clearTokens } from "./session";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

/**
 * Custom error wrapper for HTTP errors returned from FastAPI.
 */
export class ApiError extends Error {
  status: number;
  detail: any;

  constructor(status: number, message: string, detail?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Core fetch wrapper. Automatically attaches the Bearer token,
 * handles Content-Type (if not FormData), parses JSON responses,
 * and includes a single retry on 401 Unauthorized using refresh token.
 */
export async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth = false, headers: extraHeaders = {}, ...rest } = options;

  const headers: Record<string, string> = {
    ...Object.fromEntries(
      Object.entries(extraHeaders).map(([k, v]) => [k, String(v)])
    ),
  };

  // If the body is not FormData, default to application/json
  if (!(rest.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  let response = await fetch(`${BASE_URL}${path}`, {
    ...rest,
    headers,
  });

  // Attempt token refresh on 401 Unauthorized
  if (response.status === 401 && !skipAuth) {
    const refreshed = await attemptTokenRefresh();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${getAccessToken()}`;
      response = await fetch(`${BASE_URL}${path}`, {
        ...rest,
        headers,
      });
    }
  }

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}`;
    let rawDetail: any = null;
    try {
      const body = await response.json();
      rawDetail = body?.detail || body?.message;
      errorDetail = typeof rawDetail === "string" ? rawDetail : JSON.stringify(rawDetail) || errorDetail;
    } catch {
      // Ignore parse errors on error bodies
    }
    throw new ApiError(response.status, errorDetail, rawDetail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Performs a silent token refresh using the stored refresh token.
 * Returns true if successful, false otherwise.
 */
async function attemptTokenRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      if (data.access_token && data.refresh_token) {
        setTokens(data.access_token, data.refresh_token);
        return true;
      }
    }
  } catch (err) {
    console.error("Token refresh failed:", err);
  }

  // Refresh failed, clear tokens
  clearTokens();
  return false;
}

// ── Generic Request Helpers ───────────────────────────────────────────────────

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),

  post: <T>(path: string, body?: any, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: any, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  del: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),

  postForm: <T>(path: string, formData: FormData, options?: RequestOptions) =>
    request<T>(path, {
      ...options,
      method: "POST",
      body: formData,
    }),
};
