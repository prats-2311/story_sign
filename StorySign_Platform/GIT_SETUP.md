# Git Repository Setup Guide

This document provides instructions for setting up and managing the StorySign ASL Platform Git repository.

## Initial Repository Setup

### 1. Initialize Local Repository

If you haven't already initialized Git:

```bash
cd StorySign_Platform
git init
git add .
git commit -m "Initial commit: Project structure and development environment setup"
```

### 2. Connect to Remote Repository

```bash
# Add your remote repository
git remote add origin https://github.com/your-username/storysign-asl-platform.git

# Push to remote repository
git branch -M main
git push -u origin main
```

## Git Configuration Files

### `.gitignore`

Comprehensive ignore file covering:

- Operating system files (macOS, Windows, Linux)
- IDE and editor files
- Node.js dependencies and build artifacts
- Python cache and virtual environments
- Logs and temporary files
- Project-specific build outputs

### `.gitattributes`

Handles:

- Line ending normalization (LF for all text files)
- Binary file detection
- Language-specific file handling

### `.editorconfig`

Maintains consistent coding styles across different editors:

- UTF-8 encoding
- LF line endings
- Proper indentation for different file types
- Python: 4 spaces
- JavaScript/JSON/YAML: 2 spaces

## GitHub Integration

### Issue Templates

- **Bug Report**: `.github/ISSUE_TEMPLATE/bug_report.md`
- **Feature Request**: `.github/ISSUE_TEMPLATE/feature_request.md`

### Pull Request Template

- **PR Template**: `.github/pull_request_template.md`

### CI/CD Pipeline

- **GitHub Actions**: `.github/workflows/ci.yml`
  - Backend testing with multiple Python versions
  - Frontend testing and building
  - Security scanning with Trivy
  - Code quality checks (linting, formatting)

## Development Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat(scope): description of changes"

# Push feature branch
git push origin feature/your-feature-name

# Create pull request on GitHub
```

### Commit Message Convention

Follow conventional commit format:

```
type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
Examples:
- feat(backend): add ASL gesture recognition endpoint
- fix(frontend): resolve video stream connection issue
- docs(readme): update installation instructions
```

### Pre-commit Hooks (Optional)

To set up pre-commit hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Repository Maintenance

### Regular Tasks

1. **Update dependencies**: Regularly update package.json and requirements.txt
2. **Security updates**: Monitor and apply security patches
3. **Documentation**: Keep README and docs up to date
4. **Changelog**: Update CHANGELOG.md for each release

### Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Test thoroughly
5. Create GitHub release with tags
6. Merge to main branch

## Troubleshooting

### Common Issues

1. **Large files**: Use Git LFS for large binary files
2. **Merge conflicts**: Use `git mergetool` or IDE merge tools
3. **Sensitive data**: Use `.gitignore` and `git-secrets` tool

### Useful Commands

```bash
# Check repository status
git status

# View commit history
git log --oneline --graph

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Clean untracked files
git clean -fd

# View differences
git diff
git diff --staged
```

## Security Best Practices

1. **Never commit secrets**: Use environment variables
2. **Review dependencies**: Regularly audit npm and pip packages
3. **Enable branch protection**: Require PR reviews for main branch
4. **Use signed commits**: Configure GPG signing
5. **Monitor security alerts**: Enable GitHub security advisories

For more information, see [CONTRIBUTING.md](CONTRIBUTING.md).
