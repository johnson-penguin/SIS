@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo 正在關閉所有 UI 服務 (Port 5000, 5001, 5003, 5004)...

:: 定義要檢查的 Port 號
set "ports=5000 5001 5003 5004"

for %%p in (%ports%) do (
    set "pid="
    
    :: 尋找監聽該 Port 的 PID
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r /c:":%%p "') do (
        set "pid=%%a"
    )

    if defined pid (
        echo 偵測到 Port %%p (PID: !pid!), 正在終止程序...
        taskkill /PID !pid! /F >nul 2>&1
    ) else (
        echo Port %%p 目前沒有執行中的服務。
    )
)

echo.
echo ==========================================
echo 所有 UI 服務已成功關閉！
echo ==========================================
pause