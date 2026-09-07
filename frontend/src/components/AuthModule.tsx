import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Bot,
  Sparkles,
  Mail,
  Lock,
  Eye,
  EyeOff,
  User,
  ArrowRight,
  Check,
  X,
  ArrowLeft,
  Phone,
  Camera,
  CheckCircle,
  Loader2,
  Cpu,
  BookOpen,
  Laptop,
  CheckSquare,
  Award
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

// --- VALIDATION SCHEMAS USING ZOD ---

const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().optional(),
});

const signupSchema = z.object({
  fullName: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().min(1, "Email is required").email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string().min(1, "Please confirm your password"),
  role: z.enum(["Student", "Teacher", "Principal", "Support", "Parent", "Super Admin"]),
  acceptTerms: z.boolean().refine((val) => val === true, {
    message: "You must accept the terms and conditions",
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

const forgotPasswordSchema = z.object({
  email: z.string().min(1, "Email is required").email("Please enter a valid email address"),
});

const resetPasswordSchema = z.object({
  password: z.string().min(6, "Password must be at least 6 characters"),
  confirmPassword: z.string().min(1, "Please confirm your password"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});

const verifyEmailSchema = z.object({
  code: z.string().length(6, "Verification code must be exactly 6 digits"),
});

const completeProfileSchema = z.object({
  fullName: z.string().min(2, "Name must be at least 2 characters"),
  role: z.enum(["Student", "Teacher", "Principal", "Support", "Parent", "Super Admin"]),
  bio: z.string().max(300, "Biography cannot exceed 300 characters"),
  phone: z.string().min(10, "Please enter a valid phone number (min 10 digits)"),
});

// --- TYPE DEFINITIONS ---

type LoginInput = z.infer<typeof loginSchema>;
type SignupInput = z.infer<typeof signupSchema>;
type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;
type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;
type VerifyEmailInput = z.infer<typeof verifyEmailSchema>;
type CompleteProfileInput = z.infer<typeof completeProfileSchema>;

interface AuthModuleProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  onLoginSuccess: (userData: { email: string; role: string; name: string }) => void;
  triggerToast: (msg: string, type: "success" | "info" | "error") => void;
}

export default function AuthModule({
  currentPath,
  onNavigate,
  onLoginSuccess,
  triggerToast
}: AuthModuleProps) {

  // Local UI States
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [selectedAvatar, setSelectedAvatar] = useState("NB");
  const [tempEmail, setTempEmail] = useState("");

  const avatars = ["NB", "SB", "AV", "BM", "SJ", "TM", "JD"];

  // --- REACT HOOK FORMS INITIALIZATION ---

  const {
    register: loginRegister,
    handleSubmit: handleLoginSubmit,
    formState: { errors: loginErrors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
      rememberMe: false
    }
  });

  const {
    register: signupRegister,
    handleSubmit: handleSignupSubmit,
    formState: { errors: signupErrors },
    setValue: setSignupValue,
    watch: watchSignup
  } = useForm<SignupInput>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      role: "Student",
      acceptTerms: false
    }
  });

  const {
    register: forgotRegister,
    handleSubmit: handleForgotSubmit,
    formState: { errors: forgotErrors },
  } = useForm<ForgotPasswordInput>({
    resolver: zodResolver(forgotPasswordSchema)
  });

  const {
    register: resetRegister,
    handleSubmit: handleResetSubmit,
    formState: { errors: resetErrors },
  } = useForm<ResetPasswordInput>({
    resolver: zodResolver(resetPasswordSchema)
  });

  const {
    register: verifyRegister,
    handleSubmit: handleVerifySubmit,
    formState: { errors: verifyErrors },
  } = useForm<VerifyEmailInput>({
    resolver: zodResolver(verifyEmailSchema)
  });

  const {
    register: profileRegister,
    handleSubmit: handleProfileSubmit,
    formState: { errors: profileErrors },
    setValue: setProfileValue,
    watch: watchProfile
  } = useForm<CompleteProfileInput>({
    resolver: zodResolver(completeProfileSchema),
    defaultValues: {
      fullName: "",
      role: "Student",
      bio: "",
      phone: ""
    }
  });

  // --- SUBMIT HANDLERS (SUPABASE READY / ROBUST SIMULATION) ---

  const onLogin = async (data: LoginInput) => {
    setIsLoading(true);
    // Mimic API lag for rich micro-feedback experience
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);

    // Validate credentials — accept any well-formed email for sandbox simulation
    if (data.email.includes("@")) {
      triggerToast("Welcome back to NEXORA!", "success");
      onLoginSuccess({
        email: data.email,
        role: "Teacher",
        name: "Prof. Sudha Madhuri"
      });
    } else {
      triggerToast("Invalid credentials. Please try again.", "error");
    }
  };

  const onSignup = async (data: SignupInput) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);

    setTempEmail(data.email);
    triggerToast("Registration initiated! Please verify your email.", "success");
    // Ready for Supabase Auth integration: supabase.auth.signUp()
    onNavigate("/verify-email");
  };

  const onForgotPassword = async (data: ForgotPasswordInput) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1200));
    setIsLoading(false);

    triggerToast(`Password recovery link sent to ${data.email}`, "success");
    // Ready for Supabase: supabase.auth.resetPasswordForEmail()
    onNavigate("/reset-password");
  };

  const onResetPassword = async (data: ResetPasswordInput) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);

    triggerToast("Password successfully updated. Verification code sent.", "success");
    // Ready for Supabase: supabase.auth.updateUser()
    onNavigate("/verify-email");
  };

  const onVerifyEmail = async (data: VerifyEmailInput) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1200));
    setIsLoading(false);

    triggerToast("Email address verified successfully!", "success");
    onNavigate("/profile/setup");
  };

  const onCompleteProfile = async (data: CompleteProfileInput) => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);

    triggerToast("Workspace profile fully established!", "success");
    onLoginSuccess({
      email: "user@nexora.ai",
      role: data.role,
      name: data.fullName
    });
  };

  const handleGoogleSignIn = async () => {
    setGoogleLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1800));
    setGoogleLoading(false);

    triggerToast("Successfully connected with Google OAuth!", "success");
    onLoginSuccess({
      email: "google.user@stmary.edu",
      role: "Student",
      name: "Google Student Member"
    });
    // Ready for Supabase: supabase.auth.signInWithOAuth({ provider: 'google' })
  };

  return (
    <div className="min-h-screen flex bg-slate-50 relative overflow-hidden select-none">

      {/* Decorative vector background */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-100/30 rounded-full filter blur-3xl -z-10"></div>
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-indigo-100/20 rounded-full filter blur-3xl -z-10"></div>

      {/* --- LEFT SIDE: HERO PORTAL & ILLUSTRATION --- */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 text-white p-12 flex-col justify-between relative overflow-hidden shadow-2xl">

        {/* Futuristic glowing particle effect */}
        <div className="absolute top-1/4 left-1/3 w-80 h-80 bg-blue-500/20 rounded-full mix-blend-screen filter blur-[100px] animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-indigo-500/15 rounded-full mix-blend-screen filter blur-[120px]"></div>

        {/* Brand Header */}
        <div className="flex items-center gap-3 relative z-10 cursor-pointer" onClick={() => onNavigate("/")}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-500 to-sky-400 flex items-center justify-center text-white shadow-lg shadow-blue-400/20">
            <Bot className="w-5.5 h-5.5" />
          </div>
          <div>
            <span className="font-display font-bold text-lg tracking-tight">NEXORA</span>
            <span className="text-[9px] block text-blue-400 font-mono tracking-wider font-semibold uppercase">AI Student Workspace</span>
          </div>
        </div>

        {/* Middle content: Illustration representation */}
        <div className="my-auto space-y-10 relative z-10 max-w-lg">
          <div className="space-y-4">
            <span className="text-[10px] uppercase font-mono tracking-widest text-blue-400 font-bold bg-blue-950/60 px-3 py-1.5 rounded-full border border-blue-900/40 w-max block">
              System Release v2.4
            </span>
            <h1 className="font-display text-4xl font-extrabold tracking-tight leading-[1.1]">
              The Ultimate Multi-Role <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-300">
                AI Classroom Workspace
              </span>
            </h1>
            <p className="text-slate-300 text-xs leading-relaxed font-sans">
              Enter your credential files to connect with the cloud-hosted Gemini transcription tunnels. Manage active student directories, run complex web-grounded research reports, and host interactive multi-user whiteboard canvases.
            </p>
          </div>

          {/* Interactive UI Mockup Card Representation */}
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-400" />
                <span className="text-xs font-mono font-bold text-slate-200">ACTIVE COGNITIVE AGENT</span>
              </div>
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
                <span className="text-[9px] text-emerald-400 font-bold font-mono">LIVE</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono">
                <span>LECTURE TRANSCRIPTION PATH</span>
                <span>98.7% CONFIDENCE</span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: "91%" }}
                  transition={{ duration: 2, repeat: Infinity, repeatType: "reverse" }}
                  className="h-full bg-gradient-to-r from-blue-500 to-indigo-400"
                ></motion.div>
              </div>
            </div>

            <div className="flex gap-4 pt-1">
              <div className="flex items-center gap-1.5 text-[10px] text-slate-300">
                <CheckSquare className="w-3.5 h-3.5 text-blue-400" />
                <span>Zod Validated</span>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] text-slate-300">
                <Laptop className="w-3.5 h-3.5 text-blue-400" />
                <span>OAuth 2.0 Secure</span>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] text-slate-300">
                <Award className="w-3.5 h-3.5 text-blue-400" />
                <span>React 19 Ready</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="flex items-center justify-between border-t border-white/5 pt-6 text-[10px] text-slate-400 font-mono relative z-10">
          <span>St. Mary’s Digital Hub Portal</span>
          <span>© 2026 NEXORA AI Inc.</span>
        </div>
      </div>

      {/* --- RIGHT SIDE: GLASSMORPHISM CARD FOR AUTHENTICATION FORM --- */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center p-6 sm:p-12 md:p-16 relative">

        {/* Soft light background element */}
        <div className="absolute top-10 left-10 w-40 h-40 bg-indigo-200/40 rounded-full filter blur-2xl -z-10"></div>
        <div className="absolute bottom-10 right-10 w-52 h-52 bg-sky-200/30 rounded-full filter blur-2xl -z-10"></div>

        {/* Responsive Brand Header on Mobile only */}
        <div className="flex lg:hidden items-center gap-2 mb-8" onClick={() => onNavigate("/")}>
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
            <Bot className="w-4 h-4" />
          </div>
          <span className="font-display font-bold text-lg text-gray-900 tracking-tight">NEXORA</span>
        </div>

        {/* Main Content Glass Card Frame */}
        <div className="w-full max-w-md bg-white/80 backdrop-blur-md border border-gray-100 rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-300 space-y-6">

          <AnimatePresence mode="wait">

            {/* ======================================= */}
            {/* 1. LOGIN SCREEN                         */}
            {/* ======================================= */}
            {currentPath === "/login" && (
              <motion.div
                key="login-view"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
                className="space-y-6"
              >
                <div className="space-y-1.5">
                  <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Sign in to Nexora</h2>
                  <p className="text-xs text-gray-500">Access your academic student files &amp; workspace tools</p>
                </div>

                {/* Continue with Google Button */}
                <button
                  type="button"
                  onClick={handleGoogleSignIn}
                  disabled={googleLoading || isLoading}
                  className="w-full py-3 px-4 rounded-xl border border-gray-200 bg-white hover:bg-slate-50 font-semibold text-xs text-gray-700 flex items-center justify-center gap-2.5 transition-all shadow-sm active:scale-[0.99] disabled:opacity-75"
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
                <form onSubmit={handleLoginSubmit(onLogin)} className="space-y-4">

                  {/* Email field */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">Email Address</label>
                    <div className="relative">
                      <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
                      <input
                        type="email"
                        placeholder="you@example.com"
                        className={`w-full pl-10 pr-4 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${loginErrors.email ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                          }`}
                        {...loginRegister("email")}
                        disabled={isLoading || googleLoading}
                      />
                    </div>
                    {loginErrors.email && (
                      <p className="text-[10px] text-red-500 font-medium pl-1">{loginErrors.email.message}</p>
                    )}
                  </div>

                  {/* Password field */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-gray-700">Access Key / Password</label>
                      <button
                        type="button"
                        onClick={() => onNavigate("/forgot-password")}
                        className="text-[11px] text-blue-600 hover:underline font-semibold"
                      >
                        Forgot Password?
                      </button>
                    </div>
                    <div className="relative">
                      <Lock className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
                      <input
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••••••"
                        className={`w-full pl-10 pr-10 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${loginErrors.password ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                          }`}
                        {...loginRegister("password")}
                        disabled={isLoading || googleLoading}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-3.5 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {loginErrors.password && (
                      <p className="text-[10px] text-red-500 font-medium pl-1">{loginErrors.password.message}</p>
                    )}
                  </div>

                  {/* Remember me toggle */}
                  <div className="flex items-center justify-between text-xs font-semibold text-gray-500 pt-1">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        className="w-4 h-4 text-blue-600 accent-blue-600 rounded border-gray-300"
                        {...loginRegister("rememberMe")}
                      />
                      <span>Remember this sandbox session</span>
                    </label>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isLoading || googleLoading}
                    className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75 mt-4"
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
                    onClick={() => onNavigate("/signup")}
                    className="text-blue-600 hover:underline font-bold"
                  >
                    Create standard account
                  </button>
                </div>
              </motion.div>
            )}

            {/* ======================================= */}
            {/* 2. SIGN UP SCREEN                        */}
            {/* ======================================= */}
            {currentPath === "/signup" && (
              <motion.div
                key="signup-view"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
                className="space-y-6"
              >
                <div className="space-y-1.5">
                  <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Create your account</h2>
                  <p className="text-xs text-gray-500">Establish a personalized multi-perspective portal</p>
                </div>

                {/* Continue with Google */}
                <button
                  type="button"
                  onClick={handleGoogleSignIn}
                  disabled={googleLoading || isLoading}
                  className="w-full py-3 px-4 rounded-xl border border-gray-200 bg-white hover:bg-slate-50 font-semibold text-xs text-gray-700 flex items-center justify-center gap-2.5 transition-all shadow-sm active:scale-[0.99] disabled:opacity-75"
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

                <form onSubmit={handleSignupSubmit(onSignup)} className="space-y-3.5">

                  {/* Full Name field */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">Full Academic Name</label>
                    <div className="relative">
                      <User className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Professor John Doe"
                        className={`w-full pl-10 pr-4 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${signupErrors.fullName ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                          }`}
                        {...signupRegister("fullName")}
                        disabled={isLoading || googleLoading}
                      />
                    </div>
                    {signupErrors.fullName && (
                      <p className="text-[10px] text-red-500 font-medium pl-1">{signupErrors.fullName.message}</p>
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
                        className={`w-full pl-10 pr-4 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${signupErrors.email ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                          }`}
                        {...signupRegister("email")}
                        disabled={isLoading || googleLoading}
                      />
                    </div>
                    {signupErrors.email && (
                      <p className="text-[10px] text-red-500 font-medium pl-1">{signupErrors.email.message}</p>
                    )}
                  </div>

                  {/* Password block */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">

                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-gray-700">Password</label>
                      <div className="relative">
                        <Lock className="absolute left-3.5 top-3 w-4 h-4 text-gray-400" />
                        <input
                          type={showPassword ? "text" : "password"}
                          placeholder="••••••"
                          className={`w-full pl-9 pr-8 py-2.5 text-xs rounded-xl border bg-white focus:outline-none transition-all ${signupErrors.password ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                            }`}
                          {...signupRegister("password")}
                          disabled={isLoading || googleLoading}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-2.5 top-3 text-gray-400 hover:text-gray-600"
                        >
                          {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                      {signupErrors.password && (
                        <p className="text-[10px] text-red-500 font-medium pl-1">{signupErrors.password.message}</p>
                      )}
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-gray-700">Confirm</label>
                      <div className="relative">
                        <Lock className="absolute left-3.5 top-3 w-4 h-4 text-gray-400" />
                        <input
                          type={showConfirmPassword ? "text" : "password"}
                          placeholder="••••••"
                          className={`w-full pl-9 pr-8 py-2.5 text-xs rounded-xl border bg-white focus:outline-none transition-all ${signupErrors.confirmPassword ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                            }`}
                          {...signupRegister("confirmPassword")}
                          disabled={isLoading || googleLoading}
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute right-2.5 top-3 text-gray-400 hover:text-gray-600"
                        >
                          {showConfirmPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                      {signupErrors.confirmPassword && (
                        <p className="text-[10px] text-red-500 font-medium pl-1">{signupErrors.confirmPassword.message}</p>
                      )}
                    </div>

                  </div>

                  {/* Primary Perspective Role selection */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">Initial Role Perspective</label>
                    <select
                      className="w-full p-3 text-xs rounded-xl border border-gray-200 bg-white focus:outline-none focus:border-blue-600 font-medium text-gray-700"
                      {...signupRegister("role")}
                      disabled={isLoading || googleLoading}
                    >
                      <option value="Student">Student Perspective</option>
                      <option value="Teacher">Teacher Perspective</option>
                      <option value="Principal">Principal Perspective</option>
                      <option value="Support">Support Engineer Perspective</option>
                      <option value="Parent">Parent Perspective</option>
                      <option value="Super Admin">Super Admin Perspective</option>
                    </select>
                  </div>

                  {/* Accept terms checkbox */}
                  <div className="space-y-1 pt-1">
                    <label className="flex items-start gap-2.5 cursor-pointer text-xs font-semibold text-gray-500">
                      <input
                        type="checkbox"
                        className="w-4 h-4 text-blue-600 accent-blue-600 rounded border-gray-300 mt-0.5"
                        {...signupRegister("acceptTerms")}
                      />
                      <span>I agree to Nexora's academic privacy guidelines &amp; cloud storage terms.</span>
                    </label>
                    {signupErrors.acceptTerms && (
                      <p className="text-[10px] text-red-500 font-medium pl-1">{signupErrors.acceptTerms.message}</p>
                    )}
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isLoading || googleLoading}
                    className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75 mt-2"
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
                    onClick={() => onNavigate("/login")}
                    className="text-blue-600 hover:underline font-bold"
                  >
                    Sign in here
                  </button>
                </div>
              </motion.div>
            )}

            {/* ======================================= */}
            {/* 3. FORGOT PASSWORD                       */}
            {/* ======================================= */}
            {currentPath === "/forgot-password" && (
              <motion.div
                key="forgot-view"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
                className="space-y-5"
              >
                <button
                  type="button"
                  onClick={() => onNavigate("/login")}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-500 hover:text-gray-800 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" /> Back to Sign In
                </button>

                <div className="space-y-1.5">
                  <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Forgot Password</h2>
                  <p className="text-xs text-gray-500">Provide your verified institutional email to trigger a recovery file.</p>
                </div>

                <form onSubmit={handleForgotSubmit(onForgotPassword)} className="space-y-4 pt-1">

                  {/* Email address */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">Administrative Email Address</label>
                    <div className="relative">
                      <Mail className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
                      <input
                        type="email"
                        placeholder="you@example.com"
                        className={`w-full pl-10 pr-4 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${forgotErrors.email ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                          }`}
                        {...forgotRegister("email")}
                        disabled={isLoading}
                      />
                    </div>
                    {forgotErrors.email && (
                      <p className="text-[10px] text-red-500 font-medium pl-1">{forgotErrors.email.message}</p>
                    )}
                  </div>

                  {/* Submit button */}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75"
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
              </motion.div>
            )}

            {/* ======================================= */}
            {/* 4. RESET PASSWORD                        */}
            {/* ======================================= */}
            {currentPath === "/reset-password" && (
              <motion.div
                key="reset-view"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
                className="space-y-5"
              >
                <div className="space-y-1.5">
                  <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Establish Password</h2>
                  <p className="text-xs text-gray-500">Provide robust new access credentials for security</p>
                </div>

                <form onSubmit={handleResetSubmit(onResetPassword)} className="space-y-4">

                  {/* New Password */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">New Secret Key / Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
                      <input
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••••••"
                        className={`w-full pl-10 pr-10 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${resetErrors.password ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                          }`}
                        {...resetRegister("password")}
                        disabled={isLoading}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-3.5 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {resetErrors.password && (
                      <p className="text-[10px] text-red-500 font-medium pl-1">{resetErrors.password.message}</p>
                    )}
                  </div>

                  {/* Confirm Password */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">Confirm New Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3.5 top-3.5 w-4 h-4 text-gray-400" />
                      <input
                        type={showConfirmPassword ? "text" : "password"}
                        placeholder="••••••••••••"
                        className={`w-full pl-10 pr-10 py-3 text-xs rounded-xl border bg-white focus:outline-none transition-all ${resetErrors.confirmPassword ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                          }`}
                        {...resetRegister("confirmPassword")}
                        disabled={isLoading}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3.5 top-3.5 text-gray-400 hover:text-gray-600"
                      >
                        {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {resetErrors.confirmPassword && (
                      <p className="text-[10px] text-red-500 font-medium pl-1">{resetErrors.confirmPassword.message}</p>
                    )}
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75 mt-2"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Updating Security Records...</span>
                      </>
                    ) : (
                      <>
                        <span>Commit New Credentials</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>

                <div className="text-center">
                  <button
                    onClick={() => onNavigate("/login")}
                    className="text-xs text-gray-500 hover:text-gray-800 font-semibold"
                  >
                    Cancel and Sign In
                  </button>
                </div>
              </motion.div>
            )}

            {/* ======================================= */}
            {/* 5. VERIFY EMAIL                          */}
            {/* ======================================= */}
            {currentPath === "/verify-email" && (
              <motion.div
                key="verify-view"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
                className="space-y-5"
              >
                <div className="space-y-1.5">
                  <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Verify Email</h2>
                  <p className="text-xs text-gray-500">
                    Provide the 6-digit verification code dispatched to your institutional records: <span className="font-mono text-blue-600 font-bold">{tempEmail || "your registered email"}</span>
                  </p>
                </div>

                <form onSubmit={handleVerifySubmit(onVerifyEmail)} className="space-y-4">

                  {/* Verification Code input */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">6-Digit Verification Code</label>
                    <input
                      type="text"
                      maxLength={6}
                      placeholder="491204"
                      className={`w-full p-4 text-center tracking-widest font-mono text-base font-bold rounded-xl border bg-white focus:outline-none transition-all ${verifyErrors.code ? "border-red-400 focus:border-red-500" : "border-gray-200 focus:border-blue-600"
                        }`}
                      {...verifyRegister("code")}
                      disabled={isLoading}
                    />
                    {verifyErrors.code && (
                      <p className="text-[10px] text-red-500 font-medium pl-1 text-center">{verifyErrors.code.message}</p>
                    )}
                  </div>

                  {/* Resend Helper */}
                  <div className="flex justify-between items-center text-xs font-semibold">
                    <span className="text-gray-400">Didn't receive code?</span>
                    <button
                      type="button"
                      onClick={() => triggerToast("New 6-digit code has been dispatched.", "info")}
                      className="text-blue-600 hover:underline"
                    >
                      Resend Code
                    </button>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Verifying Security Code...</span>
                      </>
                    ) : (
                      <>
                        <span>Verify Academic Email</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>

                <div className="text-center pt-2">
                  <button
                    onClick={() => onNavigate("/login")}
                    className="text-xs font-bold text-gray-500 hover:text-gray-800"
                  >
                    Return to Sign In
                  </button>
                </div>
              </motion.div>
            )}

            {/* ======================================= */}
            {/* 6. COMPLETE PROFILE SETUP                */}
            {/* ======================================= */}
            {currentPath === "/profile/setup" && (
              <motion.div
                key="profile-setup-view"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.25 }}
                className="space-y-5"
              >
                <div className="space-y-1">
                  <h2 className="font-display text-2xl font-bold tracking-tight text-gray-900">Setup Academic Profile</h2>
                  <p className="text-xs text-gray-500">Provide essential details to calibrate the classroom transcript filters</p>
                </div>

                <form onSubmit={handleProfileSubmit(onCompleteProfile)} className="space-y-3.5">

                  {/* Name */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">Full Academic Name</label>
                    <input
                      type="text"
                      className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600 font-medium"
                      {...profileRegister("fullName")}
                      disabled={isLoading}
                    />
                    {profileErrors.fullName && (
                      <p className="text-[10px] text-red-500 font-medium">{profileErrors.fullName.message}</p>
                    )}
                  </div>

                  {/* Primary Contact phone */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">Contact Number (Phone)</label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="+1 (555) 019-2231"
                        className="w-full pl-9 pr-4 py-2.5 text-xs rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600 font-mono"
                        {...profileRegister("phone")}
                        disabled={isLoading}
                      />
                    </div>
                    {profileErrors.phone && (
                      <p className="text-[10px] text-red-500 font-medium">{profileErrors.phone.message}</p>
                    )}
                  </div>

                  {/* Perspective Role Selector */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">Perspective Role Assignment</label>
                    <select
                      className="w-full p-2.5 text-xs rounded-xl border border-gray-200 bg-white focus:outline-none focus:border-blue-600 font-medium text-gray-700"
                      {...profileRegister("role")}
                      disabled={isLoading}
                    >
                      <option value="Student">Student Perspective</option>
                      <option value="Teacher">Teacher Perspective</option>
                      <option value="Principal">Principal Perspective</option>
                      <option value="Support">Support Engineer</option>
                      <option value="Parent">Parent Perspective</option>
                      <option value="Super Admin">Super Admin Perspective</option>
                    </select>
                  </div>

                  {/* Biography */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">Biography / Academic Focus</label>
                    <textarea
                      rows={2.5}
                      className="w-full p-3 text-xs rounded-xl border border-gray-200 focus:outline-none focus:border-blue-600 resize-none font-medium leading-relaxed"
                      placeholder="e.g. Lead researcher overseeing the experimental biology labs and physics vector indexes."
                      {...profileRegister("bio")}
                      disabled={isLoading}
                    ></textarea>
                    {profileErrors.bio && (
                      <p className="text-[10px] text-red-500 font-medium">{profileErrors.bio.message}</p>
                    )}
                  </div>

                  {/* Avatar Picker */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-700 block">Select Profile Initials Avatar</label>
                    <div className="flex gap-2 flex-wrap pt-0.5">
                      {avatars.map((av) => (
                        <button
                          key={av}
                          type="button"
                          onClick={() => setSelectedAvatar(av)}
                          className={`w-9 h-9 rounded-xl text-[10px] font-bold flex items-center justify-center transition-all border ${selectedAvatar === av
                            ? "bg-blue-600 text-white border-blue-600 shadow-sm shadow-blue-200 scale-105"
                            : "bg-slate-50 text-slate-600 border-gray-200 hover:bg-slate-100"
                            }`}
                        >
                          {av}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Save button */}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-3.5 rounded-xl bg-blue-900 hover:bg-blue-950 text-white font-bold text-xs shadow-md shadow-blue-900/10 flex items-center justify-center gap-2 transition-all active:scale-[0.99] disabled:opacity-75 mt-3"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Calibrating Workspace...</span>
                      </>
                    ) : (
                      <>
                        <span>Finish &amp; Enter Workspace</span>
                        <CheckCircle className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>
              </motion.div>
            )}

          </AnimatePresence>

        </div>
      </div>

    </div>
  );
}
