@echo off
REM Voice Agent Platform - Poetry Setup Script for Windows

echo 🚀 Setting up Voice Agent Platform with Poetry...

REM Check if Poetry is installed
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing Poetry...
    powershell -Command "(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -"
    
    REM Add Poetry to PATH for current session
    set PATH=%USERPROFILE%\AppData\Roaming\Python\Scripts;%PATH%
    
    echo ✅ Poetry installed successfully!
) else (
    echo ✅ Poetry is already installed
)

REM Configure Poetry to create virtual environment in project directory
echo ⚙️  Configuring Poetry...
poetry config virtualenvs.in-project true

REM Install dependencies
echo 📚 Installing dependencies...
poetry install

REM Copy environment file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ⚠️  Please edit .env file with your configuration:
    echo    - LIVEKIT_URL
    echo    - LIVEKIT_API_KEY
    echo    - LIVEKIT_API_SECRET
    echo    - SIP_OUTBOUND_TRUNK_ID
    echo    - OPENAI_API_KEY
) else (
    echo ✅ .env file already exists
)

REM Create uploads directory
echo 📁 Creating uploads directory...
if not exist uploads mkdir uploads

echo.
echo 🎉 Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: poetry run dev
echo 3. Visit: http://localhost:8000/docs
echo.
echo Happy coding! 🚀
pause 