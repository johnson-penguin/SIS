# stop_uis.ps1
echo "Stopping all UI services..."

# 定義專案使用的 Port
$ports = @(5000, 5001, 5003, 5004)

foreach ($port in $ports) {
    # 尋找佔用該 Port 的 PID
    $proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($proc) {
        $pidToKill = $proc.OwningProcess
        Write-Host "Detecting Port $port (PID: $pidToKill), Killing..." -ForegroundColor Yellow
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "All UI Services Stopped." -ForegroundColor Green