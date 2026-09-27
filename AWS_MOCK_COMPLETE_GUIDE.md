---
title: "Central Host-Native AWS Mock"
subtitle: "Installation, Configuration, Service Provisioning, Integration, and Operations Guide"
author: "Local Development Platform"
date: "2026-09-27"
version: "1.0"
lang: "en-US"
papersize: "a4"
geometry: "margin=25mm"
fontsize: "11pt"
toc: true
toc-depth: 3
numbersections: true
colorlinks: true
linkcolor: blue
urlcolor: blue
---

# Document purpose

This document explains how to install, operate, and consume the central AWS Mock
located at `C:\Project_help\AWS_MOCK`. It is written as a complete onboarding and
operations guide and is structured so that it can be converted directly from
Markdown to a numbered PDF with a table of contents.

The AWS Mock runs Moto Server directly as a Windows process. Applications use
their normal AWS SDK clients. A process-level environment variable redirects
supported AWS SDK traffic to the local endpoint without adding an endpoint to
application source code.

## Document control

| Field | Value |
|---|---|
| Document version | 1.0 |
| Last updated | 2026-09-27 |
| AWS Mock implementation | Moto Server 5.2.3 |
| Operating system | Windows |
| Local endpoint | `http://127.0.0.1:4566` |
| Default region | `us-east-1` |
| Mock account ID | `123456789012` |
| Intended use | Local development and automated integration testing |

## Audience

This guide is intended for:

- developers connecting an existing application to the AWS Mock;
- DevOps engineers provisioning shared local test resources;
- test engineers running integration tests against AWS-compatible APIs; and
- maintainers responsible for keeping the central mock healthy.

## Scope

This guide covers:

- first-time installation;
- start, status, verification, and stop operations;
- zero-code endpoint redirection for new and existing projects;
- project-level resource naming and isolation;
- AWS CLI and SDK usage examples;
- initial setup examples for commonly used AWS services;
- request recording and restart behavior;
- security and operational safety;
- troubleshooting and recovery; and
- Markdown-to-PDF conversion.

This environment is an emulator. It is not a replacement for final testing in a
real AWS account.

# Architecture

## Request flow

```text
+-------------------------+
| Application or AWS CLI  |
| Normal AWS SDK clients  |
+------------+------------+
             |
             | Process environment:
             | AWS_ENDPOINT_URL=http://127.0.0.1:4566
             v
+-------------------------+
| Central Moto Server     |
| 127.0.0.1:4566          |
+------------+------------+
             |
             +--> In-memory AWS-compatible resource state
             +--> Request recording for restart replay
             +--> Local stdout and error logs
```

## Design principles

### One central service

One Moto Server process supports multiple local projects. Every project connects
to the same endpoint and mock account.

### Zero application endpoint changes

The application must initialize AWS clients normally. It must not add a local
`endpoint_url`, base URL, or hostname to its source code. The endpoint is injected
into the application process through `AWS_ENDPOINT_URL`.

### Process-level isolation

AWS Mock variables should be enabled only in the terminal, IDE launch profile,
or service process that starts the local application. Permanent machine-wide
variables are discouraged because they can redirect unrelated AWS tools.

### Fake local credentials

The server accepts fake credentials. The standard local values are:

```text
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
```

Never store real AWS credentials in an AWS Mock configuration file.

### Shared account with project-specific resource names

All projects share account `123456789012` and region `us-east-1`. Resource names
must include a project prefix to prevent collisions.

# Features and limitations

## Core features

The central AWS Mock provides:

- one AWS-compatible HTTP endpoint for supported services;
- standard AWS Signature Version 4 request handling;
- compatibility with supported AWS SDKs and the AWS CLI;
- fake local credentials;
- automatic creation of a default resource set;
- request recording and replay during restart;
- local status, smoke-test, start, and stop scripts;
- support for multiple projects at the same time;
- no requirement for a real AWS account; and
- local-only network binding on `127.0.0.1`.

## Commonly used service coverage

The server implements many control-plane and data-plane operations for services
including:

- Amazon S3;
- Amazon DynamoDB;
- Amazon SQS;
- Amazon SNS;
- AWS Secrets Manager;
- AWS Systems Manager Parameter Store;
- Amazon Kinesis Data Streams;
- AWS IAM;
- AWS STS;
- Amazon CloudWatch and CloudWatch Logs;
- Amazon EventBridge;
- AWS CloudFormation;
- Amazon API Gateway;
- Amazon EC2 control-plane resources; and
- many additional services listed in the Moto service catalog.

Support is operation-specific. A service appearing in the catalog does not mean
that every AWS operation or every validation rule is implemented.

## Important limitations

- Moto is not a byte-for-byte or behavior-for-behavior replica of AWS.
- IAM authorization enforcement may differ from real AWS.
- Quotas, throttling, latency, eventual consistency, and regional behavior are
  not guaranteed to match AWS.
- Lambda and Batch workload execution are not provided by this host-native
  configuration. Some resource-management operations may exist, but workload
  execution must be tested elsewhere.
- Request replay is not a transactional database snapshot.
- Generated identifiers can differ after replay.
- An SDK that does not support `AWS_ENDPOINT_URL` cannot use the global endpoint
  override without an SDK update or another configuration mechanism.
- The endpoint is available only from the same computer because it binds to
  `127.0.0.1`.

# Folder layout

