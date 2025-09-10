# ADR-009: Modular Learning System Architecture

## Status

Accepted

## Context

The StorySign platform needs to support multiple learning modules beyond the original ASL World:

- **ASL World**: Sign language learning through object detection and stories
- **Harmony**: Facial expression and emotion recognition training
- **Reconnect**: Therapeutic movement analysis and rehabilitation

The architecture must support:

- Easy addition of new learning modules
- Shared components and utilities across modules
- Independent development and testing of modules
- Consistent user experience across all modules
- Module-specific data models and business logic

## Decision

We have implemented a **Plugin-Style Modular Architecture** where each learning module is a self-contained unit with its own components, services, and data models, while sharing common infrastructure.

## Consequences

### Positive

- **Scalability**: Easy to add new learning modules without affecting existing ones
- **Maintainability**: Clear separation of concerns between modules
- **Team Development**: Different teams can work on different modules independently
- **Testing**: Modules can be tested in isolation
- **Code Reuse**: Shared components and utilities reduce duplication
- **Consistent UX**: Common design system ensures consistent user experience

### Negative

- **Initial Complexity**: More upfront architectural planning required
- **Abstraction Overhead**: Additional layers of abstraction for shared functionality
- **Coordination**: Need to coordinate changes to shared components
- **Bundle Size**: Potential for larger bundles if not properly code-split

## Architecture Implementation

### 1. Directory Structure

```
frontend/src/
├── modules/                 # Learning modules
│   ├── asl_world/          # ASL learning module
│   │   ├── components/     # Module-specific components
│   │   ├── hooks/          # Module-specific hooks
│   │   ├── services/       # Module API services
│   │   ├── types/          # Module TypeScript types
│   │   └── index.js        # Module exports
│   ├── harmony/            # Facial expression module
│   └── reconnect/          # Therapeutic movement module
├── components/             # Shared components
│   ├── common/            # Basic UI components
│   ├── video/             # Video processing components
│   └── navigation/        # Navigation components
├── hooks/                  # Shared hooks
├── services/              # Shared services
└── core/                  # Core module system
```

### 2. Module Interface Definition

```typescript
// core/BaseModule.ts
export interface LearningModule {
  id: string;
  name: string;
  description: string;
  icon: string;
  route: string;
  component: React.ComponentType;
  requiredPermissions?: string[];
  isEnabled: boolean;
}

export abstract class BaseModule implements LearningModule {
  abstract id: string;
  abstract name: string;
  abstract description: string;
  abstract icon: string;
  abstract route: string;
  abstract component: React.ComponentType;

  isEnabled: boolean = true;

  // Lifecycle methods
  abstract onActivate(): Promise<void>;
  abstract onDeactivate(): Promise<void>;
  abstract onDataUpdate(data: any): void;
}
```

### 3. Module Registration System

```javascript
// core/ModuleManager.ts
class ModuleManager {
  private modules: Map<string, LearningModule> = new Map();

  registerModule(module: LearningModule): void {
    this.modules.set(module.id, module);
  }

  getModule(id: string): LearningModule | undefined {
    return this.modules.get(id);
  }

  getAllModules(): LearningModule[] {
    return Array.from(this.modules.values())
      .filter(module => module.isEnabled);
  }

  async activateModule(id: string): Promise<void> {
    const module = this.getModule(id);
    if (module && 'onActivate' in module) {
      await module.onActivate();
    }
  }
}

export const moduleManager = new ModuleManager();
```

### 4. Module Implementation Example

```javascript
// modules/asl_world/index.js
import ASLWorldPage from "./ASLWorldPage";
import { BaseModule } from "../../core/BaseModule";

class ASLWorldModule extends BaseModule {
  id = "asl_world";
  name = "ASL World";
  description = "Learn sign language through interactive stories";
  icon = "hands";
  route = "/asl-world";
  component = ASLWorldPage;

  async onActivate() {
    // Initialize module-specific services
    console.log("ASL World module activated");
  }

  async onDeactivate() {
    // Cleanup module resources
    console.log("ASL World module deactivated");
  }

  onDataUpdate(data) {
    // Handle data updates
  }
}

export default new ASLWorldModule();

// Export module components
export { default as StorySetup } from "./components/StorySetup";
export { default as PracticeView } from "./components/PracticeView";
export { default as FeedbackPanel } from "./components/FeedbackPanel";
```

