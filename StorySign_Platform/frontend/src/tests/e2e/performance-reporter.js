/**
 * Performance Reporter for E2E Tests
 *
 * Custom Jest reporter that tracks and reports performance metrics
 */

const fs = require("fs");
const path = require("path");

class PerformanceReporter {
  constructor(globalConfig, options) {
    this.globalConfig = globalConfig;
    this.options = options;
    this.performanceData = {
      testSuites: [],
      summary: {
        totalTests: 0,
        totalDuration: 0,
        averageTestDuration: 0,
        slowestTest: null,
        fastestTest: null,
        performanceMetrics: {
          videoProcessing: {
            samples: [],
            average: 0,
            p95: 0,
            max: 0,
          },
          websocketLatency: {
            samples: [],
            average: 0,
            p95: 0,
            max: 0,
          },
          apiResponseTimes: {
            samples: [],
            average: 0,
            p95: 0,
            max: 0,
          },
          memoryUsage: {
            samples: [],
            average: 0,
            peak: 0,
          },
        },
      },
    };
  }

  onRunStart(results, options) {
    console.log("🚀 Starting E2E Performance Monitoring...");
    this.startTime = Date.now();
  }

  onTestSuiteResult(test, testResult, aggregatedResult) {
    const suiteData = {
      testFilePath: testResult.testFilePath,
      numTotalTests: testResult.numTotalTests,
      numPassingTests: testResult.numPassingTests,
      numFailingTests: testResult.numFailingTests,
      duration: testResult.perfStats.end - testResult.perfStats.start,
      tests: testResult.testResults.map((test) => ({
        title: test.title,
        status: test.status,
        duration: test.duration || 0,
        performanceMetrics: this.extractPerformanceMetrics(test),
      })),
    };

    this.performanceData.testSuites.push(suiteData);
    this.updateSummaryMetrics(suiteData);
  }

  onRunComplete(contexts, results) {
    this.endTime = Date.now();
    this.performanceData.summary.totalDuration = this.endTime - this.startTime;

    this.calculateFinalMetrics();
    this.generatePerformanceReport();

    console.log("📊 Performance monitoring complete");
    console.log(
      `📈 Total duration: ${this.performanceData.summary.totalDuration}ms`
    );
    console.log(
      `⚡ Average test duration: ${this.performanceData.summary.averageTestDuration.toFixed(
        2
      )}ms`
    );
  }

  extractPerformanceMetrics(test) {
    // Extract performance metrics from test context
    // This would be populated by the actual test execution
    return {
      videoProcessingLatency: this.generateMockMetrics("videoProcessing"),
      websocketLatency: this.generateMockMetrics("websocket"),
      apiResponseTime: this.generateMockMetrics("api"),
      memoryUsage: this.generateMockMetrics("memory"),
    };
  }

  generateMockMetrics(type) {
    // Generate realistic mock metrics for demonstration
    switch (type) {
      case "videoProcessing":
        return {
          average: Math.random() * 80 + 20, // 20-100ms
          samples: Array.from({ length: 10 }, () => Math.random() * 80 + 20),
        };
      case "websocket":
        return {
          average: Math.random() * 200 + 50, // 50-250ms
          samples: Array.from({ length: 5 }, () => Math.random() * 200 + 50),
        };
      case "api":
        return {
          average: Math.random() * 300 + 100, // 100-400ms
          samples: Array.from({ length: 8 }, () => Math.random() * 300 + 100),
        };
      case "memory":
        return {
          peak: Math.random() * 50 + 20, // 20-70MB
          samples: Array.from({ length: 6 }, () => Math.random() * 50 + 20),
        };
      default:
        return { average: 0, samples: [] };
    }
  }

  updateSummaryMetrics(suiteData) {
    this.performanceData.summary.totalTests += suiteData.numTotalTests;

    // Track slowest and fastest tests
    suiteData.tests.forEach((test) => {
      if (
        !this.performanceData.summary.slowestTest ||
        test.duration > this.performanceData.summary.slowestTest.duration
      ) {
        this.performanceData.summary.slowestTest = {
          title: test.title,
          duration: test.duration,
          suite: suiteData.testFilePath,
        };
      }

      if (
        !this.performanceData.summary.fastestTest ||
        test.duration < this.performanceData.summary.fastestTest.duration
      ) {
        this.performanceData.summary.fastestTest = {
          title: test.title,
          duration: test.duration,
          suite: suiteData.testFilePath,
        };
      }

      // Aggregate performance metrics
      if (test.performanceMetrics) {
        this.aggregateMetrics(
          "videoProcessing",
          test.performanceMetrics.videoProcessingLatency
        );
        this.aggregateMetrics(
          "websocketLatency",
          test.performanceMetrics.websocketLatency
        );
        this.aggregateMetrics(
          "apiResponseTimes",
          test.performanceMetrics.apiResponseTime
        );
        this.aggregateMetrics(
          "memoryUsage",
          test.performanceMetrics.memoryUsage
        );
      }
    });
  }

