# Contributing to StorySign ASL Platform

Thank you for your interest in contributing to the StorySign ASL Platform! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd StorySign_Platform
   ```

2. **Set up the development environment**

   ```bash
   ./setup_dev.sh
   ```

3. **Verify the setup**
   ```bash
   python verify_setup.py
   ```

## Development Workflow

### Backend Development

```bash
cd backend
conda activate storysign-backend
python dev_server.py
```

### Frontend Development

```bash
cd frontend
npm run electron-dev
```

## Code Style Guidelines

### Python (Backend)

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Use meaningful variable and function names

### JavaScript/React (Frontend)

- Use ES6+ features
- Follow React best practices
- Use functional components with hooks
- Write clear, descriptive component names

## Testing

### Backend Tests

```bash
cd backend
conda activate storysign-backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Commit Guidelines

- Use clear, descriptive commit messages
- Follow conventional commit format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:

```
feat(backend): add ASL gesture recognition endpoint
fix(frontend): resolve video stream connection issue
docs(readme): update installation instructions
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit them
4. Push to your fork: `git push origin feature/your-feature-name`
5. Create a pull request with a clear description

## Issue Reporting

When reporting issues, please include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Node.js version)
- Screenshots or error logs if applicable

## Code Review

All contributions require code review. Please:

- Ensure your code follows the style guidelines
- Include tests for new functionality
- Update documentation as needed
- Respond to feedback constructively

## Questions?

If you have questions about contributing, please:

- Check existing issues and discussions
- Create a new issue with the "question" label
- Reach out to the maintainers

Thank you for contributing to making ASL learning more accessible!