```text
C:\Project_help\AWS_MOCK\
|
|-- AWS_MOCK_COMPLETE_GUIDE.md       This guide
|-- README.md                        Short command reference
`-- host-moto\
    |-- README.md                    Implementation notes
    |-- requirements.txt             Pinned Python dependencies
    |-- app.env.example              Environment variable example
    |-- bootstrap.py                 Default resource provisioning
    |-- smoke_test.py                Health and service smoke test
    |-- .venv\                       Isolated Python environment
    |-- logs\                        Runtime logs
    |-- state\                       PID and request recording
    `-- scripts\
        |-- Install-AwsMock.ps1
        |-- Start-AwsMock.ps1
        |-- Get-AwsMockStatus.ps1
        |-- Stop-AwsMock.ps1
        `-- Use-AwsMock.ps1
```

The `.venv`, `logs`, and `state` directories are runtime or generated content.
Application projects should not import Python modules from the mock's virtual
environment. Each application should manage its own dependencies.

# First-time installation

## Prerequisites

The computer must have:

- Windows PowerShell or PowerShell 7;
- Python 3.10 or newer;
- network access during the first dependency installation; and
- TCP port `4566` available.

Confirm Python:

```powershell
python --version
```

Confirm that port `4566` is not already in use:

```powershell
Get-NetTCPConnection -LocalPort 4566 -State Listen -ErrorAction SilentlyContinue
```

No output means that no process is currently listening on the port.

## Allow project scripts for the current terminal

If PowerShell reports that script execution is disabled, enable scripts only for
the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This setting disappears when the terminal is closed.

## Install the server dependencies

```powershell
cd C:\Project_help\AWS_MOCK\host-moto
.\scripts\Install-AwsMock.ps1
```

The installer:

1. confirms that Python is available;
2. creates `host-moto\.venv`;
3. installs the pinned dependencies into that environment; and
4. prints the installed Moto version.

It does not install Python packages globally.

## Start the server

```powershell
cd C:\Project_help\AWS_MOCK\host-moto
.\scripts\Start-AwsMock.ps1
```

The start operation:

1. creates runtime folders when necessary;
2. launches Moto Server as a hidden Windows process;
3. waits for `http://127.0.0.1:4566` to become ready;
4. pauses request recording;
5. replays an existing request recording;
6. resumes request recording;
7. creates the default resources idempotently; and
8. writes a process ID and runtime logs.

## Check server health

```powershell
.\scripts\Get-AwsMockStatus.ps1
```

Expected output:

```text
AWS Mock is running at http://127.0.0.1:4566 (HTTP 200).
```

## Run the smoke test

```powershell
& .\.venv\Scripts\python.exe .\smoke_test.py
```

The smoke test checks identity and lists representative S3, DynamoDB, and SQS
resources.

## Stop the server

```powershell
.\scripts\Stop-AwsMock.ps1
```

Stop the server before restarting Windows, performing recovery, or changing the
server installation. The service can otherwise remain running for multiple
projects.

# Default resources

The start script creates the following resources when they do not already exist:

| AWS service | Default resource | Purpose |
|---|---|---|
| S3 | `dev-app-bucket` | Local object storage |
| DynamoDB | `dev-app-table` | Key-value and document data |
| SQS | `dev-app-queue` | Application queue |
| SNS | `dev-app-topic` | Publish/subscribe topic |
| Secrets Manager | `dev/app/config` | Local secret value |
| Kinesis | `dev-app-stream` | Local streaming records |

Applications may use these resources, but separate projects should normally
create project-prefixed resources.

## Override bootstrap resource names

Resource names can be overridden in the PowerShell process that starts the
server:

```powershell
$env:BOOTSTRAP_S3_BUCKET = "project-a-files"
$env:BOOTSTRAP_DYNAMODB_TABLE = "project-a-items"
$env:BOOTSTRAP_SQS_QUEUE = "project-a-jobs"
$env:BOOTSTRAP_SNS_TOPIC = "project-a-events"
$env:BOOTSTRAP_SECRET_NAME = "project-a/config"
$env:BOOTSTRAP_KINESIS_STREAM = "project-a-stream"

cd C:\Project_help\AWS_MOCK\host-moto
.\scripts\Start-AwsMock.ps1
```

For a shared central server, independent project provisioning is preferable to
continually changing bootstrap variables.

# Connecting a project with zero endpoint code changes

## Preferred method: PowerShell session helper

Start the central server first. In the application project's terminal, import
the helper:

```powershell
. C:\Project_help\AWS_MOCK\host-moto\scripts\Use-AwsMock.ps1
Enable-AwsMock
```

The leading dot followed by a space is required. It imports the functions into
the current PowerShell session.

Start the application from the same terminal:

```powershell
cd C:\Path\To\YourProject

# Use the command appropriate for the project.
python app.py
# npm start
# dotnet run
# mvn spring-boot:run
# java -jar .\build\application.jar
```

When finished:

```powershell
Disable-AwsMock
```

`Disable-AwsMock` restores the environment values that existed before the mock
was enabled.

## Environment variables supplied to the application

```dotenv
AWS_ENDPOINT_URL=http://127.0.0.1:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
AWS_EC2_METADATA_DISABLED=true
AWS_IGNORE_CONFIGURED_ENDPOINT_URLS=false
```

These values have the following roles:

| Variable | Purpose |
|---|---|
| `AWS_ENDPOINT_URL` | Routes supported SDK service requests to Moto |
| `AWS_ACCESS_KEY_ID` | Supplies a non-production access key |
| `AWS_SECRET_ACCESS_KEY` | Supplies a non-production secret key |
| `AWS_DEFAULT_REGION` | Supplies the default region to tools such as the AWS CLI |
| `AWS_REGION` | Supplies the region to SDKs that prefer this variable |
| `AWS_EC2_METADATA_DISABLED` | Prevents local SDKs from querying EC2 instance metadata |
| `AWS_IGNORE_CONFIGURED_ENDPOINT_URLS` | Allows configured endpoint variables to be used |

