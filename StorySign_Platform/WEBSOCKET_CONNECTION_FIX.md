# WebSocket Connection Fix for MediaPipe Video Stream

## Problem Analysis

The MediaPipe video stream with skeleton and landmarks is not showing after story generation due to WebSocket connection issues. The error messages show:

1. "WebSocket not connected, cannot send frame"
2. "Disconnected - Not connected to video processing server"

## Root Cause

The WebSocket connection is being lost after story generation, likely due to:

1. Connection timeout during story generation process
2. Missing keepalive mechanism during long operations
3. Connection state not being properly maintained

## Solution Implementation

### 1. Enhanced WebSocket Connection Management

The WebSocket connection needs better resilience during story generation:

- Add keepalive messages during story generation
- Implement automatic reconnection after story generation
- Improve connection state management
- Add connection health checks

### 2. Story Generation Integration Fix

The story generation process should not interfere with the WebSocket connection:

- Maintain WebSocket connection during story generation
- Send periodic keepalive messages
- Handle connection recovery after story generation

### 3. Frontend Connection Recovery

The frontend should automatically recover the WebSocket connection:

- Detect connection loss after story generation
- Automatically attempt reconnection
- Maintain video streaming state

## Implementation Steps

1. Fix WebSocket keepalive during story generation
2. Add automatic reconnection logic
3. Improve connection state management
4. Test connection recovery after story generation
