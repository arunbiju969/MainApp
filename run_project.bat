@echo off
REM Django Portfolio Project Quick Helper Script

echo Activating virtual environment in current directory...
call "%cd%\..\venv\Scripts\activate.bat"

if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment.
    echo Please ensure venv exists in the current directory.
    pause
    exit /b 1
)

:menu
cls
echo.
echo Django Portfolio Project (Current Directory)
echo ===========================================
echo 1. Run development server
echo 2. Make migrations
echo 3. Apply migrations
echo 4. Collect static files
echo 5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Running Tailwind CSS compiler in watch mode...
    start "" cmd.exe /c "npx @tailwindcss/cli -i static/src/input.css -o static/src/output.css --watch"
    echo Starting development server...
    python manage.py runserver
    pause
    goto menu
)

if "%choice%"=="2" (
    echo Making migrations...
    python manage.py makemigrations
    pause
    goto menu
)

if "%choice%"=="3" (
    echo Applying migrations...
    python manage.py migrate
    pause
    goto menu
)

if "%choice%"=="4" (
    echo Collecting static files...
    python manage.py collectstatic
    pause
    goto menu
)

if "%choice%"=="5" (
    echo Exiting...
    call deactivate
    exit /b 0
)

echo Invalid choice. Please try again.
pause
goto menu