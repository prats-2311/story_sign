import React from "react";
import { useNavigate } from "react-router-dom";
import { ASLWorldModule } from "../modules";
import { VideoStream } from "../components";

const ASLWorldPage = ({
  storyData,
  selectedStory,
  onStorySelect,
  currentSentenceIndex,
  latestFeedback,
  onStoryGenerate,
  onPracticeControl,
  isGeneratingStory,
  isProcessingFeedback,
  connectionStatus,
  onFrameCapture,
  gestureState,
  practiceStarted,
  onStartPractice,
  videoStreamingRef,
  processedFrameData,
  streamingConnectionStatus,
  optimizationSettings,
  onOptimizationChange,
  webcamActive,
  streamingActive,
  onConnectionChange,
  onProcessedFrame,
  onError,
  onRetryConnection,
  storyGenerationError,
  setStoryGenerationError,
}) => {
  const navigate = useNavigate();

  const handleBackToMain = () => {
    navigate("/");
  };

  return (
    <div className="asl-world-container">
      <div className="asl-world-header">
        <button className="back-to-main-btn" onClick={handleBackToMain}>
          ← Back to Main
        </button>
      </div>
      <ASLWorldModule
        storyData={storyData}
        selectedStory={selectedStory}
        onStorySelect={onStorySelect}
        currentSentenceIndex={currentSentenceIndex}
        latestFeedback={latestFeedback}
        onStoryGenerate={onStoryGenerate}
        onPracticeControl={onPracticeControl}
        isGeneratingStory={isGeneratingStory}
        isProcessingFeedback={isProcessingFeedback}
        connectionStatus={connectionStatus}
        onFrameCapture={onFrameCapture}
        gestureState={gestureState}
        practiceStarted={practiceStarted}
        onStartPractice={onStartPractice}
        streamingStats={{
          framesSent: videoStreamingRef.current?.framesSent || 0,
          framesReceived: videoStreamingRef.current?.framesReceived || 0,
        }}
        processedFrameData={processedFrameData}
        streamingConnectionStatus={streamingConnectionStatus}
        optimizationSettings={optimizationSettings}
        onOptimizationChange={onOptimizationChange}
      >
        <VideoStream
          webcamActive={webcamActive}
          streamingActive={streamingActive}
          onFrameCapture={onFrameCapture}
          videoStreamingRef={videoStreamingRef}
          onConnectionChange={onConnectionChange}
          onProcessedFrame={onProcessedFrame}
          onError={onError}
          processedFrameData={processedFrameData}
          streamingConnectionStatus={streamingConnectionStatus}
          onRetryConnection={onRetryConnection}
          hideWebcamPreview={practiceStarted}
        />
      </ASLWorldModule>
      {storyGenerationError && (
        <div className="story-generation-error">
          <p className="error-text">
            Story Generation Error: {storyGenerationError}
          </p>
          <button
            className="retry-btn"
            onClick={() => setStoryGenerationError("")}
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};

export default ASLWorldPage;
