@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

if not exist "%BACKEND%\app\main.py" (
    echo [ERROR] Backend was not found at "%BACKEND%".
    pause
    exit /b 1
)

if not exist "%FRONTEND%\package.json" (
    echo [ERROR] Frontend was not found at "%FRONTEND%".
    pause
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python 3.12 or newer and try again.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] npm was not found. Install Node.js and try again.
    pause
    exit /b 1
)

python -c "import fastapi, uvicorn, sqlalchemy" >nul 2>nul
if errorlevel 1 (
    echo Installing backend dependencies...
    pushd "%BACKEND%"
    python -m pip install -e ".[dev]"
    if errorlevel 1 (
        popd
        echo [ERROR] Backend dependency installation failed.
        pause
        exit /b 1
    )
    popd
)

if not exist "%FRONTEND%\node_modules" (
    echo Installing frontend dependencies...
    pushd "%FRONTEND%"
    call npm install
    if errorlevel 1 (
        popd
        echo [ERROR] Frontend dependency installation failed.
        pause
        exit /b 1
    )
    popd
)

echo Starting CardWise AI...
start "CardWise API" /D "%BACKEND%" cmd /k "python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "CardWise Frontend" /D "%FRONTEND%" cmd /k "npm run dev -- --host 127.0.0.1"

echo.
echo CardWise AI is starting in separate windows.
echo Frontend: http://localhost:5173
echo API:      http://localhost:8000
echo Docs:     http://localhost:8000/docs
echo.
pause

endlocal
