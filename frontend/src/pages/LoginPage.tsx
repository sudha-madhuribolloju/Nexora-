import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  Loader2
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import AuthLayout from "../layouts/AuthLayout";
import { UserRole } from "../types";

const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  role: z.enum(["Student", "Teacher", "Principal", "Support", "Parent", "Super Admin", "Institute Admin", "Support Engineer"] as any),
  rememberMe: z.boolean().optional(),
});

type LoginInput = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, triggerToast } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "srinivasb.mwa@gmail.com",
      password: "password123",
      role: "Teacher",
      rememberMe: true,
    },
  });

  const onSubmit = async (data: LoginInput) => {
    console.log("onSubmit called", data);

    setIsLoading(true);

    try {
      const success = await login(
        data.email,
        data.password,
        data.role as UserRole
      );

      if (success) {
        navigate("/");
      }
    } catch (err) {
      console.error(err);
      triggerToast("Invalid credentials. Please try again.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setGoogleLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setGoogleLoading(false);
    await login("google.user@stmary.edu", "Student", "Google Student Member");
    navigate("/");
  };

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="space-y-1.5">
          <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Sign in to Nexora</h2>
          <p className="text-xs text-gray-500">Access your academic student files &amp; workspace tools</p>
        </div>

        {/* Continue with Google Button */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={googleLoading || isLoading}
          className="w-full py-3 px-4 rounded-xl border border-gray-200 bg-white hover:bg-slate-50 font-semibold text-xs text-gray-700 flex items-center justify-center gap-2.5 transition-all shadow-sm active:scale-[0.99] disabled:opacity-75 cursor-pointer"
        >
          {googleLoading ? (
            <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
          ) : (
            <svg className="w-4.5 h-4.5 text-red-500" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12.24 10.285V13.4h6.887C18.2 15.614 15.645 18 12.24 18c-3.86 0-7-3.14-7-7s3.14-7 7-7c1.7 0 3.25.61 4.46 1.64l2.42-2.42C17.3 1.62 14.93 1 12.24 1c-5.52 0-10 4.48-10 10s4.48 10 10 10c5.77 0 9.6-4.06 9.6-9.77 0-.66-.06-1.31-.17-1.95H12.24z" />
            </svg>
          )}
          <span>Continue with Google</span>
        </button>

        {/* Divider */}
        <div className="relative flex py-1 items-center">
          <div className="flex-grow border-t border-gray-100"></div>
          <span className="flex-shrink mx-4 text-gray-400 text-[10px] font-semibold tracking-wider font-mono uppercase">or use credentials</span>
          <div className="flex-grow border-t border-gray-100"></div>
        </div>

        {/* Credentials Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">

          {/* Email field */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-700">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
              <input
                type="email"
                placeholder="srinivasb.mwa@gmail.com"
                className={`w-full pl-10 pr-4 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${errors.email ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                  }`}
                {...register("email")}
                disabled={isLoading || googleLoading}
              />
            </div>
            {errors.email && (
              <p className="text-[10px] text-red-500 font-medium pl-1">{errors.email.message}</p>
            )}
          </div>

          {/* Password field */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-gray-700">Access Key / Password</label>
              <button
                type="button"
                onClick={() => navigate("/forgot-password")}
                className="text-[11px] text-blue-600 hover:underline font-semibold cursor-pointer"
              >
                Forgot Password?
              </button>
            </div>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
              <input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••••••"
                className={`w-full pl-10 pr-10 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${errors.password ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                  }`}
                {...register("password")}
                disabled={isLoading || googleLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-3.5 text-gray-400 hover:text-gray-600 cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.password && (
              <p className="text-[10px] text-red-500 font-medium pl-1">{errors.password.message}</p>
            )}
          </div>

          {/* Role selection */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-700">Sandbox Perspective Role</label>
            <select
              className="w-full p-3 text-xs rounded-xl border border-gray-200 bg-white focus:outline-none focus:border-blue-600 font-medium text-gray-700"
              {...register("role")}
              disabled={isLoading || googleLoading}
            >
              <option value="Student">Student Perspective</option>
              <option value="Teacher">Teacher Perspective</option>
              <option value="Principal">Principal Perspective</option>
              <option value="Parent">Parent Perspective</option>
              <option value="Super Admin">Super Admin Perspective</option>
              <option value="Institute Admin">Institute Admin Perspective</option>
              <option value="Support Engineer">Support Engineer Perspective</option>
            </select>
          </div>

          {/* Remember me toggle */}
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 pt-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="w-4 h-4 text-blue-600 accent-blue-600 rounded border-gray-300"
                {...register("rememberMe")}
              />
              <span>Remember this sandbox session</span>
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading || googleLoading}
            className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75 mt-4 cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Validating Credentials...</span>
              </>
            ) : (
              <>
                <span>Authenticate Account</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer Switch */}
        <div className="text-center pt-2 border-t border-gray-50 text-xs text-gray-500 font-semibold">
          <span>New to Nexora? </span>
          <button
            onClick={() => navigate("/signup")}
            className="text-blue-600 hover:underline font-bold cursor-pointer"
          >
            Create standard account
          </button>
        </div>
      </div>
    </AuthLayout>
  );
}
