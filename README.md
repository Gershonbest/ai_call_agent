# Voice Agent Platform

A comprehensive, scalable voice conversational agent platform similar to Retell or ElevenLabs Call Agent. This platform enables you to create, manage, and deploy dynamic voice agents with tools, knowledge bases, and phone call capabilities.

## 🚀 Features

### Core Capabilities
- **Dynamic Agent Creation**: Create agents with configurable personalities, voices, and behaviors
- **Tool System**: Add API calls, functions, and webhooks to agents
- **Knowledge Base Integration**: Upload documents, FAQs, and custom knowledge
- **Phone Call Management**: Make outbound calls using LiveKit SIP integration
- **Real-time Voice Conversations**: Powered by LiveKit and OpenAI
- **Scalable Architecture**: RESTful API with database persistence

### Agent Features
- Customizable voice (OpenAI voices)
- Configurable temperature and model settings
- Dynamic tool execution
- Knowledge base context integration
- Call transfer capabilities
- Answering machine detection

### Knowledge Base Types
- **Documents**: PDF, DOCX, TXT, MD file uploads
- **FAQs**: Q&A pairs with categories and tags
- **Custom**: Flexible custom knowledge structures
- **Vector**: Semantic search capabilities (future)

### Tool Types
- **API Tools**: HTTP calls to external services
- **Function Tools**: Internal utility functions
- **Webhook Tools**: Event-driven integrations

## 🏗️ Architecture

```
app/
├── api/routes/           # REST API endpoints
│   ├── agents.py        # Agent management
│   ├── tools.py         # Tool management
│   ├── calls.py         # Call management
│   ├── phone_numbers.py # Phone number management
│   └── knowledge_base.py # Knowledge base management
├── core/                # Core business logic
│   ├── agent_factory.py # Dynamic agent creation
│   ├── tool_executor.py # Tool execution engine
│   ├── call_manager.py  # Call management
│   └── knowledge_service.py # Knowledge base operations
├── models/              # Database models
│   └── database.py      # SQLAlchemy models
├── schemas/             # Pydantic schemas
│   ├── agent.py         # Agent schemas
│   ├── tool.py          # Tool schemas
│   ├── call.py          # Call schemas
│   └── knowledge_base.py # Knowledge base schemas
├── workers/             # LiveKit workers
│   └── call_worker.py   # Call handling worker
└── main.py              # FastAPI application
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: SQLite (included, no external dependencies)
- **Voice**: LiveKit, OpenAI Realtime API
- **Phone Calls**: LiveKit SIP integration
- **File Storage**: Local filesystem (configurable for cloud)
- **Search**: Custom relevance-based search engine

## 📋 Prerequisites

- Python 3.8+
- SQLite (included with Python, no additional setup required)
- LiveKit server (cloud or self-hosted)
- OpenAI API key
- SIP trunk for phone calls

## 🚀 Quick Start

### Option 1: Poetry (Recommended)

#### 1. Clone and Setup

```bash
git clone <repository-url>
cd voice-agent-platform
```

#### 2. Run Setup Script

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

#### 3. Configure Environment

Edit the `.env` file with your API keys:

```env
# Database Configuration (SQLite - default)
DATABASE_URL=sqlite:///./voice_agent.db

# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
SIP_OUTBOUND_TRUNK_ID=your_sip_trunk_id

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

#### 4. Run the Application

**Option A: Using the convenient run scripts (Recommended)**

```bash
# Using the shell script (Linux/macOS)
./run.sh

# Using the Python script (Cross-platform)
python run.py
```

**Option B: Using Poetry commands**

```bash
# Development mode (with auto-reload)
poetry run dev

# Or production mode
poetry run start
```

**Option C: Direct Python execution**

