#!/usr/bin/env python3
import yaml
from yaml.loader import SafeLoader

import aws_cdk as cdk

from guaca_aws_transcription_stacks.guaca_aws_transcription_stack import GuacaAwsTranscriptionStack
from guaca_aws_transcription_stacks.guaca_aws_s3_stack import GuacaAwsS3Stack


app = cdk.App()
environment = app.node.try_get_context("environment")

with open(f"configuration.yaml") as f:
    config_data = yaml.load(f, Loader=SafeLoader)

account_id = config_data["AWS_ACCOUNT"]["MAIN_ACCOUNT"]
region = config_data["AWS_ACCOUNT"]["REGION"]
environment = environment.lower()

print(f"environment {environment}")

guaca_aws_s3_stack = GuacaAwsS3Stack(
    app,
    f"{environment.upper()}-GuacaAwsS3Stack",
    environment=environment,
    account_id=account_id,
    env=cdk.Environment(account=account_id, region=region),
)
GuacaAwsTranscriptionStack(
    app, 
    f"{environment.upper()}-GuacaAwsTranscriptionStack",
    environment=environment,
    raw_bucket=guaca_aws_s3_stack.created_buckets["raw"],
    env=cdk.Environment(account=account_id, region=region),
)

app.synth()
