@echo off
:: 切換到 UTF-8 編碼以支援中文路徑（選用）
chcp 65001 >nul

echo Starting PowerShell script...

:: 執行 PowerShell 腳本
:: -ExecutionPolicy Bypass: 繞過腳本執行限制
:: -File: 指定腳本路徑
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\bmwlab\Desktop\SIS\script\winsows\clean_.ps1"

if %errorlevel% equ 0 (
    echo.
    echo Script completed successfully.
) else (
    echo.
    echo [Error] Script failed with exit code %errorlevel%.
)

pause