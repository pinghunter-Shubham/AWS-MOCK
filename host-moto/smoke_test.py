"""Assert that the central AWS Mock and its default resources are healthy."""

from __future__ import annotations

import json
import os

import boto3


ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://127.0.0.1:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
EXPECTED_ACCOUNT = "123456789012"
EXPECTED_BUCKET = os.getenv("BOOTSTRAP_S3_BUCKET", "dev-app-bucket")
EXPECTED_TABLE = os.getenv("BOOTSTRAP_DYNAMODB_TABLE", "dev-app-table")
EXPECTED_QUEUE = os.getenv("BOOTSTRAP_SQS_QUEUE", "dev-app-queue")
EXPECTED_TOPIC = os.getenv("BOOTSTRAP_SNS_TOPIC", "dev-app-topic")
EXPECTED_SECRET = os.getenv("BOOTSTRAP_SECRET_NAME", "dev/app/config")
EXPECTED_STREAM = os.getenv("BOOTSTRAP_KINESIS_STREAM", "dev-app-stream")

COMMON = {
    "endpoint_url": ENDPOINT,
    "region_name": REGION,
    "aws_access_key_id": "test",
    "aws_secret_access_key": "test",
}


def client(service: str):
    return boto3.client(service, **COMMON)


def passed(label: str, detail: str) -> None:
    print(f"[PASS] {label:<18} {detail}")


def main() -> None:
    identity = client("sts").get_caller_identity()
    assert identity["Account"] == EXPECTED_ACCOUNT, identity
    passed("STS", f"account {EXPECTED_ACCOUNT}")

    s3 = client("s3")
    s3.head_bucket(Bucket=EXPECTED_BUCKET)
    passed("S3", f"bucket {EXPECTED_BUCKET}")

    table = client("dynamodb").describe_table(TableName=EXPECTED_TABLE)["Table"]
    assert table["TableStatus"] == "ACTIVE", table
    assert table["KeySchema"] == [{"AttributeName": "id", "KeyType": "HASH"}], table
    passed("DynamoDB", f"table {EXPECTED_TABLE} is ACTIVE")

    queue_url = client("sqs").get_queue_url(QueueName=EXPECTED_QUEUE)["QueueUrl"]
    assert EXPECTED_QUEUE in queue_url, queue_url
    passed("SQS", f"queue {EXPECTED_QUEUE}")

    topics = client("sns").list_topics().get("Topics", [])
    topic_arns = [item["TopicArn"] for item in topics]
    assert any(arn.endswith(f":{EXPECTED_TOPIC}") for arn in topic_arns), topic_arns
    passed("SNS", f"topic {EXPECTED_TOPIC}")

    secret_value = client("secretsmanager").get_secret_value(
        SecretId=EXPECTED_SECRET
    )["SecretString"]
    assert json.loads(secret_value)["environment"] == "local", secret_value
    passed("Secrets Manager", f"secret {EXPECTED_SECRET}")

    stream = client("kinesis").describe_stream_summary(
        StreamName=EXPECTED_STREAM
    )["StreamDescriptionSummary"]
    assert stream["StreamStatus"] == "ACTIVE", stream
    passed("Kinesis", f"stream {EXPECTED_STREAM} is ACTIVE")

    print(f"\nAWS Mock smoke test PASSED at {ENDPOINT}")


if __name__ == "__main__":
    main()
