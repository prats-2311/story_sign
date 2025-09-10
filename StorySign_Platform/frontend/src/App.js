import React, { useEffect, lazy, Suspense, useState, useCallback } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";

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
import {
  EnhancedErrorFallback,
  NetworkErrorBoundary,
  AuthenticationErrorBoundary,
  ComponentLoadingErrorBoundary,
  RouteErrorBoundary,
} from "./components/error/ErrorBoundaries";
import { useErrorRecovery } from "./services/ErrorRecoveryService";
import { useAuthErrorHandler } from "./utils/authErrorHandler";
import "./App.css";
import "./styles/accessibility.css";
import "./styles/responsive.css";
import "./components/error/ErrorBoundaries.css";

// Custom ErrorBoundary component to replace react-error-boundary
class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.FallbackComponent;
      return (
        <FallbackComponent
          error={this.state.error}
          resetErrorBoundary={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
}

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

// Enhanced error fallback component for the entire app
const AppErrorFallback = ({ error, resetErrorBoundary }) => (
  <EnhancedErrorFallback
    error={error}
    resetErrorBoundary={resetErrorBoundary}
    errorType="general"
    componentName="StorySign Application"
    customActions={[
      {
        label: "Contact Support",
        type: "secondary",
        onClick: () => window.open("mailto:support@storysign.com", "_blank"),
      },
    ]}
  />
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
  const { recoverFromError, isOnline } = useErrorRecovery();

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

  // Network status indicator
  const NetworkStatusIndicator = () => {
    if (!isOnline) {
      return (
        <div className="network-status-offline" role="alert">
          <span>⚠️ No internet connection. Some features may not work.</span>
        </div>
      );
    }
    return null;
  };

  return (
    <>
      <NetworkStatusIndicator />

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
              <AuthenticationErrorBoundary>
                <ComponentLoadingErrorBoundary componentName="Login Page">
                  <Suspense fallback={<ComponentSkeleton type="default" />}>
                    <LoginPage />
                  </Suspense>
                </ComponentLoadingErrorBoundary>
              </AuthenticationErrorBoundary>
            )
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <AuthenticationErrorBoundary>
                <ComponentLoadingErrorBoundary componentName="Register Page">
                  <Suspense fallback={<ComponentSkeleton type="default" />}>
                    <RegisterPage />
                  </Suspense>
                </ComponentLoadingErrorBoundary>
              </AuthenticationErrorBoundary>
            )
          }
        />

        {/* Protected Routes - wrapped in ProtectedRoute and PlatformShell */}
        <Route
          path="/*"
          element={
            <NetworkErrorBoundary componentName="Protected Routes">
              <ProtectedRoute>
                <PlatformShell>
                  <Routes>
                    <Route
                      path="/dashboard"
                      element={
                        <RouteErrorBoundary
                          routeName="Dashboard"
                          fallbackRoute="/dashboard"
                        >
                          <ComponentLoadingErrorBoundary componentName="Dashboard">
                            <Suspense
                              fallback={<ComponentSkeleton type="dashboard" />}
                            >
                              <MainDashboard />
                            </Suspense>
                          </ComponentLoadingErrorBoundary>
                        </RouteErrorBoundary>
                      }
                    />
                    <Route
                      path="/asl-world"
                      element={
                        <RouteErrorBoundary
                          routeName="ASL World"
                          fallbackRoute="/dashboard"
                        >
                          <ComponentLoadingErrorBoundary componentName="ASL World">
                            <Suspense
                              fallback={<ComponentSkeleton type="asl-world" />}
                            >
                              <ASLWorldPage />
                            </Suspense>
                          </ComponentLoadingErrorBoundary>
                        </RouteErrorBoundary>
                      }
                    />
                    <Route
                      path="/harmony"
                      element={
                        <RouteErrorBoundary
                          routeName="Harmony"
                          fallbackRoute="/dashboard"
                        >
                          <ComponentLoadingErrorBoundary componentName="Harmony">
                            <Suspense
                              fallback={<ComponentSkeleton type="default" />}
                            >
                              <HarmonyPage />
                            </Suspense>
                          </ComponentLoadingErrorBoundary>
                        </RouteErrorBoundary>
                      }
                    />
                    <Route
                      path="/reconnect"
                      element={
                        <RouteErrorBoundary
                          routeName="Reconnect"
                          fallbackRoute="/dashboard"
                        >
                          <ComponentLoadingErrorBoundary componentName="Reconnect">
                            <Suspense
                              fallback={<ComponentSkeleton type="default" />}
                            >
                              <ReconnectPage />
                            </Suspense>
                          </ComponentLoadingErrorBoundary>
                        </RouteErrorBoundary>
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
            </NetworkErrorBoundary>
          }
        />
      </Routes>
    </>
  );
};

function App() {
  const location = useLocation();
  const { isLoading, error: authError } = useAuth();
  const { memoryUsage, checkMemoryLeak } = usePerformanceMonitoring();
  const { registerInterval, registerCleanup } = useMemoryManagement("App");
  const [showPerformanceMonitor, setShowPerformanceMonitor] = useState(false);
  const { recoverFromError, getRecoveryStats } = useErrorRecovery();
  const authContext = useAuth();
  const authErrorHandler = useAuthErrorHandler(authContext);

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

  // Handle authentication errors during initialization
  useEffect(() => {
    if (authError) {
      console.error("Authentication initialization error:", authError);
      // Attempt recovery for auth errors
      recoverFromError(
        authError,
        async () => {
          // Retry auth initialization
          window.location.reload();
        },
        {
          operationId: "auth_init",
          returnUrl: location.pathname,
        }
      ).catch(recoveryError => {
        console.error("Failed to recover from auth error:", recoveryError);
      });
    }
  }, [authError, recoverFromError, location.pathname]);

  // Show optimized loading screen while authentication state is being determined
  if (isLoading) {
    return (
      <NetworkErrorBoundary componentName="Authentication Initialization">
        <OptimizedLoadingScreen
          message="Initializing StorySign Platform..."
          showProgress={false}
          timeout={15000}
          onTimeout={() => {
            console.warn("Authentication initialization timeout");
            // Attempt to recover from timeout
            recoverFromError(
              new Error("Authentication initialization timeout"),
              () => window.location.reload(),
              { operationId: "auth_timeout" }
            );
          }}
        />
      </NetworkErrorBoundary>
    );
  }

  return (
    <AppErrorBoundary
      FallbackComponent={AppErrorFallback}
      onError={(error, errorInfo) => {
        console.error("App-level error:", error, errorInfo);
        performanceMonitor.recordRouteTransition("error", "app-level", 0);

        // Report to error tracking service if available
        if (window.errorTracker) {
          window.errorTracker.captureException(error, {
            context: "App-level",
            extra: errorInfo,
            tags: { component: "App" },
          });
        }
      }}
      onReset={() => {
        // Clear any error state and attempt recovery
        console.log("App error boundary reset");
        const stats = getRecoveryStats();
        console.log("Recovery stats:", stats);
      }}
    >
      <AppContent />

      {/* Performance Monitor for development */}
      {process.env.NODE_ENV === "development" && (
        <ComponentLoadingErrorBoundary componentName="Performance Monitor">
          <PerformanceMonitor
            isVisible={showPerformanceMonitor}
            onToggle={() => setShowPerformanceMonitor(!showPerformanceMonitor)}
          />
        </ComponentLoadingErrorBoundary>
      )}
    </AppErrorBoundary>
  );
}

export default App;
