Of course. This is a crucial and forward-thinking step for your project. Refactoring your current application into a truly modular architecture is the key to sustainably building ambitious new features like "StorySign Harmony" and "StorySign Reconnect." Integrating a powerful database like TiDB will provide the foundation for user data, progress tracking, and personalization.

Based on an exhaustive analysis of your current source code and best practices for scalable web applications, here is a complete, step-by-step guide to refactor your entire application.

---

### **High-Level Vision: From a Single Feature to a Multi-Module Platform**

Our goal is to transform the application from its current state—a single, monolithic "ASL World" feature—into a scalable platform. This platform will have a central shell (handling navigation, user authentication, etc.) that can load different, independent modules like ASL World, Harmony, and Reconnect.

Here is the complete refactoring plan for Kiro:

### **Phase 1: Frontend Refactoring (From Single View to Multi-Page App)**

The most significant change will be on the frontend. We will move from conditionally rendering a single component to using a standard routing library to create a true multi-page feel.

#### **Step 1.1: Introduce a Routing Library**

We will use `react-router-dom`, the standard for navigation in React applications.

**Action:**

1.  Install the library in your frontend directory: `npm install react-router-dom`
2.  Update `src/index.js` to wrap the main `<App />` component in `<BrowserRouter>`.

<!-- end list -->

```javascript
// In src/index.js
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom"; // Import
import "./index.css";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      {" "}
      {/* Wrap App */}
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

[cite: src/index.js]

#### **Step 1.2: Create a Modular File Structure**

Instead of having all logic in `App.js`, we will create a new, organized folder structure within the `src` directory.

**Action:** Create the following new directories inside your `src` folder.

```
src/
|-- components/       // For shared, reusable components (e.g., buttons, loading spinners)
|-- modules/          // For the main feature modules of your application
|   |-- asl_world/    // Move all components related to ASL World here
|   |   |-- ASLWorldModule.js
|   |   |-- ASLWorldModule.css
|   |   |-- VideoStream.js
|   |   |-- etc...
|   |-- harmony/      // Placeholder for your future StorySign Harmony module
|   |-- reconnect/    // Placeholder for your future StorySign Reconnect module
|-- pages/            // For the top-level "pages" of your app
|   |-- HomePage.js
|   |-- ASLWorldPage.js
|   |-- HarmonyPage.js
|   |-- ReconnectPage.js
|-- App.js            // This will become the main router
|-- App.css
|-- ...
```

#### **Step 1.3: Refactor `App.js` into a Router**

`App.js` will no longer contain the complex state logic for ASL World. It will become a clean, simple router that directs users to the correct page.

**File to Edit:** `src/App.js` [cite: src/App.js]

**Action:** Replace the entire contents of `App.js` with this new routing structure.

```javascript
// In the new, refactored src/App.js
import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ASLWorldPage from "./pages/ASLWorldPage";
// Import future pages here as they are built
// import HarmonyPage from './pages/HarmonyPage';
// import ReconnectPage from './pages/ReconnectPage';
import "./App.css";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>StorySign Platform</h1>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/asl-world">ASL World</Link>
          {/* Add links to future modules here */}
        </nav>
      </header>
      <main className="App-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/asl-world/*" element={<ASLWorldPage />} />
          {/* Add routes for future modules here */}
        </Routes>
      </main>
    </div>
  );
}

export default App;
```

#### **Step 1.4: Create Module-Specific Pages**

We will create a new "page" component for each module. This component will be responsible for managing all the state and logic for that specific feature, keeping it completely isolated from the other modules.

**File to Create:** `src/pages/ASLWorldPage.js`

**Action:** Move all of the state management and logic from the _original_ `App.js` into this new file. This new page will now be the "brain" for the ASL World module.

```javascript
// In the new src/pages/ASLWorldPage.js
import React, { useState, useRef, useEffect } from "react";
import ASLWorldModule from "../modules/asl_world/ASLWorldModule";
// ... import all other necessary components and styles

