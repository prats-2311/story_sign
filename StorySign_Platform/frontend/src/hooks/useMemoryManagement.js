import { useEffect, useRef, useCallback, useState } from "react";
import { performanceMonitor } from "../utils/performance";

/**
 * Memory management hook for React components
 * Helps prevent memory leaks and optimize memory usage
 */
export const useMemoryManagement = (componentName = "Unknown") => {
  const cleanupFunctions = useRef([]);
  const intervalRefs = useRef([]);
  const timeoutRefs = useRef([]);
  const eventListeners = useRef([]);
  const observerRefs = useRef([]);
  const [memoryUsage, setMemoryUsage] = useState(null);

  // Register cleanup function
  const registerCleanup = useCallback(cleanupFn => {
    if (typeof cleanupFn === "function") {
      cleanupFunctions.current.push(cleanupFn);
    }
  }, []);

  // Register interval with automatic cleanup
  const registerInterval = useCallback((callback, delay) => {
    const intervalId = setInterval(callback, delay);
    intervalRefs.current.push(intervalId);
    return intervalId;
  }, []);

  // Register timeout with automatic cleanup
  const registerTimeout = useCallback((callback, delay) => {
    const timeoutId = setTimeout(callback, delay);
    timeoutRefs.current.push(timeoutId);
    return timeoutId;
  }, []);

  // Register event listener with automatic cleanup
  const registerEventListener = useCallback(
    (element, event, handler, options) => {
      element.addEventListener(event, handler, options);
      eventListeners.current.push({ element, event, handler, options });
      return () => element.removeEventListener(event, handler, options);
    },
    []
  );

  // Register observer with automatic cleanup
  const registerObserver = useCallback(observer => {
    observerRefs.current.push(observer);
    return observer;
  }, []);

  // Manual cleanup function
  const cleanup = useCallback(() => {
    // Clear intervals
    intervalRefs.current.forEach(clearInterval);
    intervalRefs.current = [];

    // Clear timeouts
    timeoutRefs.current.forEach(clearTimeout);
    timeoutRefs.current = [];

    // Remove event listeners
    eventListeners.current.forEach(({ element, event, handler, options }) => {
      try {
        element.removeEventListener(event, handler, options);
      } catch (error) {
        console.warn("Error removing event listener:", error);
      }
    });
    eventListeners.current = [];

    // Disconnect observers
    observerRefs.current.forEach(observer => {
      try {
        if (observer.disconnect) observer.disconnect();
        if (observer.unobserve) observer.unobserve();
      } catch (error) {
        console.warn("Error disconnecting observer:", error);
      }
    });
    observerRefs.current = [];

    // Run custom cleanup functions
    cleanupFunctions.current.forEach(cleanupFn => {
      try {
        cleanupFn();
      } catch (error) {
        console.warn("Error in cleanup function:", error);
      }
    });
    cleanupFunctions.current = [];
  }, []);

  // Monitor memory usage
  const checkMemoryUsage = useCallback(() => {
    const usage = performanceMonitor.measureMemoryUsage();
    setMemoryUsage(usage);

    if (usage && usage.used > 100) {
      // More than 100MB
      console.warn(
        `High memory usage detected in ${componentName}: ${usage.used}MB`
      );
    }

    return usage;
  }, [componentName]);

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  // Periodic memory monitoring
  useEffect(() => {
    const memoryCheckInterval = setInterval(checkMemoryUsage, 10000); // Check every 10 seconds

    return () => clearInterval(memoryCheckInterval);
  }, [checkMemoryUsage]);

  return {
    registerCleanup,
    registerInterval,
    registerTimeout,
    registerEventListener,
    registerObserver,
    cleanup,
    memoryUsage,
    checkMemoryUsage,
  };
};

/**
 * Hook for managing WebSocket connections with automatic cleanup
 */
