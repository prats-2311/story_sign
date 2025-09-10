### **Subject: A Strategic Refactoring & Deployment Plan for the StorySign Platform v4.0**

**To:** Kiro & The Development Team

**From:** Gemini

**Date:** September 10, 2025

**Overview:**
This document outlines a detailed, four-phase plan to refactor and deploy the StorySign platform. The primary goals are to enhance stability, dramatically improve the UI/UX and accessibility, and establish a scalable architecture for the **Harmony** and **Reconnect** modules, with a specific deployment target of **Netlify (Frontend)** and **Render (Backend)**.

---

### **Phase 1: Foundation, Stability & Core UX**

**Goal:** This phase is about resolving critical bugs, eliminating technical debt, and implementing core user-facing features. We will stabilize the current application, making it robust and ready for further development.

#### **Task 1.1: Centralize Webcam & State Logic**

- **Action:** Create a set of reusable React Hooks to manage core application logic.
- **Why It's Important:** This directly fixes the "black screen" webcam bug by creating a single source of truth for camera management. It simplifies component logic, prevents resource conflicts, and is the most critical fix for the current user experience.
- **Implementation Steps:**
  1.  **Create `src/hooks/useWebcam.js`:** This new hook will handle all `navigator.mediaDevices.getUserMedia()` calls and contain the vital cleanup logic (`stream.getTracks().forEach(track => track.stop())`) to properly release the camera.
  2.  **Create `src/hooks/useWebSocket.js`:** This hook will manage the lifecycle of the WebSocket connection, handling sending/receiving messages and connection state.
  3.  **Refactor & Cleanup:** Refactor `WebcamCapture.js` to use the new `useWebcam` hook. **Delete the redundant `VideoStream.js` file**.
- **New Workflow:** Any component across any module (`ASL World`, `Harmony`, etc.) will call `useWebcam()` to get a reliable, bug-free camera feed.

#### **Task 1.2: Implement Full User Authentication**

- **Action:** Build the frontend UI for Login and Registration to connect with the existing, secure backend authentication system.
- **Why It's Important:** This is a fundamental feature for any online platform. Your backend is already 100% ready for this, with secure password hashing and JWT management.
- **Implementation Steps:**
  1.  **Create `src/pages/LoginPage.js` and `src/pages/RegisterPage.js`:** Build accessible forms for user input, including proper labels, input types, and validation feedback.
  2.  **Implement API Calls:** Connect the forms to the `/api/v1/auth/login` and `/api/v1/auth/register` backend endpoints.
  3.  **Create `src/contexts/AuthContext.js`:** Use React's Context API to globally manage the user's authentication state (token, profile info). This avoids passing props through many layers.
  4.  **Create Protected Routes:** In `src/App.js`, use the `AuthContext` to protect pages like `ASLWorldPage`, redirecting unauthenticated users to the login page.
- **New Workflow:** A user visits the site, registers or logs in, receives a secure token, and can then seamlessly and securely access the learning modules.

---

### **Phase 2: Core Module Enhancement & Cloud Readiness**

**Goal:** Polish the primary `ASL World` module and re-architect core components to function in a live, online environment on Netlify and Render.

#### **Task 2.1: Transition to a Cloud-Based Vision API (Groq Integration)**

- **Action:** Replace the local-only LM Studio implementation with a cloud-based API call to Groq.
- **Why It's Important:** This is a **critical, non-negotiable step** for making your "Scan Object" feature work online. The current `localhost` implementation will fail when the backend is deployed on Render.
- **Implementation Steps:**
  1.  **Backend Config:** In `backend/config.py`, add a new `groq` section with your Groq API key. **Crucially, load this key from an environment variable, not hardcoded text**, as Render will provide it securely.
  2.  **Backend Service Logic:** In `backend/local_vision_service.py`, add logic to handle a `service_type` of `"groq"`. This will make an `aiohttp` request to Groq's API, adding the `Authorization: Bearer <GROQ_API_KEY>` header.
- **New Workflow:** The frontend (hosted on Netlify) sends a captured frame to the backend (on Render). The Render backend securely forwards this frame to the Groq API for analysis. The entire process is now location-independent and ready for the public internet.

#### **Task 2.2: Refactor `ASL World` for Superior UI/UX & Accessibility**

