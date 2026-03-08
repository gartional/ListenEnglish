@echo off
cd /d "%~dp0"
echo Starting HTTP server with Range support (audio/video can seek)
echo http://127.0.0.1:8000
echo.
echo VOA:    http://127.0.0.1:8000/voa-practice.html
echo Mock17: http://127.0.0.1:8000/mock17-practice.html
echo.
echo Press Ctrl+C to stop.
echo.
python tools\serve_range.py 8000
pause
