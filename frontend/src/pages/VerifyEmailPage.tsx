import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { 
  ShieldCheck, 
  ArrowLeft, 
  ArrowRight, 
  Loader2 
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import AuthLayout from "../layouts/AuthLayout";

const verifyEmailSchema = z.object({
  code: z.string().length(6, "Verification code must be exactly 6 digits").regex(/^\d+$/, "Code must contain digits only"),
});

type VerifyEmailInput = z.infer<typeof verifyEmailSchema>;

export default function VerifyEmailPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || "your email inbox";
  const { verifyCode, resendOTP, triggerToast } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<VerifyEmailInput>({
    resolver: zodResolver(verifyEmailSchema),
  });

  const onSubmit = async (data: VerifyEmailInput) => {
    setIsLoading(true);
    try {
      const success = await verifyCode(email, data.code);
      if (success) {
        navigate("/login");
      }
    } catch (err) {
      triggerToast("Error verifying email", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (email && email !== "your email inbox") {
      await resendOTP(email);
    } else {
      triggerToast("Please check your email inbox.", "info");
    }
  };


  return (
    <AuthLayout>
      <div className="space-y-5">
        <button
          type="button"
          onClick={() => navigate("/signup")}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-500 hover:text-gray-800 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Edit Email Address
        </button>

        <div className="space-y-1.5 text-center sm:text-left">
          <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Verify Email Address</h2>
          <p className="text-xs text-gray-500 leading-relaxed">
            We have dispatched a 6-digit validation file to <span className="text-blue-600 font-bold font-mono">{email}</span>. Please insert it below.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-1">
          
          {/* Code input */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-700 block text-center sm:text-left">6-Digit Verification Code</label>
            <div className="relative">
              <input
                type="text"
                placeholder="491204"
                maxLength={6}
                className={`w-full py-4 text-center tracking-[0.5em] font-mono text-lg font-bold rounded-xl border bg-white focus:outline-none focus:ring-2 focus:ring-blue-100 transition-all ${
                  errors.code ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                }`}
                {...register("code")}
                disabled={isLoading}
              />
            </div>
            {errors.code && (
              <p className="text-[10px] text-red-500 font-medium text-center">{errors.code.message}</p>
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
                <span>Confirming Security Token...</span>
              </>
            ) : (
              <>
                <span>Verify &amp; Continue</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="text-center pt-2 border-t border-gray-50 text-xs text-gray-500 font-semibold">
          <span>Didn’t receive the code? </span>
          <button
            onClick={handleResendCode}
            className="text-blue-600 hover:underline font-bold cursor-pointer"
          >
            Resend security code
          </button>
        </div>
      </div>
    </AuthLayout>
  );
}
