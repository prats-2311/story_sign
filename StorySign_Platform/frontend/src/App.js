import { useEffect, lazy, Suspense, useState, useCallback } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { ErrorBoundary } from "react-error-boundary";

import { PlatformShell } from "./components";
import { ProtectedRoute } from "./components/auth";
import { useAuth } from "./contexts/AuthContext";
import { manageFocusForSPA } from "./utils/accessibility";
import {
  performanceMonitor,
  usePerformanceMonitoring,
  useRouteTransitionPerformance,
} from "./utils/performance";
import { useMemoryManagement } from "./hooks/useMemoryManagement";
import OptimizedLoadingScreen, {
  RouteTransitionLoader,
  ComponentSkeleton,
} from "./components/loading/OptimizedLoadingScreen";
import {
  createLazyRoute,
  useRoutePreloader,
} from "./components/routing/LazyRouteWrapper";
import PerformanceMonitor from "./components/debug/PerformanceMonitor";
import "./App.css";
import "./styles/accessibility.css";
import "./styles/responsive.css";

// Lazy load page components for better performance
const MainDashboard = lazy(() =>
  import("./pages/dashboard/MainDashboard").then(module => {
    console.log("MainDashboard loaded");
    return module;
  })
);

const ASLWorldPage = lazy(() =>
  import("./pages/ASLWorldPage").then(module => {
    console.log("ASLWorldPage loaded");
    return module;
  })
);

const HarmonyPage = lazy(() =>
  import("./pages/HarmonyPage").then(module => {
    console.log("HarmonyPage loaded");
    return module;
  })
);

const ReconnectPage = lazy(() =>
  import("./pages/ReconnectPage").then(module => {
    console.log("ReconnectPage loaded");
    return module;
  })
);

const LoginPage = lazy(() =>
  import("./pages/LoginPage").then(module => {
    console.log("LoginPage loaded");
    return module;
  })
);

const RegisterPage = lazy(() =>
  import("./pages/RegisterPage").then(module => {
    console.log("RegisterPage loaded");
    return module;
  })
);

// Error fallback component for the entire app
const AppErrorFallback = ({ error, resetErrorBoundary }) => (
  <div className="app-error-fallback" role="alert">
    <div className="error-content">
      <h1>Something went wrong</h1>
      <p>The application encountered an unexpected error.</p>
      <details>
        <summary>Error details</summary>
        <pre>{error.message}</pre>
      </details>
      <button onClick={resetErrorBoundary}>Try again</button>
      <button onClick={() => window.location.reload()}>Reload page</button>
    </div>
  </div>
);

// Routes to preload for better performance
const PRELOAD_ROUTES = [
  {
    importFunction: () => import("./pages/dashboard/MainDashboard"),
    routeName: "Dashboard",
  },
  {
    importFunction: () => import("./pages/ASLWorldPage"),
    routeName: "ASL World",
  },
];

// AppContent component that handles routing after authentication state is determined
const AppContent = () => {
  const { isAuthenticated } = useAuth();
  const { startTransition, endTransition, isTransitioning } =
    useRouteTransitionPerformance();
  const location = useLocation();
  const [previousRoute, setPreviousRoute] = useState(location.pathname);

  // Track route transitions for performance monitoring
  useEffect(() => {
    if (location.pathname !== previousRoute) {
      startTransition(previousRoute, location.pathname);

      // End transition after a short delay to allow for component mounting
      const transitionTimer = setTimeout(() => {
        endTransition();
      }, 100);

      setPreviousRoute(location.pathname);

      return () => clearTimeout(transitionTimer);
    }
  }, [location.pathname, previousRoute, startTransition, endTransition]);

  return (
    <>
      <RouteTransitionLoader
        isTransitioning={isTransitioning}
        fromRoute={previousRoute}
        toRoute={location.pathname}
      />

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
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Suspense fallback={<ComponentSkeleton type="default" />}>
                <LoginPage />
              </Suspense>
            )
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Suspense fallback={<ComponentSkeleton type="default" />}>
                <RegisterPage />
              </Suspense>
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
                  <Route
                    path="/dashboard"
                    element={
                      <Suspense
                        fallback={<ComponentSkeleton type="dashboard" />}
                      >
                        <MainDashboard />
                      </Suspense>
                    }
                  />
                  <Route
                    path="/asl-world"
                    element={
                      <Suspense
                        fallback={<ComponentSkeleton type="asl-world" />}
                      >
                        <ASLWorldPage />
                      </Suspense>
                    }
                  />
                  <Route
                    path="/harmony"
                    element={
                      <Suspense fallback={<ComponentSkeleton type="default" />}>
                        <HarmonyPage />
                      </Suspense>
                    }
                  />
                  <Route
                    path="/reconnect"
                    element={
                      <Suspense fallback={<ComponentSkeleton type="default" />}>
                        <ReconnectPage />
                      </Suspense>
                    }
                  />
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
    </>
  );
};

function App() {
  const location = useLocation();
  const { isLoading } = useAuth();
  const { memoryUsage, checkMemoryLeak } = usePerformanceMonitoring();
  const { registerInterval, registerCleanup } = useMemoryManagement("App");
  const [showPerformanceMonitor, setShowPerformanceMonitor] = useState(false);

  // Preload routes for better performance
  const { preloadStatus, isPreloading } = useRoutePreloader(
    PRELOAD_ROUTES,
    3000
  );

  // Handle route changes for accessibility and performance
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

    // Track route change performance
    performanceMonitor.startTiming(`route_${location.pathname}`);

    return () => {
      performanceMonitor.endTiming(`route_${location.pathname}`);
    };
  }, [location.pathname]);

  // Memory leak detection
  useEffect(() => {
    const memoryCheckInterval = registerInterval(() => {
      const leakCheck = checkMemoryLeak();
      if (leakCheck?.isLeak) {
        console.warn("Potential memory leak detected:", leakCheck);
      }
    }, 30000); // Check every 30 seconds

    return () => clearInterval(memoryCheckInterval);
  }, [registerInterval, checkMemoryLeak]);

  // Performance monitoring
  useEffect(() => {
    // Set initial memory baseline
    performanceMonitor.setMemoryBaseline();

    // Log performance metrics periodically
    const metricsInterval = registerInterval(() => {
      const report = performanceMonitor.generateReport();
      if (report.routeTransitions?.slowTransitions > 0) {
        console.warn("Performance issue detected:", report);
      }
    }, 60000); // Check every minute

    return () => clearInterval(metricsInterval);
  }, [registerInterval]);

  // Show optimized loading screen while authentication state is being determined
  if (isLoading) {
    return (
      <OptimizedLoadingScreen
        message="Initializing StorySign Platform..."
        showProgress={false}
        timeout={15000}
        onTimeout={() => {
          console.warn("Authentication initialization timeout");
        }}
      />
    );
  }

  return (
    <ErrorBoundary
      FallbackComponent={AppErrorFallback}
      onError={(error, errorInfo) => {
        console.error("App-level error:", error, errorInfo);
        performanceMonitor.recordRouteTransition("error", "app-level", 0);
      }}
    >
      <AppContent />

      {/* Performance Monitor for development */}
      {process.env.NODE_ENV === "development" && (
        <PerformanceMonitor
          isVisible={showPerformanceMonitor}
          onToggle={() => setShowPerformanceMonitor(!showPerformanceMonitor)}
        />
      )}
    </ErrorBoundary>
  );
}

export default App;
