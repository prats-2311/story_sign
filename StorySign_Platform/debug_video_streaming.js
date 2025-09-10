// Debug script to test video streaming activation flow
// Run this in browser console on ASL World page

console.log("=== Video Streaming Debug ===");

// Check current state
console.log("Current state:");
console.log("- webcamActive:", window.webcamActive);
console.log("- streamingActive:", window.streamingActive);
console.log("- connectionStatus:", window.connectionStatus);
console.log("- streamingConnectionStatus:", window.streamingConnectionStatus);

// Check if video elements exist
const webcamVideo = document.querySelector("video");
const processedCanvas = document.querySelector(".processed-video-canvas");

console.log("DOM elements:");
console.log("- Webcam video element:", webcamVideo);
console.log("- Processed video canvas:", processedCanvas);

if (webcamVideo) {
  console.log("- Video src:", webcamVideo.src);
  console.log("- Video readyState:", webcamVideo.readyState);
  console.log("- Video paused:", webcamVideo.paused);
}

if (processedCanvas) {
  console.log("- Canvas width:", processedCanvas.width);
  console.log("- Canvas height:", processedCanvas.height);
}

// Check WebSocket connection
console.log("WebSocket status:");
const wsConnections = [];
if (window.WebSocket) {
  // This is a simplified check - actual WebSocket would be in VideoStreamingClient
  console.log("- WebSocket constructor available");
}

console.log("=== End Debug ===");
