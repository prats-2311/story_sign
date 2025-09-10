/**
 * Global Teardown for E2E Tests
 *
 * Cleans up test environment after E2E testing
 */

const fs = require("fs");
const path = require("path");

module.exports = async () => {
  console.log("🧹 Cleaning up E2E test environment...");

  // Calculate total test duration
  const totalDuration = Date.now() - (global.testStartTime || Date.now());

  // Generate final performance summary
  if (global.performanceMetrics) {
    const summary = generatePerformanceSummary(
      global.performanceMetrics,
      totalDuration
    );

    // Save performance summary
    const summaryPath = path.join(
      __dirname,
      "../../../test-results/e2e/performance-summary.json"
    );
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));

    console.log(`📊 Performance summary saved to: ${summaryPath}`);
    console.log(
      `⏱️  Total test duration: ${(totalDuration / 1000).toFixed(2)}s`
    );
  }

  // Clean up temporary files
  cleanupTempFiles();

  // Reset environment variables
  delete process.env.REACT_APP_API_URL;
  delete process.env.REACT_APP_WS_URL;
  delete process.env.REACT_APP_ENVIRONMENT;

  // Clear global test variables
  delete global.testStartTime;
  delete global.performanceMetrics;
  delete global.mockEndpoints;

  console.log("✅ E2E test environment cleanup complete");
};

function generatePerformanceSummary(metrics, totalDuration) {
  const summary = {
    timestamp: new Date().toISOString(),
    totalDuration: totalDuration,
    metrics: {},
  };

  // Calculate statistics for each metric type
  Object.keys(metrics).forEach((metricType) => {
    const values = metrics[metricType];

    if (values.length > 0) {
      const sorted = values.sort((a, b) => a - b);

      summary.metrics[metricType] = {
        count: values.length,
        average: values.reduce((sum, val) => sum + val, 0) / values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        p50: sorted[Math.floor(0.5 * sorted.length)],
        p95: sorted[Math.floor(0.95 * sorted.length)],
        p99: sorted[Math.floor(0.99 * sorted.length)],
      };
    } else {
      summary.metrics[metricType] = {
        count: 0,
        average: 0,
        min: 0,
        max: 0,
        p50: 0,
        p95: 0,
        p99: 0,
      };
    }
  });

  return summary;
}

function cleanupTempFiles() {
  // Clean up any temporary files created during testing
  const tempDirs = [
    path.join(__dirname, "../../../temp"),
    path.join(__dirname, "../../../.tmp"),
  ];

  tempDirs.forEach((dir) => {
    if (fs.existsSync(dir)) {
      try {
        fs.rmSync(dir, { recursive: true, force: true });
        console.log(`🗑️  Cleaned up temp directory: ${dir}`);
      } catch (error) {
        console.warn(
          `⚠️  Failed to clean up temp directory ${dir}:`,
          error.message
        );
      }
    }
  });
}
