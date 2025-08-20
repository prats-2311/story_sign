# **StorySign: Week 2 Implementation Plan (Vertical Slice)**

**Objective:** To build a simple but fully functional end-to-end version of the core "StorySign ASL World" loop by the end of Saturday, August 23rd. This "vertical slice" will prove that the React UI, FastAPI backend, and MediaPipe Python code can all communicate successfully.

## **Day 1: Wednesday, August 20 \- The Backend Foundation**

**Goal:** Create and run a basic FastAPI server with a single test endpoint.

- **Task 1: Project Setup**
  - **Sub-task 1.1:** Create a main project folder named StorySign_Platform.
  - **Sub-task 1.2:** Inside StorySign_Platform, create a new folder named backend.
  - **Sub-task 1.3:** Open the backend folder in your Kiro IDE.
- **Task 2: Environment & Dependencies**
  - **Sub-task 2.1:** Open the integrated terminal in Kiro IDE.
  - **Sub-task 2.2:** Create and activate your story_sign_v2 conda environment (conda activate story_sign_v2).
  - **Sub-task 2.3:** Install FastAPI and Uvicorn: pip install fastapi uvicorn\[standard\].
- **Task 3: Create the "Hello World" API**
  - **Sub-task 3.1:** Create a new file named main.py.
  - **Sub-task 3.2:** Write the basic FastAPI code for a single endpoint / that returns a JSON message {"message": "Hello from the StorySign Backend\!"}.
  - **Kiro IDE Power-Up:**
    - Use Kiro's **AI Chat** or **inline code generation**. Type a comment like \# create a fastapi endpoint for GET / and let Kiro generate the boilerplate code for you. This is a great, simple way to start documenting your use of the IDE's features.
- **Task 4: Run and Test the Server**
  - **Sub-task 4.1:** In the Kiro terminal, run the server: uvicorn main:app \--reload.
  - **Sub-task 4.2:** Open your web browser and navigate to http://127.0.0.1:8000.
  - **Goal:** You should see the JSON message {"message": "Hello from the StorySign Backend\!"}.

## **Day 2: Thursday, August 21 \- The Frontend & The Bridge**

**Goal:** Create a basic Electron/React UI that can successfully call the backend API.

- **Task 1: Project Setup**
  - **Sub-task 1.1:** In your main StorySign_Platform folder, create a new folder named frontend.
  - **Sub-task 1.2:** Use a standard tool like create-react-app with an Electron template to initialize your project inside the frontend folder.
  - **Sub-task 1.3:** Open the frontend folder in a new Kiro IDE window.
- **Task 2: Build the Basic UI**
  - **Sub-task 2.1:** Modify the main App.js (or App.tsx) component.
  - **Sub-task 2.2:** Create a simple UI with a title "StorySign," a \<div\> to display a message, and a \<button\> with the text "Test Backend."
  - **Kiro IDE Power-Up:**
    - Use Kiro's **spec-driven development**. Write a simple spec in a text file: "The main page should have a title, a button, and a text area for a message." Use Kiro's AI to generate the React component structure from this spec. This is a major feature to highlight for the hackathon.
- **Task 3: Implement the API Call**
  - **Sub-task 3.1:** Write a JavaScript function that is triggered when the button is clicked.
  - **Sub-task 3.2:** Inside this function, use the fetch API to make a GET request to your running backend at http://127.0.0.1:8000.
  - **Sub-task 3.3:** Use React state (e.g., useState) to store the message received from the backend.
  - **Sub-task 3.4:** Display this state variable in the message \<div\>.
- **Task 4: End-to-End Test**
  - **Sub-task 4.1:** Make sure your FastAPI server from Day 1 is running.
  - **Sub-task 4.2:** Run your React/Electron application.
  - **Goal:** Click the "Test Backend" button. The message on the screen should change to "Hello from the StorySign Backend\!".

## **Day 3: Friday, August 22 \- The Core Vision Integration**

**Goal:** Integrate the MediaPipe Python code and display the live, tracked video feed inside the React UI. This is the most complex task.

- **Task 1: Backend \- Create a WebSocket Endpoint**
  - **Sub-task 1.1:** Modify your FastAPI main.py. A simple HTTP request isn't fast enough for video. We need a WebSocket for a continuous stream.
  - **Sub-task 1.2:** Create a new WebSocket endpoint (e.g., /ws/video).
  - **Sub-task 1.3:** Write the Python code that will:
    1. Open the webcam using OpenCV.
    2. Run the MediaPipe Holistic model on each frame.
    3. Draw the landmarks on the frame.
    4. Encode the processed frame into a format that can be sent over the WebSocket (like a base64 encoded JPEG).
    5. Stream these encoded frames to any connected frontend client.
  - **Kiro IDE Power-Up:**
    - This is complex code. Use Kiro's **AI Chat** with context awareness. Open your MediaPipe Jupyter Notebook and your main.py. Ask the chat: "Based on the code in my notebook, can you help me refactor this into a FastAPI WebSocket endpoint that streams processed video frames?"
- **Task 2: Frontend \- Display the Video Stream**
  - **Sub-task 2.1:** In your React app, create a new component for the video display.
  - **Sub-task 2.2:** Write the JavaScript code to open a WebSocket connection to your backend's /ws/video endpoint.
  - **Sub-task 2.3:** As your component receives the base64 encoded image strings, update an \<img\> tag's src attribute to display them, creating a live video effect.
- **Task 3: Integration Test**
  - **Goal:** Run both the backend and frontend. You should see a window in your application showing your live webcam feed with the MediaPipe skeletons drawn perfectly over your hands, face, and body.

## **Day 4: Saturday, August 23 \- Buffer & Refinement**

**Goal:** Debug any issues from Day 3 and clean up the code.

- **Task 1: Debugging:** The video stream integration can be tricky. Use this day to solve any latency issues or connection problems.
- **Task 2: Code Cleanup:** Use Kiro's AI features to add comments, refactor complex functions, and ensure your code is clean and readable.
- **Task 3: Documentation:** Write a preliminary README.md file for both the frontend and backend, explaining how to run the project. You can ask Kiro's AI Chat to help you write this based on your code.

By the end of Saturday, you will have a working, end-to-end prototype that proves your architecture is sound and ready for the next phase of feature development.
