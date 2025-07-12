# Poetry Setup Guide for Voice Agent Platform

This guide covers the setup and usage of Poetry for the Voice Agent Platform project.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Setup](#project-setup)
- [Dependency Management](#dependency-management)
- [Development Workflow](#development-workflow)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Python 3.9 or higher
- Git
- macOS/Linux/Windows

### Python Version
The project requires Python 3.9+ due to dependencies:
- `livekit-agents` requires Python >= 3.9
- `fastapi` and other dependencies have specific version requirements

## Installation

### 1. Install Poetry

#### macOS/Linux
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### Windows (PowerShell)
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

#### Verify Installation
```bash
poetry --version
```

### 2. Configure Poetry (Optional)
```bash
# Configure Poetry to create virtual environments in project directory
poetry config virtualenvs.in-project true

# Configure Poetry to use system Python (if preferred)
poetry config virtualenvs.prefer-active-python true
```

## Project Setup

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd ai_call_agent
```

### 2. Install Dependencies
```bash
# Install all dependencies
poetry install

# Install with development dependencies
poetry install --with dev
```

### 3. Activate Virtual Environment
```bash
# Activate the virtual environment
poetry shell

# Or run commands directly without activation
poetry run python -m app.main
```

## Dependency Management

### Current Dependencies

#### Core Dependencies
```toml
python = "^3.9"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.23"
alembic = "^1.12.1"
python-dotenv = "^1.0.0"
pydantic = "^2.5.0"
python-multipart = "^0.0.6"
httpx = "^0.28.1"
redis = "^5.0.1"
celery = "^5.3.4"
```

#### LiveKit Dependencies
```toml
livekit-agents = {extras = ["deepgram", "openai", "cartesia", "silero", "turn-detector", "rime", "groq", "google", "playai"], version = "~1.0"}
livekit-plugins-noise-cancellation = "~0.2"
```

#### Additional Dependencies
```toml
aiohttp = "^3.12.14"
twilio = "^9.6.5"
```

### Adding Dependencies

#### Add Production Dependency
```bash
poetry add package-name
poetry add package-name@latest  # Latest version
poetry add "package-name>=1.0,<2.0"  # Version constraint
```

#### Add Development Dependency
```bash
poetry add --group dev package-name
```

#### Add with Extras
```bash
poetry add "package-name[extra1,extra2]"
```

### Removing Dependencies
```bash
poetry remove package-name
poetry remove --group dev package-name
```

### Updating Dependencies
```bash
# Update all dependencies
poetry update

# Update specific package
poetry update package-name

# Update to latest versions
poetry update --latest
```

## Development Workflow

### 1. Environment Setup
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 2. Running the Application

#### Development Mode
```bash
# Using Poetry scripts
poetry run dev

# Or directly
poetry run python -m app.main

# Or with uvicorn
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode
```bash
poetry run start
```

### 3. Testing
```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_main.py
```

### 4. Code Quality
```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Lint code
poetry run flake8

# Type checking
poetry run mypy .
```

## Common Commands

### Poetry Commands
```bash
# Show project info
poetry show

# Show dependency tree
poetry show --tree

# Show outdated packages
poetry show --outdated

# Export requirements
poetry export -f requirements.txt --output requirements.txt

# Lock dependencies
poetry lock

# Install from requirements.txt
poetry add $(cat requirements.txt)
```

### Project-Specific Commands
```bash
# Run the application
poetry run dev

# Start the application
poetry run start

# Run database migrations
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "description"
```

## Configuration Files

### pyproject.toml
The main configuration file contains:
- Project metadata
- Dependencies
- Development dependencies
- Scripts
- Tool configurations (black, isort, mypy, pytest)

### Key Sections
```toml
[tool.poetry]
name = "voice-agent-platform"
version = "1.0.0"
description = "A comprehensive, scalable voice conversational agent platform"

[tool.poetry.dependencies]
python = "^3.9"
# ... dependencies

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
black = "^23.0.0"
# ... dev dependencies

[tool.poetry.scripts]
start = "app.main:main"
dev = "app.main:main"
```

## Troubleshooting

### Common Issues

#### 1. Python Version Conflicts
```bash
# Check Python version
python --version

# Ensure Poetry uses correct Python version
poetry env info

# Recreate virtual environment
poetry env remove python
poetry install
```

#### 2. Dependency Conflicts
```bash
# Check for conflicts
poetry check

# Update lock file
poetry lock --no-update

# Resolve conflicts manually
poetry update
```

#### 3. Virtual Environment Issues
```bash
# List virtual environments
poetry env list

# Remove virtual environment
poetry env remove python

# Create new environment
poetry install
```

#### 4. Permission Issues
```bash
# Fix permissions
chmod +x run.sh
chmod +x run.py

# Or run with poetry
poetry run python run.py
```

### Dependency Resolution Issues

#### LiveKit Dependencies
The project uses specific versions to avoid conflicts:
- `httpx = "^0.28.1"` (required by livekit-agents)
- `fastapi = "^0.109.0"` (compatible with anyio >=4.8.0)
- `anyio = "^4.9.0"` (required by livekit-agents)

#### Version Constraints
```toml
# Example of version constraints
livekit-agents = {extras = ["deepgram", "openai", "cartesia", "silero", "turn-detector", "rime", "groq", "google", "playai"], version = "~1.0"}
```

### Environment Variables
```bash
# Required environment variables
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
OPENAI_API_KEY=your_openai_key
```

## Best Practices

### 1. Dependency Management
- Always use `poetry add` instead of manually editing `pyproject.toml`
- Use version constraints to prevent breaking changes
- Regularly update dependencies with `poetry update`

### 2. Development Workflow
- Always work within the Poetry virtual environment
- Use `poetry run` for one-off commands
- Use `poetry shell` for interactive development

### 3. Version Control
- Commit `pyproject.toml` and `poetry.lock`
- Don't commit virtual environment directories
- Use `.gitignore` to exclude unnecessary files

### 4. Deployment
```bash
# Install production dependencies only
poetry install --only main

# Export requirements for deployment
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LiveKit Documentation](https://docs.livekit.io/)
- [Project README](../README.md)

## Support

For issues specific to this project:
1. Check the troubleshooting section above
2. Review the project's issue tracker
3. Consult the project documentation
4. Contact the development team

For Poetry-specific issues:
1. Check [Poetry's documentation](https://python-poetry.org/docs/)
2. Review [Poetry's GitHub issues](https://github.com/python-poetry/poetry/issues)
3. Search existing solutions in the community 