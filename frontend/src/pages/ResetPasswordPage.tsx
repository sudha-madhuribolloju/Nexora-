import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { 
  Lock, 
  Eye, 
  EyeOff, 
  ArrowLeft, 
  ArrowRight, 
  Loader2 
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import AuthLayout from "../layouts/AuthLayout";

const resetPasswordSchema = z.object({
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string().min(1, "Please confirm your password"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || "user@example.com";
  const { resetPassword, triggerToast } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordInput>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = async (data: ResetPasswordInput) => {
    setIsLoading(true);
    try {
      const success = await resetPassword(data.password);
      if (success) {
        navigate("/login");
      }
    } catch (err) {
      triggerToast("Error updating password", "error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout>
      <div className="space-y-5">
        <button
          type="button"
          onClick={() => navigate("/login")}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-500 hover:text-gray-800 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Cancel
        </button>

        <div className="space-y-1.5">
          <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Reset Password</h2>
          <p className="text-xs text-gray-500">
            Establish your new access credentials for <span className="text-blue-600 font-bold font-mono">{email}</span>.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-1">
          
          {/* Password field */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-700">New Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
              <input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••••••"
                className={`w-full pl-10 pr-10 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${
                  errors.password ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                }`}
                {...register("password")}
                disabled={isLoading}
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

          {/* Confirm password field */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-700">Confirm New Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
              <input
                type={showConfirmPassword ? "text" : "password"}
                placeholder="••••••••••••"
                className={`w-full pl-10 pr-10 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${
                  errors.confirmPassword ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                }`}
                {...register("confirmPassword")}
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3.5 top-3.5 text-gray-400 hover:text-gray-600 cursor-pointer"
              >
                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="text-[10px] text-red-500 font-medium pl-1">{errors.confirmPassword.message}</p>
            )}
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75 mt-2 cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Saving New Access Key...</span>
              </>
            ) : (
              <>
                <span>Update Credentials</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </AuthLayout>
  );
}
