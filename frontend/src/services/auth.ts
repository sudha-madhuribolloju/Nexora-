import { api } from "./api";
import { UserRole } from "../types";

export interface ApiUser {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  phone: string | null;
  bio: string | null;
  avatar_url: string | null;
  updated_at?: string;
  is_active?: boolean;
  is_verified?: boolean;
}

export interface RegisterResponse {
  verification_required: boolean;
  message: string;
  id?: string;
  email?: string;
  role?: string;
  user?: ApiUser;
}

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authService = {
  /**
   * Log in with email and password.
   */
  login: async (email: string, password: string): Promise<AuthTokenResponse> => {
    return api.post<AuthTokenResponse>("/auth/login", { email, password }, { skipAuth: true });
  },

  /**
   * Register a new user account.
   */
  register: async (
    email: string,
    password: string,
    fullName: string,
    role: UserRole
  ): Promise<RegisterResponse> => {
    return api.post<RegisterResponse>(
      "/auth/register",
      {
        email,
        password,
        full_name: fullName,
        role,
      },
      { skipAuth: true }
    );
  },

  /**
   * Verify email using 6-digit OTP code.
   */
  verifyEmail: async (email: string, code: string): Promise<any> => {
    return api.post<any>("/auth/verify-email", { email, code }, { skipAuth: true });
  },

  /**
   * Resend 6-digit OTP code.
   */
  resendOTP: async (email: string): Promise<any> => {
    return api.post<any>("/auth/resend-otp", { email }, { skipAuth: true });
  },

  /**
   * Log out the current session on the backend.
   */
  logout: async (): Promise<{ status: string; message: string }> => {
    return api.post<{ status: string; message: string }>("/auth/logout", {});
  },

  /**
   * Fetch the currently authenticated user's profile from the backend.
   */
  getMe: async (): Promise<ApiUser> => {
    return api.get<ApiUser>("/auth/me");
  },

  /**
   * Update the authenticated user's profile fields on PostgreSQL.
   */
  updateProfile: async (
    userId: string,
    updates: {
      full_name?: string;
      phone?: string;
      bio?: string;
      avatar_url?: string;
    }
  ): Promise<ApiUser> => {
    return api.put<ApiUser>("/users/me", updates);
  },

  /**
   * Send a password reset email to the user.
   */
  forgotPassword: async (email: string): Promise<any> => {
    return api.post<any>("/auth/forgot-password", { email }, { skipAuth: true });
  },

  /**
   * Update the password of the user.
   */
  resetPassword: async (password: string): Promise<any> => {
    return api.post<any>("/auth/reset-password", { password });
  },

  /**
   * Refresh session tokens.
   */
  refreshToken: async (token: string): Promise<AuthTokenResponse> => {
    return api.post<AuthTokenResponse>(
      "/auth/refresh",
      { refresh_token: token },
      { skipAuth: true }
    );
  },
};
