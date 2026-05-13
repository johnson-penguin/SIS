@echo off
:: 1. 強制使用 UTF-8 編碼，防止中文亂碼
chcp 65001 >nul

:: ==========================================
:: 2. 設定硬編碼路徑 (請修改下方路徑)
:: ==========================================
set "PROJECT_ROOT=C:\Users\bmwlab\Desktop\SIS"

:: 3. 切換到該目錄
cd /d "%PROJECT_ROOT%"

echo Starting UIs in Background...
echo Working Directory: %cd%

:: 4. 啟動 Python 服務
:: 使用 /b 在背景執行，並確保引號正確
start "" /b python "2_web_monitoring_station.py"
start "" /b python "2_web_ue.py"
start "" /b python "3_party_ui.py"
start "" /b python "4_insurance_ui.py"

echo ==========================================================
echo 2_web_monitoring_station.py -^> http://localhost:5000
echo 2_web_ue.py                 -^> http://localhost:5001
echo 3_party_ui.py               -^> http://localhost:5003
echo 4_insurance_ui.py           -^> http://localhost:5004
echo ==========================================================

echo Success! Use 'stop_uis.bat' to terminate them.
pause