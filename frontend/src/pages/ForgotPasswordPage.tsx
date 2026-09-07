import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Mail,
  ArrowLeft,
  ArrowRight,
  Loader2
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import AuthLayout from "../layouts/AuthLayout";

const forgotPasswordSchema = z.object({
  email: z.string().min(1, "Email is required").email("Please enter a valid email address"),
});

type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const { forgotPassword, triggerToast } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordInput>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordInput) => {
    setIsLoading(true);
    try {
      const success = await forgotPassword(data.email);
      if (success) {
        navigate("/reset-password", { state: { email: data.email } });
      }
    } catch (err) {
      triggerToast("Failed to dispatch recovery email", "error");
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
          <ArrowLeft className="w-4 h-4" /> Back to Sign In
        </button>

        <div className="space-y-1.5">
          <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Forgot Password</h2>
          <p className="text-xs text-gray-500">Provide your verified institutional email to trigger a recovery file.</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-1">

          {/* Email address */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-700">Administrative Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
              <input
                type="email"
                placeholder="you@example.com"
                className={`w-full pl-10 pr-4 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${errors.email ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                  }`}
                {...register("email")}
                disabled={isLoading}
              />
            </div>
            {errors.email && (
              <p className="text-[10px] text-red-500 font-medium pl-1">{errors.email.message}</p>
            )}
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75 cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Dispatching Recovery Credentials...</span>
              </>
            ) : (
              <>
                <span>Dispatch Recovery Link</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-[11px] text-gray-400 font-medium max-w-xs mx-auto leading-normal">
          If the corresponding record exists in our system, you will receive a secured one-time login credentials file.
        </p>
      </div>
    </AuthLayout>
  );
}
