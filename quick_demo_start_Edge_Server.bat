@echo off
title Edge Server 控制台
:: 切換到目前批次檔所在的目錄
cd /d "%~dp0"

echo [系統訊息] 正在啟動 Edge Server...
echo [系統訊息] 正在載入虛擬環境 venv...

:: 啟動一個新的 cmd 視窗並執行 python
:: /k 參數會讓程式結束後視窗保持開啟，方便查看錯誤訊息
start "Edge Server Process" cmd /k "venv\Scripts\activate && python 0_edge_server.py"

exit