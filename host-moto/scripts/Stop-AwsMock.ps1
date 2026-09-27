$ErrorActionPreference = "Stop"
$hostRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $hostRoot "state"
$pidFile = Join-Path $statePath "moto.pid"
$endpoint = "http://127.0.0.1:4566"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "AWS Mock is not running (no PID file)."
    exit 0
}

$motoPid = [int](Get-Content -LiteralPath $pidFile -Raw)
$process = Get-Process -Id $motoPid -ErrorAction SilentlyContinue
if ($null -eq $process) {
    Remove-Item -LiteralPath $pidFile -Force
    Write-Host "AWS Mock process is no longer running; stale PID file removed."
    exit 0
}

try {
    Invoke-RestMethod -Method Post -Uri "$endpoint/moto-api/recorder/stop-recording" -TimeoutSec 5 | Out-Null
} catch {
    Write-Warning "Could not stop the recorder cleanly: $($_.Exception.Message)"
}

Stop-Process -Id $motoPid -Force
Remove-Item -LiteralPath $pidFile -Force
Write-Host "Host-native AWS Mock stopped. The request recording was retained."