```bash
# From project root (correct way)
poetry run python -m app.main

# ❌ Don't run from inside the app directory
# cd app && python main.py  # This will cause import errors
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🎯 Usage Examples

### 1. Create an Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agents/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Agent",
    "description": "A helpful customer support agent",
    "instructions": "You are a friendly customer support agent. Help customers with their inquiries professionally and efficiently.",
    "voice_id": "coral",
    "temperature": 7,
    "max_tokens": 1000,
    "model": "gpt-4"
  }'
```

### 2. Create a Tool

```bash
curl -X POST "http://localhost:8000/api/v1/tools/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Get Weather",
    "description": "Get current weather information for a location",
    "tool_type": "api",
    "configuration": {
      "endpoint": "https://api.weatherapi.com/v1/current.json",
      "method": "GET",
      "default_params": {
        "key": "your_weather_api_key"
      }
    }
  }'
```

### 3. Add Tool to Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agents/1/tools" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": 1,
    "is_enabled": true,
    "configuration": {}
  }'
```

### 4. Create Knowledge Base

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-bases/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product Documentation",
    "description": "Product manuals and guides",
    "kb_type": "document"
  }'
```

### 5. Add Document to Knowledge Base

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-bases/1/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "User Manual",
    "content": "This is the user manual content...",
    "knowledge_base_id": 1
  }'
```

### 6. Assign Knowledge Base to Agent

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-bases/agents/1/knowledge-bases/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_base_id": 1,
    "is_enabled": true,
    "priority": 1
  }'
```

### 7. Make a Phone Call

```bash
curl -X POST "http://localhost:8000/api/v1/calls/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 1,
    "phone_number": "+1234567890",
    "caller_number": "+0987654321",
    "metadata": {
      "transfer_to": "+1111111111",
      "context": "Follow-up call"
    }
  }'
```

## 🔧 API Endpoints Reference

### Agents
- `POST /agents/` - Create agent
- `GET /agents/` - List agents
- `GET /agents/{id}` - Get agent with tools
- `PUT /agents/{id}` - Update agent
- `DELETE /agents/{id}` - Delete agent
- `POST /agents/{id}/tools` - Add tool to agent
- `PUT /agents/{id}/tools/{tool_id}` - Update agent tool
- `DELETE /agents/{id}/tools/{tool_id}` - Remove tool from agent
- `GET /agents/{id}/tools` - Get agent tools
- `POST /agents/{id}/validate` - Validate agent configuration

### Tools
- `POST /tools/` - Create tool
- `GET /tools/` - List tools
- `GET /tools/{id}` - Get tool
- `PUT /tools/{id}` - Update tool
- `DELETE /tools/{id}` - Delete tool
- `POST /tools/{id}/test` - Test tool
- `GET /tools/types/available` - Get available tool types
- `GET /tools/functions/available` - Get available functions

### Knowledge Bases
- `POST /knowledge-bases/` - Create knowledge base
- `GET /knowledge-bases/` - List knowledge bases
- `GET /knowledge-bases/{id}` - Get knowledge base with content
- `PUT /knowledge-bases/{id}` - Update knowledge base
- `DELETE /knowledge-bases/{id}` - Delete knowledge base
- `POST /knowledge-bases/search` - Search knowledge bases
- `GET /knowledge-bases/types/available` - Get available types

### Documents
- `POST /knowledge-bases/{kb_id}/documents/` - Add document
- `POST /knowledge-bases/{kb_id}/documents/upload` - Upload file
- `GET /knowledge-bases/{kb_id}/documents/` - List documents
- `GET /knowledge-bases/documents/{id}` - Get document
- `PUT /knowledge-bases/documents/{id}` - Update document
- `DELETE /knowledge-bases/documents/{id}` - Delete document

### FAQs
- `POST /knowledge-bases/{kb_id}/faqs/` - Add FAQ
- `GET /knowledge-bases/{kb_id}/faqs/` - List FAQs
- `GET /knowledge-bases/faqs/{id}` - Get FAQ
- `PUT /knowledge-bases/faqs/{id}` - Update FAQ
- `DELETE /knowledge-bases/faqs/{id}` - Delete FAQ

