#!/usr/bin/env python3
"""
Voice Agent Platform - Run Script
This script ensures the application runs from the correct directory
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_colored(message, color):
    """Print a colored message"""
    print(f"{color}{message}{Colors.NC}")

def check_file_exists(file_path):
    """Check if a file exists"""
    return Path(file_path).exists()

def check_command_exists(command):
    """Check if a command exists in PATH"""
    return shutil.which(command) is not None

def run_command(command, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        return e

def main():
    print_colored("🚀 Starting Voice Agent Platform...", Colors.BLUE)
    
    # Check if we're in the correct directory
    if not check_file_exists("pyproject.toml"):
        print_colored("❌ Error: pyproject.toml not found.", Colors.RED)
        print_colored("Please run this script from the project root directory.", Colors.YELLOW)
        print_colored(f"Current directory: {os.getcwd()}", Colors.YELLOW)
        sys.exit(1)
    
    # Check if Poetry is available
    if not check_command_exists("poetry"):
        print_colored("❌ Error: Poetry is not installed.", Colors.RED)
        print_colored("Please install Poetry first: https://python-poetry.org/docs/#installation", Colors.YELLOW)
        sys.exit(1)
    
    # Check if dependencies are installed
    if not check_file_exists(".venv"):
        print_colored("⚠️  Virtual environment not found. Installing dependencies...", Colors.YELLOW)
        result = run_command("poetry install")
        if result.returncode != 0:
            print_colored("❌ Error: Failed to install dependencies.", Colors.RED)
            sys.exit(1)
    
    # Check if .env file exists
    if not check_file_exists(".env"):
        print_colored("⚠️  .env file not found. Creating from template...", Colors.YELLOW)
        if check_file_exists("env.example"):
            shutil.copy("env.example", ".env")
            print_colored("📝 Please edit .env file with your configuration:", Colors.YELLOW)
            print_colored("   - LIVEKIT_URL", Colors.YELLOW)
            print_colored("   - LIVEKIT_API_KEY", Colors.YELLOW)
            print_colored("   - LIVEKIT_API_SECRET", Colors.YELLOW)
            print_colored("   - SIP_OUTBOUND_TRUNK_ID", Colors.YELLOW)
            print_colored("   - OPENAI_API_KEY", Colors.YELLOW)
        else:
            print_colored("❌ Error: env.example file not found.", Colors.RED)
            sys.exit(1)
    
    print_colored("✅ Environment ready!", Colors.GREEN)
    print_colored("🌐 Starting server at http://localhost:8000", Colors.BLUE)
    print_colored("📚 API Documentation: http://localhost:8000/docs", Colors.BLUE)
    print_colored("🏥 Health Check: http://localhost:8000/health", Colors.BLUE)
    print_colored("Press Ctrl+C to stop the server", Colors.YELLOW)
    print()
    
    # Run the application
    try:
        subprocess.run(["poetry", "run", "python", "-m", "app.main", "--port", "8000"], check=True)
    except KeyboardInterrupt:
        print_colored("\n👋 Server stopped by user.", Colors.GREEN)
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Error running application: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main() 