## Manual environment configuration

If the helper cannot be used, set process-scoped variables manually:

```powershell
$env:AWS_ENDPOINT_URL = "http://127.0.0.1:4566"
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
Remove-Item Env:AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:AWS_REGION = "us-east-1"
$env:AWS_EC2_METADATA_DISABLED = "true"
$env:AWS_IGNORE_CONFIGURED_ENDPOINT_URLS = "false"
```

These variables affect only the current PowerShell process and applications
started from it.

## Project `.env` file

A project can store the same non-secret local values in a `.env` file:

```dotenv
AWS_ENDPOINT_URL=http://127.0.0.1:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
AWS_EC2_METADATA_DISABLED=true
AWS_IGNORE_CONFIGURED_ENDPOINT_URLS=false
```

A `.env` file does not modify the process environment by itself. The framework,
IDE, task runner, or launcher must load it before creating an AWS SDK client.

## IDE and Windows service configuration

An application launched by an IDE does not inherit environment variables from
an unrelated terminal. Add the variables to the IDE's run configuration, or
launch the IDE from an enabled terminal.

A Windows service must receive the variables through its service wrapper or
service-specific configuration. User-level PowerShell variables do not
automatically flow into an already-running Windows service.

## Verify redirection before running the application

Check the endpoint:

```powershell
$env:AWS_ENDPOINT_URL
```

Expected value:

```text
http://127.0.0.1:4566
```

For Python, inspect the endpoint selected by botocore without making an AWS
request:

```powershell
python -c "import boto3; print(boto3.client('s3').meta.endpoint_url)"
```

Expected value:

```text
http://127.0.0.1:4566
```

List all endpoint variables to detect a service-specific override:

```powershell
Get-ChildItem Env:AWS_ENDPOINT_URL*
```

An `AWS_ENDPOINT_URL_<SERVICE>` value has higher priority than the global
`AWS_ENDPOINT_URL` value for that service. An endpoint explicitly assigned in
application code has still higher priority.

# Standard AWS SDK examples

The following examples show normal client creation. None contains a local
endpoint. The process environment performs the redirection.

## Python with boto3

Install the SDK in the application's own environment:

```powershell
python -m pip install boto3
```

Create and use clients normally:

```python
import boto3

s3 = boto3.client("s3")
dynamodb = boto3.client("dynamodb")
sqs = boto3.client("sqs")

print(s3.list_buckets())
print(dynamodb.list_tables())
print(sqs.list_queues())
```

## Node.js with AWS SDK for JavaScript v3

Install the required service clients:

```powershell
npm install @aws-sdk/client-s3 @aws-sdk/client-dynamodb @aws-sdk/client-sqs
```

Use default client configuration:

```javascript
import { S3Client, ListBucketsCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({});
const result = await s3.send(new ListBucketsCommand({}));
console.log(result.Buckets);
```

## Java with AWS SDK v2

Use the SDK's default credential, region, and endpoint setting providers:

```java
import software.amazon.awssdk.services.s3.S3Client;

public class ListBuckets {
    public static void main(String[] args) {
        try (S3Client s3 = S3Client.create()) {
            s3.listBuckets().buckets()
                .forEach(bucket -> System.out.println(bucket.name()));
        }
    }
}
```

## .NET AWS SDK

```csharp
using Amazon.S3;

using var s3 = new AmazonS3Client();
var response = await s3.ListBucketsAsync();

foreach (var bucket in response.Buckets)
{
    Console.WriteLine(bucket.BucketName);
}
```

## Go AWS SDK v2

```go
package main

import (
    "context"
    "fmt"
    "log"

    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/service/s3"
)

func main() {
    ctx := context.Background()
    cfg, err := config.LoadDefaultConfig(ctx)
    if err != nil {
        log.Fatal(err)
    }

    client := s3.NewFromConfig(cfg)
    result, err := client.ListBuckets(ctx, &s3.ListBucketsInput{})
    if err != nil {
        log.Fatal(err)
    }

    for _, bucket := range result.Buckets {
        fmt.Println(*bucket.Name)
    }
}
```

## SDK compatibility rule

If a normal client still selects an AWS hostname:

1. confirm that `AWS_ENDPOINT_URL` is visible to the application process;
2. confirm that `AWS_IGNORE_CONFIGURED_ENDPOINT_URLS` is not `true`;
3. look for a higher-priority service-specific endpoint variable;
4. look for an endpoint explicitly configured in existing application code; and
5. update the AWS SDK to a version that supports the global endpoint setting.

There is no universal, reliable, zero-code redirection mechanism for an old SDK
that ignores both environment endpoint settings and shared endpoint settings.

# Resource naming and project isolation

## Naming convention

Use this pattern:

```text
<project>-<environment>-<purpose>
```

Examples:

```text
orders-local-files
orders-local-table
orders-local-jobs
billing-local-events
billing/local/config
```

For S3 buckets, use lowercase letters, digits, and hyphens. Keep names between 3
and 63 characters.

## Shared-state rules

- Do not use another project's resource prefix.
- Integration tests should add a unique suffix when running concurrently.
- Tests should delete temporary resources in a `finally` block or teardown step.
- Stable development resources should be created by an idempotent provisioning
  script.
