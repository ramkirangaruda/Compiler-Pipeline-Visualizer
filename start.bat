@echo off
rem One-click launcher (Windows): sets everything up on first run, then serves the API and the UI on http://localhost:8000
setlocal
cd /d "%~dp0"

if not exist backend\.venv\Scripts\python.exe (
  echo [1/3] Creating the Python environment...
  py -3 -m venv backend\.venv 2>nul || python -m venv backend\.venv
  backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt || goto :fail
)
if not exist frontend\node_modules (
  echo [2/3] Installing frontend packages...
  pushd frontend
  call npm install || goto :fail
  popd
)
if not exist frontend\dist\index.html (
  echo [3/3] Building the web UI...
  pushd frontend
  call npm run build || goto :fail
  popd
)

echo.
echo  Compiler Pipeline Visualizer is starting at http://localhost:8000
echo  (Ctrl+C to stop)
echo.
start "" http://localhost:8000
backend\.venv\Scripts\python.exe -m uvicorn --app-dir backend app.main:app --port 8000
goto :eof

:fail
echo Setup failed - see the messages above.
exit /b 1
