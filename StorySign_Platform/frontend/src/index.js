import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import "./index.css";
import App from "./App";
import { AuthProvider } from "./contexts/AuthContext";
import pwaService from "./services/PWAService";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
);

// Initialize PWA Service after React app is rendered
// Only register service worker in production or when explicitly enabled
if (
  process.env.NODE_ENV === "production" ||
  process.env.REACT_APP_ENABLE_SW === "true"
) {
  pwaService.init().catch(error => {
    console.warn("PWA Service initialization failed:", error);
    // Don't throw error in development to avoid breaking the app
  });
}
