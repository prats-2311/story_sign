/**
 * Performance testing utilities for StorySign frontend
 * Tests route transitions, memory usage, and loading times
 */

import { performanceMonitor, performanceUtils } from "../../utils/performance";

// Performance test configuration
const PERFORMANCE_THRESHOLDS = {
  routeTransition: 1000, // 1 second max
  componentRender: 100, // 100ms max
  memoryIncrease: 50, // 50MB max increase
  initialLoad: 3000, // 3 seconds max initial load
};

/**
 * Test suite for route transition performance
 */
export class RouteTransitionPerformanceTest {
  constructor() {
    this.results = [];
    this.isRunning = false;
  }

  async testRouteTransition(fromRoute, toRoute, navigationFn) {
    const testId = `${fromRoute}_to_${toRoute}`;
    console.log(`Testing route transition: ${testId}`);

    const startTime = performance.now();
    const startMemory = performanceMonitor.measureMemoryUsage();

    try {
      // Execute navigation
      await navigationFn();

      // Wait for route to stabilize
      await this.waitForRouteStabilization();

      const endTime = performance.now();
      const endMemory = performanceMonitor.measureMemoryUsage();
      const duration = endTime - startTime;

      const result = {
        testId,
        fromRoute,
        toRoute,
        duration,
        memoryBefore: startMemory,
        memoryAfter: endMemory,
        memoryIncrease: endMemory ? endMemory.used - startMemory.used : 0,
        passed: duration < PERFORMANCE_THRESHOLDS.routeTransition,
        timestamp: Date.now(),
      };

      this.results.push(result);

      if (!result.passed) {
        console.warn(
          `Route transition performance issue: ${testId} took ${duration}ms`
        );
      }

      return result;
    } catch (error) {
      const result = {
        testId,
        fromRoute,
        toRoute,
        error: error.message,
        passed: false,
        timestamp: Date.now(),
      };

      this.results.push(result);
      return result;
    }
  }

  async waitForRouteStabilization(timeout = 2000) {
    return new Promise(resolve => {
      const checkStability = () => {
        // Check if DOM has stabilized
        const observer = new MutationObserver(mutations => {
          if (mutations.length === 0) {
            observer.disconnect();
            resolve();
          }
        });

        observer.observe(document.body, {
          childList: true,
          subtree: true,
          attributes: true,
        });

        // Timeout fallback
        setTimeout(() => {
          observer.disconnect();
          resolve();
        }, timeout);
      };

      // Wait a bit for initial rendering
      setTimeout(checkStability, 100);
    });
  }

