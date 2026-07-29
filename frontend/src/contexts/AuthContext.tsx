import React, { createContext, useContext, useState, useEffect, useRef } from "react";
import { UserRole } from "../types";
import { authService } from "../services/auth";
import {
  setTokens,
  clearTokens,
  getAccessToken,
  getRefreshToken,
} from "../services/session";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  phone?: string;
  bio?: string;
  avatarUrl?: string;
}

export interface ToastItem {
  id: string;
  message: string;
  type: "success" | "info" | "error";
}

interface AuthContextType {
  user: UserProfile | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  toasts: ToastItem[];
  triggerToast: (message: string, type?: "success" | "info" | "error") => void;
  dismissToast: (id: string) => void;
  login: (email: string, password: string, role?: UserRole) => Promise<boolean>;
  signup: (fullName: string, email: string, password: string, role?: UserRole) => Promise<{ success: boolean; verification_required: boolean }>;
  verifyCode: (email: string, code: string) => Promise<boolean>;
  resendOTP: (email: string) => Promise<boolean>;
  completeProfile: (fullName: string, role: UserRole, phone: string, bio: string) => Promise<boolean>;
  forgotPassword: (email: string) => Promise<boolean>;
  resetPassword: (password: string) => Promise<boolean>;
  changeRole: (role: UserRole) => void;
  logout: () => void;
}


// ── Helpers ───────────────────────────────────────────────────────────────────

/** Map an API user response to our frontend UserProfile shape. */
function mapApiUser(apiUser: {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  phone?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
}): UserProfile {
  return {
    id: apiUser.id,
    email: apiUser.email,
    fullName: apiUser.full_name || "Academic User",
    role: (apiUser.role || "Student") as UserRole,
    phone: apiUser.phone || "",
    bio: apiUser.bio || "",
    avatarUrl: apiUser.avatar_url || "",
  };
}

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState(true);
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  // ── Restore session from stored JWT on mount ────────────────────────────────
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      try {
        const token = getAccessToken();
        if (token) {
          // Fetch the authenticated user profile with the stored token via GET /auth/me
          const apiUser = await authService.getMe();
          if (apiUser) {
            setUser(mapApiUser(apiUser));
            setIsLoggedIn(true);
          } else {
            clearTokens();
            setUser(null);
            setIsLoggedIn(false);
          }
        } else {
          clearTokens();
          setUser(null);
          setIsLoggedIn(false);
        }
      } catch (err) {
        console.error("Auth initialization failed:", err);
        clearTokens();
        setUser(null);
        setIsLoggedIn(false);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // ── Toast helpers ─────────────────────────────────────────────────────────

  const triggerToast = (
    message: string,
    type: "success" | "info" | "error" = "success"
  ) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      dismissToast(id);
    }, 4000);
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // ── Auth actions ──────────────────────────────────────────────────────────

  /**
   * Log in with email + password via FastAPI.
   * 1. Store tokens
   * 2. Fetch authenticated profile via GET /auth/me
   * 3. Set isLoggedIn = true & update AuthContext
   */
  const login = async (
    email: string,
    password: string,
    role?: UserRole
  ): Promise<boolean> => {
    setIsLoading(true);
    try {
      if (!password) {
        triggerToast("Please enter your password.", "error");
        return false;
      }

      // 1. Send login credentials to backend
      const tokenData = await authService.login(email, password);
      setTokens(tokenData.access_token, tokenData.refresh_token);

      // 2. Fetch authenticated user profile via GET /auth/me
      const apiUser = await authService.getMe();
      const profile = mapApiUser(apiUser);
      if (role && profile.role !== role) {
        profile.role = role;
      }

      setUser(profile);
      setIsLoggedIn(true);

      triggerToast("Successfully logged in as " + (profile.role || "User"), "success");
      return true;
    } catch (err: any) {
      clearTokens();
      setUser(null);
      setIsLoggedIn(false);
      triggerToast(err.message || "Invalid credentials. Please try again.", "error");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Register a new user via FastAPI.
   */
  const signup = async (
    fullName: string,
    email: string,
    password: string,
    role?: UserRole
  ): Promise<{ success: boolean; verification_required: boolean }> => {
    setIsLoading(true);
    try {
      if (!password || password.length < 6) {
        triggerToast("Password must be at least 6 characters.", "error");
        return { success: false, verification_required: false };
      }

      const res = await authService.register(email, password, fullName, role || "Student");

      if (res.verification_required) {
        triggerToast("Account created! Please check your email for the verification code.", "info");
      } else {
        triggerToast("Registration successful! You may now log in.", "success");
      }

      return {
        success: true,
        verification_required: res.verification_required,
      };
    } catch (err: any) {
      triggerToast(err.message || "Error signing up. Please try again.", "error");
      return { success: false, verification_required: false };
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * OTP/email verification code.
   */
  const verifyCode = async (email: string, code: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      await authService.verifyEmail(email, code);
      triggerToast("Email verified successfully! You may now log in.", "success");
      return true;
    } catch (err: any) {
      triggerToast(err.message || "Invalid or expired verification code.", "error");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Resend OTP verification code.
   */
  const resendOTP = async (email: string): Promise<boolean> => {
    try {
      const res = await authService.resendOTP(email);
      triggerToast(res.message || "Fresh security code dispatched.", "info");
      return true;
    } catch (err: any) {
      triggerToast(err.message || "Failed to resend verification code.", "error");
      return false;
    }
  };


  /**
   * Update the user's profile fields in PostgreSQL via PUT /api/v1/users/me.
   */
  const completeProfile = async (
    fullName: string,
    role: UserRole,
    phone: string,
    bio: string
  ): Promise<boolean> => {
    setIsLoading(true);
    try {
      if (!user) throw new Error("No authenticated user session.");

      const updatedApiUser = await authService.updateProfile(user.id, {
        full_name: fullName,
        phone,
        bio,
      });

      if (updatedApiUser) {
        setUser(mapApiUser(updatedApiUser));
      } else {
        setUser({ ...user, fullName, role, phone, bio });
      }

      triggerToast("Profile updated successfully", "success");
      return true;
    } catch (err: any) {
      triggerToast(err.message || "Unable to save profile", "error");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Forgot password.
   */
  const forgotPassword = async (email: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      await authService.forgotPassword(email);
      triggerToast(
        `Password recovery instructions sent to ${email}. Check your inbox.`,
        "success"
      );
      return true;
    } catch (err: any) {
      triggerToast(err.message || "Failed to dispatch recovery email.", "error");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Reset password.
   */
  const resetPassword = async (password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      await authService.resetPassword(password);
      triggerToast("Password reset successful. Please log in with your new password.", "success");
      return true;
    } catch (err: any) {
      triggerToast(err.message || "Error updating password.", "error");
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Switch the active role context locally.
   */
  const changeRole = (role: UserRole) => {
    if (user) {
      setUser({ ...user, role });
      triggerToast("Role context modified to " + role, "success");
    }
  };

  /**
   * Log out — call the backend endpoint and clear local tokens.
   */
  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } catch (err) {
      console.warn("Logout endpoint notice:", err);
    } finally {
      clearTokens();
      setUser(null);
      setIsLoggedIn(false);
      setIsLoading(false);
      triggerToast("Successfully signed out.", "success");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoggedIn,
        isLoading,
        toasts,
        triggerToast,
        dismissToast,
        login,
        signup,
        verifyCode,
        resendOTP,
        completeProfile,

        forgotPassword,
        resetPassword,
        changeRole,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
