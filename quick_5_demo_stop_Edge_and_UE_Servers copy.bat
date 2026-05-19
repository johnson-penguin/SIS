@echo off
:: 載入 .env 檔案
if exist "%~dp0.env" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0.env") do set "%%a=%%b"
) else (
    echo [錯誤] 找不到 .env 檔案！
    pause
    exit /b
)

:: 切換到 UTF-8 編碼以支援中文路徑（選用）
chcp 65001 >nul

echo Starting PowerShell script...

:: 執行 PowerShell 腳本
:: -ExecutionPolicy Bypass: 繞過腳本執行限制
:: -File: 指定腳本路徑
powershell.exe -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\%CLEAN_SCRIPT_PATH%"

if %errorlevel% equ 0 (
    echo.
    echo Script completed successfully.
) else (
    echo.
    echo [Error] Script failed with exit code %errorlevel%.
)

:: 關閉指定的視窗 (使用萬用字元 * 以防標題帶有其他路徑資訊)
echo.
echo Closing specific process windows...
taskkill /F /FI "WINDOWTITLE eq Single UE Process*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Edge Server Process*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Web Monitoring Station UI*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Web UE UI*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Party UI*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Insurance UI*" >nul 2>&1

:: (已移除 pause，視窗將會自動關閉)