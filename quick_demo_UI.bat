@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

:: ==========================================================
:: 2. 設定硬編碼路徑 (請修改下方路徑)
:: ==========================================================
set "PROJECT_ROOT=C:\Users\bmwlab\Desktop\SIS"

:: 3. 切換到該目錄
cd /d "%PROJECT_ROOT%"

echo Starting UIs in Background...
echo Working Directory: %cd%

:: 4. 啟動 Python 服務
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
echo.
echo 服務已在背景啟動！當您完成測試並希望關閉所有 UI 服務時...

:: 使用 choice 指令，/C K 代表只接受 K 鍵輸入，/N 代表不顯示預設的 [K,N]? 提示
choice /C K /N /M "請按 [K] 鍵執行關閉程序："

echo.
echo [1/2] 正在搜尋並終止指定的 Python 腳本程序...
echo ----------------------------------------------------------
call :kill_script "2_web_monitoring_station.py"
call :kill_script "2_web_ue.py"
call :kill_script "3_party_ui.py"
call :kill_script "4_insurance_ui.py"

:: 等待 2 秒讓作業系統確實釋放資源
timeout /t 2 /nobreak >nul

echo.
echo [2/2] 驗證程序是否已成功關閉...
echo ----------------------------------------------------------
call :verify_script "2_web_monitoring_station.py"
timeout /t 1 /nobreak >nul
call :verify_script "2_web_ue.py"
timeout /t 1 /nobreak >nul
call :verify_script "3_party_ui.py"
timeout /t 1 /nobreak >nul
call :verify_script "4_insurance_ui.py"
timeout /t 1 /nobreak >nul

echo.
echo ==========================================================
echo 所有指定的 Python 腳本已成功關閉！
echo ==========================================================
pause
exit /b

:: ==========================================================
:: 副程式區塊
:: ==========================================================

:kill_script
set "script_name=%~1"
echo 正在結束腳本: %script_name% ...
:: 呼叫 PowerShell 抓取包含該腳本名稱的 Python 程序並強制結束
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match '%script_name%' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
exit /b

:verify_script
set "script_name=%~1"
set "count=0"
:: 呼叫 PowerShell 計算目前還剩幾個包含該腳本名稱的 Python 程序
for /f "tokens=*" %%a in ('powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match '%script_name%' }).Count"') do set "count=%%a"

if "!count!"=="0" (
    echo 腳本 %script_name% 狀態: 已成功關閉/清除
) else (
    echo [警告] 腳本 %script_name% 仍在執行中！^(發現 !count! 個殘留程序^)
)
exit /b