import React from "react";

const PerformanceMonitorSimple = ({
  streamingStats,
  processedFrameData,
  connectionStatus,
  onOptimizationChange,
}) => {
  return (
    <div className="performance-monitor-simple">
      <h4>🚀 Performance Monitor</h4>

      <div className="simple-metrics">
        <div className="metric-row">
          <span>Connection Status:</span>
          <span className={`status ${connectionStatus}`}>
            {connectionStatus}
          </span>
        </div>

        <div className="metric-row">
          <span>Frames Sent:</span>
          <span>{streamingStats?.framesSent || 0}</span>
        </div>

        <div className="metric-row">
          <span>Frames Received:</span>
          <span>{streamingStats?.framesReceived || 0}</span>
        </div>

        {processedFrameData && processedFrameData.metadata && (
          <>
            <div className="metric-row">
              <span>Processing Time:</span>
              <span>
                {processedFrameData.metadata.processing_time_ms?.toFixed(1) ||
                  0}
                ms
              </span>
            </div>

            <div className="metric-row">
              <span>Total Latency:</span>
              <span>
                {processedFrameData.metadata.total_pipeline_time_ms?.toFixed(
                  1
                ) || 0}
                ms
              </span>
            </div>

            <div className="metric-row">
              <span>Landmarks Detected:</span>
              <span>
                {processedFrameData.metadata.landmarks_detected
                  ? Object.entries(
                      processedFrameData.metadata.landmarks_detected
                    )
                      .filter(([_, detected]) => detected)
                      .map(([type, _]) => type)
                      .join(", ") || "None"
                  : "None"}
              </span>
            </div>
          </>
        )}
      </div>

      <div className="performance-tips">
        <h5>💡 Tips</h5>
        <ul>
          <li>Ensure good lighting for better detection</li>
          <li>Keep hands visible in frame</li>
          <li>Close other applications to free resources</li>
        </ul>
      </div>
    </div>
  );
};

export default PerformanceMonitorSimple;