- Do not assume that stopping the server deletes resources.

# AWS CLI setup

## Confirm AWS CLI availability

```powershell
aws --version
```

The CLI can use the environment endpoint when supported. For provisioning,
examples in this guide also pass `--endpoint-url` explicitly so that the target
is obvious at the command line.

## Prepare a provisioning terminal

```powershell
. C:\Project_help\AWS_MOCK\host-moto\scripts\Use-AwsMock.ps1
Enable-AwsMock

$AwsMockEndpoint = "http://127.0.0.1:4566"
$env:AWS_PAGER = ""
```

Confirm that the request reaches the mock:

```powershell
aws --endpoint-url $AwsMockEndpoint sts get-caller-identity
```

Expected account ID:

```text
123456789012
```

Do not continue with resource-changing commands if the endpoint variable is
empty or the returned account is a real AWS account.

# Service provisioning and usage examples

This section provides initial setup and basic usage examples for the most common
services. Run them from a provisioning terminal prepared in the previous
section.

## AWS Security Token Service

STS is useful for verifying connectivity and the active mock identity.

```powershell
aws --endpoint-url $AwsMockEndpoint sts get-caller-identity
```

Example SDK call:

```python
import boto3

identity = boto3.client("sts").get_caller_identity()
print(identity["Account"])
```

## Amazon S3

### Create a bucket

```powershell
aws --endpoint-url $AwsMockEndpoint s3api create-bucket `
    --bucket orders-local-files
```

### Upload and download an object

```powershell
Set-Content -LiteralPath .\hello.txt -Value "Hello from the AWS Mock"

aws --endpoint-url $AwsMockEndpoint s3 cp `
    .\hello.txt `
    s3://orders-local-files/hello.txt

aws --endpoint-url $AwsMockEndpoint s3 cp `
    s3://orders-local-files/hello.txt `
    .\downloaded-hello.txt
```

### List buckets and objects

```powershell
aws --endpoint-url $AwsMockEndpoint s3api list-buckets
aws --endpoint-url $AwsMockEndpoint s3api list-objects-v2 `
    --bucket orders-local-files
```

### Python example

```python
import boto3

s3 = boto3.client("s3")
s3.put_object(
    Bucket="orders-local-files",
    Key="orders/order-1001.json",
    Body=b'{"id":"order-1001"}',
    ContentType="application/json",
)

result = s3.get_object(
    Bucket="orders-local-files",
    Key="orders/order-1001.json",
)
print(result["Body"].read().decode("utf-8"))
```

## Amazon DynamoDB

### Create a table

```powershell
aws --endpoint-url $AwsMockEndpoint dynamodb create-table `
    --table-name orders-local-table `
    --attribute-definitions AttributeName=id,AttributeType=S `
    --key-schema AttributeName=id,KeyType=HASH `
    --billing-mode PAY_PER_REQUEST
```

### Create `order-item.json`

```json
{
  "id": {"S": "order-1001"},
  "status": {"S": "CREATED"},
  "amount": {"N": "42.50"}
}
```

### Put and retrieve an item

```powershell
aws --endpoint-url $AwsMockEndpoint dynamodb put-item `
    --table-name orders-local-table `
    --item file://order-item.json

aws --endpoint-url $AwsMockEndpoint dynamodb get-item `
    --table-name orders-local-table `
    --key '{"id":{"S":"order-1001"}}'
```

### Python example

```python
import boto3

table = boto3.resource("dynamodb").Table("orders-local-table")
table.put_item(Item={
    "id": "order-1002",
    "status": "CREATED",
    "amount": "15.00",
})

result = table.get_item(Key={"id": "order-1002"})
print(result["Item"])
```

## Amazon SQS

### Create a queue

```powershell
$QueueUrl = aws --endpoint-url $AwsMockEndpoint sqs create-queue `
    --queue-name orders-local-jobs `
    --query QueueUrl `
    --output text

$QueueUrl
```

### Send and receive a message

```powershell
aws --endpoint-url $AwsMockEndpoint sqs send-message `
    --queue-url $QueueUrl `
    --message-body '{"orderId":"order-1001"}'

aws --endpoint-url $AwsMockEndpoint sqs receive-message `
    --queue-url $QueueUrl `
    --max-number-of-messages 1 `
    --wait-time-seconds 1
```

### Python example

```python
import boto3

sqs = boto3.client("sqs")
queue_url = sqs.get_queue_url(QueueName="orders-local-jobs")["QueueUrl"]

sqs.send_message(
    QueueUrl=queue_url,
    MessageBody='{"orderId":"order-1002"}',
)

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1,
)
print(response.get("Messages", []))
```

## Amazon SNS

### Create a topic and publish an event

```powershell
$TopicArn = aws --endpoint-url $AwsMockEndpoint sns create-topic `
    --name orders-local-events `
    --query TopicArn `
    --output text

aws --endpoint-url $AwsMockEndpoint sns publish `
    --topic-arn $TopicArn `
    --message '{"event":"OrderCreated","orderId":"order-1001"}'
```

### Subscribe an SQS queue

```powershell
$QueueArn = aws --endpoint-url $AwsMockEndpoint sqs get-queue-attributes `
    --queue-url $QueueUrl `
    --attribute-names QueueArn `
    --query Attributes.QueueArn `
    --output text

aws --endpoint-url $AwsMockEndpoint sns subscribe `
    --topic-arn $TopicArn `
    --protocol sqs `
    --notification-endpoint $QueueArn
```

Real AWS requires an SQS access policy that permits the SNS topic to send
messages. Moto's policy enforcement can be less strict, so validate the final
policy in a real AWS test environment.

