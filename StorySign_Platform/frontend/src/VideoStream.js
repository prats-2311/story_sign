// src/VideoStream.js
import React from 'react';
import WebcamCapture from './WebcamCapture';
import VideoStreamingClient from './VideoStreamingClient';
import ProcessedVideoDisplay from './ProcessedVideoDisplay';

const VideoStream = ({
  webcamActive,
  streamingActive,
  onFrameCapture,
  videoStreamingRef,
  onConnectionChange,
  onProcessedFrame,
  onError,
  processedFrameData,
  streamingConnectionStatus,
  streamingStats,
  onRetryConnection,
}) => {
  return (
    <div className="video-stream-container">
      {/* Webcam Capture Component (sends frames) */}
      <WebcamCapture
        isActive={webcamActive}
        onFrameCapture={onFrameCapture}
        onError={onError}
      />

      {/* WebSocket Client (manages connection) */}
      <VideoStreamingClient
        ref={videoStreamingRef}
        isActive={streamingActive}
        onConnectionChange={onConnectionChange}
        onProcessedFrame={onProcessedFrame}
        onError={onError}
      />

      {/* Processed Video Display (receives and shows frames) */}
      <ProcessedVideoDisplay
        processedFrameData={processedFrameData}
        connectionStatus={streamingConnectionStatus}
        streamingStats={streamingStats}
        onRetryConnection={onRetryConnection}
        isActive={streamingActive}
      />
    </div>
  );
};

export default VideoStream;
