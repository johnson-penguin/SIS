@echo off
title UE 模擬控制台
:: 切換到目前批次檔所在的目錄
cd /d "%~dp0"

echo [系統訊息] 正在啟動 Single UE 模擬...
echo [系統訊息] 正在載入虛擬環境 venv...

:: 啟動一個新的 cmd 視窗並設定顏色為綠底白字 (color 27)，再執行 python
start "Single UE Process" cmd /k "color E0 && venv\Scripts\activate && python src\0_single_ue_windows.py"

exit