## AWS Secrets Manager

### Create and read a secret

```powershell
aws --endpoint-url $AwsMockEndpoint secretsmanager create-secret `
    --name orders/local/config `
    --secret-string '{"database":"local","apiKey":"fake-local-key"}'

aws --endpoint-url $AwsMockEndpoint secretsmanager get-secret-value `
    --secret-id orders/local/config
```

### Python example

```python
import json
import boto3

client = boto3.client("secretsmanager")
response = client.get_secret_value(SecretId="orders/local/config")
config = json.loads(response["SecretString"])
print(config["database"])
```

Only fake development secrets should be stored in the mock.

## AWS Systems Manager Parameter Store

### Create and read parameters

```powershell
aws --endpoint-url $AwsMockEndpoint ssm put-parameter `
    --name /orders/local/log-level `
    --type String `
    --value DEBUG `
    --overwrite

aws --endpoint-url $AwsMockEndpoint ssm get-parameter `
    --name /orders/local/log-level
```

### Python example

```python
import boto3

ssm = boto3.client("ssm")
value = ssm.get_parameter(
    Name="/orders/local/log-level"
)["Parameter"]["Value"]
print(value)
```

## Amazon Kinesis Data Streams

### Create a stream

```powershell
aws --endpoint-url $AwsMockEndpoint kinesis create-stream `
    --stream-name orders-local-stream `
    --shard-count 1
```

### Put a record

```powershell
aws --endpoint-url $AwsMockEndpoint kinesis put-record `
    --stream-name orders-local-stream `
    --partition-key customer-1001 `
    --data SGVsbG8tZnJvbS10aGUtbW9jaw==
```

AWS CLI v2 treats binary input according to its binary format setting. The value
above is base64-encoded text.

### Python example

```python
import boto3

kinesis = boto3.client("kinesis")
kinesis.put_record(
    StreamName="orders-local-stream",
    PartitionKey="customer-1001",
    Data=b'{"orderId":"order-1001"}',
)
```

## AWS IAM

IAM APIs are useful when a project needs roles, users, policies, or instance
profiles to exist. Local policy evaluation may not exactly match AWS.

### Create and list a user

```powershell
aws --endpoint-url $AwsMockEndpoint iam create-user `
    --user-name orders-local-user

aws --endpoint-url $AwsMockEndpoint iam list-users
```

### Create `trust-policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Create a role

```powershell
aws --endpoint-url $AwsMockEndpoint iam create-role `
    --role-name orders-local-role `
    --assume-role-policy-document file://trust-policy.json
```

## Amazon CloudWatch Metrics

### Create `metric-data.json`

```json
[
  {
    "MetricName": "OrdersCreated",
    "Dimensions": [
      {"Name": "Environment", "Value": "local"}
    ],
    "Value": 1,
    "Unit": "Count"
  }
]
```

### Publish and query a metric

```powershell
aws --endpoint-url $AwsMockEndpoint cloudwatch put-metric-data `
    --namespace Orders/Application `
    --metric-data file://metric-data.json

aws --endpoint-url $AwsMockEndpoint cloudwatch list-metrics `
    --namespace Orders/Application
```

## Amazon CloudWatch Logs

### Create a log group and stream

```powershell
aws --endpoint-url $AwsMockEndpoint logs create-log-group `
    --log-group-name /orders/local/application

aws --endpoint-url $AwsMockEndpoint logs create-log-stream `
    --log-group-name /orders/local/application `
    --log-stream-name instance-1

aws --endpoint-url $AwsMockEndpoint logs describe-log-groups `
    --log-group-name-prefix /orders/local
```

Moto can emulate many CloudWatch Logs control-plane calls, but production log
delivery behavior, retention timing, and service integrations can differ.

## Amazon EventBridge

### Create an event bus

```powershell
aws --endpoint-url $AwsMockEndpoint events create-event-bus `
    --name orders-local-bus
```

### Create `event-pattern.json`

```json
{
  "source": ["orders.application"],
  "detail-type": ["OrderCreated"]
}
```

### Create a rule

```powershell
aws --endpoint-url $AwsMockEndpoint events put-rule `
    --name orders-local-created-rule `
    --event-bus-name orders-local-bus `
    --event-pattern file://event-pattern.json `
    --state ENABLED
```

### Create `event-entry.json`

```json
[
  {
    "Source": "orders.application",
    "DetailType": "OrderCreated",
    "Detail": "{\"orderId\":\"order-1001\"}",
    "EventBusName": "orders-local-bus"
  }
]
```

### Publish an event

```powershell
aws --endpoint-url $AwsMockEndpoint events put-events `
    --entries file://event-entry.json
```

## AWS CloudFormation

CloudFormation can provision supported Moto resources. Not every resource type,
transform, attribute, or deployment behavior is available.

### Create `local-stack-template.yml`

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: Local resources for the orders project

Resources:
  OrdersBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: orders-local-cfn-files

  OrdersQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: orders-local-cfn-jobs
```

### Create and inspect the stack

```powershell
aws --endpoint-url $AwsMockEndpoint cloudformation create-stack `
    --stack-name orders-local-stack `
    --template-body file://local-stack-template.yml

aws --endpoint-url $AwsMockEndpoint cloudformation describe-stacks `
    --stack-name orders-local-stack
```

Use CloudFormation locally only for resource types listed as implemented by
Moto. Always validate production infrastructure against AWS.

## Amazon API Gateway

### Create and list REST APIs

