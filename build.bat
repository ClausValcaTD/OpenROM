@echo off
echo ========================================
echo   OpenROM Build Script - M5 Dev
echo ========================================

pip install -r requirements.txt

pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "OpenROM" ^
  --add-data "assets;assets" ^
  --icon "assets/icon.ico" ^
  main.py

echo.
echo ✅ Build complete! Check dist/OpenROM.exe
pause
