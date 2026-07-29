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
  User, 
  ArrowRight, 
  Loader2 
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import AuthLayout from "../layouts/AuthLayout";

const signupSchema = z.object({
  fullName: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().min(1, "Email is required").email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string().min(1, "Please confirm your password"),
  role: z.enum(["Student", "Teacher", "Principal", "Support", "Parent", "Super Admin", "Institute Admin", "Support Engineer"] as any),
  acceptTerms: z.boolean().refine((val) => val === true, {
    message: "You must accept the terms and conditions",
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

type SignupInput = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const navigate = useNavigate();
  const { signup, triggerToast } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupInput>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      role: "Student",
      acceptTerms: false,
    },
  });

  const onSubmit = async (data: SignupInput) => {
    setIsLoading(true);
    try {
      const res = await signup(data.fullName, data.email, data.password, data.role as any);
      if (res.success) {
        if (res.verification_required) {
          navigate("/verify-email", { state: { email: data.email } });
        } else {
          navigate("/login");
        }
      }
    } catch (err) {
      triggerToast("Error signing up. Please try again.", "error");
    } finally {
      setIsLoading(false);
    }
  };


  const handleGoogleSignIn = async () => {
    setGoogleLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setGoogleLoading(false);
    navigate("/");
  };

  return (
    <AuthLayout>
      <div className="space-y-6">
        <div className="space-y-1.5">
          <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Create your account</h2>
          <p className="text-xs text-gray-500">Establish a personalized multi-perspective portal</p>
        </div>

        {/* Continue with Google */}
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
          <span>Sign up with Google</span>
        </button>

        <div className="relative flex py-1 items-center">
          <div className="flex-grow border-t border-gray-100"></div>
          <span className="flex-shrink mx-4 text-gray-400 text-[10px] font-semibold tracking-wider font-mono uppercase">or use credentials</span>
          <div className="flex-grow border-t border-gray-100"></div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
          
          {/* Full Name field */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-700">Full Academic Name</label>
            <div className="relative">
              <User className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Professor John Doe"
                className={`w-full pl-10 pr-4 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${
                  errors.fullName ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                }`}
                {...register("fullName")}
                disabled={isLoading || googleLoading}
              />
            </div>
            {errors.fullName && (
              <p className="text-[10px] text-red-500 font-medium pl-1">{errors.fullName.message}</p>
            )}
          </div>

          {/* Email address */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-700">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
              <input
                type="email"
                placeholder="john.doe@university.edu"
                className={`w-full pl-10 pr-4 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${
                  errors.email ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                }`}
                {...register("email")}
                disabled={isLoading || googleLoading}
              />
            </div>
            {errors.email && (
              <p className="text-[10px] text-red-500 font-medium pl-1">{errors.email.message}</p>
            )}
          </div>

          {/* Password block */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            
            <div className="space-y-1">
              <label className="text-xs font-semibold text-gray-700">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••"
                  className={`w-full pl-9 pr-8 py-2.5 text-xs rounded-xl border bg-white focus:outline-none transition-all ${
                    errors.password ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                  }`}
                  {...register("password")}
                  disabled={isLoading || googleLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 top-3 text-gray-400 hover:text-gray-600 cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-[10px] text-red-500 font-medium pl-1">{errors.password.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-gray-700">Confirm</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="••••••"
                  className={`w-full pl-9 pr-8 py-2.5 text-xs rounded-xl border bg-white focus:outline-none transition-all ${
                    errors.confirmPassword ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                  }`}
                  {...register("confirmPassword")}
                  disabled={isLoading || googleLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-2.5 top-3 text-gray-400 hover:text-gray-600 cursor-pointer"
                >
                  {showConfirmPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="text-[10px] text-red-500 font-medium pl-1">{errors.confirmPassword.message}</p>
              )}
            </div>

          </div>

          {/* Primary Perspective Role selection */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-700">Initial Role Perspective</label>
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

          {/* Accept terms checkbox */}
          <div className="space-y-1 pt-1">
            <label className="flex items-start gap-2.5 cursor-pointer text-xs font-semibold text-gray-500">
              <input 
                type="checkbox" 
                className="w-4 h-4 text-blue-600 accent-blue-600 rounded border-gray-300 mt-0.5"
                {...register("acceptTerms")}
              />
              <span>I agree to Nexora's academic privacy guidelines &amp; cloud storage terms.</span>
            </label>
            {errors.acceptTerms && (
              <p className="text-[10px] text-red-500 font-medium pl-1">{errors.acceptTerms.message}</p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading || googleLoading}
            className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75 mt-2 cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Creating Portal Instance...</span>
              </>
            ) : (
              <>
                <span>Establish Account</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer Switch */}
        <div className="text-center pt-2 border-t border-gray-50 text-xs text-gray-500 font-semibold">
          <span>Already have an account? </span>
          <button
            onClick={() => navigate("/login")}
            className="text-blue-600 hover:underline font-bold cursor-pointer"
          >
            Sign in here
          </button>
        </div>
      </div>
    </AuthLayout>
  );
}