```powershell
$RestApiId = aws --endpoint-url $AwsMockEndpoint apigateway create-rest-api `
    --name orders-local-api `
    --query id `
    --output text

aws --endpoint-url $AwsMockEndpoint apigateway get-rest-apis
```

Moto is best suited to testing API Gateway resource configuration and related
control-plane calls. It is not a complete replacement for a deployed API's
runtime request pipeline.

## Amazon EC2 control plane

### Create and inspect a VPC

```powershell
$VpcId = aws --endpoint-url $AwsMockEndpoint ec2 create-vpc `
    --cidr-block 10.50.0.0/16 `
    --query Vpc.VpcId `
    --output text

aws --endpoint-url $AwsMockEndpoint ec2 describe-vpcs `
    --vpc-ids $VpcId
```

EC2 resources are metadata models only. Moto does not start real virtual
machines or create operating-system networking.

## Lambda and Batch

This host-native setup must not be used to validate Lambda or Batch workload
execution. It does not provide the external execution runtime required for those
workloads. Test business logic as normal application code and validate actual
managed-runtime behavior in a dedicated AWS test account.

# Complete new-project workflow

The following workflow should be used when onboarding a new project.

## Step 1: choose a project prefix

Example:

```text
Project: orders-service
Prefix:  orders-local
```

## Step 2: document required services and names

| Service | Application setting | Local resource |
|---|---|---|
| S3 | `ORDERS_BUCKET` | `orders-local-files` |
| DynamoDB | `ORDERS_TABLE` | `orders-local-table` |
| SQS | `ORDERS_QUEUE` | `orders-local-jobs` |
| SNS | `ORDERS_TOPIC` | `orders-local-events` |
| Secrets Manager | `ORDERS_SECRET` | `orders/local/config` |

Use the application's existing configuration mechanism to supply resource names.
The zero-code endpoint policy does not require every application resource name to
be identical.

## Step 3: start and verify the central mock

```powershell
cd C:\Project_help\AWS_MOCK\host-moto
.\scripts\Start-AwsMock.ps1
.\scripts\Get-AwsMockStatus.ps1
```

## Step 4: enable the mock in the project terminal

```powershell
. C:\Project_help\AWS_MOCK\host-moto\scripts\Use-AwsMock.ps1
Enable-AwsMock
```

## Step 5: provision the project's resources

Use the AWS CLI examples in this guide or a project-owned idempotent bootstrap
script. Provisioning code should also rely on the environment endpoint instead
of embedding the endpoint in the script.

## Step 6: confirm SDK routing

```powershell
python -c "import boto3; print(boto3.client('s3').meta.endpoint_url)"
```

## Step 7: start the application in the same terminal

```powershell
cd C:\Path\To\orders-service
python app.py
```

Replace the final command with the project's normal start command.

## Step 8: run integration tests

Tests should:

1. use unique resource or item identifiers;
2. create only the data required by the test;
3. assert expected AWS SDK responses;
4. delete temporary resources in teardown; and
5. avoid assumptions about AWS latency or eventual consistency.

## Step 9: restore the terminal environment

```powershell
Disable-AwsMock
```

# Working reference project

The independent reference project is located at:

```text
C:\Project_help\AWS_MOCK_CLIENT_TEST
```

Install and execute it:

```powershell
cd C:\Project_help\AWS_MOCK_CLIENT_TEST
.\Install.ps1
.\Run-Test.ps1
```

The test uses ordinary boto3 clients without an endpoint in `app.py`. Its launcher
sets the endpoint in the process environment. It exercises:

- STS identity;
- S3 create, put, and get;
- DynamoDB create, put, and get;
- SQS create, send, and receive;
- SNS create and publish;
- Secrets Manager create and get; and
- Kinesis create and put.

Temporary test resources are removed during teardown.

# Multiple-project operation

## Recommended model

Keep the central server running and give each project its own:

- PowerShell or IDE launch environment;
- resource prefix;
- provisioning script;
- test data namespace; and
- cleanup procedure.

Example:

```text
Central endpoint: http://127.0.0.1:4566

Project A:
  orders-local-files
  orders-local-table
  orders-local-jobs

Project B:
  billing-local-files
  billing-local-table
  billing-local-jobs
```

## Concurrency considerations

- Use a unique suffix for resources created by parallel test runs.
- Do not assert that a service list contains only one project's resources.
- SQS receive operations can consume messages, so use a queue per test suite.
- Avoid resetting the central server while other projects are running.
- Coordinate changes to stable shared resources.

# Persistence and state management

## How persistence works

Moto stores active state in server memory. This package enables Moto Recorder,
which appends incoming HTTP requests to:

```text
C:\Project_help\AWS_MOCK\host-moto\state\moto-recording.log
```

During the next start, the start script replays the recorded requests.

## Persistence limitations

Request replay is useful for reconstructing common development resources, but it
has limitations:

- generated IDs may be different after replay;
- reads and message receives are recorded alongside mutations;
- create/delete sequences are replayed in order;
- complex service integrations may not reconstruct perfectly; and
- a corrupted or very large recording can slow startup.

Keep project provisioning idempotent even when recording is enabled.

## Runtime files

| Path | Purpose |
|---|---|
| `host-moto\state\moto.pid` | Process ID used by stop and status operations |
| `host-moto\state\moto-recording.log` | Recorded requests for replay |
| `host-moto\logs\moto.stdout.log` | Standard server output |
| `host-moto\logs\moto.stderr.log` | Server warnings and errors |

## Back up recorded state

Stop the server before copying the recording:

```powershell
cd C:\Project_help\AWS_MOCK\host-moto
.\scripts\Stop-AwsMock.ps1

$BackupStamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item `
    -LiteralPath .\state\moto-recording.log `
    -Destination ".\state\moto-recording-$BackupStamp.backup.log"
```

Restart after the copy:

```powershell
.\scripts\Start-AwsMock.ps1
```

## Recover from an unusable recording

This procedure starts from fresh runtime state while keeping the old recording
as a recoverable backup.

```powershell
cd C:\Project_help\AWS_MOCK\host-moto
.\scripts\Stop-AwsMock.ps1

$RecoveryStamp = Get-Date -Format "yyyyMMdd-HHmmss"
Move-Item `
    -LiteralPath .\state\moto-recording.log `
    -Destination ".\state\moto-recording-$RecoveryStamp.recovery.log"

.\scripts\Start-AwsMock.ps1
```

The start script creates the default resources again. Re-provision each project's
resources afterward. Perform this reset only when no other project is using the
central server.

# Resource cleanup

Stopping the server does not mean that resources will disappear after the next
replay. Delete temporary resources through their service APIs.

Examples:

```powershell
# S3 objects must be removed before the bucket.
aws --endpoint-url $AwsMockEndpoint s3 rm `
    s3://orders-local-files `
    --recursive
aws --endpoint-url $AwsMockEndpoint s3api delete-bucket `
    --bucket orders-local-files

aws --endpoint-url $AwsMockEndpoint dynamodb delete-table `
    --table-name orders-local-table

aws --endpoint-url $AwsMockEndpoint sqs delete-queue `
    --queue-url $QueueUrl

aws --endpoint-url $AwsMockEndpoint sns delete-topic `
    --topic-arn $TopicArn

aws --endpoint-url $AwsMockEndpoint secretsmanager delete-secret `
    --secret-id orders/local/config `
    --force-delete-without-recovery

aws --endpoint-url $AwsMockEndpoint ssm delete-parameter `
    --name /orders/local/log-level

aws --endpoint-url $AwsMockEndpoint kinesis delete-stream `
    --stream-name orders-local-stream
```

Use cleanup commands only for resources owned by the current project.

# Security and operational safety

## Never use real credentials

Use `test` credentials only. The emulator does not need access to a real AWS
account.

## Prefer temporary environment activation

Use `Enable-AwsMock` and `Disable-AwsMock`. Avoid `setx` or permanent Windows
environment variables for `AWS_ENDPOINT_URL`.

## Verify the target before destructive operations

Before creating, updating, or deleting resources:

```powershell
$env:AWS_ENDPOINT_URL
aws --endpoint-url $AwsMockEndpoint sts get-caller-identity
```

The endpoint must be `http://127.0.0.1:4566`, and the account must be
`123456789012`.

## Keep the endpoint local

The service is intentionally bound to `127.0.0.1`. Do not expose it on a shared
network. The fake credential model is appropriate only for local access.

## Keep production data out

Do not place real customer data, production secrets, production certificates,
or regulated information in the mock.

## Separate local and real-AWS terminals

Use a clearly identified terminal for local mock work. Run `Disable-AwsMock`
before performing any task intended for real AWS.

# Daily operations

## Start-of-day checklist

```powershell
cd C:\Project_help\AWS_MOCK\host-moto
.\scripts\Start-AwsMock.ps1
.\scripts\Get-AwsMockStatus.ps1
```

For each project terminal:

```powershell
. C:\Project_help\AWS_MOCK\host-moto\scripts\Use-AwsMock.ps1
Enable-AwsMock
```

## End-of-day checklist

In each application terminal:

```powershell
Disable-AwsMock
```

Optionally stop the central server:

```powershell
cd C:\Project_help\AWS_MOCK\host-moto
.\scripts\Stop-AwsMock.ps1
```

## Periodic maintenance checklist

- Run the status script.
- Run `smoke_test.py`.
- Review `moto.stderr.log` for errors.
- Monitor the size of `moto-recording.log`.
- Back up important local recordings.
- Confirm that project bootstrap scripts remain idempotent.
- Test the reference client after dependency or operating-system updates.
- Keep Moto and AWS SDK versions pinned and upgrade deliberately.

# Troubleshooting

## Connection refused

Symptoms:

```text
Could not connect to the endpoint URL
Connection refused
```

Checks:

```powershell
cd C:\Project_help\AWS_MOCK\host-moto
.\scripts\Get-AwsMockStatus.ps1
Get-NetTCPConnection -LocalPort 4566 -State Listen -ErrorAction SilentlyContinue
```

Resolution:

```powershell
.\scripts\Start-AwsMock.ps1
```

## Application still contacts an AWS hostname

Check variables in the exact application process or its launch terminal:

```powershell
$env:AWS_ENDPOINT_URL
$env:AWS_IGNORE_CONFIGURED_ENDPOINT_URLS
Get-ChildItem Env:AWS_ENDPOINT_URL*
```

Common causes:

- the application was started before variables were enabled;
- the application was launched by an IDE with a different environment;
- `AWS_IGNORE_CONFIGURED_ENDPOINT_URLS=true`;
- a service-specific endpoint overrides the global endpoint;
- existing application code explicitly configures another endpoint; or
- the SDK version does not support the endpoint environment setting.

## Credentials error

Check:

```powershell
$env:AWS_ACCESS_KEY_ID
$env:AWS_SECRET_ACCESS_KEY
$env:AWS_EC2_METADATA_DISABLED
```

