#!/bin/bash

# Voice Agent Platform - Poetry Setup Script

set -e

echo "🚀 Setting up Voice Agent Platform with Poetry..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add Poetry to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    
    echo "✅ Poetry installed successfully!"
else
    echo "✅ Poetry is already installed"
fi

# Configure Poetry to create virtual environment in project directory
echo "⚙️  Configuring Poetry..."
poetry config virtualenvs.in-project true

# Install dependencies
echo "📚 Installing dependencies..."
poetry install

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your configuration:"
    echo "   - LIVEKIT_URL"
    echo "   - LIVEKIT_API_KEY"
    echo "   - LIVEKIT_API_SECRET"
    echo "   - SIP_OUTBOUND_TRUNK_ID"
    echo "   - OPENAI_API_KEY"
else
    echo "✅ .env file already exists"
fi

# Create uploads directory
echo "📁 Creating uploads directory..."
mkdir -p uploads

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: poetry run dev"
echo "3. Visit: http://localhost:8000/docs"
echo ""
echo "Happy coding! 🚀" 