### Calls
- `POST /calls/initiate` - Make a call
- `GET /calls/` - List calls
- `GET /calls/{id}` - Get call details
- `PUT /calls/{id}` - Update call
- `POST /calls/{id}/end` - End call

### Phone Numbers
- `POST /phone-numbers/` - Create phone number
- `GET /phone-numbers/` - List phone numbers
- `GET /phone-numbers/{id}` - Get phone number
- `PUT /phone-numbers/{id}` - Update phone number
- `DELETE /phone-numbers/{id}` - Delete phone number

## 🔍 Search Functionality

The platform includes a powerful search system for knowledge bases:

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge-bases/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "refund policy",
    "knowledge_base_ids": [1, 2],
    "search_type": "all",
    "limit": 10
  }'
```

Search types:
- `all`: Search both documents and FAQs
- `documents`: Search only documents
- `faqs`: Search only FAQs

## 🛠️ Tool Configuration Examples

### API Tool
```json
{
  "name": "Get User Info",
  "description": "Retrieve user information from CRM",
  "tool_type": "api",
  "configuration": {
    "endpoint": "https://api.crm.com/users/{user_id}",
    "method": "GET",
    "headers": {
      "Authorization": "Bearer {api_key}"
    }
  }
}
```

### Function Tool
```json
{
  "name": "Calculate Discount",
  "description": "Calculate discount based on order amount",
  "tool_type": "function",
  "configuration": {
    "function_name": "calculate_discount"
  }
}
```

### Webhook Tool
```json
{
  "name": "Send Notification",
  "description": "Send notification via webhook",
  "tool_type": "webhook",
  "configuration": {
    "webhook_url": "https://hooks.slack.com/services/...",
    "method": "POST",
    "default_payload": {
      "channel": "#notifications"
    }
  }
}
```

## 🔧 Development

### Running Tests
```bash
pytest
```

### Database Migrations
The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations.

### Adding Custom Functions
Extend the `FunctionRegistry` in `app/core/tool_executor.py`:

```python
def my_custom_function(param1: str, param2: int):
    """My custom function description"""
    return f"Processed {param1} with {param2}"

function_registry.register_function("my_custom_function", my_custom_function)
```

## 🚀 Deployment

### Production Considerations

1. **Database**: SQLite works for small to medium scale. For high-traffic production, consider PostgreSQL
2. **File Storage**: Use cloud storage (AWS S3, Google Cloud Storage)
3. **Environment Variables**: Set all required environment variables
4. **HTTPS**: Use reverse proxy (nginx) with SSL certificates
5. **Monitoring**: Add logging and monitoring
6. **Scaling**: Use multiple workers for high availability

### Docker Deployment

The Voice Agent Platform can be easily deployed using Docker for consistent environments across development and production.

#### Quick Start with Docker

```bash
# Build and run with Docker Compose (Recommended)
docker-compose up --build

# Or build and run manually
docker build -t voice-agent-platform .
docker run -p 8000:8000 --env-file .env voice-agent-platform
```

#### Dockerfile

```dockerfile
# Use Python 3.9 slim image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not create virtual environment in container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose Configuration

Create a `docker-compose.yml` file for easy deployment:

```yaml
version: '3.8'

services:
  voice-agent-platform:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./voice_agent.db
      - LIVEKIT_URL=${LIVEKIT_URL}
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=False
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Add Redis for caching and session management
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  # Optional: Add PostgreSQL for production database
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=voice_agent
      - POSTGRES_USER=voice_agent
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

#### Environment Configuration

Create a `.env` file for Docker deployment:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
SIP_OUTBOUND_TRUNK_ID=your_sip_trunk_id

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration (for PostgreSQL)
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://voice_agent:your_secure_password@postgres:5432/voice_agent

# Redis Configuration
REDIS_URL=redis://redis:6379

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
```

#### Production Docker Deployment