Expected values are `test`, `test`, and `true`.

## Region error

Check:

```powershell
$env:AWS_DEFAULT_REGION
$env:AWS_REGION
```

Both should normally be `us-east-1`.

## Resource not found

Possible causes:

- the resource was never provisioned;
- the application expects a different name;
- the project is using another region;
- a previous test deleted the shared resource; or
- a recording was reset.

List resources with the relevant AWS CLI command and compare names to the
application's configuration.

## Resource already exists

Use project-prefixed names or make provisioning idempotent. For integration tests,
append a random or run-specific suffix.

## Port 4566 is occupied

Identify the listener:

```powershell
Get-NetTCPConnection -LocalPort 4566 -State Listen |
    Select-Object LocalAddress, LocalPort, OwningProcess
```

Inspect the owning process:

```powershell
Get-Process -Id <OwningProcess>
```

Do not terminate an unknown process until its ownership and purpose are known.

## Server starts but replay fails

Review logs:

```powershell
Get-Content `
    C:\Project_help\AWS_MOCK\host-moto\logs\moto.stderr.log `
    -Tail 100
```

If the recording is unusable, follow the recoverable recording reset procedure
in the persistence section.

## `.env` file appears to have no effect

Confirm that the project's framework or launcher actually loads `.env`. Plain
Python, Java, and many command-line launchers do not load `.env` automatically.
Use `Enable-AwsMock` when uncertain.

## One operation is unsupported

Check the Moto service page for that service and operation. If the operation is
not implemented:

1. isolate the unsupported integration behind an existing test boundary;
2. test business logic separately;
3. use a dedicated AWS test account for the unsupported behavior; and
4. do not assume that a successful related operation guarantees full service
   parity.

# Upgrade procedure

Upgrade only when there is a clear need for a new service or bug fix.

Recommended process:

1. stop the server;
2. back up `moto-recording.log`;
3. review Moto release notes and supported-operation changes;
4. update pinned versions in `requirements.txt`;
5. rebuild the isolated Python environment;
6. start the server;
7. run the central smoke test;
8. run `AWS_MOCK_CLIENT_TEST`; and
9. run each project's integration suite.

Do not perform an untested automatic upgrade of the shared central service.

# Quick reference

## Central server commands

```powershell
cd C:\Project_help\AWS_MOCK\host-moto

# First-time installation
.\scripts\Install-AwsMock.ps1

# Daily operation
.\scripts\Start-AwsMock.ps1
.\scripts\Get-AwsMockStatus.ps1
& .\.venv\Scripts\python.exe .\smoke_test.py
.\scripts\Stop-AwsMock.ps1
```

## Application project commands

```powershell
. C:\Project_help\AWS_MOCK\host-moto\scripts\Use-AwsMock.ps1
Enable-AwsMock

cd C:\Path\To\YourProject
# Start the application here.

Disable-AwsMock
```

## Safety verification

```powershell
$env:AWS_ENDPOINT_URL
aws --endpoint-url http://127.0.0.1:4566 sts get-caller-identity
```

Expected values:

```text
Endpoint: http://127.0.0.1:4566
Account:  123456789012
Region:   us-east-1
```

# Markdown-to-PDF conversion

The document begins with Pandoc-compatible metadata for A4 paper, margins,
numbered sections, link colors, and a generated table of contents.

## Pandoc example

After installing Pandoc and a supported PDF engine:

```powershell
cd C:\Project_help\AWS_MOCK

pandoc .\AWS_MOCK_COMPLETE_GUIDE.md `
    --output .\AWS_MOCK_COMPLETE_GUIDE.pdf `
    --toc `
    --number-sections `
    --pdf-engine=xelatex
```

If `xelatex` is not installed, use a PDF engine available on the computer or a
Markdown editor with a PDF export feature.

## PDF quality checklist

After conversion, verify:

- the title and version appear correctly;
- the table of contents contains clickable entries;
- headings are numbered consistently;
- command blocks do not overflow page margins;
- tables fit within A4 page width;
- URLs are clickable;
- no code block is unexpectedly split across pages; and
- the final references are included.

# References

- AWS SDKs and Tools Reference Guide, service-specific and global endpoint
  settings: <https://docs.aws.amazon.com/sdkref/latest/guide/feature-ss-endpoints.html>
- AWS service-specific endpoint identifiers:
  <https://docs.aws.amazon.com/sdkref/latest/guide/ss-endpoints-table.html>
- Moto Server mode:
  <https://docs.getmoto.org/en/latest/docs/server_mode.html>
- Moto implemented services:
  <https://docs.getmoto.org/en/latest/docs/services/>
- Moto Recorder:
  <https://docs.getmoto.org/en/latest/docs/configuration/recorder/>
- AWS CLI command reference:
  <https://docs.aws.amazon.com/cli/latest/reference/>

# Final readiness checklist

Before declaring a project ready to use the AWS Mock, confirm every item:

- [ ] Python 3.10 or newer is installed.
- [ ] The central dependencies are installed.
- [ ] The server is running on `127.0.0.1:4566`.
- [ ] The central smoke test passes.
- [ ] The project has a unique resource prefix.
- [ ] Required resources are provisioned.
- [ ] The application process receives `AWS_ENDPOINT_URL`.
- [ ] The application uses fake local credentials.
- [ ] The SDK selects `http://127.0.0.1:4566`.
- [ ] No local endpoint was added to application source code.
- [ ] Integration tests clean up temporary resources.
- [ ] The project team understands emulator limitations.
- [ ] Real-AWS validation remains part of the release process.

