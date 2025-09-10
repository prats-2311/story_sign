import React, { Suspense, lazy, useState, useEffect } from "react";
import { ErrorBoundary } from "react-error-boundary";
import {
  performanceMonitor,
  useRouteTransitionPerformance,
} from "../../utils/performance";
import OptimizedLoadingScreen, {
  ComponentSkeleton,
} from "../loading/OptimizedLoadingScreen";

/**
 * Error fallback component for route loading failures
 */
const RouteErrorFallback = ({ error, resetErrorBoundary, routeName }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="route-error-fallback" role="alert">
      <div className="error-content">
        <div className="error-icon" aria-hidden="true">
          ⚠️
        </div>
        <h2>Failed to load {routeName || "page"}</h2>
        <p>
          There was an error loading this page. This might be due to a network
          issue or a temporary problem.
        </p>

        <div className="error-actions">
          <button className="retry-button primary" onClick={resetErrorBoundary}>
            Try Again
          </button>
          <button
            className="details-button"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? "Hide" : "Show"} Details
          </button>
        </div>

        {showDetails && (
          <details className="error-details">
            <summary>Technical Details</summary>
            <pre className="error-message">{error.message}</pre>
            <pre className="error-stack">{error.stack}</pre>
          </details>
        )}

        <div className="error-suggestions">
          <h3>Try these solutions:</h3>
          <ul>
            <li>Check your internet connection</li>
            <li>Refresh the page</li>
            <li>Clear your browser cache</li>
            <li>Try again in a few minutes</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

/**
 * Lazy route wrapper with performance monitoring and error handling
 */
export const LazyRouteWrapper = ({
  importFunction,
  routeName,
  fallbackType = "default",
  preloadDelay = 2000,
  retryAttempts = 3,
}) => {
  const [retryCount, setRetryCount] = useState(0);
  const [isPreloading, setIsPreloading] = useState(false);
  const { startTransition, endTransition, isTransitioning } =
    useRouteTransitionPerformance();

  // Create lazy component with retry logic
  const LazyComponent = lazy(async () => {
    const startTime = performance.now();

    try {
      startTransition(window.location.pathname, routeName);

      const module = await importFunction();

      const loadTime = performance.now() - startTime;
      performanceMonitor.recordRouteTransition(
        "lazy-load",
        routeName,
        loadTime,
        performanceMonitor.measureMemoryUsage()
      );

      // Log slow loading
      if (loadTime > 2000) {
        console.warn(
          `Slow route loading detected: ${routeName} (${loadTime}ms)`
        );
      }

      endTransition();
      return module;
    } catch (error) {
      endTransition();

      // Retry logic for network errors
      if (
        retryCount < retryAttempts &&
        (error.name === "ChunkLoadError" ||
          error.message.includes("Loading chunk"))
      ) {
        console.warn(
          `Route loading failed, retrying... (${
            retryCount + 1
          }/${retryAttempts})`
        );
        setRetryCount(prev => prev + 1);

        // Exponential backoff
        await new Promise(resolve =>
          setTimeout(resolve, Math.pow(2, retryCount) * 1000)
        );

        // Retry the import
        return importFunction();
      }

      throw error;
    }
  });

  // Preload component after delay
  useEffect(() => {
    const preloadTimer = setTimeout(() => {
      if (!isPreloading) {
        setIsPreloading(true);
        importFunction().catch(() => {
          // Ignore preload errors - component will load when needed
        });
      }
    }, preloadDelay);

    return () => clearTimeout(preloadTimer);
  }, [importFunction, preloadDelay, isPreloading]);

  // Reset retry count when route changes
  useEffect(() => {
    setRetryCount(0);
  }, [routeName]);

  return (
    <ErrorBoundary
      FallbackComponent={props => (
        <RouteErrorFallback {...props} routeName={routeName} />
      )}
      onError={(error, errorInfo) => {
        console.error(`Route error in ${routeName}:`, error, errorInfo);

        // Track error in performance monitor
        performanceMonitor.recordRouteTransition(
          "error",
          routeName,
          0,
          performanceMonitor.measureMemoryUsage()
        );
      }}
      onReset={() => {
        setRetryCount(0);
      }}
    >
      <Suspense
        fallback={
          <div className="lazy-route-loading">
            <ComponentSkeleton type={fallbackType} className="route-skeleton" />
            {isTransitioning && (
              <div className="transition-indicator">Loading {routeName}...</div>
            )}
          </div>
        }
      >
        <LazyComponent />
      </Suspense>
    </ErrorBoundary>
  );
};

/**
 * Higher-order component for creating lazy routes
 */
export const createLazyRoute = (importFunction, options = {}) => {
  const {
    routeName = "Unknown Route",
    fallbackType = "default",
    preloadDelay = 2000,
    retryAttempts = 3,
  } = options;

  return props => (
    <LazyRouteWrapper
      importFunction={importFunction}
      routeName={routeName}
      fallbackType={fallbackType}
      preloadDelay={preloadDelay}
      retryAttempts={retryAttempts}
      {...props}
    />
  );
};

/**
 * Preload routes for better performance
 */
export const preloadRoutes = routes => {
  const preloadPromises = routes.map(async ({ importFunction, routeName }) => {
    try {
      const startTime = performance.now();
      await importFunction();
      const loadTime = performance.now() - startTime;

      console.log(`Preloaded ${routeName} in ${loadTime}ms`);
      return { routeName, success: true, loadTime };
    } catch (error) {
      console.warn(`Failed to preload ${routeName}:`, error);
      return { routeName, success: false, error: error.message };
    }
  });

  return Promise.allSettled(preloadPromises);
};

/**
 * Route preloader hook
 */
export const useRoutePreloader = (routes, delay = 3000) => {
  const [preloadStatus, setPreloadStatus] = useState({});
  const [isPreloading, setIsPreloading] = useState(false);

  useEffect(() => {
    const preloadTimer = setTimeout(async () => {
      setIsPreloading(true);

      const results = await preloadRoutes(routes);
      const status = {};

      results.forEach((result, index) => {
        const routeName = routes[index].routeName;
        if (result.status === "fulfilled") {
          status[routeName] = result.value;
        } else {
          status[routeName] = {
            routeName,
            success: false,
            error: result.reason?.message || "Unknown error",
          };
        }
      });

      setPreloadStatus(status);
      setIsPreloading(false);
    }, delay);

    return () => clearTimeout(preloadTimer);
  }, [routes, delay]);

  return { preloadStatus, isPreloading };
};

export default LazyRouteWrapper;
