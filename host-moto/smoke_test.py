from __future__ import annotations

import boto3

ENDPOINT = "http://127.0.0.1:4566"
COMMON = {
    "endpoint_url": ENDPOINT,
    "region_name": "us-east-1",
    "aws_access_key_id": "test",
    "aws_secret_access_key": "test",
}

print("Caller:", boto3.client("sts", **COMMON).get_caller_identity()["Account"])
print("Buckets:", [b["Name"] for b in boto3.client("s3", **COMMON).list_buckets()["Buckets"]])
print("Tables:", boto3.client("dynamodb", **COMMON).list_tables()["TableNames"])
print("Queues:", boto3.client("sqs", **COMMON).list_queues().get("QueueUrls", []))
