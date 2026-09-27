$ErrorActionPreference = "Stop"

$hostRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $hostRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$requirements = Join-Path $hostRoot "requirements.txt"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10 or newer is required. Python was not found on PATH."
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating isolated Python environment at $venvPath..."
    & python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the Python environment." }
}

Write-Host "Installing the pinned Moto Server dependency..."
& $venvPython -m pip install --disable-pip-version-check --only-binary=:all: -r $requirements
if ($LASTEXITCODE -ne 0) { throw "Failed to install Moto Server." }

& $venvPython -c "import moto; print('Moto version:', moto.__version__)"
Write-Host "Host-native AWS Mock installation complete."
