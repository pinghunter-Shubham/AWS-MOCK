$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$endpoint = "http://127.0.0.1:4566"

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Run .\Install.ps1 first."
}

try {
    Invoke-WebRequest -UseBasicParsing -Uri "$endpoint/moto-api/" -TimeoutSec 3 | Out-Null
} catch {
    throw "AWS Mock is not reachable at $endpoint. Start it before running this test."
}

$keys = @(
    "AWS_ENDPOINT_URL",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_DEFAULT_REGION",
    "AWS_REGION",
    "AWS_EC2_METADATA_DISABLED",
    "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS"
)

$saved = @{}
foreach ($key in $keys) {
    $saved[$key] = [Environment]::GetEnvironmentVariable($key, "Process")
}

try {
    $env:AWS_ENDPOINT_URL = $endpoint
    $env:AWS_ACCESS_KEY_ID = "test"
    $env:AWS_SECRET_ACCESS_KEY = "test"
    Remove-Item Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
    $env:AWS_DEFAULT_REGION = "us-east-1"
    $env:AWS_REGION = "us-east-1"
    $env:AWS_EC2_METADATA_DISABLED = "true"
    $env:AWS_IGNORE_CONFIGURED_ENDPOINT_URLS = "false"

    & $venvPython (Join-Path $PSScriptRoot "app.py")
    if ($LASTEXITCODE -ne 0) { throw "Integration test failed." }
} finally {
    foreach ($key in $keys) {
        if ($null -eq $saved[$key]) {
            Remove-Item "Env:$key" -ErrorAction SilentlyContinue
        } else {
            [Environment]::SetEnvironmentVariable($key, $saved[$key], "Process")
        }
    }
}