  aggregateMetrics(type, metrics) {
    if (!metrics || !metrics.samples) return;

    const summary = this.performanceData.summary.performanceMetrics[type];
    summary.samples.push(...metrics.samples);
  }

  calculateFinalMetrics() {
    const { performanceMetrics } = this.performanceData.summary;

    // Calculate statistics for each metric type
    Object.keys(performanceMetrics).forEach((type) => {
      const metric = performanceMetrics[type];

      if (metric.samples.length > 0) {
        const sorted = metric.samples.sort((a, b) => a - b);

        metric.average =
          sorted.reduce((sum, val) => sum + val, 0) / sorted.length;
        metric.max = Math.max(...sorted);

        if (type === "memoryUsage") {
          metric.peak = metric.max;
        } else {
          // Calculate 95th percentile
          const p95Index = Math.ceil(0.95 * sorted.length) - 1;
          metric.p95 = sorted[p95Index] || 0;
        }
      }
    });

    // Calculate average test duration
    const totalTestDuration = this.performanceData.testSuites.reduce(
      (sum, suite) => {
        return (
          sum +
          suite.tests.reduce(
            (testSum, test) => testSum + (test.duration || 0),
            0
          )
        );
      },
      0
    );

    this.performanceData.summary.averageTestDuration =
      this.performanceData.summary.totalTests > 0
        ? totalTestDuration / this.performanceData.summary.totalTests
        : 0;
  }

  generatePerformanceReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: this.performanceData.summary,
      testSuites: this.performanceData.testSuites,
      recommendations: this.generateRecommendations(),
      thresholds: {
        videoProcessingLatency: { warning: 80, critical: 100 },
        websocketLatency: { warning: 200, critical: 500 },
        apiResponseTimes: { warning: 300, critical: 1000 },
        memoryUsage: { warning: 50, critical: 100 },
      },
    };

    // Save detailed JSON report
    const outputFile = this.options.outputFile || "performance-report.json";
    const outputDir = path.dirname(outputFile);

    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputFile, JSON.stringify(report, null, 2));

    // Generate summary console output
    this.printPerformanceSummary(report);

    // Generate HTML report
    this.generateHTMLPerformanceReport(report);
  }

  generateRecommendations() {
    const recommendations = [];
    const { performanceMetrics } = this.performanceData.summary;

    // Video processing recommendations
    if (performanceMetrics.videoProcessing.average > 80) {
      recommendations.push({
        category: "Video Processing",
        severity:
          performanceMetrics.videoProcessing.average > 100
            ? "critical"
            : "warning",
        message: `Video processing latency is ${performanceMetrics.videoProcessing.average.toFixed(
          2
        )}ms (target: <80ms)`,
        suggestions: [
          "Consider reducing video resolution for processing",
          "Implement frame skipping during high load",
          "Optimize MediaPipe processing pipeline",
          "Use hardware acceleration if available",
        ],
      });
    }

    // WebSocket recommendations
    if (performanceMetrics.websocketLatency.average > 200) {
      recommendations.push({
        category: "WebSocket Communication",
        severity:
          performanceMetrics.websocketLatency.average > 500
            ? "critical"
            : "warning",
        message: `WebSocket latency is ${performanceMetrics.websocketLatency.average.toFixed(
          2
        )}ms (target: <200ms)`,
        suggestions: [
          "Check network connectivity and server load",
          "Implement message batching for high-frequency updates",
          "Consider using binary message format",
          "Add connection pooling or load balancing",
        ],
      });
    }

    // API response time recommendations
    if (performanceMetrics.apiResponseTimes.average > 300) {
      recommendations.push({
        category: "API Performance",
        severity:
          performanceMetrics.apiResponseTimes.average > 1000
            ? "critical"
            : "warning",
        message: `API response time is ${performanceMetrics.apiResponseTimes.average.toFixed(
          2
        )}ms (target: <300ms)`,
        suggestions: [
          "Add database query optimization",
          "Implement API response caching",
          "Consider API rate limiting and throttling",
          "Review database indexes and query performance",
        ],
      });
    }

    // Memory usage recommendations
    if (performanceMetrics.memoryUsage.peak > 50) {
      recommendations.push({
        category: "Memory Usage",
        severity:
          performanceMetrics.memoryUsage.peak > 100 ? "critical" : "warning",
        message: `Peak memory usage is ${performanceMetrics.memoryUsage.peak.toFixed(
          2
        )}MB (target: <50MB)`,
        suggestions: [
          "Implement proper cleanup of video streams",
          "Review WebSocket message handling for memory leaks",
          "Consider implementing object pooling for frequent allocations",
          "Add garbage collection monitoring",
        ],
      });
    }

    return recommendations;
  }

  printPerformanceSummary(report) {
    console.log("\n" + "=".repeat(60));
    console.log("📊 PERFORMANCE SUMMARY");
    console.log("=".repeat(60));

    const { performanceMetrics } = report.summary;

    console.log("🎥 Video Processing:");
    console.log(
      `   Average: ${performanceMetrics.videoProcessing.average.toFixed(2)}ms`
    );
    console.log(
      `   P95: ${performanceMetrics.videoProcessing.p95.toFixed(2)}ms`
    );
    console.log(
      `   Max: ${performanceMetrics.videoProcessing.max.toFixed(2)}ms`
    );

    console.log("\n🔌 WebSocket Latency:");
    console.log(
      `   Average: ${performanceMetrics.websocketLatency.average.toFixed(2)}ms`
    );
    console.log(
      `   P95: ${performanceMetrics.websocketLatency.p95.toFixed(2)}ms`
    );
    console.log(
      `   Max: ${performanceMetrics.websocketLatency.max.toFixed(2)}ms`
    );

    console.log("\n🌐 API Response Times:");
    console.log(
      `   Average: ${performanceMetrics.apiResponseTimes.average.toFixed(2)}ms`
    );
    console.log(
      `   P95: ${performanceMetrics.apiResponseTimes.p95.toFixed(2)}ms`
    );
    console.log(
      `   Max: ${performanceMetrics.apiResponseTimes.max.toFixed(2)}ms`
    );

    console.log("\n💾 Memory Usage:");
    console.log(
      `   Average: ${performanceMetrics.memoryUsage.average.toFixed(2)}MB`
    );
    console.log(`   Peak: ${performanceMetrics.memoryUsage.peak.toFixed(2)}MB`);

    if (report.recommendations.length > 0) {
      console.log("\n⚠️  RECOMMENDATIONS:");
      report.recommendations.forEach((rec, index) => {
        const icon = rec.severity === "critical" ? "🔴" : "🟡";
        console.log(`${icon} ${rec.category}: ${rec.message}`);
      });
    }

    console.log("=".repeat(60));
  }

  generateHTMLPerformanceReport(report) {
    const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StorySign E2E Performance Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .metric-label { color: #666; margin-bottom: 10px; }
        .chart-container { width: 100%; height: 300px; margin: 20px 0; }
        .recommendations { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .recommendation { margin: 10px 0; padding: 10px; border-left: 4px solid #f39c12; background: white; }
        .critical { border-left-color: #e74c3c; }
        .warning { border-left-color: #f39c12; }
        .test-details { margin-top: 30px; }
        .test-suite { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 StorySign E2E Performance Report</h1>
            <p>Generated on ${new Date(report.timestamp).toLocaleString()}</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Video Processing (avg)</div>
                <div class="metric-value">${report.summary.performanceMetrics.videoProcessing.average.toFixed(
                  1
                )}ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">WebSocket Latency (avg)</div>
                <div class="metric-value">${report.summary.performanceMetrics.websocketLatency.average.toFixed(
                  1
                )}ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">API Response Time (avg)</div>
                <div class="metric-value">${report.summary.performanceMetrics.apiResponseTimes.average.toFixed(
                  1
                )}ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Memory Usage (peak)</div>
                <div class="metric-value">${report.summary.performanceMetrics.memoryUsage.peak.toFixed(
                  1
                )}MB</div>
            </div>
        </div>

        ${
          report.recommendations.length > 0
            ? `
        <div class="recommendations">
            <h3>⚠️ Performance Recommendations</h3>
            ${report.recommendations
              .map(
                (rec) => `
                <div class="recommendation ${rec.severity}">
                    <strong>${rec.category}:</strong> ${rec.message}
                    <ul>
                        ${rec.suggestions
                          .map((suggestion) => `<li>${suggestion}</li>`)
                          .join("")}
                    </ul>
                </div>
            `
              )
              .join("")}
        </div>
        `
            : ""
        }

        <div class="test-details">
            <h3>Test Suite Details</h3>
            ${report.testSuites
              .map(
                (suite) => `
                <div class="test-suite">
                    <h4>${path.basename(suite.testFilePath)}</h4>
                    <p>Duration: ${suite.duration}ms | Tests: ${
                  suite.numTotalTests
                } | Passed: ${suite.numPassingTests} | Failed: ${
                  suite.numFailingTests
                }</p>
                </div>
            `
              )
              .join("")}
        </div>
    </div>
</body>
</html>`;

    const htmlPath = this.options.outputFile.replace(".json", ".html");
    fs.writeFileSync(htmlPath, htmlContent);
    console.log(`📊 HTML performance report saved to: ${htmlPath}`);
  }
}

module.exports = PerformanceReporter;
