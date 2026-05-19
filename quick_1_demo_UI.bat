@echo off
chcp 65001 >nul
title UI Central
:: 載入 .env 檔案
if exist "%~dp0.env" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0.env") do set "%%a=%%b"
) else (
    echo [錯誤] 找不到 .env 檔案！
    pause
    exit /b
)

:: 切換到專案根目錄
cd /d "%PROJECT_ROOT%"

echo [系統訊息] 正在啟動各項 UI 服務...
echo [系統訊息] 正在載入虛擬環境 venv...

:: 啟動 Python UI 服務
start "Web Monitoring Station UI" cmd /k "color 0A && %VENV_ACTIVATE_PATH% && python src\2_web_monitoring_station.py"
start "Web UE UI" cmd /k "color 0A && %VENV_ACTIVATE_PATH% && python src\2_web_ue.py"
start "Party UI" cmd /k "color 0A && %VENV_ACTIVATE_PATH% && python src\2_party_ui.py"
start "Insurance UI" cmd /k "color 0A && %VENV_ACTIVATE_PATH% && python src\2_insurance_ui.py"

exit