from __future__ import annotations

import argparse
import os

import boto3
from botocore.exceptions import ClientError


def client(service: str, endpoint_url: str, region: str):
    return boto3.client(
        service,
        endpoint_url=endpoint_url,
        region_name=region,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint-url", default="http://127.0.0.1:4566")
    args = parser.parse_args()

    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    bucket = os.getenv("BOOTSTRAP_S3_BUCKET", "dev-app-bucket")
    table = os.getenv("BOOTSTRAP_DYNAMODB_TABLE", "dev-app-table")
    queue = os.getenv("BOOTSTRAP_SQS_QUEUE", "dev-app-queue")
    topic = os.getenv("BOOTSTRAP_SNS_TOPIC", "dev-app-topic")
    secret = os.getenv("BOOTSTRAP_SECRET_NAME", "dev/app/config")
    secret_value = os.getenv("BOOTSTRAP_SECRET_VALUE", '{"environment":"local"}')
    stream = os.getenv("BOOTSTRAP_KINESIS_STREAM", "dev-app-stream")

    s3 = client("s3", args.endpoint_url, region)
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket)
        else:
            s3.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": region},
            )

    dynamodb = client("dynamodb", args.endpoint_url, region)
    try:
        dynamodb.describe_table(TableName=table)
    except dynamodb.exceptions.ResourceNotFoundException:
        dynamodb.create_table(
            TableName=table,
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST",
        )

    sqs = client("sqs", args.endpoint_url, region)
    try:
        sqs.get_queue_url(QueueName=queue)
    except sqs.exceptions.QueueDoesNotExist:
        sqs.create_queue(QueueName=queue)

    client("sns", args.endpoint_url, region).create_topic(Name=topic)

    secrets = client("secretsmanager", args.endpoint_url, region)
    try:
        secrets.describe_secret(SecretId=secret)
    except secrets.exceptions.ResourceNotFoundException:
        secrets.create_secret(Name=secret, SecretString=secret_value)

    kinesis = client("kinesis", args.endpoint_url, region)
    try:
        kinesis.describe_stream_summary(StreamName=stream)
    except kinesis.exceptions.ResourceNotFoundException:
        kinesis.create_stream(StreamName=stream, ShardCount=1)

    print("Host-native AWS Mock resources are ready:")
    print(f"  S3 bucket:       {bucket}")
    print(f"  DynamoDB table:  {table}")
    print(f"  SQS queue:       {queue}")
    print(f"  SNS topic:       {topic}")
    print(f"  Secret:          {secret}")
    print(f"  Kinesis stream:  {stream}")


if __name__ == "__main__":
    main()
