# Developer Onboarding Guide

## Welcome to StorySign Platform Development

This guide will help you get up and running with the StorySign Platform development environment and understand our development workflow.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Code Review Process](#code-review-process)
7. [Deployment Process](#deployment-process)
8. [Troubleshooting](#troubleshooting)
9. [Resources](#resources)

## Prerequisites

### Required Software

- **Node.js**: Version 18+ (use `.nvmrc` file for exact version)
- **Python**: Version 3.11+
- **Git**: Latest version
- **Docker**: For database and service containers (optional but recommended)

### Recommended Tools

- **VS Code**: With recommended extensions (see `.vscode/extensions.json`)
- **Postman**: For API testing
- **Chrome DevTools**: For frontend debugging
- **React Developer Tools**: Browser extension
- **Python extension for VS Code**: For backend development

### Accounts Needed

- **GitHub**: Access to the repository
- **Netlify**: For frontend deployment (if deploying)
- **Render**: For backend deployment (if deploying)
- **TiDB Cloud**: For database access (if working with production data)

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/storysign-platform.git
cd storysign-platform/StorySign_Platform
```

### 2. Frontend Setup

```bash
cd frontend

# Install Node.js version from .nvmrc
nvm use

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Start development server
npm start
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run database migrations (if using local database)
python run_migrations.py

# Start development server
python main.py
```

### 4. Environment Variables

#### Frontend (.env.local)

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=development
```

#### Backend (.env)

```bash
# Database
DATABASE_URL=sqlite:///./storysign.db  # For local development
# DATABASE_URL=mysql://user:pass@localhost/storysign  # For MySQL

# Authentication
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External APIs
GROQ_API_KEY=your-groq-api-key  # Optional for local development
GROQ_BASE_URL=https://api.groq.com/openai/v1

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### 5. Verify Setup

```bash
# Test frontend
cd frontend
npm test -- --watchAll=false

# Test backend
cd backend
python -m pytest tests/ -v

# Test integration
# Start both frontend and backend, then visit http://localhost:3000
```

## Project Structure

### High-Level Overview

```
StorySign_Platform/
├── frontend/           # React application
├── backend/            # FastAPI application
├── mobile/             # React Native app (future)
├── docs/               # Documentation
├── scripts/            # Deployment and utility scripts
└── README.md
```

### Frontend Structure

```
frontend/src/
├── components/         # Reusable UI components
│   ├── common/        # Basic components (Button, Modal)
│   ├── auth/          # Authentication components
│   ├── video/         # Video processing components
│   └── navigation/    # Navigation components
├── modules/           # Learning modules
│   ├── asl_world/     # ASL World module
│   ├── harmony/       # Harmony module
│   └── reconnect/     # Reconnect module
├── pages/             # Top-level page components
├── hooks/             # Custom React hooks
├── contexts/          # React Context providers
├── services/          # API communication
├── utils/             # Utility functions
├── styles/            # Global styles
└── tests/             # Test suites
```

### Backend Structure

```
backend/
├── api/               # FastAPI route handlers
├── services/          # Business logic layer
├── repositories/      # Data access layer
├── models/            # Pydantic data models
├── core/              # Core infrastructure
├── middleware/        # Request/response middleware
├── migrations/        # Database migrations
└── tests/             # Test suites
```

## Development Workflow

### 1. Feature Development Process

#### Step 1: Create Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

#### Step 2: Development

1. **Write Tests First** (TDD approach recommended)
2. **Implement Feature** following coding standards
3. **Test Locally** with both unit and integration tests
4. **Update Documentation** if needed

#### Step 3: Code Quality Checks

```bash
# Frontend checks
cd frontend
npm run lint
npm run test
npm run build  # Ensure it builds successfully

# Backend checks
cd backend
black .  # Format code
isort .  # Sort imports
flake8 .  # Lint code
python -m pytest tests/  # Run tests
```

#### Step 4: Commit and Push

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add user authentication system

- Implement JWT-based authentication
- Add login and registration forms
- Include proper error handling
- Add comprehensive tests"

# Push to remote
git push origin feature/your-feature-name
```

### 2. Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
feat(auth): add JWT authentication system
fix(video): resolve webcam black screen issue
docs(api): update authentication endpoint documentation
test(hooks): add tests for useWebcam hook
```

### 3. Branch Naming Convention

- `feature/feature-name`: New features
- `fix/bug-description`: Bug fixes
- `docs/documentation-update`: Documentation updates
- `refactor/component-name`: Code refactoring
- `test/test-description`: Test additions/updates

## Testing Guidelines

### Frontend Testing

#### Unit Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- UserProfile.test.js
```

#### Component Testing Example

```javascript
import { render, screen, fireEvent } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import UserProfile from "./UserProfile";

expect.extend(toHaveNoViolations);

describe("UserProfile", () => {
  const mockUser = {
    id: 1,
    name: "John Doe",
    email: "john@example.com",
  };

  it("renders user information correctly", () => {
    render(<UserProfile user={mockUser} />);

    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("john@example.com")).toBeInTheDocument();
  });

  it("should be accessible", async () => {
    const { container } = render(<UserProfile user={mockUser} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("calls onEdit when edit button is clicked", () => {
    const mockOnEdit = jest.fn();
    render(<UserProfile user={mockUser} onEdit={mockOnEdit} />);

    fireEvent.click(screen.getByRole("button", { name: /edit/i }));
    expect(mockOnEdit).toHaveBeenCalledWith(mockUser);
  });
});
```

### Backend Testing

#### Unit Tests

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=backend

# Run specific test file
python -m pytest tests/test_auth_service.py
```

#### Service Testing Example

```python
import pytest
from unittest.mock import Mock, AsyncMock
from backend.services.auth_service import AuthService
from backend.models.user import UserCreate

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def auth_service(mock_repository):
    return AuthService(mock_repository)

@pytest.mark.asyncio
async def test_create_user_success(auth_service, mock_repository):
    # Arrange
    user_data = UserCreate(
        email="test@example.com",
        password="securepassword123"
    )
    mock_repository.get_by_email = AsyncMock(return_value=None)
    mock_repository.create = AsyncMock(return_value=Mock(id=1))

    # Act
    result = await auth_service.create_user(user_data)

    # Assert
    assert result.id == 1
    mock_repository.create.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_duplicate_email(auth_service, mock_repository):
    # Arrange
    user_data = UserCreate(
        email="existing@example.com",
        password="securepassword123"
    )
    mock_repository.get_by_email = AsyncMock(return_value=Mock(id=1))

    # Act & Assert
    with pytest.raises(ValueError, match="Email already exists"):
        await auth_service.create_user(user_data)
```

### Integration Testing

```bash
# Frontend integration tests
npm run test:integration

# Backend integration tests
python -m pytest tests/integration/

# End-to-end tests
npm run test:e2e
```

## Code Review Process

### 1. Creating Pull Requests

#### PR Title Format

```
<type>(<scope>): <description>

Example: feat(auth): implement JWT authentication system
```

#### PR Description Template

```markdown
## Description

Brief description of the changes made.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Accessibility testing completed

## Screenshots (if applicable)

Add screenshots to help explain your changes.

## Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### 2. Review Guidelines

#### For Reviewers

- **Functionality**: Does the code work as intended?
- **Code Quality**: Is the code clean, readable, and maintainable?
- **Performance**: Are there any performance implications?
- **Security**: Are there any security concerns?
- **Accessibility**: Does the code maintain accessibility standards?
- **Tests**: Are there adequate tests for the changes?
- **Documentation**: Is documentation updated if needed?

#### Review Checklist

```markdown
- [ ] Code follows project coding standards
- [ ] All tests pass
- [ ] No security vulnerabilities introduced
- [ ] Accessibility requirements met
- [ ] Performance impact considered
- [ ] Documentation updated if needed
- [ ] Breaking changes properly documented
```

### 3. Approval Process

- **Minimum 1 approval** required for merging
- **All CI checks must pass**
- **No unresolved conversations**
- **Branch must be up to date with main**

## Deployment Process

### Development Environment

- **Frontend**: Automatically deployed on push to `develop` branch
- **Backend**: Manually deployed to staging environment

### Production Environment

- **Frontend**: Deployed via Netlify on merge to `main`
- **Backend**: Deployed via Render on merge to `main`

### Deployment Checklist

```markdown
- [ ] All tests pass in CI
- [ ] Code review completed and approved
- [ ] Database migrations tested (if applicable)
- [ ] Environment variables configured
- [ ] Monitoring and logging configured
- [ ] Rollback plan prepared
```

## Troubleshooting

### Common Issues

#### Frontend Issues

**Issue: `npm install` fails**

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

**Issue: Tests fail with "Cannot resolve module"**

```bash
# Check if all dependencies are installed
npm install

# Clear Jest cache
npm test -- --clearCache
```

**Issue: Webcam not working in development**

- Ensure you're using HTTPS or localhost
- Check browser permissions
- Verify camera is not in use by another application

#### Backend Issues

**Issue: Database connection fails**

```bash
# Check database URL in .env file
# Ensure database server is running
# Verify credentials and permissions
```

**Issue: Import errors in Python**

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: MediaPipe installation fails**

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-dev

# Install MediaPipe
pip install mediapipe

# If still failing, try conda
conda install -c conda-forge mediapipe
```

### Getting Help

1. **Check Documentation**: Review relevant documentation first
2. **Search Issues**: Look for similar issues in GitHub
3. **Ask Team**: Reach out to team members on Slack/Discord
4. **Create Issue**: If it's a bug, create a GitHub issue with details

## Resources

### Documentation

- [Architecture Documentation](./ARCHITECTURE.md)
- [Coding Standards](./CODING_STANDARDS.md)
- [API Documentation](./API.md)
- [Accessibility Guidelines](./frontend/src/docs/ACCESSIBILITY.md)

### External Resources

- [React Documentation](https://react.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MediaPipe Documentation](https://mediapipe.dev/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### Development Tools

- [React DevTools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
- [Axe DevTools](https://chrome.google.com/webstore/detail/axe-devtools-web-accessib/lhdoppojpmngadmnindnejefpokejbdd)
- [Postman](https://www.postman.com/)
- [VS Code Extensions](./.vscode/extensions.json)

### Community

- **Team Slack**: #storysign-dev
- **GitHub Discussions**: For feature discussions
- **Weekly Standups**: Mondays at 10 AM
- **Code Review Sessions**: Fridays at 2 PM

## Next Steps

After completing this onboarding:

1. **Set up your development environment**
2. **Run the test suite** to ensure everything works
3. **Pick up your first issue** from the GitHub project board
4. **Join the team Slack channel**
5. **Attend the next team meeting**
6. **Review the codebase** to familiarize yourself with patterns

Welcome to the team! 🎉
