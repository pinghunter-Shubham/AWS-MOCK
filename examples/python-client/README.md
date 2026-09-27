# Python client integration example

This independent application proves that ordinary boto3 clients can use the
central AWS Mock without an `endpoint_url` in application code.

`Run-Test.ps1` supplies the endpoint and fake credentials only to the test
process. `app.py` verifies the selected endpoint, exercises seven services, and
deletes its temporary resources during teardown.

## Run

Start the central server from the repository root:

```powershell
.\host-moto\scripts\Start-AwsMock.ps1
```

Then run the example:

```powershell
cd .\examples\python-client
.\Install.ps1
.\Run-Test.ps1
```

Expected result:

```text
AWS mock integration test PASSED
[PASS] endpoint_redirect  all clients selected http://127.0.0.1:4566
[PASS] sts                caller identity succeeded
[PASS] s3                 create, put, and get succeeded
[PASS] dynamodb           create, put, and get succeeded
[PASS] sqs                create, send, and receive succeeded
[PASS] sns                create and publish succeeded
[PASS] secretsmanager     create and get succeeded
[PASS] kinesis            create and put succeeded
```