export const useWebSocketMemoryManagement = (url, options = {}) => {
  const wsRef = useRef(null);
  const { registerCleanup } = useMemoryManagement("WebSocket");
  const [connectionState, setConnectionState] = useState("disconnected");

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return wsRef.current;
    }

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setConnectionState("connected");
        options.onOpen?.();
      };

      wsRef.current.onclose = () => {
        setConnectionState("disconnected");
        options.onClose?.();
      };

      wsRef.current.onerror = error => {
        setConnectionState("error");
        options.onError?.(error);
      };

      wsRef.current.onmessage = options.onMessage;

      // Register cleanup
      registerCleanup(() => {
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
      });

      return wsRef.current;
    } catch (error) {
      console.error("WebSocket connection error:", error);
      setConnectionState("error");
      return null;
    }
  }, [url, options, registerCleanup]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setConnectionState("disconnected");
    }
  }, []);

  const send = useCallback(data => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
      return true;
    }
    return false;
  }, []);

  return {
    connect,
    disconnect,
    send,
    connectionState,
    isConnected: connectionState === "connected",
  };
};

/**
 * Hook for managing video streams with automatic cleanup
 */
export const useVideoStreamMemoryManagement = () => {
  const streamRef = useRef(null);
  const videoElementRefs = useRef([]);
  const { registerCleanup } = useMemoryManagement("VideoStream");

  const startStream = useCallback(
    async (constraints = { video: true, audio: false }) => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        streamRef.current = stream;

        // Register cleanup for stream
        registerCleanup(() => {
          if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => {
              track.stop();
            });
            streamRef.current = null;
          }
        });

        return stream;
      } catch (error) {
        console.error("Error starting video stream:", error);
        throw error;
      }
    },
    [registerCleanup]
  );

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => {
        track.stop();
      });
      streamRef.current = null;
    }

    // Clear video elements
    videoElementRefs.current.forEach(video => {
      if (video.srcObject) {
        video.srcObject = null;
      }
    });
    videoElementRefs.current = [];
  }, []);

  const attachToVideo = useCallback(videoElement => {
    if (videoElement && streamRef.current) {
      videoElement.srcObject = streamRef.current;
      videoElementRefs.current.push(videoElement);
    }
  }, []);

  return {
    startStream,
    stopStream,
    attachToVideo,
    stream: streamRef.current,
  };
};

/**
 * Hook for managing large data sets with pagination and cleanup
 */
export const useDataMemoryManagement = (initialData = [], pageSize = 50) => {
  const [data, setData] = useState(initialData);
  const [currentPage, setCurrentPage] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const cacheRef = useRef(new Map());
  const { registerCleanup } = useMemoryManagement("DataManager");

  // Clear cache on unmount
  registerCleanup(() => {
    cacheRef.current.clear();
  });

  const loadPage = useCallback(
    async (page, loader) => {
      const cacheKey = `page_${page}`;

      // Check cache first
      if (cacheRef.current.has(cacheKey)) {
        const cachedData = cacheRef.current.get(cacheKey);
        setData(cachedData);
        setCurrentPage(page);
        return cachedData;
      }

      setIsLoading(true);
      try {
        const pageData = await loader(page, pageSize);

        // Cache the data
        cacheRef.current.set(cacheKey, pageData);

        // Limit cache size to prevent memory issues
        if (cacheRef.current.size > 10) {
          const firstKey = cacheRef.current.keys().next().value;
          cacheRef.current.delete(firstKey);
        }

        setData(pageData);
        setCurrentPage(page);
        return pageData;
      } catch (error) {
        console.error("Error loading page:", error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [pageSize]
  );

  const clearCache = useCallback(() => {
    cacheRef.current.clear();
  }, []);

  const preloadPage = useCallback(
    async (page, loader) => {
      const cacheKey = `page_${page}`;

      if (!cacheRef.current.has(cacheKey)) {
        try {
          const pageData = await loader(page, pageSize);
          cacheRef.current.set(cacheKey, pageData);
        } catch (error) {
          console.warn("Error preloading page:", error);
        }
      }
    },
    [pageSize]
  );

  return {
    data,
    currentPage,
    isLoading,
    loadPage,
    clearCache,
    preloadPage,
    cacheSize: cacheRef.current.size,
  };
};

export default useMemoryManagement;