For production deployment, use the following setup:

1. **Build the production image:**
```bash
docker build -t voice-agent-platform:latest .
```

2. **Create a production docker-compose.yml:**
```yaml
version: '3.8'

services:
  voice-agent-platform:
    image: voice-agent-platform:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://voice_agent:${POSTGRES_PASSWORD}@postgres:5432/voice_agent
      - LIVEKIT_URL=${LIVEKIT_URL}
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=False
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - voice-agent-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=voice_agent
      - POSTGRES_USER=voice_agent
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - voice-agent-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes
    networks:
      - voice-agent-network

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - voice-agent-platform
    restart: unless-stopped
    networks:
      - voice-agent-network
```

3. **Create nginx.conf for reverse proxy:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream voice_agent {
        server voice-agent-platform:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location / {
            proxy_pass http://voice_agent;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

#### Docker Deployment Commands

```bash
# Development deployment
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f voice-agent-platform

# Stop services
docker-compose down

# Remove volumes (careful - this deletes data)
docker-compose down -v
```

#### Docker Best Practices

1. **Security:**
   - Use non-root user in container
   - Keep base images updated
   - Scan images for vulnerabilities
   - Use secrets management for sensitive data

2. **Performance:**
   - Use multi-stage builds for smaller images
   - Implement proper health checks
   - Use volume mounts for persistent data
   - Configure resource limits

3. **Monitoring:**
   - Add logging to stdout/stderr
   - Implement health check endpoints
   - Use Docker's built-in monitoring
   - Set up external monitoring (Prometheus, Grafana)

4. **Scaling:**
   - Use Docker Swarm or Kubernetes for orchestration
   - Implement load balancing
   - Use external databases for high availability
   - Configure auto-scaling policies

#### Troubleshooting Docker Deployment

```bash
# Check container status
docker ps

# View container logs
docker logs voice-agent-platform

# Access container shell
docker exec -it voice-agent-platform bash

# Check resource usage
docker stats

# Restart services
docker-compose restart voice-agent-platform
```

## 🏃‍♂️ Run Scripts

The project includes convenient run scripts that handle common setup tasks automatically:

### `run.sh` (Linux/macOS)
A bash script that:
- ✅ Checks if you're in the correct directory
- ✅ Verifies Poetry is installed
- ✅ Installs dependencies if needed
- ✅ Creates `.env` file from template if missing
- ✅ Runs the application with proper error handling

```bash
./run.sh
```

### `run.py` (Cross-platform)
A Python script that provides the same functionality but works on all platforms:

```bash
python run.py
```

### What the scripts do:
1. **Environment Check**: Verify you're in the project root directory
2. **Dependency Check**: Ensure Poetry and virtual environment are set up
3. **Configuration Check**: Create `.env` file from template if missing
4. **Application Launch**: Start the server with proper error handling
5. **User Feedback**: Provide colored output and helpful messages

### Benefits:
- 🎯 **No more import errors**: Always runs from the correct directory
- 🔧 **Automatic setup**: Handles common configuration issues
- 🌈 **User-friendly**: Clear, colored output with helpful messages
- 🛡️ **Error handling**: Graceful handling of common issues
- 🔄 **Cross-platform**: Python script works on Windows, macOS, and Linux

### Troubleshooting:
If you encounter issues:
1. Make sure you're in the project root directory
2. Ensure Poetry is installed: `curl -sSL https://install.python-poetry.org | python3 -`
3. Check that all environment variables are set in `.env`
4. Try running `poetry install` manually if dependencies are missing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the example configurations

## 🔮 Roadmap

- [ ] Vector database integration for semantic search
- [ ] Multi-language support
- [ ] Advanced analytics and reporting
- [ ] Webhook integrations for call events
- [ ] Agent conversation history
- [ ] Advanced voice customization
- [ ] Bulk operations for knowledge bases
- [ ] Real-time agent monitoring dashboard 