# start_uis.ps1
$scriptDir = $PSScriptRoot
# 退回 situation_1 根目錄
$parentDir = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $parentDir

Write-Host "Starting UIs in Background..." -ForegroundColor Cyan

# 確保每一行只有一個 -ArgumentList
Start-Process python -ArgumentList "2_web_monitoring_station.py" -WindowStyle Hidden
Start-Process python -ArgumentList "2_web_ue.py" -WindowStyle Hidden
Start-Process python -ArgumentList "3_party_ui.py" -WindowStyle Hidden
Start-Process python -ArgumentList "4_insurance_ui.py" -WindowStyle Hidden

Write-Host "=========================================================="
Write-Host "2_web_monitoring_station.py -> http://localhost:5000"
Write-Host "2_web_ue.py                 -> http://localhost:5001"
Write-Host "3_party_ui.py               -> http://localhost:5003"
Write-Host "4_insurance_ui.py           -> http://localhost:5004"
Write-Host "=========================================================="
Write-Host "Success! Use 'stop_uis.ps1' to terminate them." -ForegroundColor Green