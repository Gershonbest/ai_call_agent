# Contributing to Voice Agent Platform

Thank you for your interest in contributing to the Voice Agent Platform! This document provides guidelines and information for contributors.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Code Review Guidelines](#code-review-guidelines)
- [Release Process](#release-process)
- [Community Guidelines](#community-guidelines)

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- Poetry (for dependency management)
- Basic understanding of FastAPI, LiveKit, and voice agent technologies

### Quick Start
1. Fork the repository
2. Clone your fork locally
3. Set up the development environment
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### 1. Fork and Clone
```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/ai_call_agent.git
cd ai_call_agent

# Add the original repository as upstream
git remote add upstream https://github.com/ORIGINAL_OWNER/ai_call_agent.git
```

### 2. Environment Setup
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup
```bash
# Run database migrations
poetry run alembic upgrade head

# Create new migration (if needed)
poetry run alembic revision --autogenerate -m "description"
```

### 4. Verify Setup
```bash
# Run tests to ensure everything is working
poetry run pytest

# Start the development server
poetry run dev
```

## Code Standards

### Python Style Guide
We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

#### Code Formatting
- Use **Black** for code formatting (line length: 88 characters)
- Use **isort** for import sorting
- Use **mypy** for type checking

#### Naming Conventions
```python
# Variables and functions: snake_case
user_name = "john"
def get_user_info():
    pass

# Classes: PascalCase
class UserManager:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

#### Type Hints
```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

def process_user_data(user_id: int, data: Dict[str, Any]) -> Optional[User]:
    pass

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True
```

### File Structure
```
app/
├── __init__.py
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── models/              # Database models
│   ├── __init__.py
│   ├── user.py
│   └── call.py
├── api/                 # API routes
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   └── dependencies.py
├── services/            # Business logic
│   ├── __init__.py
│   ├── livekit_service.py
│   └── voice_service.py
├── utils/               # Utility functions
│   ├── __init__.py
│   └── helpers.py
└── tests/               # Test files
    ├── __init__.py
    ├── conftest.py
    ├── test_api/
    └── test_services/
```

### Documentation Standards

#### Docstrings
Use Google-style docstrings:
```python
def process_voice_call(call_id: str, audio_data: bytes) -> CallResult:
    """Process incoming voice call data.
    
    Args:
        call_id: Unique identifier for the call
        audio_data: Raw audio data in bytes
        
    Returns:
        CallResult: Processed call result with transcription and response
        
    Raises:
        ValueError: If call_id is invalid
        AudioProcessingError: If audio data cannot be processed
    """
    pass
```

#### README Updates
- Update README.md for new features
- Include usage examples
- Document configuration changes
- Update API documentation

### Commit Message Format
Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

#### Examples
```
feat(api): add voice call endpoint

fix(auth): resolve token validation issue

docs(readme): update installation instructions

test(services): add unit tests for voice processing
```

## Testing Guidelines

### Test Structure
```
tests/
├── conftest.py          # Shared fixtures
├── test_api/            # API endpoint tests
│   ├── test_calls.py
│   └── test_auth.py
├── test_services/       # Service layer tests
│   ├── test_livekit.py
│   └── test_voice.py
└── test_utils/          # Utility function tests
    └── test_helpers.py
```

### Writing Tests
```python
import pytest
from unittest.mock import Mock, patch
from app.services.livekit_service import LiveKitService

class TestLiveKitService:
    """Test cases for LiveKitService."""
    
    @pytest.fixture
    def livekit_service(self):
        """Create LiveKitService instance for testing."""
        return LiveKitService()
    
    def test_create_room_success(self, livekit_service):
        """Test successful room creation."""
        # Arrange
        room_name = "test-room"
        
        # Act
        result = livekit_service.create_room(room_name)
        
        # Assert
        assert result.room_name == room_name
        assert result.status == "created"
    
    @patch('app.services.livekit_service.LiveKitClient')
    def test_create_room_failure(self, mock_client, livekit_service):
        """Test room creation failure."""
        # Arrange
        mock_client.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(Exception):
            livekit_service.create_room("test-room")
```

### Test Categories

#### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Focus on business logic

#### Integration Tests
- Test API endpoints
- Test database interactions
- Test service integrations

#### End-to-End Tests
- Test complete user workflows
- Test with real external services (in staging)

### Running Tests
```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_api/test_calls.py

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run tests in parallel
poetry run pytest -n auto

# Run only unit tests
poetry run pytest tests/ -k "not integration"
```

### Test Coverage Requirements
- Minimum 80% code coverage
- 100% coverage for critical paths
- All new features must include tests

## Pull Request Process

### Before Submitting

1. **Update your fork**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow coding standards
   - Write tests for new functionality
   - Update documentation

4. **Run quality checks**
   ```bash
   # Format code
   poetry run black .
   poetry run isort .
   
   # Lint code
   poetry run flake8
   
   # Type checking
   poetry run mypy .
   
   # Run tests
   poetry run pytest
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat(api): add voice call endpoint"
   ```

### Pull Request Guidelines

#### PR Title
Use conventional commit format:
```
feat(api): add voice call endpoint
fix(auth): resolve token validation issue
```

#### PR Description Template
```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows the style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Documentation is updated
- [ ] Changes generate no new warnings
- [ ] Tests added that prove fix is effective or feature works
- [ ] New and existing unit tests pass locally

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Additional Notes
Any additional information or context.
```

### Review Process

1. **Automated Checks**
   - CI/CD pipeline runs tests
   - Code coverage is checked
   - Linting and formatting are verified

2. **Code Review**
   - At least one maintainer must approve
   - Address all review comments
   - Update PR based on feedback

3. **Merge Requirements**
   - All tests must pass
   - Code coverage requirements met
   - No merge conflicts
   - Approved by maintainers

## Issue Reporting

### Bug Reports
Use the bug report template:
```markdown
## Bug Description
Clear and concise description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g. macOS, Windows, Linux]
- Python Version: [e.g. 3.9.0]
- Poetry Version: [e.g. 1.4.0]

## Additional Context
Any other context about the problem.
```

### Feature Requests
```markdown
## Feature Description
Clear and concise description of the feature.

## Use Case
Why is this feature needed?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Any alternative solutions or features you've considered.

## Additional Context
Any other context or screenshots about the feature request.
```

## Code Review Guidelines

### For Reviewers

#### What to Look For
- **Functionality**: Does the code work as intended?
- **Security**: Are there any security vulnerabilities?
- **Performance**: Is the code efficient?
- **Maintainability**: Is the code readable and well-structured?
- **Testing**: Are there adequate tests?

#### Review Checklist
- [ ] Code follows project standards
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No security issues
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate

#### Providing Feedback
- Be constructive and respectful
- Explain the reasoning behind suggestions
- Provide specific examples when possible
- Focus on the code, not the person

### For Contributors

#### Responding to Reviews
- Address all comments
- Ask for clarification if needed
- Explain your reasoning when appropriate
- Update the PR based on feedback

#### Handling Conflicts
- Rebase your branch if needed
- Resolve merge conflicts carefully
- Test after resolving conflicts

## Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Prepare Release**
   ```bash
   # Update version in pyproject.toml
   poetry version patch  # or minor/major
   
   # Update CHANGELOG.md
   # Create release notes
   ```

2. **Create Release Branch**
   ```bash
   git checkout -b release/v1.2.3
   git add .
   git commit -m "chore: prepare release v1.2.3"
   ```

3. **Merge and Tag**
   ```bash
   git checkout main
   git merge release/v1.2.3
   git tag v1.2.3
   git push origin main --tags
   ```

4. **Create GitHub Release**
   - Go to GitHub releases page
   - Create new release with tag
   - Add release notes
   - Attach any artifacts

## Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Use welcoming and inclusive language
- Be collaborative and open to feedback
- Focus on what is best for the community
- Show empathy towards other community members

### Communication
- Use clear and concise language
- Be patient with newcomers
- Provide constructive feedback
- Ask questions when unsure

### Getting Help
- Check existing documentation first
- Search existing issues and PRs
- Ask questions in discussions
- Join community channels

## Additional Resources

### Documentation
- [Project README](../README.md)
- [Poetry Setup Guide](POETRY_SETUP.md)
- [API Documentation](../docs/api.md)
- [Architecture Guide](../docs/architecture.md)

### Tools and Services
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LiveKit Documentation](https://docs.livekit.io/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pytest Documentation](https://docs.pytest.org/)

### Community Channels
- GitHub Discussions
- Discord/Slack (if available)
- Email list (if available)

## Support

If you need help with contributing:
1. Check this document first
2. Search existing issues and discussions
3. Ask questions in GitHub Discussions
4. Contact maintainers directly

Thank you for contributing to the Voice Agent Platform! 🎉 