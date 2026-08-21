@echo off
echo ========================================
echo   OpenROM Build Script - Windows
echo   M5 Dev
echo ========================================

:: Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller>=6.0.0

:: Build
echo [2/3] Building executable...
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --name "OpenROM" ^
  --add-data "assets;assets" ^
  --icon "assets/icon.ico" ^
  main.py

:: Done
echo.
echo [3/3] Done!
if exist "dist\OpenROM.exe" (
    echo ✅ dist\OpenROM.exe is ready!
) else (
    echo ❌ Build failed — check errors above
)
pause