  async runFullRouteTest() {
    this.isRunning = true;
    console.log("Starting comprehensive route transition performance test...");

    const routes = [
      { path: "/dashboard", name: "Dashboard" },
      { path: "/asl-world", name: "ASL World" },
      { path: "/harmony", name: "Harmony" },
      { path: "/reconnect", name: "Reconnect" },
    ];

    const testResults = [];

    // Test transitions between all routes
    for (let i = 0; i < routes.length; i++) {
      for (let j = 0; j < routes.length; j++) {
        if (i !== j) {
          const fromRoute = routes[i];
          const toRoute = routes[j];

          const result = await this.testRouteTransition(
            fromRoute.path,
            toRoute.path,
            () => {
              window.history.pushState({}, "", toRoute.path);
              window.dispatchEvent(new PopStateEvent("popstate"));
              return Promise.resolve();
            }
          );

          testResults.push(result);

          // Wait between tests to avoid interference
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
    }

    this.isRunning = false;
    return this.generateReport(testResults);
  }

  generateReport(results = this.results) {
    const passedTests = results.filter(r => r.passed).length;
    const totalTests = results.length;
    const failedTests = results.filter(r => !r.passed);

    const durations = results.filter(r => r.duration).map(r => r.duration);

    const avgDuration =
      durations.length > 0
        ? durations.reduce((a, b) => a + b, 0) / durations.length
        : 0;

    const maxDuration = durations.length > 0 ? Math.max(...durations) : 0;

    return {
      summary: {
        totalTests,
        passedTests,
        failedTests: totalTests - passedTests,
        successRate: (passedTests / totalTests) * 100,
        averageDuration: Math.round(avgDuration),
        maxDuration: Math.round(maxDuration),
      },
      details: results,
      failedTests,
      recommendations: this.generateRecommendations(results),
    };
  }

  generateRecommendations(results) {
    const recommendations = [];
    const slowTransitions = results.filter(
      r => r.duration > PERFORMANCE_THRESHOLDS.routeTransition
    );
    const memoryIssues = results.filter(
      r => r.memoryIncrease > PERFORMANCE_THRESHOLDS.memoryIncrease
    );

    if (slowTransitions.length > 0) {
      recommendations.push({
        type: "performance",
        message: `${slowTransitions.length} route transitions are slower than ${PERFORMANCE_THRESHOLDS.routeTransition}ms`,
        suggestion:
          "Consider implementing code splitting or optimizing component rendering",
      });
    }

    if (memoryIssues.length > 0) {
      recommendations.push({
        type: "memory",
        message: `${memoryIssues.length} route transitions show high memory usage`,
        suggestion:
          "Check for memory leaks and implement proper cleanup in components",
      });
    }

    return recommendations;
  }
}

/**
 * Memory usage monitoring test
 */
export class MemoryUsageTest {
  constructor() {
    this.measurements = [];
    this.isMonitoring = false;
  }

  startMonitoring(interval = 1000) {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    this.measurements = [];

    const monitor = () => {
      if (!this.isMonitoring) return;

      const usage = performanceMonitor.measureMemoryUsage();
      if (usage) {
        this.measurements.push({
          ...usage,
          route: window.location.pathname,
        });
      }

      setTimeout(monitor, interval);
    };

    monitor();
  }

  stopMonitoring() {
    this.isMonitoring = false;
  }

  async testMemoryLeakDuringNavigation(duration = 30000) {
    console.log(`Testing memory leaks during navigation for ${duration}ms...`);

    const routes = ["/dashboard", "/asl-world", "/harmony", "/reconnect"];
    let currentRouteIndex = 0;

    this.startMonitoring(1000);

    const navigationInterval = setInterval(() => {
      currentRouteIndex = (currentRouteIndex + 1) % routes.length;
      const newRoute = routes[currentRouteIndex];

      window.history.pushState({}, "", newRoute);
      window.dispatchEvent(new PopStateEvent("popstate"));
    }, 2000);

    // Run test for specified duration
    await new Promise(resolve => setTimeout(resolve, duration));

    clearInterval(navigationInterval);
    this.stopMonitoring();

    return this.analyzeMemoryUsage();
  }

  analyzeMemoryUsage() {
    if (this.measurements.length === 0) {
      return { error: "No memory measurements available" };
    }

    const initial = this.measurements[0];
    const final = this.measurements[this.measurements.length - 1];
    const peak = this.measurements.reduce((max, current) =>
      current.used > max.used ? current : max
    );

    const memoryIncrease = final.used - initial.used;
    const peakIncrease = peak.used - initial.used;

    return {
      initial: initial.used,
      final: final.used,
      peak: peak.used,
      memoryIncrease,
      peakIncrease,
      measurements: this.measurements.length,
      hasLeak: memoryIncrease > PERFORMANCE_THRESHOLDS.memoryIncrease,
      analysis: {
        trend: memoryIncrease > 0 ? "increasing" : "stable",
        severity:
          memoryIncrease > 100
            ? "high"
            : memoryIncrease > 50
            ? "medium"
            : "low",
      },
    };
  }
}

/**
 * Component rendering performance test
 */
export class ComponentRenderingTest {
  constructor() {
    this.renderTimes = new Map();
  }

  measureComponentRender(componentName, renderFn) {
    const startTime = performance.now();
    const result = renderFn();
    const endTime = performance.now();
    const duration = endTime - startTime;

    if (!this.renderTimes.has(componentName)) {
      this.renderTimes.set(componentName, []);
    }

    this.renderTimes.get(componentName).push(duration);

    if (duration > PERFORMANCE_THRESHOLDS.componentRender) {
      console.warn(
        `Slow component render: ${componentName} took ${duration}ms`
      );
    }

    return { result, duration };
  }

  getComponentStats(componentName) {
    const times = this.renderTimes.get(componentName);
    if (!times || times.length === 0) {
      return null;
    }

    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const max = Math.max(...times);
    const min = Math.min(...times);

    return {
      componentName,
      renderCount: times.length,
      averageTime: Math.round(avg * 100) / 100,
      maxTime: Math.round(max * 100) / 100,
      minTime: Math.round(min * 100) / 100,
      slowRenders: times.filter(t => t > PERFORMANCE_THRESHOLDS.componentRender)
        .length,
    };
  }

  getAllStats() {
    const stats = [];
    for (const componentName of this.renderTimes.keys()) {
      stats.push(this.getComponentStats(componentName));
    }
    return stats.sort((a, b) => b.averageTime - a.averageTime);
  }
}

/**
 * Main performance test runner
 */
export class PerformanceTestRunner {
  constructor() {
    this.routeTest = new RouteTransitionPerformanceTest();
    this.memoryTest = new MemoryUsageTest();
    this.renderTest = new ComponentRenderingTest();
  }

  async runAllTests() {
    console.log("Starting comprehensive performance test suite...");

    const results = {
      timestamp: Date.now(),
      tests: {},
    };

    try {
      // Route transition tests
      console.log("Running route transition tests...");
      results.tests.routeTransitions = await this.routeTest.runFullRouteTest();

      // Memory leak tests
      console.log("Running memory leak tests...");
      results.tests.memoryUsage =
        await this.memoryTest.testMemoryLeakDuringNavigation(20000);

      // Component rendering stats
      console.log("Collecting component rendering stats...");
      results.tests.componentRendering = this.renderTest.getAllStats();

      // Overall performance metrics
      results.overallMetrics = performanceMonitor.generateReport();

      console.log("Performance test suite completed:", results);
      return results;
    } catch (error) {
      console.error("Performance test suite failed:", error);
      results.error = error.message;
      return results;
    }
  }

  generatePerformanceReport(results) {
    const report = {
      summary: {
        timestamp: new Date(results.timestamp).toISOString(),
        overallHealth: "good", // Will be calculated based on results
      },
      issues: [],
      recommendations: [],
    };

    // Analyze route transition performance
    if (results.tests.routeTransitions) {
      const routeResults = results.tests.routeTransitions;
      if (routeResults.summary.successRate < 80) {
        report.issues.push(
          "Route transition performance is below acceptable threshold"
        );
        report.recommendations.push(
          "Implement lazy loading and code splitting"
        );
      }
    }

    // Analyze memory usage
    if (results.tests.memoryUsage) {
      const memoryResults = results.tests.memoryUsage;
      if (memoryResults.hasLeak) {
        report.issues.push("Potential memory leak detected during navigation");
        report.recommendations.push(
          "Review component cleanup and event listener removal"
        );
      }
    }

    // Determine overall health
    if (report.issues.length === 0) {
      report.summary.overallHealth = "excellent";
    } else if (report.issues.length <= 2) {
      report.summary.overallHealth = "good";
    } else if (report.issues.length <= 4) {
      report.summary.overallHealth = "fair";
    } else {
      report.summary.overallHealth = "poor";
    }

    return report;
  }
}

// Export test runner instance
export const performanceTestRunner = new PerformanceTestRunner();

// Utility function to run quick performance check
export const runQuickPerformanceCheck = async () => {
  const routeTest = new RouteTransitionPerformanceTest();
  const memoryTest = new MemoryUsageTest();

  // Quick route transition test
  const routeResult = await routeTest.testRouteTransition(
    window.location.pathname,
    "/dashboard",
    () => Promise.resolve()
  );

  // Quick memory check
  const memoryResult = performanceMonitor.checkMemoryLeak();

  return {
    routeTransition: routeResult,
    memoryCheck: memoryResult,
    timestamp: Date.now(),
  };
};
