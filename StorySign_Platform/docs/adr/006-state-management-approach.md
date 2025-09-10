# ADR-006: Frontend State Management Approach

## Status

Accepted

## Context

The StorySign platform requires sophisticated state management to handle:

- User authentication state across the application
- Webcam and video stream management
- WebSocket connection state and real-time data
- Learning module progress and session data
- UI state for complex multi-step workflows
- Accessibility state (focus management, screen reader announcements)

The solution must be lightweight, maintainable, and integrate well with React's component lifecycle.

## Decision

We have chosen a **Custom Hooks + React Context** approach for state management, avoiding external state management libraries.

## Consequences

### Positive

- **No External Dependencies**: Reduces bundle size and eliminates third-party library risks
- **React Native**: Uses React's built-in state management capabilities
- **Type Safety**: Full TypeScript support without additional configuration
- **Simplicity**: Easier to understand and maintain for team members
- **Performance**: Optimized re-renders through careful context splitting
- **Accessibility Integration**: Direct integration with React's accessibility features
- **Testing**: Simpler testing without mocking external state libraries

### Negative

- **Boilerplate**: More manual setup compared to libraries like Redux Toolkit
- **Performance Considerations**: Requires careful context design to avoid unnecessary re-renders
- **DevTools**: No specialized debugging tools like Redux DevTools
- **Complex State Logic**: May become unwieldy for very complex state interactions

## Implementation Strategy

### 1. Custom Hooks for Stateful Logic

```javascript
// hooks/useWebcam.js
const useWebcam = () => {
  const [stream, setStream] = useState(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState(null);

  const startWebcam = useCallback(async () => {
    // Webcam logic with proper cleanup
  }, []);

  const stopWebcam = useCallback(() => {
    // Cleanup logic
  }, [stream]);

  return { stream, isActive, error, startWebcam, stopWebcam };
};
```

### 2. Context Providers for Global State

```javascript
// contexts/AuthContext.js
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Authentication methods
  const login = useCallback(async (credentials) => {
    // Login logic
  }, []);

  const logout = useCallback(() => {
    // Logout logic
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      isLoading,
      login,
      logout,
      isAuthenticated: !!token,
    }),
    [user, token, isLoading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

### 3. Context Splitting for Performance

```javascript
// Separate contexts to prevent unnecessary re-renders
export const UserContext = createContext(); // User profile data
export const AuthStateContext = createContext(); // Authentication state
export const SessionContext = createContext(); // Current session data
```

### 4. Module-Specific State Management

```javascript
// modules/asl_world/ASLWorldProvider.js
export const ASLWorldProvider = ({ children }) => {
  const [currentStory, setCurrentStory] = useState(null);
  const [practiceSession, setPracticeSession] = useState(null);
  const [feedback, setFeedback] = useState([]);

  // Module-specific state management
  return (
    <ASLWorldContext.Provider
      value={{
        currentStory,
        practiceSession,
        feedback,
        // ... methods
      }}
    >
      {children}
    </ASLWorldContext.Provider>
  );
};
```

## Alternatives Considered

### Redux Toolkit

- **Pros**: Mature ecosystem, excellent DevTools, predictable state updates
- **Cons**: Additional bundle size, learning curve, overkill for our use case
- **Decision**: Too complex for our relatively simple state requirements

### Zustand

- **Pros**: Lightweight, simple API, good TypeScript support
- **Cons**: Another dependency, less React-native approach
- **Decision**: Custom hooks provide similar benefits without external dependency

### Jotai/Recoil

- **Pros**: Atomic state management, good performance characteristics
- **Cons**: Experimental status, additional complexity, learning curve
- **Decision**: Too experimental for production application

### MobX

- **Pros**: Simple reactive programming model, automatic dependency tracking
- **Cons**: Different paradigm from React, decorator syntax, bundle size
- **Decision**: Doesn't align well with functional React patterns

## Performance Optimizations

### 1. Context Splitting

```javascript
// Split contexts by update frequency
const FastUpdatingContext = createContext(); // WebSocket data
const SlowUpdatingContext = createContext(); // User preferences
```

### 2. Memoization

```javascript
const value = useMemo(
  () => ({
    // Expensive computations
  }),
  [dependencies]
);
```

### 3. Selective Subscriptions

```javascript
// Custom hook for selective context consumption
const useAuthState = () => {
  const context = useContext(AuthStateContext);
  return useMemo(
    () => ({
      isAuthenticated: context.isAuthenticated,
      isLoading: context.isLoading,
    }),
    [context.isAuthenticated, context.isLoading]
  );
};
```

## Testing Strategy

### 1. Hook Testing

```javascript
import { renderHook, act } from "@testing-library/react";
import { useWebcam } from "../hooks/useWebcam";

test("should start and stop webcam correctly", async () => {
  const { result } = renderHook(() => useWebcam());

  await act(async () => {
    await result.current.startWebcam();
  });

  expect(result.current.isActive).toBe(true);
});
```

### 2. Context Testing

```javascript
import { render, screen } from "@testing-library/react";
import { AuthProvider } from "../contexts/AuthContext";

const TestComponent = () => {
  const { isAuthenticated } = useAuth();
  return <div>{isAuthenticated ? "Logged in" : "Logged out"}</div>;
};

test("should provide authentication state", () => {
  render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );

  expect(screen.getByText("Logged out")).toBeInTheDocument();
});
```

## Migration Path

If the application grows and requires more sophisticated state management:

1. **Gradual Migration**: Can introduce Redux Toolkit for specific complex features
2. **Coexistence**: Custom hooks and Redux can work together
3. **Incremental Adoption**: Migrate module by module if needed

## References

- [React Context Documentation](https://react.dev/learn/passing-data-deeply-with-context)
- [React Hooks Documentation](https://react.dev/reference/react)
- [React Performance Optimization](https://react.dev/learn/render-and-commit)
- [Testing React Hooks](https://testing-library.com/docs/react-testing-library/api/#renderhook)
