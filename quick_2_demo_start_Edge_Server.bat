@echo off
title Edge Server 控制台
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

echo [系統訊息] 正在啟動 Edge Server...
echo [系統訊息] 正在載入虛擬環境 venv...

:: 在啟動新視窗的指令中加入 color B0
:: 使用 /k 確保新開的視窗也會變成藍色
start "Edge Server Process" cmd /k "color B0 && %VENV_ACTIVATE_PATH% && python src\0_edge_server.py"

exit