export default function ASLWorldPage() {
  // --- ALL THE STATE AND LOGIC FROM THE OLD App.js GOES HERE ---
  // const [backendMessage, setBackendMessage] = useState("");
  // const [isLoading, setIsLoading] = useState(false);
  // const [storyData, setStoryData] = useState(null);
  // const handleStoryGenerate = async (payload) => { ... };
  // ...and so on.

  // This new component will now render the ASLWorldModule and its children.
  // The return statement will look very similar to the one in the old App.js,
  // but without the main control panel logic.
  return (
    <div>
      <h2>ASL World Module</h2>
      {/* The main ASLWorldModule component and its logic will be rendered here */}
    </div>
  );
}
```

This modular structure ensures that when you start working on `StorySign-Harmony`, you can create a new `HarmonyPage.js` with its own independent state and logic, without any risk of interfering with the existing `ASLWorldPage.js`.

---

### **Phase 2: Backend Refactoring and TiDB Integration**

We will apply the same modular philosophy to the backend, breaking the API into smaller, more manageable pieces and integrating the database.

#### **Step 2.1: Implement a Modular API with `APIRouter`**

Instead of having all API endpoints in `main.py`, we will use FastAPI's `APIRouter` to create separate files for each feature.

**Action:** Create the following new directories and files in your `backend` folder.

```
backend/
|-- api/
|   |-- __init__.py
|   |-- asl_world.py      // All routes related to ASL World go here
|   |-- harmony.py        // Placeholder for future Harmony routes
|   |-- reconnect.py      // Placeholder for future Reconnect routes
|-- core/
|   |-- db.py             // For TiDB database connection and sessions
|   |-- config.py
|-- models/
|   |-- user.py           // Pydantic and SQLAlchemy models
|   |-- practice_session.py
|-- services/
|   |-- ollama_service.py
|   |-- local_vision_service.py
|-- main.py               // Will now assemble the routers
|-- ...
```

**File to Edit:** `backend/main.py` [cite: backend/main.py]

**Action:** Modify `main.py` to import and include the new routers. Move the existing `/api/story/recognize_and_generate` endpoint logic into `api/asl_world.py`.

```python
# In the refactored backend/main.py
from fastapi import FastAPI
from api import asl_world #, harmony, reconnect

app = FastAPI(
    title="StorySign Platform Backend",
    # ...
)

# Include the router for the ASL World module
app.include_router(asl_world.router, prefix="/api/asl_world", tags=["ASL World"])
# Include other routers for future modules here

# The WebSocket endpoint and other global routes can remain in main.py
# @app.websocket("/ws/video")
# ...
```

#### **Step 2.2: Integrate TiDB Database**

We will use SQLAlchemy, the standard Python SQL toolkit, to connect to your TiDB database. TiDB is compatible with the MySQL protocol, so we can use a standard MySQL driver.

**Action:**

1.  **Install necessary libraries:** `pip install sqlalchemy "mysqlclient<2.2"`
2.  **Update `backend/config.py`** [cite: backend/config.py]: Add a new `DatabaseConfig` class for your TiDB connection details (host, port, user, password, database name).
3.  **Create `backend/core/db.py`**: This new file will manage the database connection pool and sessions.

<!-- end list -->

```python
# In the new backend/core/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from core.config import get_config

config = get_config()

# TiDB is MySQL compatible, so we use the mysql+mysqlclient dialect
DATABASE_URL = (
    f"mysql+mysqlclient://{config.db.user}:{config.db.password}"
    f"@{config.db.host}:{config.db.port}/{config.db.name}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

4.  **Create `backend/models/practice_session.py`**: Here you will define your database tables using SQLAlchemy's ORM.

<!-- end list -->

```python
# In the new backend/models/practice_session.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from core.db import Base

class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # Foreign key to a future users table
    topic = Column(String(255))
    difficulty = Column(String(50))
    overall_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # ... any other fields you want to track
```

You can now use this `get_db` dependency in your API endpoints in `asl_world.py` (and future modules) to get a database session and save user progress, scores, and other important data. This data persistence is the foundation for building personalized learning paths in `StorySign Harmony` and `StorySign Reconnect`.
