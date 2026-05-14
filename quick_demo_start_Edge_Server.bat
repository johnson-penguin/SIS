@echo off
title Edge Server 控制台
:: 切換到目前批次檔所在的目錄
cd /d "%~dp0"

echo [系統訊息] 正在啟動 Edge Server...
echo [系統訊息] 正在載入虛擬環境 venv...

:: 在啟動新視窗的指令中加入 color 17
:: 使用 /k "color 17 && ..." 確保新開的視窗也會變成藍色
start "Edge Server Process" cmd /k "color B0 && venv\Scripts\activate && python src\0_edge_server.py"

exit