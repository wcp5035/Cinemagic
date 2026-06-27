@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Run: uv sync
    exit /b 1
)

echo Installing PyInstaller...
uv pip install pyinstaller -q
if errorlevel 1 exit /b 1

echo Building Cinemagic.exe ...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean cinemagic.spec
if errorlevel 1 exit /b 1

set "DIST_DIR=%~dp0dist\Cinemagic"
if not exist "%DIST_DIR%\storage\tasks" mkdir "%DIST_DIR%\storage\tasks"
if not exist "%DIST_DIR%\config.toml" (
    if exist "%~dp0config.toml" (
        copy /Y "%~dp0config.toml" "%DIST_DIR%\config.toml" >nul
    ) else if exist "%DIST_DIR%\_internal\config.example.toml" (
        copy /Y "%DIST_DIR%\_internal\config.example.toml" "%DIST_DIR%\config.toml" >nul
    )
)

echo.
echo Build complete!
echo Output: %DIST_DIR%\Cinemagic.exe
echo.
echo Run Cinemagic.exe from the dist\Cinemagic folder.
echo Edit config.toml next to the exe before first use if needed.
