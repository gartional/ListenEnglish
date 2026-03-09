@echo off
cd /d "%~dp0"
echo 阶段一：只下载音频（已有会跳过，断点续传）
python tools/batch_fetch_mocks.py --download-only
pause
