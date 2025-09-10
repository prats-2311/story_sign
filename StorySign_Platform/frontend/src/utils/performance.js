/**
 * Performance optimization utilities for StorySign frontend
 * Provides tools for monitoring and optimizing application performance
 */

// Performance monitoring class
export class PerformanceMonitor {
  constructor() {
    this.metrics = new Map();
    this.observers = new Map();
    this.memoryBaseline = null;
    this.routeTransitions = [];
    this.maxTransitionHistory = 50;
  }

  // Start timing a performance metric
  startTiming(name) {
    const startTime = performance.now();
    this.metrics.set(name, { startTime, endTime: null, duration: null });
    return startTime;
  }

  // End timing and calculate duration
  endTiming(name) {
    const metric = this.metrics.get(name);
    if (!metric) {
      console.warn(`Performance metric "${name}" was not started`);
      return null;
    }

    const endTime = performance.now();
    const duration = endTime - metric.startTime;

    this.metrics.set(name, {
      ...metric,
      endTime,
      duration,
    });

    return duration;
  }

  // Get timing for a specific metric
  getTiming(name) {
    return this.metrics.get(name);
  }

  // Get all metrics
  getAllMetrics() {
    return Object.fromEntries(this.metrics);
  }

  // Monitor route transitions
  recordRouteTransition(fromRoute, toRoute, duration, memoryUsage = null) {
    const transition = {
      from: fromRoute,
      to: toRoute,
      duration,
      memoryUsage,
      timestamp: Date.now(),
    };

    this.routeTransitions.push(transition);

    // Keep only recent transitions
    if (this.routeTransitions.length > this.maxTransitionHistory) {
      this.routeTransitions = this.routeTransitions.slice(
        -this.maxTransitionHistory
      );
    }

    // Log slow transitions
    if (duration > 1000) {
      console.warn(
        `Slow route transition detected: ${fromRoute} → ${toRoute} (${duration}ms)`
      );
    }

    return transition;
  }

  // Get route transition statistics
  getRouteTransitionStats() {
    if (this.routeTransitions.length === 0) {
      return null;
    }

    const durations = this.routeTransitions.map(t => t.duration);
    const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
    const maxDuration = Math.max(...durations);
    const minDuration = Math.min(...durations);

    return {
      totalTransitions: this.routeTransitions.length,
      averageDuration: Math.round(avgDuration),
      maxDuration: Math.round(maxDuration),
      minDuration: Math.round(minDuration),
      slowTransitions: this.routeTransitions.filter(t => t.duration > 1000)
        .length,
    };
  }

  // Monitor memory usage
  measureMemoryUsage() {
    if ("memory" in performance) {
      const memory = performance.memory;
      return {
        used: Math.round(memory.usedJSHeapSize / 1024 / 1024), // MB
        total: Math.round(memory.totalJSHeapSize / 1024 / 1024), // MB
        limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024), // MB
        timestamp: Date.now(),
      };
    }
    return null;
  }

  // Set memory baseline for comparison
  setMemoryBaseline() {
    this.memoryBaseline = this.measureMemoryUsage();
    return this.memoryBaseline;
  }

  // Check for memory leaks
  checkMemoryLeak() {
    const current = this.measureMemoryUsage();
    if (!current || !this.memoryBaseline) {
      return null;
    }

    const increase = current.used - this.memoryBaseline.used;
    const percentIncrease = (increase / this.memoryBaseline.used) * 100;

    return {
      baseline: this.memoryBaseline,
      current,
      increase,
      percentIncrease: Math.round(percentIncrease * 100) / 100,
      isLeak: increase > 50 && percentIncrease > 50, // Threshold: 50MB or 50% increase
    };
  }

  // Clear metrics
  clear() {
    this.metrics.clear();
    this.routeTransitions = [];
  }

  // Generate performance report
  generateReport() {
    return {
      metrics: this.getAllMetrics(),
      routeTransitions: this.getRouteTransitionStats(),
      memoryUsage: this.measureMemoryUsage(),
      memoryLeak: this.checkMemoryLeak(),
      timestamp: Date.now(),
    };
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor();

// Performance optimization utilities
export const performanceUtils = {
  // Debounce function for performance optimization
  debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        timeout = null;
        if (!immediate) func(...args);
      };
      const callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func(...args);
    };
  },

  // Throttle function for performance optimization
  throttle(func, limit) {
    let inThrottle;
    return function (...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  },

  // Measure component render time
  measureRender(componentName, renderFunction) {
    const startTime = performance.now();
    const result = renderFunction();
    const endTime = performance.now();
    const duration = endTime - startTime;

    if (duration > 16) {
      // More than one frame at 60fps
      console.warn(`Slow render detected in ${componentName}: ${duration}ms`);
    }

    performanceMonitor.recordRouteTransition("render", componentName, duration);

    return result;
  },

  // Optimize image loading
  preloadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });
  },

  // Check if user prefers reduced motion
  prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  },

  // Get connection quality
  getConnectionQuality() {
    if ("connection" in navigator) {
      const connection = navigator.connection;
      return {
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData,
      };
    }
    return null;
  },

  // Adaptive loading based on connection
  shouldLoadHeavyContent() {
    const connection = this.getConnectionQuality();
    if (!connection) return true; // Default to loading if unknown

    // Don't load heavy content on slow connections or data saver mode
    return (
      !connection.saveData &&
      connection.effectiveType !== "slow-2g" &&
      connection.effectiveType !== "2g"
    );
  },
};

// React performance hooks
export const usePerformanceMonitoring = () => {
  const [metrics, setMetrics] = React.useState({});
  const [memoryUsage, setMemoryUsage] = React.useState(null);

  React.useEffect(() => {
    // Set initial memory baseline
    performanceMonitor.setMemoryBaseline();

    // Update metrics periodically
    const interval = setInterval(() => {
      setMetrics(performanceMonitor.getAllMetrics());
      setMemoryUsage(performanceMonitor.measureMemoryUsage());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const startTiming = React.useCallback(name => {
    return performanceMonitor.startTiming(name);
  }, []);

  const endTiming = React.useCallback(name => {
    return performanceMonitor.endTiming(name);
  }, []);

  const checkMemoryLeak = React.useCallback(() => {
    return performanceMonitor.checkMemoryLeak();
  }, []);

  return {
    metrics,
    memoryUsage,
    startTiming,
    endTiming,
    checkMemoryLeak,
    generateReport: () => performanceMonitor.generateReport(),
  };
};

// Route transition performance hook
export const useRouteTransitionPerformance = () => {
  const [isTransitioning, setIsTransitioning] = React.useState(false);
  const [transitionDuration, setTransitionDuration] = React.useState(null);
  const transitionStartRef = React.useRef(null);

  const startTransition = React.useCallback((fromRoute, toRoute) => {
    setIsTransitioning(true);
    transitionStartRef.current = {
      startTime: performance.now(),
      fromRoute,
      toRoute,
    };
  }, []);

  const endTransition = React.useCallback(() => {
    if (transitionStartRef.current) {
      const duration = performance.now() - transitionStartRef.current.startTime;
      setTransitionDuration(duration);
      setIsTransitioning(false);

      // Record the transition
      performanceMonitor.recordRouteTransition(
        transitionStartRef.current.fromRoute,
        transitionStartRef.current.toRoute,
        duration,
        performanceMonitor.measureMemoryUsage()
      );

      transitionStartRef.current = null;
    }
  }, []);

  return {
    isTransitioning,
    transitionDuration,
    startTransition,
    endTransition,
  };
};

// Export React for hooks
import React from "react";
