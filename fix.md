### **Implementation Plan for StorySign Platform Fixes**

This document outlines the detailed steps required to resolve two key issues in the StorySign platform: streamlining the backend connection process and implementing user logout functionality.

---

### **Issue 1: Resolve Manual Backend Connection Requirement**

**Objective:**
Automate the frontend-to-backend connection to remove the need for the manual "Test Backend" button, ensuring features like story generation work immediately upon application start.

**Workflow:**

This task involves two main parts: ensuring the backend server is running independently and configuring the frontend to connect to it by default.

**Step 1: Run the Standalone Backend Server**

The backend is designed to run as a separate service.

1.  **Open a new terminal** in the root of the `backend` directory.
2.  **Start the FastAPI server** using the command specified in the project's documentation. This server includes all the necessary API endpoints for authentication, content, and real-time features.
    ```bash
    uvicorn main_api:app --reload --port 8000
    ```
3.  **Verify the server is running** by navigating to `http://127.0.0.1:8000/docs` in your browser. You should see the Swagger UI for the API documentation.

**Step 2: Configure the Frontend API Endpoint**

Modify the frontend application to use the running backend server's URL by default.

1.  **Navigate to the frontend configuration file:**

    - **File Path:** `src/config/api.js`

2.  **Modify the API configuration:**

    - Update the file to export the local backend URL directly. This removes any logic that defaults to a mock service.

    **Modify `src/config/api.js` to the following:**

    ```javascript
    // src/config/api.js

    const API_BASE_URL = "http://127.0.0.1:8000";

    export default API_BASE_URL;
    ```

**Step 3: Verification**

1.  Ensure both the frontend and backend development servers are running.
2.  Launch the frontend application.
3.  Navigate to the **ASL World** module and try the "Scan Object to Start" functionality.
4.  **Expected Result:** The story generation should now work without needing to click the "Test Backend" button first. The button itself can now be removed from the UI.

---

### **Issue 2: Implement Missing Logout Functionality**

**Objective:**
Add a "Logout" button to the user interface and implement the client-side logic to terminate the user's session, clear stored credentials, and redirect to the login page.

**Workflow:**

This involves updating the `AuthContext` to include a `logout` method and then adding a button to the `PlatformShell` that triggers this method.

**Step 1: Enhance the Authentication Context**

Add a `logout` function to the `AuthContext` to handle the client-side session termination.

1.  **Navigate to the authentication context file:**

    - **File Path:** `src/contexts/AuthContext.js`

2.  **Implement the `logout` function:**

    - This function will clear the authentication token from `localStorage`, reset the user state, and redirect the user.

    **Add the following code to `src/contexts/AuthContext.js`:**

    ```javascript
    // src/contexts/AuthContext.js
    import { useNavigate } from "react-router-dom";

    export const AuthProvider = ({ children }) => {
      const [user, setUser] = useState(null);
      const [isAuthenticated, setIsAuthenticated] = useState(false);
      const navigate = useNavigate();
      // ... existing login and register functions

      const logout = () => {
        console.log("Logging out...");
        // 1. Clear the token from local storage
        localStorage.removeItem("authToken");

        // 2. Reset the user state in the context
        setUser(null);
        setIsAuthenticated(false);

        // 3. Redirect the user to the login page
        navigate("/login");
      };

      const value = { user, isAuthenticated, login, register, logout };

      return (
        <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
      );
    };
    ```

**Step 2: Add the Logout Button to the UI**

Integrate the logout functionality into the user menu within the main `PlatformShell`.

1.  **Navigate to the Platform Shell component:**

    - **File Path:** `src/components/shell/PlatformShell.js`

2.  **Add the "Logout" button:**

    - Import the `useAuth` hook to access the `logout` function.
    - Add a new button within the user menu dropdown that calls this function on click.

    **Modify `src/components/shell/PlatformShell.js` as follows:**

    ```javascript
    // src/components/shell/PlatformShell.js
    import React from "react";
    import { NavLink } from "react-router-dom";
    // ... other imports
    import { LogOut, User } from "lucide-react"; // Import LogOut icon
    import { useAuth } from "../../contexts/AuthContext"; // Import useAuth hook

    const PlatformShell = ({ children }) => {
      const { user, logout } = useAuth(); // Destructure user and logout

      // ... existing component logic

      return (
        <div className="platform-shell">
          <header className="platform-header">
            {/* ... other header content ... */}
            <div className="user-menu">
              <button className="user-menu-button">
                <User size={20} />
                <span>{user ? user.username : "Guest"}</span>
              </button>
              <div className="user-menu-dropdown">
                <NavLink to="/profile">Profile</NavLink>
                <NavLink to="/settings">Settings</NavLink>
                <div className="dropdown-divider"></div>
                {/* --- ADD LOGOUT BUTTON --- */}
                <button onClick={logout} className="logout-button">
                  <LogOut size={16} style={{ marginRight: "8px" }} />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </header>
          {/* ... rest of the component ... */}
        </div>
      );
    };

    export default PlatformShell;
    ```

**Step 3: Verification**

1.  Log into the application.
2.  Click on the user menu in the top-right corner of the header.
3.  Click the newly added "Logout" button.
4.  **Expected Result:** The application should immediately redirect you to the login page, and you should no longer have access to protected routes.
