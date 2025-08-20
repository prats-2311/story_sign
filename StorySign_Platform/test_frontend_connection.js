#!/usr/bin/env node
/**
 * Test frontend WebSocket connection to MediaPipe backend
 */

const WebSocket = require("ws");

function testConnection() {
  console.log("🔌 Testing WebSocket connection to MediaPipe backend...");

  const ws = new WebSocket("ws://localhost:8000/ws/video");

  ws.on("open", function open() {
    console.log("✅ WebSocket connected successfully!");
    console.log("📤 Sending test message...");

    // Send a simple test message
    const testMessage = {
      type: "test",
      message: "Frontend connection test",
    };

    ws.send(JSON.stringify(testMessage));

    // Close after 2 seconds
    setTimeout(() => {
      console.log("🔌 Closing connection...");
      ws.close();
    }, 2000);
  });

  ws.on("message", function message(data) {
    console.log("📥 Received message:", data.toString());
  });

  ws.on("error", function error(err) {
    console.log("❌ WebSocket error:", err.message);
  });

  ws.on("close", function close() {
    console.log("🔌 WebSocket connection closed");
  });
}

testConnection();
