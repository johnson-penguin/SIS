@echo off
chcp 65001 >nul

echo =======================================
echo    SIS 專案 - 自動建置環境腳本
echo =======================================

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

echo [1/3] 正在建立虛擬環境 (venv)...
python -m venv venv

echo [2/3] 正在更新 pip...
:: 直接使用 venv 裡的 python 來執行，完全免除 activate 的權限問題
.\venv\Scripts\python.exe -m pip install --upgrade pip

echo [3/3] 正在安裝 requirements.txt 相依套件...
.\venv\Scripts\python.exe -m pip install -r requirements.txt

echo =======================================
echo    環境建置全部完成！
echo    請使用 .\venv\Scripts\Activate.ps1 啟動虛擬環境
echo =======================================
pause