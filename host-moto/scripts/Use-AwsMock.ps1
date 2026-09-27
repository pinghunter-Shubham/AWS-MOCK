$script:HostAwsMockKeys = @(
    "AWS_ENDPOINT_URL",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_DEFAULT_REGION",
    "AWS_REGION",
    "AWS_EC2_METADATA_DISABLED",
    "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS"
)

function Enable-AwsMock {
    if ($null -ne $Global:HostAwsMockSavedEnvironment) {
        throw "AWS Mock environment is already enabled in this PowerShell session."
    }

    $saved = @{}
    foreach ($key in $script:HostAwsMockKeys) {
        $saved[$key] = [Environment]::GetEnvironmentVariable($key, "Process")
    }
    $Global:HostAwsMockSavedEnvironment = $saved

    $env:AWS_ENDPOINT_URL = "http://127.0.0.1:4566"
    $env:AWS_ACCESS_KEY_ID = "test"
    $env:AWS_SECRET_ACCESS_KEY = "test"
    Remove-Item Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
    $env:AWS_DEFAULT_REGION = "us-east-1"
    $env:AWS_REGION = "us-east-1"
    $env:AWS_EC2_METADATA_DISABLED = "true"
    $env:AWS_IGNORE_CONFIGURED_ENDPOINT_URLS = "false"
    Write-Host "This PowerShell process now targets the host-native AWS Mock."
}

function Disable-AwsMock {
    if ($null -eq $Global:HostAwsMockSavedEnvironment) {
        throw "No saved AWS environment exists in this PowerShell session."
    }

    foreach ($key in $script:HostAwsMockKeys) {
        $oldValue = $Global:HostAwsMockSavedEnvironment[$key]
        if ($null -eq $oldValue) {
            Remove-Item "Env:$key" -ErrorAction SilentlyContinue
        } else {
            [Environment]::SetEnvironmentVariable($key, $oldValue, "Process")
        }
    }
    $Global:HostAwsMockSavedEnvironment = $null
    Write-Host "The previous AWS environment has been restored."
}
