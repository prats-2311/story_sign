import { useEffect } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";

import { PlatformShell } from "./components";
import { ProtectedRoute } from "./components/auth";
import { useAuth } from "./contexts/AuthContext";
import { MainDashboard, ASLWorldPage, HarmonyPage } from "./pages";
import LoginPage from "./pages/LoginPage";
import ReconnectPage from "./pages/ReconnectPage";
import RegisterPage from "./pages/RegisterPage";
import { manageFocusForSPA } from "./utils/accessibility";
import "./App.css";
import "./styles/accessibility.css";
import "./styles/responsive.css";

// Loading component for authentication state
const LoadingScreen = () => (
  <div className="loading-screen" role="status" aria-live="polite">
    <div className="loading-spinner" aria-hidden="true"></div>
    <p>Loading StorySign Platform...</p>
  </div>
);

// AppContent component that handles routing after authentication state is determined
const AppContent = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Root path redirect - authenticated users go to dashboard, unauthenticated to login */}
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      {/* Public Routes - accessible without authentication */}
      <Route
        path="/login"
        element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
        }
      />
      <Route
        path="/register"
        element={
          isAuthenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <RegisterPage />
          )
        }
      />

      {/* Protected Routes - wrapped in ProtectedRoute and PlatformShell */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <PlatformShell>
              <Routes>
                <Route path="/dashboard" element={<MainDashboard />} />
                <Route path="/asl-world" element={<ASLWorldPage />} />
                <Route path="/harmony" element={<HarmonyPage />} />
                <Route path="/reconnect" element={<ReconnectPage />} />
                {/* Catch-all for unknown protected routes */}
                <Route
                  path="*"
                  element={<Navigate to="/dashboard" replace />}
                />
              </Routes>
            </PlatformShell>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

function App() {
  const location = useLocation();
  const { isLoading } = useAuth();

  // Handle route changes for accessibility
  useEffect(() => {
    const getPageTitle = pathname => {
      const titleMap = {
        "/": "StorySign - Dashboard",
        "/dashboard": "StorySign - Dashboard",
        "/login": "StorySign - Sign In",
        "/register": "StorySign - Register",
        "/asl-world": "StorySign - ASL World",
        "/harmony": "StorySign - Harmony",
        "/reconnect": "StorySign - Reconnect",
      };
      return titleMap[pathname] || "StorySign Platform";
    };

    const pageTitle = getPageTitle(location.pathname);
    manageFocusForSPA(pageTitle);
  }, [location.pathname]);

  // Show loading screen while authentication state is being determined
  if (isLoading) {
    return <LoadingScreen />;
  }

  return <AppContent />;
}

export default App;
