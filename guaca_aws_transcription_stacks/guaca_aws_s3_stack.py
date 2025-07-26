from typing import List
from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_iam as iam,
)
from constructs import Construct
import yaml
from yaml.loader import SafeLoader

class GuacaAwsS3Stack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str,
        account_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        with open(f"configuration.yaml") as f:
            data = yaml.load(f, Loader=SafeLoader)

            s3_config = data[environment.upper()]["S3"]
            staged_bucket_name = s3_config["STAGED_BUCKET"]
            shared_bucket_name = s3_config["SHARED_BUCKET"]
            raw_bucket_name = s3_config["RAW_BUCKET"]
            bucket_list = [staged_bucket_name, shared_bucket_name, raw_bucket_name]
            self.created_buckets = {}
            environment = environment.lower()
            for bucket in bucket_list:
                created_bucket = self.create_bucket(
                    name=f"{environment}-guaca-{bucket}-{account_id}",
                    construct_id=f"{construct_id}-{bucket}",
                )

                self.created_buckets[bucket] = created_bucket

    def create_bucket(self, name: str, construct_id: str):
        bucket = s3.Bucket(
            self,
            construct_id,
            bucket_name=name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )
        bucket_resource: s3.CfnBucket = bucket.node.find_child("Resource")
        # Enable Event Bridge
        bucket_resource.add_property_override(
            "NotificationConfiguration.EventBridgeConfiguration.EventBridgeEnabled",
            True,
        )

        return bucket