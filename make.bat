@echo off
setlocal

:: Prefer native make.exe or mingw32-make.exe if available
where make.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    make.exe %*
    exit /b %ERRORLEVEL%
)

where mingw32-make.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    mingw32-make.exe %*
    exit /b %ERRORLEVEL%
)

:: Fallback implementation for Windows systems without Make installed
set TARGET=%~1
if "%TARGET%"=="" set TARGET=start

if /i "%TARGET%"=="start" goto :target_start
if /i "%TARGET%"=="dev" goto :target_start
if /i "%TARGET%"=="serve" goto :target_serve
if /i "%TARGET%"=="build" goto :target_build
if /i "%TARGET%"=="backend" goto :target_backend
if /i "%TARGET%"=="dev-backend" goto :target_backend
if /i "%TARGET%"=="frontend" goto :target_frontend
if /i "%TARGET%"=="dev-frontend" goto :target_frontend
if /i "%TARGET%"=="run" goto :target_run
if /i "%TARGET%"=="test" goto :target_test
if /i "%TARGET%"=="test-integration" goto :target_test_integration
if /i "%TARGET%"=="test-e2e" goto :target_test_e2e
if /i "%TARGET%"=="sync" goto :target_sync
if /i "%TARGET%"=="docker-build" goto :target_docker_build
if /i "%TARGET%"=="docker-run" goto :target_docker_run
if /i "%TARGET%"=="clean" goto :target_clean
if /i "%TARGET%"=="help" goto :target_help

echo Error: Unknown target "%TARGET%"
echo Run "make help" for available commands.
exit /b 1

:target_start
echo Starting Mini Kanban Board (Backend + Frontend)...
start "Mini Kanban Backend" cmd /c "cd /d "%~dp0Backend" && uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
start "Mini Kanban Frontend" cmd /c "cd /d "%~dp0Frontend" && npm run dev"
exit /b 0

:target_backend
cd /d "%~dp0Backend" && uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
exit /b %ERRORLEVEL%

:target_frontend
cd /d "%~dp0Frontend" && npm run dev
exit /b %ERRORLEVEL%

:target_build
echo Building frontend static assets...
cd /d "%~dp0Frontend" && npm run build
exit /b %ERRORLEVEL%

:target_serve
echo Building frontend and starting backend to serve full app...
cd /d "%~dp0Frontend" && npm run build
set FRONT_ERR=%ERRORLEVEL%
if %FRONT_ERR% neq 0 exit /b %FRONT_ERR%
cd /d "%~dp0Backend" && uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
exit /b %ERRORLEVEL%

:target_run
cd /d "%~dp0Backend" && uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
exit /b %ERRORLEVEL%

:target_test
cd /d "%~dp0Backend" && uv run pytest
exit /b %ERRORLEVEL%

:target_test_integration
uv run --directory "%~dp0Backend" pytest "%~dp0tests\integration" -v
exit /b %ERRORLEVEL%

:target_test_e2e
cd /d "%~dp0Frontend" && npx.cmd playwright test --config="%~dp0playwright.config.ts"
exit /b %ERRORLEVEL%

:target_sync
echo Synchronizing Backend dependencies (uv sync)...
cd /d "%~dp0Backend" && uv sync
set BACKEND_ERR=%ERRORLEVEL%
if %BACKEND_ERR% neq 0 exit /b %BACKEND_ERR%

echo Synchronizing Frontend dependencies (npm install)...
cd /d "%~dp0Frontend" && npm install
exit /b %ERRORLEVEL%

:target_docker_build
echo Building Docker image mini-kanban:latest...
docker build -t mini-kanban:latest .
exit /b %ERRORLEVEL%

:target_docker_run
echo Running Docker container on http://localhost:8000...
docker run -p 8000:8000 mini-kanban:latest
exit /b %ERRORLEVEL%

:target_clean
cd /d "%~dp0Backend" && uv run python -c "import shutil, glob; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + glob.glob('**/.pytest_cache', recursive=True)]"
exit /b %ERRORLEVEL%

:target_help
echo Mini Kanban Board - Management
echo.
echo Available commands:
echo   make              Start backend (serving frontend) and frontend dev servers
echo   make serve        Build frontend and run backend to serve both API and frontend
echo   make build        Build frontend production assets
echo   make backend      Run backend server with auto-reload (port 8000)
echo   make frontend     Run frontend development server (Vite)
echo   make run              Run backend server directly without auto-reload
echo   make test             Run full unit pytest test suite
echo   make test-integration Run integration tests against docker-compose stack
echo   make test-e2e         Run Playwright E2E browser tests against docker-compose stack
echo   make sync             Install and synchronize dependencies using uv and npm
echo   make docker-build Build the multi-stage Docker image
echo   make docker-run   Run the containerized application on port 8000
echo   make clean        Remove cache files and temporary artifacts
echo   make help         Display this help message
echo.
exit /b 0
