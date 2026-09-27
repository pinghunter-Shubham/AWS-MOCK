"""Prove that standard boto3 clients can use the mock without endpoint code."""

from __future__ import annotations

import json
import os
import uuid

import boto3


def main() -> None:
    expected_endpoint = os.environ["AWS_ENDPOINT_URL"].rstrip("/")
    suffix = uuid.uuid4().hex[:10]
    names = {
        "bucket": f"aws-mock-client-{suffix}",
        "table": f"aws-mock-client-{suffix}",
        "queue": f"aws-mock-client-{suffix}",
        "topic": f"aws-mock-client-{suffix}",
        "secret": f"aws-mock-client/{suffix}",
        "stream": f"aws-mock-client-{suffix}",
    }

    # No client below contains endpoint_url. Botocore reads AWS_ENDPOINT_URL.
    clients = {
        "sts": boto3.client("sts"),
        "s3": boto3.client("s3"),
        "dynamodb": boto3.client("dynamodb"),
        "sqs": boto3.client("sqs"),
        "sns": boto3.client("sns"),
        "secretsmanager": boto3.client("secretsmanager"),
        "kinesis": boto3.client("kinesis"),
    }

    for service, sdk_client in clients.items():
        selected = sdk_client.meta.endpoint_url.rstrip("/")
        assert selected == expected_endpoint, f"{service} selected {selected}"

    created: dict[str, str | bool] = {}
    results: dict[str, str] = {
        "endpoint_redirect": f"all clients selected {expected_endpoint}"
    }

    try:
        identity = clients["sts"].get_caller_identity()
        assert identity["Account"] == "123456789012", identity
        results["sts"] = "caller identity succeeded"

        clients["s3"].create_bucket(Bucket=names["bucket"])
        created["bucket"] = True
        clients["s3"].put_object(
            Bucket=names["bucket"], Key="hello.txt", Body=b"hello from external project"
        )
        body = clients["s3"].get_object(
            Bucket=names["bucket"], Key="hello.txt"
        )["Body"].read()
        assert body == b"hello from external project"
        results["s3"] = "create, put, and get succeeded"

        clients["dynamodb"].create_table(
            TableName=names["table"],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        created["table"] = True
        clients["dynamodb"].put_item(
            TableName=names["table"],
            Item={"id": {"S": "item-1"}, "message": {"S": "hello"}},
        )
        item = clients["dynamodb"].get_item(
            TableName=names["table"], Key={"id": {"S": "item-1"}}
        )["Item"]
        assert item["message"]["S"] == "hello"
        results["dynamodb"] = "create, put, and get succeeded"

        queue_url = clients["sqs"].create_queue(QueueName=names["queue"])["QueueUrl"]
        created["queue_url"] = queue_url
        clients["sqs"].send_message(QueueUrl=queue_url, MessageBody="hello")
        messages = clients["sqs"].receive_message(
            QueueUrl=queue_url, MaxNumberOfMessages=1
        ).get("Messages", [])
        assert messages and messages[0]["Body"] == "hello"
        results["sqs"] = "create, send, and receive succeeded"

        topic_arn = clients["sns"].create_topic(Name=names["topic"])["TopicArn"]
        created["topic_arn"] = topic_arn
        message_id = clients["sns"].publish(
            TopicArn=topic_arn, Message="hello"
        )["MessageId"]
        assert message_id
        results["sns"] = "create and publish succeeded"

        clients["secretsmanager"].create_secret(
            Name=names["secret"], SecretString='{"value":"hello"}'
        )
        created["secret"] = True
        secret = clients["secretsmanager"].get_secret_value(
            SecretId=names["secret"]
        )["SecretString"]
        assert json.loads(secret)["value"] == "hello"
        results["secretsmanager"] = "create and get succeeded"

        clients["kinesis"].create_stream(StreamName=names["stream"], ShardCount=1)
        created["stream"] = True
        clients["kinesis"].put_record(
            StreamName=names["stream"], Data=b"hello", PartitionKey="partition-1"
        )
        results["kinesis"] = "create and put succeeded"

        print("AWS mock integration test PASSED")
        for name, result in results.items():
            print(f"[PASS] {name:<18} {result}")
    finally:
        if created.get("stream"):
            clients["kinesis"].delete_stream(StreamName=names["stream"])
        if created.get("secret"):
            clients["secretsmanager"].delete_secret(
                SecretId=names["secret"], ForceDeleteWithoutRecovery=True
            )
        if topic_arn := created.get("topic_arn"):
            clients["sns"].delete_topic(TopicArn=str(topic_arn))
        if queue_url := created.get("queue_url"):
            clients["sqs"].delete_queue(QueueUrl=str(queue_url))
        if created.get("table"):
            clients["dynamodb"].delete_table(TableName=names["table"])
        if created.get("bucket"):
            clients["s3"].delete_object(Bucket=names["bucket"], Key="hello.txt")
            clients["s3"].delete_bucket(Bucket=names["bucket"])


if __name__ == "__main__":
    main()
