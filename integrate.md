### **Subject: Action Plan for Activating the Refactored StorySign Frontend**

**To:** Kiro

**From:** Prateek & Gemini

**Date:** September 10, 2025

**Overview:**
The refactoring of the StorySign frontend is complete. All new components, hooks, pages, and contexts have been built. This document outlines the final integration steps required to switch the application's entry point (`App.js`) from the old, monolithic view to the new, modular, and authenticated architecture.

By following these three steps, the entire updated application, including the new design and features, will become fully active.

---

### **Step 1: Set Up the Global Authentication State**

**Goal:** Wrap the entire application in the `AuthProvider`. This makes the user's login status and profile information available to all components.

**File to Modify:** `src/index.js`

**Instructions:**

Open `src/index.js` and import the `AuthProvider` from the new `AuthContext.js`. Then, wrap the `<App />` component with it.

**Code:**

```javascript
// In: src/index.js

import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import reportWebVitals from "./reportWebVitals";

// 1. Import the AuthProvider
import { AuthProvider } from "./contexts/AuthContext";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    {/* 2. Wrap the entire App component with the AuthProvider */}
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);

reportWebVitals();
```

---

### **Step 2: Implement the New Application Router in `App.js`**

**Goal:** This is the main step. We will replace the content of `App.js` with the new routing logic. This will enable the login page, protected routes, and the new `PlatformShell` that provides the consistent, modern UI.

**File to Modify:** `src/App.js`

**Instructions:**

Replace the **entire contents** of your current `src/App.js` file with the code below. This new code sets up all the URL routes and protects the learning modules, ensuring only logged-in users can access them.

**Code:**

```javascript
// In: src/App.js

import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";

// Import all the new pages
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ASLWorldPage from "./pages/ASLWorldPage";
import HarmonyPage from "./pages/HarmonyPage";
import ReconnectPage from "./pages/ReconnectPage";
import MainDashboard from "./pages/dashboard/MainDashboard";
import PlatformShell from "./components/shell/PlatformShell";

// Import global styles
import "./App.css";
import "./styles/accessibility.css";
import "./styles/responsive.css";

// This sub-component handles the main routing logic after we know the auth state
function AppContent() {
  const { isLoading } = useAuth();

  // Display a loading indicator while the AuthContext is checking for a stored token
  if (isLoading) {
    return <div>Loading Application...</div>;
  }

  return (
    <Routes>
      {/* Public routes for login and registration */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* This catch-all route handles all protected parts of the application */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <PlatformShell>
              <Routes>
                {/* Routes accessible only when logged in */}
                <Route path="/asl-world" element={<ASLWorldPage />} />
                <Route path="/harmony" element={<HarmonyPage />} />
                <Route path="/reconnect" element={<ReconnectPage />} />
                <Route path="/dashboard" element={<MainDashboard />} />

                {/* The default page after logging in is the dashboard */}
                <Route
                  path="/"
                  element={<Navigate to="/dashboard" replace />}
                />
              </Routes>
            </PlatformShell>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

// The main App component now simply sets up the providers and the router
function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
```

---

### **Step 3: Verify the Complete Application Workflow**

**Goal:** After making the code changes, run the application and verify that the new, complete workflow is active.

**Verification Checklist:**

1.  **Start the Frontend:** Run `npm start` in your `frontend` directory.
2.  **Verify Login Redirect:** Open `http://localhost:3000`. You should be automatically redirected to the new login page at `http://localhost:3000/login`.
3.  **Test Protected Route:** Try to manually navigate to `http://localhost:3000/asl-world`. You should be redirected back to the login page. This confirms the `ProtectedRoute` is working.
4.  **Test Registration:** Navigate to the registration page and create a new account.
5.  **Test Login:** Log in with your new account credentials.
6.  **Verify Dashboard:** Upon successful login, you should be redirected to the new dashboard page (`/dashboard`), which is the view shown in your latest screenshot.
7.  **Test Navigation:** Use the header navigation to click on "ASL World". You should now be taken to the refactored `ASLWorldPage`, which will show the new "Story Setup" component.

By completing these steps, you will have successfully integrated the refactored components. The application will now reflect the new design, enforce authentication, and provide the modular structure necessary for future development.
