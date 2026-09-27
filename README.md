# Central host-native AWS Mock

This workspace contains one implementation: the Moto-based AWS Mock under
[`host-moto`](host-moto/README.md). It runs directly as a Windows Python
process at `http://127.0.0.1:4566`.

For complete installation, project integration, service examples, operations,
troubleshooting, and PDF conversion guidance, see
[`AWS_MOCK_COMPLETE_GUIDE.md`](AWS_MOCK_COMPLETE_GUIDE.md).

## Commands

```powershell
cd C:\Project_help\AWS_MOCK\host-moto

.\scripts\Install-AwsMock.ps1
.\scripts\Start-AwsMock.ps1
.\scripts\Get-AwsMockStatus.ps1
& .\.venv\Scripts\python.exe .\smoke_test.py
.\scripts\Stop-AwsMock.ps1
```

## Use from another project

```powershell
. C:\Project_help\AWS_MOCK\host-moto\scripts\Use-AwsMock.ps1
Enable-AwsMock

# Start the application from this PowerShell session.

Disable-AwsMock
```

See [the complete host-native guide](host-moto/README.md) for supported AWS
services, persistence behavior, resource provisioning, and limitations.
