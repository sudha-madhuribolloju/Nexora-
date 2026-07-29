import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { UserRole } from "../types";

interface ProtectedRoutesProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
}

export default function ProtectedRoutes({ children, allowedRoles }: ProtectedRoutesProps) {
  const { user, isLoggedIn, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md animate-pulse">
          <span className="font-mono font-bold text-xs">NX</span>
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    // Save path to return back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role-based authentication check
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // If user's role is not authorized, redirect to root or overview page
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
