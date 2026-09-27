$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10 or newer is required."
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating the example's isolated Python environment..."
    & python -m venv (Join-Path $projectRoot ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the Python environment." }
}

& $venvPython -m pip install --disable-pip-version-check --only-binary=:all: -r (Join-Path $projectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install dependencies." }

Write-Host "Python client example installation complete."
