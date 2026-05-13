# stop_servers.ps1

Write-Host "Stop Demo Python Services..." -ForegroundColor Yellow

# 定義要關閉的檔案名稱
$targets = @("0_edge_server.py", "0_single_ue_windows.py")

foreach ($file in $targets) {
    # 尋找指令列中包含該檔名的 python 程序並刪除
    $process = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' AND CommandLine LIKE '%$file%'"
    
    if ($process) {
        Stop-Process -Id $process.ProcessId -Force
        Write-Host "Killed: $file" -ForegroundColor Green
    } else {
        Write-Host "Process Not Found: $file" -ForegroundColor Gray
    }
}

Write-Host "Done!" -ForegroundColor Cyan