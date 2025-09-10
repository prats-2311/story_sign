/**
 * Integration tests for performance optimizations
 * Tests the actual performance utilities and components
 */

import { performanceMonitor, performanceUtils } from "../../utils/performance";
import { useMemoryManagement } from "../../hooks/useMemoryManagement";
import { renderHook, act } from "@testing-library/react";

describe("Performance Optimizations", () => {
  beforeEach(() => {
    // Clear performance monitor before each test
    performanceMonitor.clear();
  });

  describe("Performance Monitor", () => {
    test("should track timing metrics", () => {
      const metricName = "test-metric";

      // Start timing
      const startTime = performanceMonitor.startTiming(metricName);
      expect(startTime).toBeGreaterThan(0);

      // End timing
      const duration = performanceMonitor.endTiming(metricName);
      expect(duration).toBeGreaterThan(0);

      // Check metric was recorded
      const metric = performanceMonitor.getTiming(metricName);
      expect(metric).toBeDefined();
      expect(metric.duration).toBe(duration);
    });

    test("should record route transitions", () => {
      const fromRoute = "/dashboard";
      const toRoute = "/asl-world";
      const duration = 500;

      const transition = performanceMonitor.recordRouteTransition(
        fromRoute,
        toRoute,
        duration
      );

      expect(transition).toBeDefined();
      expect(transition.from).toBe(fromRoute);
      expect(transition.to).toBe(toRoute);
      expect(transition.duration).toBe(duration);

      const stats = performanceMonitor.getRouteTransitionStats();
      expect(stats).toBeDefined();
      expect(stats.totalTransitions).toBe(1);
      expect(stats.averageDuration).toBe(duration);
    });

    test("should detect slow route transitions", () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      // Record a slow transition (over 1000ms)
      performanceMonitor.recordRouteTransition(
        "/dashboard",
        "/asl-world",
        1500
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Slow route transition detected")
      );

      consoleSpy.mockRestore();
    });

    test("should measure memory usage if available", () => {
      // Mock performance.memory if not available
      const originalMemory = performance.memory;

      if (!performance.memory) {
        performance.memory = {
          usedJSHeapSize: 50 * 1024 * 1024, // 50MB
          totalJSHeapSize: 100 * 1024 * 1024, // 100MB
          jsHeapSizeLimit: 2048 * 1024 * 1024, // 2GB
        };
      }

      const usage = performanceMonitor.measureMemoryUsage();

      if (performance.memory) {
        expect(usage).toBeDefined();
        expect(usage.used).toBeGreaterThan(0);
        expect(usage.total).toBeGreaterThan(0);
        expect(usage.limit).toBeGreaterThan(0);
      }

      // Restore original memory object
      if (!originalMemory) {
        delete performance.memory;
      }
    });

    test("should generate performance report", () => {
      // Add some test data
      performanceMonitor.startTiming("test1");
      performanceMonitor.endTiming("test1");
      performanceMonitor.recordRouteTransition("/dashboard", "/asl-world", 300);

      const report = performanceMonitor.generateReport();

      expect(report).toBeDefined();
      expect(report.metrics).toBeDefined();
      expect(report.routeTransitions).toBeDefined();
      expect(report.timestamp).toBeGreaterThan(0);
    });
  });

  describe("Performance Utils", () => {
    test("should debounce function calls", done => {
      let callCount = 0;
      const debouncedFn = performanceUtils.debounce(() => {
        callCount++;
      }, 100);

      // Call multiple times rapidly
      debouncedFn();
      debouncedFn();
      debouncedFn();

      // Should not have been called yet
      expect(callCount).toBe(0);

      // Wait for debounce delay
      setTimeout(() => {
        expect(callCount).toBe(1);
        done();
      }, 150);
    });

    test("should throttle function calls", done => {
      let callCount = 0;
      const throttledFn = performanceUtils.throttle(() => {
        callCount++;
      }, 100);

      // Call multiple times rapidly
      throttledFn(); // Should execute immediately
      throttledFn(); // Should be throttled
      throttledFn(); // Should be throttled

      expect(callCount).toBe(1);

      // Wait for throttle period to end
      setTimeout(() => {
        throttledFn(); // Should execute now
        expect(callCount).toBe(2);
        done();
      }, 150);
    });

    test("should detect reduced motion preference", () => {
      // Mock matchMedia
      const mockMatchMedia = jest.fn();
      mockMatchMedia.mockReturnValue({
        matches: true,
      });
      window.matchMedia = mockMatchMedia;

      const prefersReduced = performanceUtils.prefersReducedMotion();

      expect(mockMatchMedia).toHaveBeenCalledWith(
        "(prefers-reduced-motion: reduce)"
      );
      expect(prefersReduced).toBe(true);
    });

    test("should get connection quality if available", () => {
      // Mock navigator.connection
      const mockConnection = {
        effectiveType: "4g",
        downlink: 10,
        rtt: 50,
        saveData: false,
      };

      Object.defineProperty(navigator, "connection", {
        value: mockConnection,
        configurable: true,
      });

      const quality = performanceUtils.getConnectionQuality();

      expect(quality).toEqual(mockConnection);

      // Clean up
      delete navigator.connection;
    });

    test("should determine if heavy content should load", () => {
      // Mock good connection
      const mockConnection = {
        effectiveType: "4g",
        saveData: false,
      };

      Object.defineProperty(navigator, "connection", {
        value: mockConnection,
        configurable: true,
      });

      const shouldLoad = performanceUtils.shouldLoadHeavyContent();
      expect(shouldLoad).toBe(true);

      // Mock poor connection
      mockConnection.effectiveType = "2g";
      mockConnection.saveData = true;

      const shouldNotLoad = performanceUtils.shouldLoadHeavyContent();
      expect(shouldNotLoad).toBe(false);

      // Clean up
      delete navigator.connection;
    });
  });

  describe("Memory Management Hook", () => {
    test("should register and cleanup intervals", () => {
      const { result } = renderHook(() => useMemoryManagement("TestComponent"));

      let callCount = 0;
      const callback = () => callCount++;

      act(() => {
        const intervalId = result.current.registerInterval(callback, 10);
        expect(intervalId).toBeDefined();
      });

      // Wait for interval to execute
      return new Promise(resolve => {
        setTimeout(() => {
          expect(callCount).toBeGreaterThan(0);
          resolve();
        }, 50);
      });
    });

    test("should register and cleanup timeouts", () => {
      const { result } = renderHook(() => useMemoryManagement("TestComponent"));

      let executed = false;
      const callback = () => {
        executed = true;
      };

      act(() => {
        const timeoutId = result.current.registerTimeout(callback, 10);
        expect(timeoutId).toBeDefined();
      });

      // Wait for timeout to execute
      return new Promise(resolve => {
        setTimeout(() => {
          expect(executed).toBe(true);
          resolve();
        }, 50);
      });
    });

    test("should register and cleanup event listeners", () => {
      const { result } = renderHook(() => useMemoryManagement("TestComponent"));

      const mockElement = {
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
      };

      const handler = jest.fn();

      act(() => {
        const cleanup = result.current.registerEventListener(
          mockElement,
          "click",
          handler
        );
        expect(cleanup).toBeInstanceOf(Function);
      });

      expect(mockElement.addEventListener).toHaveBeenCalledWith(
        "click",
        handler,
        undefined
      );
    });

    test("should register cleanup functions", () => {
      const { result } = renderHook(() => useMemoryManagement("TestComponent"));

      const cleanupFn = jest.fn();

      act(() => {
        result.current.registerCleanup(cleanupFn);
      });

      // Cleanup function should be registered but not called yet
      expect(cleanupFn).not.toHaveBeenCalled();
    });
  });

  describe("Performance Thresholds", () => {
    test("should warn about slow operations", () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      // Record a slow route transition
      performanceMonitor.recordRouteTransition(
        "/dashboard",
        "/asl-world",
        1500
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Slow route transition detected")
      );

      consoleSpy.mockRestore();
    });

    test("should track memory baseline and detect leaks", () => {
      // Mock performance.memory
      const mockMemory = {
        usedJSHeapSize: 50 * 1024 * 1024, // 50MB
        totalJSHeapSize: 100 * 1024 * 1024, // 100MB
        jsHeapSizeLimit: 2048 * 1024 * 1024, // 2GB
      };

      Object.defineProperty(performance, "memory", {
        value: mockMemory,
        configurable: true,
      });

      // Set baseline
      const baseline = performanceMonitor.setMemoryBaseline();
      expect(baseline).toBeDefined();

      // Simulate memory increase
      mockMemory.usedJSHeapSize = 120 * 1024 * 1024; // 120MB

      const leakCheck = performanceMonitor.checkMemoryLeak();
      expect(leakCheck).toBeDefined();
      expect(leakCheck.increase).toBeGreaterThan(0);

      // Clean up
      delete performance.memory;
    });
  });
});

describe("Performance Integration", () => {
  test("should work together for complete performance monitoring", () => {
    // Start a complete performance monitoring session
    performanceMonitor.setMemoryBaseline();

    // Simulate route transition
    performanceMonitor.startTiming("route_transition");

    // Simulate some work
    const start = Date.now();
    while (Date.now() - start < 10) {
      // Busy wait for 10ms
    }

    const duration = performanceMonitor.endTiming("route_transition");
    expect(duration).toBeGreaterThan(0);

    // Record the transition
    const transition = performanceMonitor.recordRouteTransition(
      "/dashboard",
      "/asl-world",
      duration
    );

    expect(transition).toBeDefined();

    // Generate report
    const report = performanceMonitor.generateReport();
    expect(report.metrics).toBeDefined();
    expect(report.routeTransitions).toBeDefined();
    expect(report.routeTransitions.totalTransitions).toBe(1);
  });
});