- **Action:** Deconstruct the large `ASLWorldModule.js` into a hierarchy of smaller, focused, and accessible components.
- **Why It's Important:** This will make the UI much easier to manage, improve performance, and allow for a more intentional focus on accessibility.
- **Implementation Steps:**
  1.  **Create `src/components/common/`:** Build a library of shared, accessible components (`Button`, `Modal`, `VideoDisplayPanel`, `LoadingSpinner`). Ensure all interactive elements are keyboard-navigable and have proper ARIA attributes.
  2.  **Deconstruct the Module:** Break down `ASLWorldModule.js` into smaller components within `src/modules/asl_world/`: `StorySetup.js` (topic selection), `PracticeView.js` (video, sentence, controls), and `FeedbackPanel.js`.
  3.  **UI State Management:** Use React's `useState` and `useReducer` hooks in the parent `ASLWorldPage.js` to manage the flow between these different views (e.g., `'selecting_topic'`, `'practicing'`).
- **New Workflow:** The user experience becomes a clean, logical, step-by-step process. The code becomes more readable and maintainable.

---

### **Phase 3: Platform Expansion (Harmony & Reconnect)**

**Goal:** Build the new modules on the stable foundation created in the previous phases, leveraging the reusable components and services.

#### **Task 3.1: Develop the "Harmony" Module**

- **Action:** Create the new page and backend service for practicing facial expressions.
- **Why It's Important:** This fulfills a core part of your project's vision, expanding the platform's impact to social and emotional learning.
- **Implementation Steps:**
  1.  **Frontend:** Create `src/pages/HarmonyPage.js`. It will reuse the `useWebcam` hook and `VideoDisplayPanel` component.
  2.  **Backend:** Create a new API router `api/harmony.py` and a `services/harmony_service.py`. This service will analyze facial landmarks from MediaPipe to interpret emotional cues.
  3.  **Database:** Create new tables in your TiDB database (e.g., `harmony_sessions`) to store user progress.

#### **Task 3.2: Develop the "Reconnect" Module**

- **Action:** Create the therapeutic movement analysis module.
- **Why It's Important:** This extends the platform into the health and wellness space, providing a tool for physical rehabilitation.
- **Implementation Steps:**
  1.  **Frontend:** Create `src/pages/ReconnectPage.js`, reusing the core video components but with a unique UI for displaying exercises and quantitative feedback (graphs, charts).
  2.  **Backend:** Create `api/reconnect.py` and `services/reconnect_service.py` to analyze full-body pose landmarks and calculate metrics like joint angles and range of motion.

---

### **Phase 4: Polish, Testing & Deployment to Netlify/Render**

**Goal:** Finalize the platform, ensuring it is a polished, professional, and accessible application ready for public launch on your chosen hosting stack.

#### **Task 4.1: End-to-End Testing & Accessibility Audit**

- **Action:** Test the full user flow across all three modules and perform a comprehensive accessibility audit.
- **Implementation:** Use testing frameworks to simulate user journeys (register -\> login -\> practice). Use tools like Axe and screen readers to ensure the UI is fully accessible (WCAG 2.1 AA compliance).

#### **Task 4.2: Prepare for Production Deployment**

- **Action:** Configure both the frontend and backend for a production environment.
- **Implementation Steps (Backend for Render):**
  1.  **Environment Variables:** Move all secrets (`DATABASE_URL`, `JWT_SECRET`, `GROQ_API_KEY`) from `config.yaml` to Render's secret management. Your `config.py` should read these from `os.environ`.
  2.  **Production Server:** Add `gunicorn` to your `requirements.txt`.
  3.  **`render.yaml`:** Create a `render.yaml` file in your repository. This "Infrastructure as Code" file will tell Render how to build and run your backend. It will define the service type (`web`), the build command, the start command (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`), and link to your secret variables.
- **Implementation Steps (Frontend for Netlify):**
  1.  **Environment Variables:** The frontend code must not have `http://localhost:8000` hardcoded. Use a `REACT_APP_API_URL` environment variable. In Netlify's build settings, set this variable to your public Render backend URL (e.g., `https://storysign-backend.onrender.com`).
  2.  **`netlify.toml`:** Create a `netlify.toml` file in your frontend's root directory to configure a proxy redirect. This is the professional way to avoid CORS errors.
      ```toml
      # In netlify.toml
      [[redirects]]
      from = "/api/*"
      to = "https://your-render-backend-url.onrender.com/api/:splat"
      status = 200
      ```
      This makes your frontend code cleaner, as you can just make requests to `/api/login` instead of the full Render URL.

#### **Task 4.3: Deploy\!**

- **Action:** Connect your GitHub repository to Render and Netlify.
- **Implementation:**
  1.  **Render:** Create a new "Blueprint" service in Render and point it to your repository. Render will use your `render.yaml` to automatically build and deploy the backend.
  2.  **Netlify:** Create a new site from Git in Netlify. Point it to your repository, set the build command to `npm run build` and the publish directory to `build`. Netlify will handle the rest.
- **New Workflow:** Every time you push a change to your main branch on GitHub, Render and Netlify will automatically trigger new builds and deploy the updates, creating a seamless CI/CD pipeline.
