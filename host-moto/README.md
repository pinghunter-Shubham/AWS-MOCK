# Central host-native AWS Mock

This implementation runs Moto Server 5.2.3 directly as a Windows Python process
at `http://127.0.0.1:4566`. Applications use the standard external endpoint
environment setting, so supported SDKs require no application source changes.

In command examples, replace `<repository-root>` with the directory where this
repository was cloned.

## Supported scope

The single endpoint emulates commonly used operations for S3, DynamoDB, SQS,
SNS, IAM, STS, Secrets Manager, Kinesis, CloudFormation, EventBridge, API Gateway,
CloudWatch, SSM, and other Moto-supported control-plane APIs.

Limitations:

- Lambda and Batch workloads are not executed by this host-native emulator.
- Moto implements a subset of each AWS API and does not provide exact AWS parity.
- Moto has no true state snapshot persistence. This package enables Moto Recorder,
  which replays recorded HTTP requests on restart. Workflows involving generated
  IDs, message receives, deletes, or complex transitions can diverge. Keep
  provisioning idempotent and do not treat the mock as durable storage.
- SDKs which ignore `AWS_ENDPOINT_URL` cannot be redirected universally.

## Install

Python 3.10 or newer is required.

```powershell
cd <repository-root>\host-moto
.\scripts\Install-AwsMock.ps1
```

Installation is isolated in `host-moto\.venv`; it needs no administrator access
and does not install packages globally.

## Start, inspect, and stop

```powershell
.\scripts\Start-AwsMock.ps1
.\scripts\Get-AwsMockStatus.ps1

# When finished:
.\scripts\Stop-AwsMock.ps1
```

The start script:

1. launches Moto on `127.0.0.1:4566` in a hidden process;
2. replays the retained request recording when present;
3. starts recording new requests;
4. idempotently creates the default resources;
5. writes logs under `host-moto\logs` and a PID under `host-moto\state`.

Default resources:

- S3 bucket `dev-app-bucket`
- DynamoDB table `dev-app-table`
- SQS queue `dev-app-queue`
- SNS topic `dev-app-topic`
- Secrets Manager secret `dev/app/config`
- Kinesis stream `dev-app-stream`

Override resource names before starting, for example:

```powershell
$env:BOOTSTRAP_S3_BUCKET = "project-a-files"
$env:BOOTSTRAP_DYNAMODB_TABLE = "project-a-items"
.\scripts\Start-AwsMock.ps1
```

## Verify

```powershell
& .\.venv\Scripts\python.exe .\smoke_test.py
```

## Use from another project

Start the central mock, then in the other project's PowerShell terminal:

```powershell
. <repository-root>\host-moto\scripts\Use-AwsMock.ps1
Enable-AwsMock

# Start the application in this same terminal.

Disable-AwsMock
```

The application process receives:

```dotenv
AWS_ENDPOINT_URL=http://127.0.0.1:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
AWS_EC2_METADATA_DISABLED=true
AWS_IGNORE_CONFIGURED_ENDPOINT_URLS=false
```

Alternatively, copy `app.env.example` and make the project's launcher or IDE
load it. A file does not inject itself; the framework, IDE, or launcher must load
the values into the application process.

## Multiple projects

Every project uses the same Moto process and account. Prefix resource names, for
example `project-a-files`, `project-a-items`, and `project-a-jobs`.

For repeatable projects, add resource creation to `bootstrap.py` or point the
project's existing infrastructure provisioning at `http://127.0.0.1:4566`.

Official references:

- https://docs.getmoto.org/en/latest/docs/server_mode.html
- https://docs.getmoto.org/en/latest/docs/services/
- https://docs.getmoto.org/en/latest/docs/configuration/recorder/
- https://docs.aws.amazon.com/sdkref/latest/guide/feature-ss-endpoints.html