### 5. Shared Component System

```javascript
// components/common/VideoDisplayPanel.js
const VideoDisplayPanel = ({
  stream,
  overlayData,
  onFrameCapture,
  moduleId,
  ...props
}) => {
  const { processFrame } = useVideoProcessing(moduleId);

  return (
    <div className="video-display-panel" {...props}>
      <video
        ref={videoRef}
        srcObject={stream}
        onLoadedMetadata={handleVideoLoad}
        aria-label="Live video feed for learning module"
      />
      {overlayData && <ModuleOverlay data={overlayData} moduleId={moduleId} />}
    </div>
  );
};
```

### 6. Module-Specific Services

```javascript
// modules/harmony/services/HarmonyService.js
class HarmonyService {
  constructor() {
    this.baseUrl = "/api/v1/harmony";
  }

  async startEmotionSession(userId) {
    const response = await fetch(`${this.baseUrl}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId }),
    });
    return response.json();
  }

  async analyzeEmotion(sessionId, imageData) {
    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, imageData }),
    });
    return response.json();
  }
}

export default new HarmonyService();
```

## Backend Module Architecture

### 1. Module-Specific APIs

```python
# backend/api/harmony.py
from fastapi import APIRouter, Depends
from ..services.harmony_service import HarmonyService
from ..models.harmony import EmotionSessionCreate, EmotionAnalysis

router = APIRouter(prefix="/api/v1/harmony", tags=["harmony"])

@router.post("/sessions")
async def create_emotion_session(
    session_data: EmotionSessionCreate,
    harmony_service: HarmonyService = Depends(get_harmony_service)
) -> EmotionAnalysis:
    return await harmony_service.create_session(session_data)
```

### 2. Module-Specific Services

```python
# backend/services/harmony_service.py
class HarmonyService:
    def __init__(self, repository: HarmonyRepository):
        self.repository = repository
        self.mediapipe_processor = MediaPipeProcessor()

    async def analyze_facial_expression(self, image_data: bytes) -> EmotionData:
        landmarks = await self.mediapipe_processor.process_face(image_data)
        emotions = self._classify_emotions(landmarks)
        return EmotionData(landmarks=landmarks, emotions=emotions)
```

### 3. Module-Specific Models

```python
# backend/models/harmony.py
from pydantic import BaseModel
from typing import List, Dict

class EmotionSessionCreate(BaseModel):
    user_id: int
    target_emotion: str

class EmotionData(BaseModel):
    session_id: int
    detected_emotions: List[Dict[str, float]]
    confidence_scores: List[float]
    timestamp: datetime
```

## Module Development Guidelines

### 1. Module Structure Standards

- Each module must implement the `LearningModule` interface
- Module components should be self-contained
- Shared functionality should use common components/hooks
- Module-specific styles should be scoped

### 2. Data Flow Patterns

- Modules communicate with backend through dedicated API endpoints
- Shared state managed through React Context
- Module state isolated within module boundaries
- Cross-module communication through event system

### 3. Testing Requirements

- Unit tests for module components
- Integration tests for module workflows
- Accessibility tests for module interfaces
- Performance tests for video processing

### 4. Documentation Standards

- Module README with setup instructions
- Component documentation with Storybook
- API documentation for backend endpoints
- User guide for module functionality

## Future Module Examples

### Potential New Modules

- **ASL Grammar**: Advanced grammar and sentence structure
- **Fingerspelling**: Letter-by-letter spelling practice
- **Conversation**: Interactive dialogue practice
- **Assessment**: Skill evaluation and certification
- **Community**: Social learning and peer interaction

### Module Addition Process

1. Create module directory structure
2. Implement module interface
3. Develop module components and services
4. Add backend API endpoints and models
5. Write comprehensive tests
6. Register module with ModuleManager
7. Update navigation and routing

## References

- [Micro-frontend Architecture](https://micro-frontends.org/)
- [Plugin Architecture Patterns](https://www.oreilly.com/library/view/software-architecture-patterns/9781491971437/ch05.html)
- [React Component Composition](https://react.dev/learn/passing-props-to-a-component)
- [FastAPI Modular Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
