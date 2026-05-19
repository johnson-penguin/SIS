# clean.ps1

Write-Host "Stop Demo Python Services..." -ForegroundColor Yellow

# 定義要關閉的檔案名稱關鍵字
$targets = @("0_edge_server.py", "0_single_ue_windows.py", "2_insurance_ui.py", "2_party_ui.py", "2_web_ue.py", "2_web_monitoring_station.py")

# 1. 一次性撈出目前系統中「所有」正在執行的 python.exe 進程
$allPythonProcesses = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'"

if ($allPythonProcesses) {
    foreach ($file in $targets) {
        # 2. 直接在記憶體中篩選，速度極快且不會受進程樹變動引發延遲
        $process = $allPythonProcesses | Where-Object { $_.CommandLine -like "*$file*" }
        
        if ($process) {
            foreach ($p in $process) {
                Stop-Process -Id $p.ProcessId -Force
            }
            Write-Host "Killed: $file" -ForegroundColor Green
        } else {
            Write-Host "Process Not Found: $file" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "No Python processes running at all." -ForegroundColor Gray
}

Write-Host "Done!" -ForegroundColor Cyan