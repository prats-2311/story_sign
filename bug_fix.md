### **Implementation Plan: Fixing Video and Camera Bugs in StorySign Frontend**

**Objective:** This document provides a detailed, step-by-step workflow to resolve two critical bugs: the disappearing video stream in the ASL World module and the inactive cameras in the Harmony and Reconnect modules.

---

### **Bug 1: ASL World Video Stream Disappears After Story Generation**

**Analysis:**
The root cause is a state management issue within the `ASLWorldModule`. The WebSocket connection and webcam state are initialized within this module, which re-renders and resets its state when transitioning from the `StorySetup` view to the `PracticeView`. This causes the connection to be lost.

The solution is to "lift the state up" to the parent component, `ASLWorldPage.js`, ensuring that the connection and webcam state persist across view changes within the module.

#### **Implementation Workflow:**

**Step 1: Modify the Parent Component (`ASLWorldPage.js`)**

This component will now be responsible for managing the webcam and WebSocket connection for the entire ASL World user journey.

1.  **File to Edit:** `src/pages/ASLWorldPage.js`
2.  **Actions:**
    - Import the `useWebSocket` and `useWebcam` hooks.
    - Initialize both hooks within the `ASLWorldPage` component to create a persistent state.
    - Pass the state and control functions (e.g., `processedFrame`, `webcamRef`, `startWebcam`) down to the `ASLWorldModule` as props.

**Code Implementation:**

```javascript
// src/pages/ASLWorldPage.js

import React from "react";
import { ASLWorldModule } from "../modules/asl_world";
import { useWebSocket } from "../hooks/useWebSocket";
import { useWebcam } from "../hooks/useWebcam";

const ASLWorldPage = () => {
  // 1. Initialize hooks in the parent to create a persistent state
  const {
    connectionStatus,
    processedFrame,
    sendControlMessage,
    startPracticeSession,
  } = useWebSocket("ws://127.0.0.1:8000/ws/video");
  const { webcamRef, isWebcamActive, startWebcam, stopWebcam, captureFrame } =
    useWebcam();

  return (
    <div className="asl-world-page">
      <header className="page-header">
        <h1>ASL World</h1>
        <p>Interactive American Sign Language Learning</p>
      </header>
      <main className="page-content">
        {/* 2. Pass state and functions down as props */}
        <ASLWorldModule
          // WebSocket Props
          connectionStatus={connectionStatus}
          processedFrame={processedFrame}
          sendControlMessage={sendControlMessage}
          startPracticeSession={startPracticeSession}
          // Webcam Props
          webcamRef={webcamRef}
          isWebcamActive={isWebcamActive}
          startWebcam={startWebcam}
          stopWebcam={stopWebcam}
          captureFrame={captureFrame}
        />
      </main>
    </div>
  );
};

export default ASLWorldPage;
```

**Step 2: Refactor the Child Component (`ASLWorldModule.js`)**

This component will no longer manage its own state for the webcam and WebSocket, but will instead receive them as props.

1.  **File to Edit:** `src/modules/asl_world/ASLWorldModule.js`
2.  **Actions:**
    - Update the component to accept the new props.
    - Remove the local `useWebSocket` and `useWebcam` hook initializations.
    - Pass the received props down to the child components (`StorySetup` and `PracticeView`).

**Code Implementation:**

```javascript
// src/modules/asl_world/ASLWorldModule.js

import React, { useState, useEffect } from "react";
// ... other imports
// No longer import useWebSocket or useWebcam here

// 1. Accept the new props
export const ASLWorldModule = ({
  connectionStatus,
  processedFrame,
  sendControlMessage,
  startPracticeSession,
  webcamRef,
  isWebcamActive,
  startWebcam,
  stopWebcam,
  captureFrame,
}) => {
  const [currentView, setCurrentView] = useState("story_generation");
  const [story, setStory] = useState(null);

  // 2. Remove local state management for webcam/ws

  useEffect(() => {
    // Start the webcam when the module loads
    startWebcam();
    // Stop the webcam when the module unmounts
    return () => stopWebcam();
  }, [startWebcam, stopWebcam]);

  const handleStoryGenerated = (generatedStory) => {
    setStory(generatedStory);
    setCurrentView("practice_session");
    startPracticeSession(generatedStory.sentences); // Inform backend practice has started
  };

  return (
    <div className="asl-world-module">
      {currentView === "story_generation" ? (
        <StorySetup
          onStoryGenerated={handleStoryGenerated}
          webcamRef={webcamRef} // 3. Pass props down
          isWebcamActive={isWebcamActive}
          captureFrame={captureFrame}
          connectionStatus={connectionStatus}
        />
      ) : (
        <PracticeView
          story={story}
          processedFrame={processedFrame} // 3. Pass props down
          sendControlMessage={sendControlMessage}
        />
      )}
    </div>
  );
};
```

