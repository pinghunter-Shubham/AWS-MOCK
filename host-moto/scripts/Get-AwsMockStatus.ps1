param(
    [ValidateRange(1, 65535)]
    [int]$Port = 4566
)

$endpoint = "http://127.0.0.1:$Port"
try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri "$endpoint/moto-api/" -TimeoutSec 3
    Write-Host "AWS Mock is running at $endpoint (HTTP $($response.StatusCode))."
    exit 0
} catch {
    Write-Host "AWS Mock is not reachable at $endpoint."
    exit 1
}

