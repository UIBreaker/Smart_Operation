@echo off
title Smart Operation [Pixel Edition] - Tu Dong Hoa HIS
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo [THONG BAO] Dang kiem tra va cai dat thu vien (requirements.txt)...
    pip install -r requirements.txt
    python main.py
)
pause
