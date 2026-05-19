@echo off
start http://127.0.0.1:5000/
timeout /t 1 >nul
start http://127.0.0.1:5001/
timeout /t 1 >nul
start http://127.0.0.1:5003/
timeout /t 1 >nul
start http://127.0.0.1:5004/