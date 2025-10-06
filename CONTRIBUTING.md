# Contributing to StorySign Platform

Thank you for your interest in contributing to the StorySign Platform! This document provides guidelines and information for contributors.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Process](#development-process)
4. [Coding Standards](#coding-standards)
5. [Testing Requirements](#testing-requirements)
6. [Accessibility Requirements](#accessibility-requirements)
7. [Pull Request Process](#pull-request-process)
8. [Issue Reporting](#issue-reporting)
9. [Feature Requests](#feature-requests)
10. [Documentation](#documentation)

## Code of Conduct

### Our Pledge

We are committed to making participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Unacceptable Behavior

Examples of unacceptable behavior include:

- The use of sexualized language or imagery and unwelcome sexual attention or advances
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, please ensure you have:

- Read the [Developer Onboarding Guide](./docs/DEVELOPER_ONBOARDING.md)
- Set up your development environment
- Familiarized yourself with the [Architecture Documentation](./docs/ARCHITECTURE.md)
- Reviewed the [Coding Standards](./docs/CODING_STANDARDS.md)

### First-Time Contributors

If you're new to the project:

1. Look for issues labeled `good first issue` or `help wanted`
2. Comment on the issue to express interest
3. Wait for maintainer assignment before starting work
4. Ask questions if anything is unclear

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/storysign-platform.git
cd storysign-platform/StorySign_Platform

# Follow setup instructions in Developer Onboarding Guide
# Frontend setup
cd frontend && npm install && npm start

# Backend setup
cd backend && pip install -r requirements.txt && python main.py
```

## Development Process

### 1. Issue Assignment

- **Check existing issues** before starting work
- **Comment on issues** to request assignment
- **Wait for assignment** before beginning development
- **Ask questions** if requirements are unclear

### 2. Branch Strategy

We use a Git Flow-inspired branching strategy:

```bash
# Main branches
main          # Production-ready code
develop       # Integration branch for features

# Supporting branches
feature/*     # New features
fix/*         # Bug fixes
hotfix/*      # Critical production fixes
release/*     # Release preparation
```

### 3. Feature Development Workflow

#### Step 1: Create Feature Branch

```bash
# Update develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/issue-number-short-description

# Example
git checkout -b feature/123-user-authentication
```

#### Step 2: Development

1. **Write tests first** (Test-Driven Development)
2. **Implement the feature** following coding standards
3. **Ensure accessibility compliance**
4. **Update documentation** as needed
5. **Test thoroughly** (unit, integration, manual)

#### Step 3: Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

# Examples
feat(auth): add JWT authentication system
fix(video): resolve webcam initialization issue
docs(api): update authentication endpoints
test(hooks): add comprehensive useWebcam tests
```

**Commit Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

#### Step 4: Pre-commit Checks

Before committing, ensure:

```bash
# Frontend checks
cd frontend
npm run lint          # ESLint checks
npm run test          # Unit tests
npm run test:a11y     # Accessibility tests
npm run build         # Build verification

# Backend checks
cd backend
black .               # Code formatting
isort .               # Import sorting
flake8 .              # Linting
python -m pytest     # Unit tests
```

## Coding Standards

### General Principles

- **Accessibility First**: All features must be accessible (WCAG 2.1 AA)
- **Performance Conscious**: Consider performance impact of changes
- **Security Minded**: Follow security best practices
- **Test Coverage**: Maintain high test coverage (>80%)
- **Documentation**: Document complex logic and public APIs

### Frontend Standards (React)

#### Component Structure

```javascript
/**
 * ComponentName - Brief description
 *
 * @param {Object} props - Component props
 * @param {string} props.title - Title to display
 * @param {Function} props.onClick - Click handler
 * @returns {JSX.Element} Rendered component
 */
const ComponentName = ({ title, onClick, ...props }) => {
  // Hooks
  const [isLoading, setIsLoading] = useState(false);

  // Event handlers
  const handleClick = useCallback(async () => {
    setIsLoading(true);
    try {
      await onClick();
    } finally {
      setIsLoading(false);
    }
  }, [onClick]);

  // Render
  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading ? "Loading..." : title}
    </button>
  );
};

ComponentName.propTypes = {
  title: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default ComponentName;
```

#### Accessibility Requirements

```javascript
// ✅ Good - Accessible component
const AccessibleButton = ({ children, onClick, disabled }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    aria-label={typeof children === "string" ? children : "Action button"}
    className="btn"
  >
    {children}
  </button>
);

// ❌ Bad - Not accessible
const BadButton = ({ children, onClick }) => (
  <div onClick={onClick} className="btn">
    {children}
  </div>
);
```

### Backend Standards (Python/FastAPI)

#### API Endpoint Structure

```python
@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create a new user account with the provided information"
)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    """
    Create a new user account.

    Args:
        user_data: User creation data
        current_user: Currently authenticated user
        service: User service instance

    Returns:
        Created user information

    Raises:
        HTTPException: If creation fails or user lacks permissions
    """
    try:
        # Validate permissions
        if not current_user.can_create_users():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        # Create user
        user = await service.create_user(user_data)
        return UserResponse.from_orm(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

#### Service Layer Pattern

```python
class UserService:
    """Service for user-related business logic."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user with validation.

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            ValueError: If validation fails
        """
        # Validate business rules
        await self._validate_user_data(user_data)

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        user = await self.repository.create({
            **user_data.dict(exclude={'password'}),
            'hashed_password': hashed_password,
            'created_at': datetime.utcnow()
        })

        return user

    async def _validate_user_data(self, user_data: UserCreate) -> None:
        """Validate user data according to business rules."""
        # Check for existing email
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Validate password strength
        if len(user_data.password) < 8:
            raise ValueError("Password must be at least 8 characters")
```

## Testing Requirements

### Test Coverage Requirements

- **Minimum 80% code coverage** for new code
- **100% coverage** for critical security functions
- **Accessibility tests** for all UI components
- **Integration tests** for API endpoints
- **End-to-end tests** for critical user journeys

### Frontend Testing

#### Unit Tests

```javascript
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import UserProfile from "./UserProfile";

expect.extend(toHaveNoViolations);

describe("UserProfile", () => {
  const mockUser = {
    id: 1,
    name: "John Doe",
    email: "john@example.com",
  };

  it("renders user information", () => {
    render(<UserProfile user={mockUser} />);
    expect(screen.getByText("John Doe")).toBeInTheDocument();
  });

  it("is accessible", async () => {
    const { container } = render(<UserProfile user={mockUser} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("handles edit action", async () => {
    const mockOnEdit = jest.fn();
    render(<UserProfile user={mockUser} onEdit={mockOnEdit} />);

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    await waitFor(() => {
      expect(mockOnEdit).toHaveBeenCalledWith(mockUser);
    });
  });
});
```

#### Accessibility Testing

```javascript
// Test keyboard navigation
it("supports keyboard navigation", () => {
  render(<NavigationMenu />);
  const firstItem = screen.getByRole("menuitem", { name: /home/i });

  firstItem.focus();
  expect(firstItem).toHaveFocus();

  fireEvent.keyDown(firstItem, { key: "ArrowDown" });
  const secondItem = screen.getByRole("menuitem", { name: /about/i });
  expect(secondItem).toHaveFocus();
});

// Test screen reader announcements
it("announces status changes to screen readers", async () => {
  render(<StatusComponent />);
  const liveRegion = screen.getByRole("status");

  fireEvent.click(screen.getByRole("button", { name: /save/i }));

  await waitFor(() => {
    expect(liveRegion).toHaveTextContent("Changes saved successfully");
  });
});
```

### Backend Testing

#### Unit Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock
from backend.services.user_service import UserService

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def user_service(mock_repository):
    return UserService(mock_repository)

@pytest.mark.asyncio
async def test_create_user_success(user_service, mock_repository):
    # Arrange
    user_data = UserCreate(email="test@example.com", password="password123")
    mock_repository.get_by_email = AsyncMock(return_value=None)
    mock_repository.create = AsyncMock(return_value=Mock(id=1))

    # Act
    result = await user_service.create_user(user_data)

    # Assert
    assert result.id == 1
    mock_repository.create.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_duplicate_email(user_service, mock_repository):
    # Arrange
    user_data = UserCreate(email="existing@example.com", password="password123")
    mock_repository.get_by_email = AsyncMock(return_value=Mock(id=1))

    # Act & Assert
    with pytest.raises(ValueError, match="Email already registered"):
        await user_service.create_user(user_data)
```

#### Integration Tests

```python
import pytest
from httpx import AsyncClient
from backend.main import app

@pytest.mark.asyncio
async def test_create_user_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/users", json={
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "password" not in data  # Ensure password not returned
```

## Accessibility Requirements

All contributions must meet **WCAG 2.1 AA** standards:

### Required Accessibility Features

- **Keyboard Navigation**: All interactive elements must be keyboard accessible
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **Color Contrast**: Minimum 4.5:1 ratio for normal text, 3:1 for large text
- **Focus Management**: Visible focus indicators and logical tab order
- **Alternative Text**: All images must have appropriate alt text
- **Form Labels**: All form inputs must have associated labels

### Accessibility Testing Checklist

```markdown
- [ ] All interactive elements are keyboard accessible
- [ ] Tab order is logical and intuitive
- [ ] Focus indicators are visible and clear
- [ ] All images have appropriate alt text
- [ ] Form inputs have associated labels
- [ ] Color is not the only way to convey information
- [ ] Text has sufficient color contrast
- [ ] Page has proper heading structure (h1, h2, h3, etc.)
- [ ] ARIA labels are used appropriately
- [ ] Screen reader testing completed
- [ ] Automated accessibility tests pass
```

### Accessibility Testing Tools

```bash
# Automated testing
npm run test:a11y

# Manual testing tools
# - Screen reader (NVDA, JAWS, VoiceOver)
# - Keyboard-only navigation
# - Color contrast analyzer
# - axe DevTools browser extension
```

## Pull Request Process

### 1. Before Creating a Pull Request

- [ ] Code follows project coding standards
- [ ] All tests pass locally
- [ ] Accessibility requirements met
- [ ] Documentation updated if needed
- [ ] Self-review completed

### 2. Pull Request Template

```markdown
## Description

Brief description of the changes made.

## Related Issue

Fixes #(issue number)

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Accessibility tests pass
- [ ] Manual testing completed

## Accessibility Checklist

- [ ] Keyboard navigation works correctly
- [ ] Screen reader compatibility verified
- [ ] Color contrast meets WCAG standards
- [ ] Focus management implemented properly
- [ ] ARIA labels added where appropriate

## Screenshots (if applicable)

Add screenshots to help explain your changes.

## Additional Notes

Any additional information that reviewers should know.
```

### 3. Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one maintainer approval required
3. **Accessibility Review**: Accessibility compliance verified
4. **Testing**: All tests must pass
5. **Documentation**: Documentation review if applicable

### 4. Merge Requirements

- [ ] All CI checks pass
- [ ] At least 1 maintainer approval
- [ ] No unresolved review comments
- [ ] Branch is up to date with target branch
- [ ] Accessibility compliance verified

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

```markdown
**Bug Description**
A clear and concise description of what the bug is.

**Steps to Reproduce**

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Actual Behavior**
A clear and concise description of what actually happened.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment**

- OS: [e.g. iOS, Windows, macOS]
- Browser: [e.g. chrome, safari]
- Version: [e.g. 22]
- Device: [e.g. iPhone6, Desktop]

**Additional Context**
Add any other context about the problem here.
```

### Security Issues

For security vulnerabilities:

1. **Do NOT create a public issue**
2. **Email security@storysign.com** with details
3. **Include steps to reproduce** if possible
4. **Wait for response** before public disclosure

## Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Accessibility Considerations**
How will this feature work for users with disabilities?

**Additional context**
Add any other context or screenshots about the feature request here.
```

### Feature Development Process

1. **Discussion**: Feature requests are discussed in GitHub issues
2. **Design**: Technical design document created if needed
3. **Approval**: Maintainer approval required before implementation
4. **Implementation**: Follow standard development process
5. **Review**: Thorough review including accessibility compliance

## Documentation

### Documentation Requirements

- **Code Comments**: Complex logic must be commented
- **API Documentation**: All public APIs must be documented
- **README Updates**: Update relevant README files
- **Architecture Docs**: Update if architectural changes made
- **User Guides**: Update user-facing documentation

### Documentation Standards

- Use clear, concise language
- Include code examples where helpful
- Keep documentation up to date with code changes
- Follow established documentation templates

## Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **GitHub contributors** section
- **Annual contributor highlights**

## Questions?

If you have questions about contributing:

1. **Check existing documentation** first
2. **Search closed issues** for similar questions
3. **Ask in GitHub Discussions**
4. **Contact maintainers** directly if needed

Thank you for contributing to StorySign Platform! 🎉
