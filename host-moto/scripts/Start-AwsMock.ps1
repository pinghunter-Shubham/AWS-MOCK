param(
    [ValidateRange(1, 65535)]
    [int]$Port = 4566
)

$ErrorActionPreference = "Stop"
$hostRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $hostRoot ".venv"
$motoServer = Join-Path $venvPath "Scripts\moto_server.exe"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$statePath = Join-Path $hostRoot "state"
$logPath = Join-Path $hostRoot "logs"
$pidFile = Join-Path $statePath "moto.pid"
$recordingFile = Join-Path $statePath "moto-recording.log"
$bootstrapScript = Join-Path $hostRoot "bootstrap.py"
$endpoint = "http://127.0.0.1:$Port"

if (-not (Test-Path -LiteralPath $motoServer)) {
    throw "Moto Server is not installed. Run .\scripts\Install-AwsMock.ps1 first."
}

New-Item -ItemType Directory -Force -Path $statePath, $logPath | Out-Null

if (Test-Path -LiteralPath $pidFile) {
    $existingPid = [int](Get-Content -LiteralPath $pidFile -Raw)
    if (Get-Process -Id $existingPid -ErrorAction SilentlyContinue) {
        Write-Host "AWS Mock is already running with PID $existingPid at $endpoint."
        exit 0
    }
    Remove-Item -LiteralPath $pidFile -Force
}

$env:MOTO_ENABLE_RECORDING = "True"
$env:MOTO_RECORDER_FILEPATH = $recordingFile
$env:S3_IGNORE_SUBDOMAIN_BUCKETNAME = "true"
$env:MOTO_IAM_LOAD_MANAGED_POLICIES = "true"
$env:MOTO_PRETTIFY_RESPONSES = "false"

$stdoutLog = Join-Path $logPath "moto.stdout.log"
$stderrLog = Join-Path $logPath "moto.stderr.log"
$hadRecording = (Test-Path -LiteralPath $recordingFile) -and ((Get-Item -LiteralPath $recordingFile).Length -gt 0)
$startParameters = @{
    FilePath               = $motoServer
    ArgumentList           = @("-H", "127.0.0.1", "-p", "$Port")
    RedirectStandardOutput = $stdoutLog
    RedirectStandardError  = $stderrLog
    WindowStyle             = "Hidden"
    PassThru                = $true
}
$process = Start-Process @startParameters

Set-Content -LiteralPath $pidFile -Value $process.Id -NoNewline

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($process.HasExited) {
            throw "Moto Server exited during startup. Inspect $stderrLog."
        }
        try {
            Invoke-WebRequest -UseBasicParsing -Uri "$endpoint/moto-api/" -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    if (-not $ready) { throw "Moto Server did not become ready at $endpoint." }

    # MOTO_ENABLE_RECORDING starts recording immediately. Pause it before replay
    # so replayed requests are not appended to the recording a second time.
    Invoke-RestMethod -Method Post -Uri "$endpoint/moto-api/recorder/stop-recording" | Out-Null

    if ($hadRecording) {
        Write-Host "Replaying the recorded AWS requests..."
        Invoke-RestMethod -Method Post -Uri "$endpoint/moto-api/recorder/replay-recording" | Out-Null
    } else {
        # Discard the readiness probe recorded during the first startup.
        Invoke-RestMethod -Method Post -Uri "$endpoint/moto-api/recorder/reset-recording" | Out-Null
    }

    Invoke-RestMethod -Method Post -Uri "$endpoint/moto-api/recorder/start-recording" | Out-Null
    if (-not $hadRecording) {
        Invoke-RestMethod -Method Post -Uri "$endpoint/moto-api/seed?a=42" | Out-Null
    }

    & $venvPython $bootstrapScript --endpoint-url $endpoint
    if ($LASTEXITCODE -ne 0) { throw "Resource bootstrap failed." }

    Write-Host "Host-native AWS Mock is ready at $endpoint (PID $($process.Id))."
    Write-Host "Logs: $logPath"
} catch {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    throw
}
