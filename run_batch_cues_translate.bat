@echo off
cd /d "%~dp0"
echo 阶段二：对已下载的音频做字幕、分段、翻译
python tools/batch_fetch_mocks.py --skip-fetch
pause
