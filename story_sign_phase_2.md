This is the plan to build the complete **"StorySign ASL World"**.

---

# **StorySign: Final Implementation Plan (ASL World)**

**Objective:** To build the complete, interactive user experience for the "StorySign ASL World" module. This plan integrates a hybrid AI model for story generation (local vision + cloud LLM) and implements the sentence-by-sentence practice loop on top of the existing, high-performance streaming platform.

## **Phase 1: Hybrid AI Story Generation**

**Goal:** Implement the "Scan Object" feature, allowing users to generate a story by showing an object to the camera. This leverages the hybrid AI architecture defined in the blueprint.

- **Task 1: Backend - Local Vision Endpoint**

  - **Sub-task 1.1:** Configure a local vision model (e.g., `moondream2` or `phi3:vision`) via Ollama or LM Studio. Ensure it is running and accessible.
  - **Sub-task 1.2:** In `backend/config.yaml`, add the URL for this local vision model service.
  - **Sub-task 1.3:** Create a new file, `backend/local_vision_service.py`. Implement a service that can take a base64-encoded image and get a one-word identification from the local model.
  - **Sub-task 1.4:** In `backend/main.py`, create a new endpoint: `POST /api/story/recognize_and_generate`. This endpoint will:
    1.  Receive an image from the frontend.
    2.  Call the `local_vision_service` to identify the object.
    3.  Call the existing `OllamaService.generate_story` method (from the previous plan) using the identified word.
    4.  Return the complete, generated story.

- **Task 2: Frontend - "Scan Object" UI and Logic**
  - **Sub-task 2.1:** In `frontend/App.js`, create a new state variable to manage the story generation flow (e.g., `storyState`).
  - **Sub-task 2.2:** Add a "Scan Object to Start" button to the UI.
  - **Sub-task 2.3:** When clicked, this button will trigger a function in `WebcamCapture.js` to capture a single, high-quality frame and pass it up to `App.js`.
  - **Sub-task 2.4:** `App.js` will then call the new `/api/story/recognize_and_generate` backend endpoint with this frame.
  - **Sub-task 2.5:** Upon receiving the story, `App.js` will update its state and pass the sentences to the new `ASLWorldModule.js` component.

## **Phase 2: Sentence-by-Sentence Practice Loop**

**Goal:** Implement the core learning loop where the user practices one sentence at a time and receives targeted feedback.

- **Task 3: Backend - Gesture Segmentation and Analysis**

  - **Sub-task 3.1:** In `backend/video_processor.py`, enhance the `VideoProcessingService` to make it stateful for gesture analysis. Add state variables like `is_practicing`, `target_sentence`, `landmark_buffer`, and `is_signing`.
  - **Sub-task 3.2:** Implement the gesture segmentation logic. Use hand movement velocity or displacement from the MediaPipe landmarks to detect the start of a signing motion (transitioning `is_signing` to `True`) and a subsequent pause to detect the end.
  - **Sub-task 3.3:** While `is_signing` is `True`, collect all landmark data for that period into the `landmark_buffer`.
  - **Sub-task 3.4:** When the sign is complete, asynchronously call the `OllamaService.analyze_signing_attempt` method, passing the `landmark_buffer` and the `target_sentence`.
  - **Sub-task 3.5:** Broadcast the returned feedback from the LLM via the WebSocket using the typed message format we designed: `{"type": "asl_feedback", "data": ...}`.

- **Task 4: Frontend - Interactive Learning UI**

  - **Sub-task 4.1:** Create the main UI component: `frontend/ASLWorldModule.js`.
  - **Sub-task 4.2:** This component will receive the array of story sentences as a prop. It will manage its own state for `currentSentenceIndex` and `latestFeedback`.
  - **Sub-task 4.3:** The UI will display the full story but visually highlight the sentence at the `currentSentenceIndex`. The `ProcessedVideoDisplay` component will be active.
  - **Sub-task 4.4:** Create a dedicated area in this component to display the `latestFeedback` string.
  - **Sub-task 4.5:** Add "Next Sentence" and "Try Again" buttons. "Next Sentence" will increment the `currentSentenceIndex`. "Try Again" will clear the `latestFeedback` and allow the user to make another attempt.

- **Task 5: Frontend - State Management and WebSocket Integration**
  - **Sub-task 5.1:** In `frontend/VideoStreamingClient.js`, ensure the `onmessage` handler correctly parses the `asl_feedback` message type.
  - **Sub-task 5.2:** Use a callback to pass the feedback data up to `App.js`, which then passes it down as a prop to `ASLWorldModule.js`.
  - **Sub-task 5.3:** When the "Next Sentence" button is clicked in `ASLWorldModule.js`, it should notify the backend via a new WebSocket message (e.g., `{"type": "control", "action": "next_sentence", "index": ...}`) so the `VideoProcessingService` knows which sentence to analyze next.

## **Phase 3: Final Polish and Integration**

**Goal:** Ensure a smooth, intuitive, and robust user experience.

- **Task 6: Comprehensive Testing**

  - **Sub-task 6.1:** Write a new backend integration test (`pytest`) that simulates a full session: call the recognize endpoint, receive a story, and then send mock landmark data through the WebSocket to verify that the analysis and feedback loop works.
  - **Sub-task 6.2:** Manually perform end-to-end testing of the entire user journey. Use the `PerformanceMonitor.js` to ensure the new AI API calls do not negatively impact the application's responsiveness.

- **Task 7: UI/UX Refinements**
  - **Sub-task 7.1:** Add clear loading indicators in the frontend for when the local vision model is recognizing an object and when the cloud LLM is generating a story or feedback.
  - **Sub-task 7.2:** Design clear visual cues to show the user when the application is actively listening for a sign and when it is processing.
  - **Sub-task 7.3:** Ensure all error states (e.g., object not recognized, API call failed) are handled gracefully with user-friendly messages.