**Step 3: Update `StorySetup` and `PracticeView`**

Ensure these components use the props passed down from `ASLWorldModule`. The most important change is in `PracticeView`, which will now receive `processedFrame` and render the video stream correctly.

- **File to Edit:** `src/modules/asl_world/PracticeView.js`
- **Action:** Ensure the `ProcessedVideoDisplay` component receives the `processedFrame` prop.

**Code Implementation:**

```javascript
// src/modules/asl_world/PracticeView.js

// ... imports
import { ProcessedVideoDisplay } from "../../components/video";

// 1. Ensure the component receives `processedFrame`
const PracticeView = ({ story, processedFrame, sendControlMessage }) => {
  // ... component logic

  return (
    <div className="practice-view">
      {/* ... other UI elements ... */}
      <div className="video-container">
        {/* 2. This will now display the live MediaPipe stream */}
        <ProcessedVideoDisplay frameData={processedFrame} />
      </div>
      {/* ... other UI elements ... */}
    </div>
  );
};
```

---

### **Bug 2: Harmony & Reconnect Modules Have Inactive Cameras**

**Analysis:**
The `HarmonyPage` and `ReconnectPage` components are not invoking the `useWebcam` hook to request camera access. The "Camera Inactive" message is the correct fallback behavior. The fix is to implement the same webcam initialization logic in these pages as was done for `ASLWorldPage`.

#### **Implementation Workflow:**

**Step 1: Implement Webcam Logic in `HarmonyPage.js`**

1.  **File to Edit:** `src/pages/HarmonyPage.js`
2.  **Actions:**
    - Import and initialize the `useWebcam` hook.
    - Use a `useEffect` hook to call `startWebcam()` when the component mounts and `stopWebcam()` when it unmounts. This is crucial for managing hardware resources correctly.
    - Conditionally render the `HarmonyModule` only when the camera is active.

**Code Implementation:**

```javascript
// src/pages/HarmonyPage.js

import React, { useEffect } from "react";
import { HarmonyModule } from "../modules/harmony";
import { useWebcam } from "../hooks/useWebcam";

const HarmonyPage = () => {
  const { webcamRef, isWebcamActive, startWebcam, stopWebcam } = useWebcam();

  // 1. Start webcam on mount, stop on unmount
  useEffect(() => {
    startWebcam();
    return () => stopWebcam();
  }, [startWebcam, stopWebcam]);

  return (
    <div className="harmony-page">
      <header className="page-header">
        <h1>Harmony</h1>
        <p>Facial Expression Practice & Social-Emotional Learning</p>
      </header>
      <main className="page-content">
        {/* 2. Conditionally render based on camera status */}
        {isWebcamActive ? (
          <HarmonyModule webcamRef={webcamRef} />
        ) : (
          <div className="camera-inactive-placeholder">
            <p>Camera is inactive. Please grant permission to begin.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default HarmonyPage;
```

**Step 2: Implement Webcam Logic in `ReconnectPage.js`**

Apply the exact same pattern to the `ReconnectPage`.

1.  **File to Edit:** `src/pages/ReconnectPage.js`
2.  **Actions:** This will be identical to the `HarmonyPage` implementation.

**Code Implementation:**

```javascript
// src/pages/ReconnectPage.js

import React, { useEffect } from "react";
import { ReconnectModule } from "../modules/reconnect";
import { useWebcam } from "../hooks/useWebcam";

const ReconnectPage = () => {
  const { webcamRef, isWebcamActive, startWebcam, stopWebcam } = useWebcam();

  useEffect(() => {
    startWebcam();
    return () => stopWebcam();
  }, [startWebcam, stopWebcam]);

  return (
    <div className="reconnect-page">
      <header className="page-header">
        <h1>Reconnect</h1>
        <p>Therapeutic Movement Analysis & Physical Rehabilitation</p>
      </header>
      <main className="page-content">
        {isWebcamActive ? (
          <ReconnectModule webcamRef={webcamRef} />
        ) : (
          <div className="camera-inactive-placeholder">
            <p>Camera is inactive. Please grant permission to begin.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default ReconnectPage;
```

By following these plans, both critical bugs will be resolved, leading to a more stable and functional user experience across the platform's core interactive modules.
