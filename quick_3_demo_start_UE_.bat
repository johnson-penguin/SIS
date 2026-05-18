@echo off
title UE 模擬控制台
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

echo [系統訊息] 正在啟動 Single UE 模擬...
echo [系統訊息] 正在載入虛擬環境 venv...

:: 啟動一個新的 cmd 視窗並設定顏色為綠底白字，再執行 python
start "Single UE Process" cmd /k "color E0 && %VENV_ACTIVATE_PATH% && python src\0_single_ue_windows.py"

exit