import React from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import LandingPage from "../components/LandingPage";
import LoginPage from "../pages/LoginPage";
import SignupPage from "../pages/SignupPage";
import ForgotPasswordPage from "../pages/ForgotPasswordPage";
import ResetPasswordPage from "../pages/ResetPasswordPage";
import VerifyEmailPage from "../pages/VerifyEmailPage";
import ProfilePage from "../pages/ProfilePage";
import SettingsPage from "../pages/SettingsPage";
import NotificationsPage from "../pages/NotificationsPage";
import OverviewPage from "../pages/OverviewPage";
import NotFoundPage from "../pages/NotFoundPage";

// Submodules
import ModuleAudioVoice from "../components/ModuleAudioVoice";
import ModuleNLPAndSummary from "../components/ModuleNLPAndSummary";
import ModuleAIChat from "../components/ModuleAIChat";
import ModuleAIResearch from "../components/ModuleAIResearch";
import ModuleQuizAndAssignments from "../components/ModuleQuizAndAssignments";
import ModuleNotesAndWhiteboard from "../components/ModuleNotesAndWhiteboard";
import ModuleLiveClassroom from "../components/ModuleLiveClassroom";
import ModuleAcademicProgress from "../components/ModuleAcademicProgress";
import ModuleCampusDirectory from "../components/ModuleCampusDirectory";
import ModuleAccountAndBilling from "../components/ModuleAccountAndBilling";
import ModuleAnalyticsPerformance from "../components/ModuleAnalyticsPerformance";
import RecordedLecturesPage from "../pages/RecordedLecturesPage";

import DashboardLayout from "../layouts/DashboardLayout";

import ProtectedRoutes from "./ProtectedRoutes";

export default function AppRoutes() {
  const { isLoggedIn } = useAuth();
  const navigate = useNavigate();

  return (
    <Routes>
      {/* Root Route: Render Overview if logged in, otherwise LandingPage */}
      <Route 
        path="/" 
        element={
          isLoggedIn ? (
            <ProtectedRoutes>
              <DashboardLayout>
                <OverviewPage />
              </DashboardLayout>
            </ProtectedRoutes>
          ) : (
            <LandingPage onEnterApp={() => navigate("/login")} />
          )
        } 
      />

      {/* Auth Dedicated Pages */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />

      {/* Profile setup route */}
      <Route 
        path="/profile/setup" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ProfilePage />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />

      {/* Protected Dashboard Module Routes */}
      <Route 
        path="/live-classroom" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleLiveClassroom />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/recorded-lectures" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <RecordedLecturesPage />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />

      <Route 
        path="/audio-voice" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleAudioVoice />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/nlp-summary" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleNLPAndSummary />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/nlp-summary/:sessionId" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleNLPAndSummary />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />

      <Route 
        path="/ai-chat" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleAIChat />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/research" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleAIResearch />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/quizzes" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleQuizAndAssignments />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/whiteboard" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleNotesAndWhiteboard />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/progress" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleAcademicProgress />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/directory" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleCampusDirectory />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/analytics" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleAnalyticsPerformance />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/account-billing" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ModuleAccountAndBilling />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/profile" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <ProfilePage />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/settings" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <SettingsPage />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />
      <Route 
        path="/notifications" 
        element={
          <ProtectedRoutes>
            <DashboardLayout>
              <NotificationsPage />
            </DashboardLayout>
          </ProtectedRoutes>
        } 
      />

      {/* Fallback 404 page */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
