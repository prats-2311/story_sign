# Module Development Guide

## Overview

This guide provides comprehensive instructions for developing new learning modules for the StorySign Platform. Following these guidelines ensures consistency, maintainability, and seamless integration with the existing system.

## Table of Contents

1. [Module Architecture](#module-architecture)
2. [Development Setup](#development-setup)
3. [Frontend Module Development](#frontend-module-development)
4. [Backend Module Development](#backend-module-development)
5. [Testing Requirements](#testing-requirements)
6. [Documentation Standards](#documentation-standards)
7. [Integration Process](#integration-process)
8. [Quality Assurance](#quality-assurance)

## Module Architecture

### Module Interface Definition

Every learning module must implement the `LearningModule` interface:

```typescript
interface LearningModule {
  id: string; // Unique module identifier
  name: string; // Display name
  description: string; // Module description
  icon: string; // Icon identifier
  route: string; // Base route path
  component: React.ComponentType; // Main component
  requiredPermissions?: string[]; // Required user permissions
  isEnabled: boolean; // Module availability
}
```

### Module Structure Template

```
modules/your_module/
├── frontend/
│   ├── components/          # React components
│   │   ├── ModuleMain.js   # Main module component
│   │   ├── FeatureA.js     # Feature components
│   │   ├── FeatureB.js
│   │   └── index.js        # Component exports
│   ├── hooks/              # Custom hooks
│   │   ├── useModuleLogic.js
│   │   └── useModuleData.js
│   ├── services/           # API services
│   │   └── ModuleService.js
│   ├── types/              # TypeScript definitions
│   │   └── module.types.ts
│   ├── styles/             # Module-specific styles
│   │   └── module.css
│   ├── tests/              # Frontend tests
│   │   ├── components/
│   │   ├── hooks/
│   │   └── integration/
│   └── index.js            # Module entry point
├── backend/
│   ├── api/                # API endpoints
│   │   └── module_api.py
│   ├── services/           # Business logic
│   │   └── module_service.py
│   ├── models/             # Data models
│   │   └── module_models.py
│   ├── repositories/       # Data access
│   │   └── module_repository.py
│   ├── migrations/         # Database migrations
│   │   └── create_module_tables.py
│   └── tests/              # Backend tests
│       ├── test_api.py
│       ├── test_service.py
│       └── test_repository.py
├── docs/                   # Module documentation
│   ├── README.md          # Module overview
│   ├── API.md             # API documentation
│   └── USER_GUIDE.md      # User instructions
└── package.json           # Module metadata
```

## Development Setup

### 1. Create Module Directory

```bash
# Create module structure
mkdir -p modules/your_module/{frontend,backend,docs}
cd modules/your_module

# Initialize module metadata
cat > package.json << EOF
{
  "name": "@storysign/your-module",
  "version": "1.0.0",
  "description": "Description of your learning module",
  "main": "frontend/index.js",
  "keywords": ["storysign", "learning", "accessibility"],
  "author": "Your Name <your.email@example.com>",
  "license": "MIT"
}
EOF
```

### 2. Frontend Setup

```bash
cd frontend

# Create component structure
mkdir -p components hooks services types styles tests
touch components/index.js hooks/index.js services/index.js
```

### 3. Backend Setup

```bash
cd ../backend

# Create backend structure
mkdir -p api services models repositories migrations tests
touch __init__.py api/__init__.py services/__init__.py
```

## Frontend Module Development

### 1. Main Module Component

```javascript
// frontend/components/YourModuleMain.js
import React, { useState, useEffect } from "react";
import { useAuth } from "../../../contexts/AuthContext";
import { useWebcam } from "../../../hooks/useWebcam";
import { VideoDisplayPanel } from "../../../components/common";
import { useYourModuleLogic } from "../hooks/useYourModuleLogic";
import "./YourModule.css";

/**
 * YourModuleMain - Main component for Your Module
 *
 * Provides the primary interface for users to interact with your learning module.
 * Integrates with the platform's webcam system and follows accessibility guidelines.
 */
const YourModuleMain = () => {
  // Authentication and user context
  const { user } = useAuth();

  // Webcam integration
  const {
    stream,
    isActive,
    startWebcam,
    stopWebcam,
    error: webcamError,
  } = useWebcam();

  // Module-specific logic
  const {
    moduleState,
    isLoading,
    error,
    startSession,
    processFrame,
    endSession,
  } = useYourModuleLogic();

  // Component state
  const [currentView, setCurrentView] = useState("setup"); // setup, active, results

  // Initialize module
  useEffect(() => {
    if (user && !moduleState.sessionId) {
      startSession(user.id);
    }
  }, [user, moduleState.sessionId, startSession]);

  // Handle webcam frame processing
  const handleFrameCapture = async (frameData) => {
    if (currentView === "active" && frameData) {
      await processFrame(frameData);
    }
  };

  // Start learning session
  const handleStartSession = async () => {
    const webcamStarted = await startWebcam();
    if (webcamStarted) {
      setCurrentView("active");
    }
  };

  // End learning session
  const handleEndSession = async () => {
    await endSession();
    stopWebcam();
    setCurrentView("results");
  };

  // Error handling
  if (error || webcamError) {
    return (
      <div className="your-module-error" role="alert">
        <h2>Module Error</h2>
        <p>{error?.message || webcamError?.message}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="your-module-loading" aria-live="polite">
        <div className="loading-spinner" />
        <p>Loading Your Module...</p>
      </div>
    );
  }

  // Render based on current view
  return (
    <div className="your-module-main">
      <header className="your-module-header">
        <h1>Your Learning Module</h1>
        <p>Interactive learning experience description</p>
      </header>

      <main className="your-module-content">
        {currentView === "setup" && (
          <SetupView onStart={handleStartSession} user={user} />
        )}

        {currentView === "active" && (
          <ActiveView
            stream={stream}
            moduleState={moduleState}
            onFrameCapture={handleFrameCapture}
            onEnd={handleEndSession}
          />
        )}

        {currentView === "results" && (
          <ResultsView
            sessionData={moduleState.sessionData}
            onRestart={() => setCurrentView("setup")}
          />
        )}
      </main>
    </div>
  );
};

export default YourModuleMain;
```

### 2. Module-Specific Hook

```javascript
// frontend/hooks/useYourModuleLogic.js
import { useState, useCallback, useRef } from "react";
import { YourModuleService } from "../services/YourModuleService";

/**
 * useYourModuleLogic - Custom hook for module business logic
 *
 * Manages module state, API interactions, and data processing.
 * Provides a clean interface for components to interact with module functionality.
 */
export const useYourModuleLogic = () => {
  // State management
  const [moduleState, setModuleState] = useState({
    sessionId: null,
    sessionData: null,
    progress: 0,
    currentTask: null,
    results: [],
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Service reference
  const serviceRef = useRef(new YourModuleService());

  /**
   * Start a new learning session
   */
  const startSession = useCallback(async (userId) => {
    setIsLoading(true);
    setError(null);

    try {
      const session = await serviceRef.current.createSession(userId);
      setModuleState((prev) => ({
        ...prev,
        sessionId: session.id,
        sessionData: session,
        progress: 0,
        currentTask: session.firstTask,
      }));
    } catch (err) {
      setError({
        type: "SESSION_START_ERROR",
        message: "Failed to start learning session",
        details: err.message,
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Process video frame data
   */
  const processFrame = useCallback(
    async (frameData) => {
      if (!moduleState.sessionId) return;

      try {
        const analysis = await serviceRef.current.analyzeFrame(
          moduleState.sessionId,
          frameData
        );

        setModuleState((prev) => ({
          ...prev,
          results: [...prev.results, analysis],
          progress: analysis.progress || prev.progress,
        }));

        return analysis;
      } catch (err) {
        console.error("Frame processing error:", err);
        // Don't set error state for individual frame failures
        return null;
      }
    },
    [moduleState.sessionId]
  );

  /**
   * End the current session
   */
  const endSession = useCallback(async () => {
    if (!moduleState.sessionId) return;

    setIsLoading(true);

    try {
      const finalResults = await serviceRef.current.endSession(
        moduleState.sessionId
      );

      setModuleState((prev) => ({
        ...prev,
        sessionData: { ...prev.sessionData, ...finalResults },
        progress: 100,
      }));
    } catch (err) {
      setError({
        type: "SESSION_END_ERROR",
        message: "Failed to end session properly",
        details: err.message,
      });
    } finally {
      setIsLoading(false);
    }
  }, [moduleState.sessionId]);

  /**
   * Reset module state
   */
  const resetModule = useCallback(() => {
    setModuleState({
      sessionId: null,
      sessionData: null,
      progress: 0,
      currentTask: null,
      results: [],
    });
    setError(null);
  }, []);

  return {
    moduleState,
    isLoading,
    error,
    startSession,
    processFrame,
    endSession,
    resetModule,

    // Computed values
    hasActiveSession: !!moduleState.sessionId,
    progressPercentage: moduleState.progress,
    canProcessFrames: !!moduleState.sessionId && !isLoading,
  };
};
```

### 3. API Service

```javascript
// frontend/services/YourModuleService.js
import { ApiService } from "../../../services/ApiService";

/**
 * YourModuleService - API service for module backend communication
 *
 * Handles all HTTP requests to the module's backend endpoints.
 * Provides error handling and data transformation.
 */
export class YourModuleService extends ApiService {
  constructor() {
    super("/api/v1/your-module");
  }

  /**
   * Create a new learning session
   */
  async createSession(userId) {
    try {
      const response = await this.post("/sessions", {
        user_id: userId,
        module_version: "1.0.0",
        timestamp: new Date().toISOString(),
      });

      return this.handleResponse(response);
    } catch (error) {
      throw this.handleError(error, "Failed to create session");
    }
  }

  /**
   * Analyze video frame
   */
  async analyzeFrame(sessionId, frameData) {
    try {
      const response = await this.post(`/sessions/${sessionId}/analyze`, {
        frame_data: frameData,
        timestamp: new Date().toISOString(),
      });

      return this.handleResponse(response);
    } catch (error) {
      throw this.handleError(error, "Failed to analyze frame");
    }
  }

  /**
   * End learning session
   */
  async endSession(sessionId) {
    try {
      const response = await this.post(`/sessions/${sessionId}/end`, {
        end_timestamp: new Date().toISOString(),
      });

      return this.handleResponse(response);
    } catch (error) {
      throw this.handleError(error, "Failed to end session");
    }
  }

  /**
   * Get session history
   */
  async getSessionHistory(userId, limit = 10) {
    try {
      const response = await this.get(`/users/${userId}/sessions`, {
        params: { limit },
      });

      return this.handleResponse(response);
    } catch (error) {
      throw this.handleError(error, "Failed to get session history");
    }
  }
}
```

### 4. Module Registration

```javascript
// frontend/index.js
import YourModuleMain from "./components/YourModuleMain";
import { BaseModule } from "../../core/BaseModule";

/**
 * YourModule - Module implementation
 *
 * Defines the module configuration and lifecycle methods.
 */
class YourModule extends BaseModule {
  id = "your_module";
  name = "Your Learning Module";
  description = "Interactive learning experience for [specific skill]";
  icon = "your-module-icon";
  route = "/your-module";
  component = YourModuleMain;
  requiredPermissions = ["module:your_module:access"];
  isEnabled = true;

  async onActivate() {
    console.log("Your Module activated");
    // Initialize module-specific services
    // Set up event listeners
    // Load module configuration
  }

  async onDeactivate() {
    console.log("Your Module deactivated");
    // Cleanup resources
    // Remove event listeners
    // Save state if needed
  }

  onDataUpdate(data) {
    // Handle real-time data updates
    console.log("Your Module data update:", data);
  }
}

export default new YourModule();

// Export components for testing
export { YourModuleMain };
export { useYourModuleLogic } from "./hooks/useYourModuleLogic";
export { YourModuleService } from "./services/YourModuleService";
```

## Backend Module Development

### 1. API Endpoints

```python
# backend/api/your_module_api.py
"""
Your Module API endpoints.

Provides REST API for your learning module functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..core.auth import get_current_user
from ..models.user import User
from ..models.your_module import (
    YourModuleSession,
    YourModuleSessionCreate,
    YourModuleAnalysis,
    YourModuleAnalysisCreate
)
from ..services.your_module_service import YourModuleService
from ..repositories.your_module_repository import YourModuleRepository

# Router configuration
router = APIRouter(
    prefix="/api/v1/your-module",
    tags=["your-module"],
    responses={404: {"description": "Not found"}}
)

# Dependency injection
async def get_your_module_service(
    db: AsyncSession = Depends(get_db_session)
) -> YourModuleService:
    """Get your module service instance."""
    repository = YourModuleRepository(db)
    return YourModuleService(repository)

@router.post(
    "/sessions",
    response_model=YourModuleSession,
    status_code=status.HTTP_201_CREATED,
    summary="Create learning session",
    description="Create a new learning session for the current user"
)
async def create_session(
    session_data: YourModuleSessionCreate,
    current_user: User = Depends(get_current_user),
    service: YourModuleService = Depends(get_your_module_service)
) -> YourModuleSession:
    """
    Create a new learning session.

    Args:
        session_data: Session creation data
        current_user: Currently authenticated user
        service: Your module service instance

    Returns:
        Created session information

    Raises:
        HTTPException: If creation fails or user lacks permissions
    """
    try:
        session = await service.create_session(
            user_id=current_user.id,
            session_data=session_data
        )
        return session

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )

@router.post(
    "/sessions/{session_id}/analyze",
    response_model=YourModuleAnalysis,
    summary="Analyze frame data",
    description="Process and analyze video frame data for learning feedback"
)
async def analyze_frame(
    session_id: int,
    analysis_data: YourModuleAnalysisCreate,
    current_user: User = Depends(get_current_user),
    service: YourModuleService = Depends(get_your_module_service)
) -> YourModuleAnalysis:
    """
    Analyze video frame data.

    Args:
        session_id: ID of the learning session
        analysis_data: Frame data to analyze
        current_user: Currently authenticated user
        service: Your module service instance

    Returns:
        Analysis results and feedback

    Raises:
        HTTPException: If analysis fails or session not found
    """
    try:
        # Verify session ownership
        session = await service.get_session_by_id(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Process frame data
        analysis = await service.analyze_frame(session_id, analysis_data)
        return analysis

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze frame"
        )

@router.post(
    "/sessions/{session_id}/end",
    response_model=YourModuleSession,
    summary="End learning session",
    description="Complete the learning session and generate final results"
)
async def end_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    service: YourModuleService = Depends(get_your_module_service)
) -> YourModuleSession:
    """
    End a learning session.

    Args:
        session_id: ID of the session to end
        current_user: Currently authenticated user
        service: Your module service instance

    Returns:
        Updated session with final results

    Raises:
        HTTPException: If session not found or cannot be ended
    """
    try:
        session = await service.end_session(session_id, current_user.id)
        return session

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end session"
        )

@router.get(
    "/users/{user_id}/sessions",
    response_model=List[YourModuleSession],
    summary="Get user sessions",
    description="Retrieve learning session history for a user"
)
async def get_user_sessions(
    user_id: int,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    service: YourModuleService = Depends(get_your_module_service)
) -> List[YourModuleSession]:
    """
    Get user's learning sessions.

    Args:
        user_id: ID of the user
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip
        current_user: Currently authenticated user
        service: Your module service instance

    Returns:
        List of user's learning sessions

    Raises:
        HTTPException: If user not found or access denied
    """
    # Check permissions (users can only access their own sessions)
    if current_user.id != user_id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    try:
        sessions = await service.get_user_sessions(user_id, limit, offset)
        return sessions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )
```

### 2. Service Layer

```python
# backend/services/your_module_service.py
"""
Your Module Service.

Business logic for your learning module functionality.
"""

from typing import List, Optional
from datetime import datetime
import asyncio
import logging

from ..models.your_module import (
    YourModuleSession,
    YourModuleSessionCreate,
    YourModuleAnalysis,
    YourModuleAnalysisCreate
)
from ..repositories.your_module_repository import YourModuleRepository
from ..core.exceptions import ValidationError, NotFoundError
from ..core.mediapipe_processor import MediaPipeProcessor

logger = logging.getLogger(__name__)

class YourModuleService:
    """Service class for your module business logic."""

    def __init__(self, repository: YourModuleRepository):
        """
        Initialize service with repository dependency.

        Args:
            repository: Your module repository instance
        """
        self.repository = repository
        self.mediapipe_processor = MediaPipeProcessor()

    async def create_session(
        self,
        user_id: int,
        session_data: YourModuleSessionCreate
    ) -> YourModuleSession:
        """
        Create a new learning session.

        Args:
            user_id: ID of the user creating the session
            session_data: Session creation data

        Returns:
            Created session

        Raises:
            ValidationError: If session data is invalid
        """
        # Validate business rules
        await self._validate_session_data(user_id, session_data)

        # Create session
        session = await self.repository.create({
            **session_data.dict(),
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "status": "active"
        })

        logger.info(f"Created session {session.id} for user {user_id}")
        return session

    async def analyze_frame(
        self,
        session_id: int,
        analysis_data: YourModuleAnalysisCreate
    ) -> YourModuleAnalysis:
        """
        Analyze video frame data.

        Args:
            session_id: ID of the session
            analysis_data: Frame data to analyze

        Returns:
            Analysis results

        Raises:
            ValidationError: If frame data is invalid
            NotFoundError: If session not found
        """
        # Verify session exists and is active
        session = await self.repository.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Session {session_id} not found")

        if session.status != "active":
            raise ValidationError("Session is not active")

        # Process frame data asynchronously
        loop = asyncio.get_event_loop()
        analysis_result = await loop.run_in_executor(
            None,
            self._process_frame_data,
            analysis_data.frame_data
        )

        # Store analysis result
        analysis = await self.repository.create_analysis({
            "session_id": session_id,
            "frame_data": analysis_data.frame_data,
            "analysis_result": analysis_result,
            "timestamp": datetime.utcnow()
        })

        # Update session progress
        await self._update_session_progress(session_id)

        return analysis

    async def end_session(
        self,
        session_id: int,
        user_id: int
    ) -> YourModuleSession:
        """
        End a learning session.

        Args:
            session_id: ID of the session to end
            user_id: ID of the user ending the session

        Returns:
            Updated session with final results

        Raises:
            NotFoundError: If session not found
            ValidationError: If user cannot end session
        """
        # Get session and verify ownership
        session = await self.repository.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Session {session_id} not found")

        if session.user_id != user_id:
            raise ValidationError("User cannot end this session")

        # Calculate final results
        final_results = await self._calculate_final_results(session_id)

        # Update session
        updated_session = await self.repository.update(session_id, {
            "status": "completed",
            "ended_at": datetime.utcnow(),
            "final_results": final_results
        })

        logger.info(f"Ended session {session_id} for user {user_id}")
        return updated_session

    async def get_session_by_id(
        self,
        session_id: int,
        user_id: int
    ) -> Optional[YourModuleSession]:
        """
        Get session by ID with user access check.

        Args:
            session_id: ID of the session
            user_id: ID of the requesting user

        Returns:
            Session if found and accessible, None otherwise
        """
        session = await self.repository.get_by_id(session_id)

        if not session or session.user_id != user_id:
            return None

        return session

    async def get_user_sessions(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[YourModuleSession]:
        """
        Get sessions for a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of user's sessions
        """
        return await self.repository.get_user_sessions(user_id, limit, offset)

    def _process_frame_data(self, frame_data: str) -> dict:
        """
        Process video frame data using MediaPipe.

        Args:
            frame_data: Base64 encoded frame data

        Returns:
            Analysis results dictionary
        """
        try:
            # Decode frame data
            import base64
            import cv2
            import numpy as np

            # Convert base64 to image
            image_data = base64.b64decode(frame_data.split(',')[1])
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Process with MediaPipe (implement your specific processing)
            results = self.mediapipe_processor.process_image(image)

            # Extract relevant features for your module
            analysis_result = {
                "landmarks_detected": len(results.landmarks) if results.landmarks else 0,
                "confidence_score": results.confidence if hasattr(results, 'confidence') else 0.0,
                "processing_time": results.processing_time if hasattr(results, 'processing_time') else 0,
                "feedback": self._generate_feedback(results),
                "timestamp": datetime.utcnow().isoformat()
            }

            return analysis_result

        except Exception as e:
            logger.error(f"Error processing frame data: {e}")
            return {
                "error": str(e),
                "landmarks_detected": 0,
                "confidence_score": 0.0,
                "feedback": "Processing failed",
                "timestamp": datetime.utcnow().isoformat()
            }

    def _generate_feedback(self, results) -> str:
        """
        Generate learning feedback based on analysis results.

        Args:
            results: MediaPipe processing results

        Returns:
            Feedback message for the user
        """
        # Implement your module-specific feedback logic
        if not results.landmarks:
            return "No landmarks detected. Please ensure you're visible in the camera."

        confidence = getattr(results, 'confidence', 0.0)
        if confidence > 0.8:
            return "Excellent! Your form looks great."
        elif confidence > 0.6:
            return "Good job! Try to be more precise with your movements."
        else:
            return "Keep practicing! Focus on the correct positioning."

    async def _validate_session_data(
        self,
        user_id: int,
        session_data: YourModuleSessionCreate
    ) -> None:
        """
        Validate session creation data.

        Args:
            user_id: ID of the user
            session_data: Session data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Check user session limits
        active_sessions = await self.repository.count_active_sessions(user_id)
        if active_sessions >= 5:  # Business rule example
            raise ValidationError("User has too many active sessions")

        # Validate session data
        if not session_data.module_version:
            raise ValidationError("Module version is required")

    async def _update_session_progress(self, session_id: int) -> None:
        """
        Update session progress based on analysis count.

        Args:
            session_id: ID of the session to update
        """
        analysis_count = await self.repository.count_session_analyses(session_id)

        # Calculate progress (example: 10 analyses = 100% progress)
        progress = min(100, (analysis_count / 10) * 100)

        await self.repository.update(session_id, {"progress": progress})

    async def _calculate_final_results(self, session_id: int) -> dict:
        """
        Calculate final session results.

        Args:
            session_id: ID of the session

        Returns:
            Final results dictionary
        """
        analyses = await self.repository.get_session_analyses(session_id)

        if not analyses:
            return {"total_analyses": 0, "average_confidence": 0.0}

        total_confidence = sum(
            analysis.analysis_result.get("confidence_score", 0.0)
            for analysis in analyses
        )

        return {
            "total_analyses": len(analyses),
            "average_confidence": total_confidence / len(analyses),
            "session_duration": self._calculate_session_duration(analyses),
            "improvement_trend": self._calculate_improvement_trend(analyses)
        }

    def _calculate_session_duration(self, analyses: List) -> int:
        """Calculate session duration in seconds."""
        if len(analyses) < 2:
            return 0

        start_time = analyses[0].timestamp
        end_time = analyses[-1].timestamp
        return int((end_time - start_time).total_seconds())

    def _calculate_improvement_trend(self, analyses: List) -> str:
        """Calculate improvement trend based on confidence scores."""
        if len(analyses) < 3:
            return "insufficient_data"

        # Compare first third with last third
        first_third = analyses[:len(analyses)//3]
        last_third = analyses[-len(analyses)//3:]

        first_avg = sum(a.analysis_result.get("confidence_score", 0) for a in first_third) / len(first_third)
        last_avg = sum(a.analysis_result.get("confidence_score", 0) for a in last_third) / len(last_third)

        if last_avg > first_avg + 0.1:
            return "improving"
        elif last_avg < first_avg - 0.1:
            return "declining"
        else:
            return "stable"
```

## Testing Requirements

### Frontend Testing

```javascript
// frontend/tests/components/YourModuleMain.test.js
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import YourModuleMain from "../components/YourModuleMain";
import { AuthProvider } from "../../../contexts/AuthContext";

expect.extend(toHaveNoViolations);

// Mock dependencies
jest.mock("../hooks/useYourModuleLogic");
jest.mock("../../../hooks/useWebcam");

const mockUser = {
  id: 1,
  name: "Test User",
  email: "test@example.com",
};

const renderWithProviders = (component) => {
  return render(
    <AuthProvider value={{ user: mockUser }}>{component}</AuthProvider>
  );
};

describe("YourModuleMain", () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
  });

  it("renders module interface correctly", () => {
    renderWithProviders(<YourModuleMain />);

    expect(screen.getByText("Your Learning Module")).toBeInTheDocument();
    expect(
      screen.getByText("Interactive learning experience description")
    ).toBeInTheDocument();
  });

  it("is accessible", async () => {
    const { container } = renderWithProviders(<YourModuleMain />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("handles session start correctly", async () => {
    const mockStartSession = jest.fn();
    const mockStartWebcam = jest.fn().mockResolvedValue(true);

    // Mock hook returns
    require("../hooks/useYourModuleLogic").useYourModuleLogic.mockReturnValue({
      moduleState: { sessionId: null },
      startSession: mockStartSession,
      isLoading: false,
      error: null,
    });

    require("../../../hooks/useWebcam").useWebcam.mockReturnValue({
      startWebcam: mockStartWebcam,
      isActive: false,
      error: null,
    });

    renderWithProviders(<YourModuleMain />);

    const startButton = screen.getByRole("button", { name: /start/i });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(mockStartWebcam).toHaveBeenCalled();
    });
  });

  it("displays error states appropriately", () => {
    const mockError = {
      type: "SESSION_ERROR",
      message: "Failed to start session",
    };

    require("../hooks/useYourModuleLogic").useYourModuleLogic.mockReturnValue({
      moduleState: { sessionId: null },
      isLoading: false,
      error: mockError,
    });

    renderWithProviders(<YourModuleMain />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Failed to start session")).toBeInTheDocument();
  });

  it("supports keyboard navigation", () => {
    renderWithProviders(<YourModuleMain />);

    const startButton = screen.getByRole("button", { name: /start/i });
    startButton.focus();
    expect(startButton).toHaveFocus();

    fireEvent.keyDown(startButton, { key: "Enter" });
    // Verify appropriate action is triggered
  });
});
```

### Backend Testing

```python
# backend/tests/test_your_module_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from backend.services.your_module_service import YourModuleService
from backend.models.your_module import YourModuleSessionCreate, YourModuleAnalysisCreate
from backend.core.exceptions import ValidationError, NotFoundError

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def your_module_service(mock_repository):
    return YourModuleService(mock_repository)

@pytest.mark.asyncio
async def test_create_session_success(your_module_service, mock_repository):
    # Arrange
    user_id = 1
    session_data = YourModuleSessionCreate(
        module_version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

    mock_repository.count_active_sessions = AsyncMock(return_value=0)
    mock_repository.create = AsyncMock(return_value=Mock(id=1, user_id=user_id))

    # Act
    result = await your_module_service.create_session(user_id, session_data)

    # Assert
    assert result.id == 1
    assert result.user_id == user_id
    mock_repository.create.assert_called_once()

@pytest.mark.asyncio
async def test_create_session_too_many_active(your_module_service, mock_repository):
    # Arrange
    user_id = 1
    session_data = YourModuleSessionCreate(
        module_version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )

    mock_repository.count_active_sessions = AsyncMock(return_value=5)

    # Act & Assert
    with pytest.raises(ValidationError, match="too many active sessions"):
        await your_module_service.create_session(user_id, session_data)

@pytest.mark.asyncio
async def test_analyze_frame_success(your_module_service, mock_repository):
    # Arrange
    session_id = 1
    analysis_data = YourModuleAnalysisCreate(
        frame_data="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
    )

    mock_session = Mock(id=session_id, status="active")
    mock_repository.get_by_id = AsyncMock(return_value=mock_session)
    mock_repository.create_analysis = AsyncMock(return_value=Mock(id=1))
    mock_repository.count_session_analyses = AsyncMock(return_value=1)
    mock_repository.update = AsyncMock()

    # Act
    result = await your_module_service.analyze_frame(session_id, analysis_data)

    # Assert
    assert result.id == 1
    mock_repository.create_analysis.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_frame_session_not_found(your_module_service, mock_repository):
    # Arrange
    session_id = 999
    analysis_data = YourModuleAnalysisCreate(
        frame_data="data:image/jpeg;base64,test"
    )

    mock_repository.get_by_id = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(NotFoundError, match="Session 999 not found"):
        await your_module_service.analyze_frame(session_id, analysis_data)

@pytest.mark.asyncio
async def test_end_session_success(your_module_service, mock_repository):
    # Arrange
    session_id = 1
    user_id = 1

    mock_session = Mock(id=session_id, user_id=user_id, status="active")
    mock_repository.get_by_id = AsyncMock(return_value=mock_session)
    mock_repository.get_session_analyses = AsyncMock(return_value=[])
    mock_repository.update = AsyncMock(return_value=Mock(id=session_id, status="completed"))

    # Act
    result = await your_module_service.end_session(session_id, user_id)

    # Assert
    assert result.status == "completed"
    mock_repository.update.assert_called_once()

class TestYourModuleAPI:
    """Integration tests for Your Module API endpoints."""

    @pytest.mark.asyncio
    async def test_create_session_endpoint(self, client, auth_headers):
        response = await client.post(
            "/api/v1/your-module/sessions",
            json={
                "module_version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat()
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_analyze_frame_endpoint(self, client, auth_headers, test_session):
        response = await client.post(
            f"/api/v1/your-module/sessions/{test_session.id}/analyze",
            json={
                "frame_data": "data:image/jpeg;base64,test_data",
                "timestamp": datetime.utcnow().isoformat()
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "analysis_result" in data

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        response = await client.post(
            "/api/v1/your-module/sessions",
            json={"module_version": "1.0.0"}
        )

        assert response.status_code == 401
```

## Quality Assurance Checklist

### Code Quality ✅

- [ ] Code follows established patterns and conventions
- [ ] All functions have proper documentation
- [ ] Error handling is comprehensive
- [ ] No hardcoded values or magic numbers
- [ ] Proper separation of concerns

### Accessibility ✅

- [ ] All interactive elements are keyboard accessible
- [ ] Proper ARIA labels and roles implemented
- [ ] Color contrast meets WCAG 2.1 AA standards
- [ ] Screen reader compatibility verified
- [ ] Focus management implemented correctly

### Performance ✅

- [ ] Components use proper memoization
- [ ] API calls are optimized and cached when appropriate
- [ ] Large computations are moved to web workers or backend
- [ ] Bundle size impact is minimal
- [ ] Loading states provide good user experience

### Security ✅

- [ ] Input validation on both frontend and backend
- [ ] Proper authentication and authorization
- [ ] No sensitive data exposed in client code
- [ ] API endpoints follow security best practices
- [ ] Error messages don't leak sensitive information

### Testing ✅

- [ ] Unit tests cover all major functionality
- [ ] Integration tests verify API endpoints
- [ ] Accessibility tests pass
- [ ] Error scenarios are tested
- [ ] Performance tests validate response times

This comprehensive guide provides everything needed to develop high-quality, maintainable learning modules for the StorySign Platform while ensuring consistency and accessibility across the entire system.
