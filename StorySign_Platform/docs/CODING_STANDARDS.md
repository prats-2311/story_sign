# StorySign Platform Coding Standards

## Overview

This document outlines the coding standards, patterns, and best practices for the StorySign Platform. Following these guidelines ensures consistency, maintainability, and accessibility across the codebase.

## Table of Contents

1. [General Principles](#general-principles)
2. [JavaScript/React Standards](#javascriptreact-standards)
3. [Python/FastAPI Standards](#pythonfastapi-standards)
4. [File Organization](#file-organization)
5. [Naming Conventions](#naming-conventions)
6. [Documentation Standards](#documentation-standards)
7. [Accessibility Guidelines](#accessibility-guidelines)
8. [Testing Standards](#testing-standards)
9. [Performance Guidelines](#performance-guidelines)
10. [Security Best Practices](#security-best-practices)

## General Principles

### Code Quality Principles

- **Readability First**: Code should be self-documenting and easy to understand
- **Consistency**: Follow established patterns throughout the codebase
- **Modularity**: Write reusable, composable components and functions
- **Accessibility**: Ensure all code supports users with disabilities
- **Performance**: Consider performance implications of all code changes
- **Security**: Follow security best practices for all user-facing features

### SOLID Principles

- **Single Responsibility**: Each function/class should have one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Derived classes must be substitutable for base classes
- **Interface Segregation**: Clients shouldn't depend on interfaces they don't use
- **Dependency Inversion**: Depend on abstractions, not concretions

## JavaScript/React Standards

### Code Formatting

Use Prettier with the following configuration:

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": false,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
```

### ESLint Configuration

```json
{
  "extends": ["react-app", "react-app/jest", "plugin:jsx-a11y/recommended"],
  "plugins": ["jsx-a11y"],
  "rules": {
    "jsx-a11y/anchor-is-valid": "error",
    "jsx-a11y/alt-text": "error",
    "jsx-a11y/aria-props": "error",
    "jsx-a11y/aria-proptypes": "error",
    "jsx-a11y/aria-unsupported-elements": "error",
    "jsx-a11y/role-has-required-aria-props": "error",
    "jsx-a11y/role-supports-aria-props": "error"
  }
}
```

### Component Structure

#### Functional Components with Hooks

```javascript
/**
 * ComponentName - Brief description of component purpose
 *
 * @param {Object} props - Component props
 * @param {string} props.title - Title to display
 * @param {Function} props.onClick - Click handler
 * @param {boolean} props.disabled - Whether component is disabled
 * @param {string} props.ariaLabel - Accessibility label
 * @returns {JSX.Element} Rendered component
 */
const ComponentName = ({
  title,
  onClick,
  disabled = false,
  ariaLabel,
  ...props
}) => {
  // State declarations
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Refs
  const buttonRef = useRef(null);

  // Custom hooks
  const { user } = useAuth();
  const { sendMessage } = useWebSocket();

  // Memoized values
  const computedValue = useMemo(() => {
    return expensiveCalculation(title);
  }, [title]);

  // Callbacks
  const handleClick = useCallback(async () => {
    if (disabled || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      await onClick();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [onClick, disabled, isLoading]);

  // Effects
  useEffect(() => {
    // Effect logic
    return () => {
      // Cleanup
    };
  }, []);

  // Early returns for loading/error states
  if (error) {
    return <ErrorMessage message={error} />;
  }

  // Main render
  return (
    <button
      ref={buttonRef}
      className={`component-name ${disabled ? "disabled" : ""}`}
      onClick={handleClick}
      disabled={disabled || isLoading}
      aria-label={ariaLabel || title}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading ? <LoadingSpinner /> : title}
    </button>
  );
};

// PropTypes for development
ComponentName.propTypes = {
  title: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  ariaLabel: PropTypes.string,
};

export default ComponentName;
```

#### Custom Hooks Pattern

```javascript
/**
 * useCustomHook - Description of hook purpose
 *
 * @param {string} initialValue - Initial value for the hook
 * @param {Object} options - Configuration options
 * @returns {Object} Hook return value with state and actions
 */
const useCustomHook = (initialValue, options = {}) => {
  // State management
  const [value, setValue] = useState(initialValue);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Configuration with defaults
  const config = {
    autoSave: true,
    debounceMs: 300,
    ...options,
  };

  // Memoized actions
  const updateValue = useCallback(
    async (newValue) => {
      setIsLoading(true);
      setError(null);

      try {
        // Update logic
        setValue(newValue);

        if (config.autoSave) {
          await saveValue(newValue);
        }
      } catch (err) {
        setError(err);
      } finally {
        setIsLoading(false);
      }
    },
    [config.autoSave]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cleanup logic
    };
  }, []);

  return {
    value,
    isLoading,
    error,
    updateValue,
    // Computed values
    hasValue: value !== null && value !== undefined,
    isValid: !error && value !== null,
  };
};
```

### Context Providers

```javascript
/**
 * ContextProvider - Manages global state for specific domain
 */
const SomeContext = createContext();

export const SomeProvider = ({ children }) => {
  // State management
  const [state, setState] = useState(initialState);

  // Actions
  const actions = useMemo(
    () => ({
      updateState: (newState) => setState((prev) => ({ ...prev, ...newState })),
      resetState: () => setState(initialState),
    }),
    []
  );

  // Memoized context value
  const contextValue = useMemo(
    () => ({
      ...state,
      ...actions,
    }),
    [state, actions]
  );

  return (
    <SomeContext.Provider value={contextValue}>{children}</SomeContext.Provider>
  );
};

// Custom hook for consuming context
export const useSome = () => {
  const context = useContext(SomeContext);
  if (!context) {
    throw new Error("useSome must be used within SomeProvider");
  }
  return context;
};
```

## Python/FastAPI Standards

### Code Formatting

Use Black with the following configuration:

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### Import Organization (isort)

```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["backend"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]
```

### FastAPI Route Structure

```python
"""
Module: api/module_name.py
Description: API endpoints for ModuleName functionality
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..core.auth import get_current_user
from ..models.user import User
from ..models.module_name import ModuleModel, ModuleCreate, ModuleUpdate
from ..services.module_service import ModuleService
from ..repositories.module_repository import ModuleRepository

# Router configuration
router = APIRouter(
    prefix="/api/v1/module-name",
    tags=["module-name"],
    responses={404: {"description": "Not found"}}
)

# Dependency injection
async def get_module_service(
    db: AsyncSession = Depends(get_db_session)
) -> ModuleService:
    """Get module service instance with database session."""
    repository = ModuleRepository(db)
    return ModuleService(repository)

@router.post(
    "/",
    response_model=ModuleModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create new module item",
    description="Create a new module item with the provided data"
)
async def create_module_item(
    item_data: ModuleCreate,
    current_user: User = Depends(get_current_user),
    service: ModuleService = Depends(get_module_service)
) -> ModuleModel:
    """
    Create a new module item.

    Args:
        item_data: Data for creating the module item
        current_user: Currently authenticated user
        service: Module service instance

    Returns:
        Created module item

    Raises:
        HTTPException: If creation fails or user lacks permissions
    """
    try:
        # Validate user permissions
        if not current_user.has_permission("module:create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create module items"
            )

        # Create item through service
        item = await service.create_item(
            user_id=current_user.id,
            item_data=item_data
        )

        return item

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log error for debugging
        logger.error(f"Error creating module item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/{item_id}",
    response_model=ModuleModel,
    summary="Get module item by ID",
    description="Retrieve a specific module item by its ID"
)
async def get_module_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    service: ModuleService = Depends(get_module_service)
) -> ModuleModel:
    """
    Get module item by ID.

    Args:
        item_id: ID of the module item to retrieve
        current_user: Currently authenticated user
        service: Module service instance

    Returns:
        Module item data

    Raises:
        HTTPException: If item not found or access denied
    """
    item = await service.get_item_by_id(item_id, current_user.id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module item with ID {item_id} not found"
        )

    return item
```

### Service Layer Pattern

```python
"""
Module: services/module_service.py
Description: Business logic for ModuleName functionality
"""

from typing import List, Optional
from datetime import datetime

from ..models.module_name import ModuleModel, ModuleCreate, ModuleUpdate
from ..repositories.module_repository import ModuleRepository
from ..core.exceptions import ValidationError, NotFoundError

class ModuleService:
    """Service class for module business logic."""

    def __init__(self, repository: ModuleRepository):
        """
        Initialize service with repository dependency.

        Args:
            repository: Module repository instance
        """
        self.repository = repository

    async def create_item(
        self,
        user_id: int,
        item_data: ModuleCreate
    ) -> ModuleModel:
        """
        Create a new module item.

        Args:
            user_id: ID of the user creating the item
            item_data: Data for the new item

        Returns:
            Created module item

        Raises:
            ValidationError: If item data is invalid
        """
        # Validate business rules
        await self._validate_item_data(item_data)

        # Check user limits
        user_item_count = await self.repository.count_user_items(user_id)
        if user_item_count >= 100:  # Business rule example
            raise ValidationError("User has reached maximum item limit")

        # Create item
        item = await self.repository.create({
            **item_data.dict(),
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })

        return item

    async def get_item_by_id(
        self,
        item_id: int,
        user_id: int
    ) -> Optional[ModuleModel]:
        """
        Get module item by ID with user access check.

        Args:
            item_id: ID of the item to retrieve
            user_id: ID of the requesting user

        Returns:
            Module item if found and accessible, None otherwise
        """
        item = await self.repository.get_by_id(item_id)

        if not item:
            return None

        # Check user access
        if not await self._user_can_access_item(user_id, item):
            return None

        return item

    async def _validate_item_data(self, item_data: ModuleCreate) -> None:
        """
        Validate item data according to business rules.

        Args:
            item_data: Item data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Example validation
        if len(item_data.name) < 3:
            raise ValidationError("Item name must be at least 3 characters")

        # Check for duplicates
        existing = await self.repository.get_by_name(item_data.name)
        if existing:
            raise ValidationError("Item with this name already exists")

    async def _user_can_access_item(
        self,
        user_id: int,
        item: ModuleModel
    ) -> bool:
        """
        Check if user can access the item.

        Args:
            user_id: ID of the user
            item: Item to check access for

        Returns:
            True if user can access item, False otherwise
        """
        # Owner can always access
        if item.user_id == user_id:
            return True

        # Check if item is public
        if item.is_public:
            return True

        # Check shared access (implement as needed)
        return False
```

### Repository Pattern

```python
"""
Module: repositories/module_repository.py
Description: Data access layer for ModuleName
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from .base_repository import BaseRepository
from ..models.module_name import ModuleModel

class ModuleRepository(BaseRepository[ModuleModel]):
    """Repository for module data access."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db_session: Async database session
        """
        super().__init__(ModuleModel, db_session)

    async def get_by_name(self, name: str) -> Optional[ModuleModel]:
        """
        Get module item by name.

        Args:
            name: Name to search for

        Returns:
            Module item if found, None otherwise
        """
        query = select(ModuleModel).where(ModuleModel.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_items(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[ModuleModel]:
        """
        Get items belonging to a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List of user's module items
        """
        query = (
            select(ModuleModel)
            .where(ModuleModel.user_id == user_id)
            .order_by(ModuleModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_user_items(self, user_id: int) -> int:
        """
        Count items belonging to a specific user.

        Args:
            user_id: ID of the user

        Returns:
            Number of items owned by user
        """
        query = select(func.count(ModuleModel.id)).where(
            ModuleModel.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def search_items(
        self,
        search_term: str,
        user_id: Optional[int] = None
    ) -> List[ModuleModel]:
        """
        Search for items by name or description.

        Args:
            search_term: Term to search for
            user_id: Optional user ID to filter by

        Returns:
            List of matching module items
        """
        query = select(ModuleModel).where(
            ModuleModel.name.ilike(f"%{search_term}%") |
            ModuleModel.description.ilike(f"%{search_term}%")
        )

        if user_id:
            query = query.where(ModuleModel.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalars().all()
```

## File Organization

### Frontend Directory Structure

```
src/
├── components/           # Reusable UI components
│   ├── common/          # Basic components (Button, Modal, etc.)
│   ├── forms/           # Form-specific components
│   ├── navigation/      # Navigation components
│   └── video/           # Video processing components
├── modules/             # Learning modules
│   ├── asl_world/       # ASL World module
│   ├── harmony/         # Harmony module
│   └── reconnect/       # Reconnect module
├── pages/               # Top-level page components
├── hooks/               # Custom React hooks
├── contexts/            # React Context providers
├── services/            # API communication
├── utils/               # Utility functions
├── styles/              # Global styles
├── tests/               # Test suites
└── docs/                # Component documentation
```

### Backend Directory Structure

```
backend/
├── api/                 # FastAPI route handlers
├── services/            # Business logic layer
├── repositories/        # Data access layer
├── models/              # Pydantic data models
├── core/                # Core infrastructure
├── middleware/          # Request/response middleware
├── migrations/          # Database migrations
├── tests/               # Test suites
└── config/              # Configuration files
```

## Naming Conventions

### JavaScript/React

- **Components**: PascalCase (`UserProfile`, `VideoDisplayPanel`)
- **Files**: PascalCase for components, camelCase for utilities (`UserProfile.js`, `apiService.js`)
- **Variables/Functions**: camelCase (`userName`, `handleClick`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`, `MAX_RETRY_ATTEMPTS`)
- **CSS Classes**: kebab-case (`user-profile`, `video-display-panel`)

### Python

- **Classes**: PascalCase (`UserService`, `ModuleRepository`)
- **Files/Modules**: snake_case (`user_service.py`, `module_repository.py`)
- **Functions/Variables**: snake_case (`get_user_by_id`, `user_name`)
- **Constants**: UPPER_SNAKE_CASE (`DATABASE_URL`, `JWT_SECRET_KEY`)

### Database

- **Tables**: snake_case (`user_profiles`, `learning_sessions`)
- **Columns**: snake_case (`user_id`, `created_at`)
- **Indexes**: `idx_table_column` (`idx_users_email`)

## Documentation Standards

### JSDoc for JavaScript

```javascript
/**
 * Brief description of the function
 *
 * Longer description if needed, explaining the purpose,
 * behavior, and any important details.
 *
 * @param {string} param1 - Description of parameter
 * @param {Object} param2 - Description of object parameter
 * @param {number} param2.value - Description of object property
 * @param {boolean} [param3=false] - Optional parameter with default
 * @returns {Promise<Object>} Description of return value
 * @throws {Error} When validation fails
 *
 * @example
 * const result = await functionName('test', { value: 42 });
 * console.log(result.data);
 */
```

### Python Docstrings

```python
def function_name(param1: str, param2: dict, param3: bool = False) -> dict:
    """
    Brief description of the function.

    Longer description if needed, explaining the purpose,
    behavior, and any important details.

    Args:
        param1: Description of parameter
        param2: Description of dictionary parameter
        param3: Optional parameter with default value

    Returns:
        Dictionary containing the result data

    Raises:
        ValueError: If param1 is empty
        TypeError: If param2 is not a dictionary

    Example:
        >>> result = function_name('test', {'value': 42})
        >>> print(result['data'])
        'processed_data'
    """
```

### README Templates

#### Component README

````markdown
# ComponentName

Brief description of what the component does.

## Usage

```jsx
import ComponentName from "./ComponentName";

<ComponentName prop1="value" prop2={42} onAction={handleAction} />;
```
````

## Props

| Prop     | Type     | Default | Description                 |
| -------- | -------- | ------- | --------------------------- |
| prop1    | string   | -       | Description of prop1        |
| prop2    | number   | 0       | Description of prop2        |
| onAction | function | -       | Callback when action occurs |

## Accessibility

- Supports keyboard navigation
- Includes proper ARIA labels
- Compatible with screen readers

## Examples

### Basic Usage

[Example code]

### Advanced Usage

[Example code]

````

## Accessibility Guidelines

### WCAG 2.1 AA Compliance
- **Keyboard Navigation**: All interactive elements must be keyboard accessible
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **Color Contrast**: Minimum 4.5:1 ratio for normal text, 3:1 for large text
- **Focus Management**: Visible focus indicators and logical tab order

### Implementation Patterns
```javascript
// Accessible button component
const AccessibleButton = ({ children, onClick, disabled, ariaLabel }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    aria-label={ariaLabel || children}
    className="btn"
    onKeyDown={(e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onClick();
      }
    }}
  >
    {children}
  </button>
);

// Accessible form with proper labels
const AccessibleForm = () => (
  <form>
    <label htmlFor="username">
      Username
      <input
        id="username"
        type="text"
        required
        aria-describedby="username-help"
      />
    </label>
    <div id="username-help" className="help-text">
      Enter your username (3-20 characters)
    </div>
  </form>
);
````

## Testing Standards

### Unit Test Structure

```javascript
describe("ComponentName", () => {
  // Setup and teardown
  beforeEach(() => {
    // Test setup
  });

  afterEach(() => {
    // Cleanup
  });

  describe("when rendered with default props", () => {
    it("should display the correct title", () => {
      // Test implementation
    });

    it("should be accessible", async () => {
      // Accessibility test
    });
  });

  describe("when user interacts", () => {
    it("should call onClick handler", () => {
      // Interaction test
    });
  });

  describe("error handling", () => {
    it("should display error message when API fails", () => {
      // Error test
    });
  });
});
```

### Integration Test Patterns

```javascript
describe("User Journey: ASL World Practice", () => {
  it("should complete full practice session", async () => {
    // 1. Login
    await loginUser();

    // 2. Navigate to ASL World
    await navigateToASLWorld();

    // 3. Start practice session
    await startPracticeSession();

    // 4. Complete practice
    await completePractice();

    // 5. Verify results
    expect(screen.getByText("Practice Complete")).toBeInTheDocument();
  });
});
```

## Performance Guidelines

### React Performance

- Use `useMemo` for expensive calculations
- Use `useCallback` for event handlers passed to child components
- Implement proper dependency arrays in hooks
- Use `React.memo` for components that render frequently
- Implement code splitting with `React.lazy`

### Bundle Optimization

- Import only needed functions from libraries
- Use dynamic imports for large dependencies
- Implement proper tree shaking
- Optimize images and assets

### Backend Performance

- Use async/await for all I/O operations
- Implement proper database indexing
- Use connection pooling
- Cache frequently accessed data
- Implement pagination for large datasets

## Security Best Practices

### Frontend Security

- Sanitize all user inputs
- Use HTTPS for all communications
- Implement proper CORS policies
- Validate data on both client and server
- Use secure authentication tokens

### Backend Security

- Validate and sanitize all inputs
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Use secure password hashing (bcrypt)
- Implement rate limiting
- Log security events

### Example Secure Patterns

```python
# Secure password hashing
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Input validation
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    email: str
    password: str

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
```

This coding standards document should be regularly updated as the project evolves and new patterns emerge.
