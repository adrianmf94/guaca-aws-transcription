import os
from aws_cdk import (
    BundlingOptions,
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct

class GuacaAwsTranscriptionStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str,
        raw_bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the IAM role for the data ingestion lambda function
        deepgram_transcription_lambda_role = iam.Role(
            scope=self,
            id=f"{construct_id}-deepgram-transcription-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        deepgram_transcription_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:*",
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    raw_bucket.bucket_arn,
                    f"{raw_bucket.bucket_arn}/*"
                ],
            )
        )

        deepgram_transcription_lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:DescribeTable",
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:Query",
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    "arn:aws:dynamodb:*:*:table/Audio_transcripts_demo",
                ],
            )
        )

        bundling_command = [
            "bash",
            "-c",
            "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output",
        ]

        # First Lambda function for speech to text
        deepgram_transcription_lambda = lambda_.Function(
            self,
            id=f"{construct_id}-deepgram-transcription-lambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="main.handler",
            timeout=Duration.minutes(2),
            role=deepgram_transcription_lambda_role,
            environment={
                "DEEPGRAM_API_KEY": os.environ.get("DEEPGRAM_API_KEY"),
                "RAW_S3_BUCKET": raw_bucket.bucket_name,
            },
            code=lambda_.Code.from_asset(
                "./deepgram_transcription_lambda",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_9.bundling_image,
                    command=bundling_command,
                ),
            ),

        )

        bundling_command = [
            "bash",
            "-c",
            "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output",
        ]

        # Second Lambda function that uses OpenAI
        openai_entities_lambda = lambda_.Function(
            self,
            id=f"{construct_id}-openai-entities-lambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="main.handler",
            timeout=Duration.minutes(2),
            role=deepgram_transcription_lambda_role,
            environment={
                "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "your-openai-api-key-here"),
                "DYNAMODB_TABLE": "Audio_transcripts_demo"
            },
            code=lambda_.Code.from_asset(
                "./openai_entities_lambda",
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_9.bundling_image,
                    command=bundling_command,
                ),
            ),

        )

        state_machine_role = iam.Role(
            self,
            "Role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("states.amazonaws.com"),
            ),
        )

        sfn_deepgram_transcription_lambda_invoke = tasks.LambdaInvoke(
            self,
            id="deepgram-transcription-lambda-invoke",
            lambda_function=deepgram_transcription_lambda,
            retry_on_service_exceptions=True,
            result_path="$.transcript_result",
        )

        sfn_openai_entities_lambda_invoke = tasks.LambdaInvoke(
            self,
            id="openai-entities-lambda-invoke",
            lambda_function=openai_entities_lambda,
            retry_on_service_exceptions=True,
            payload=sfn.TaskInput.from_object({
                "transcript.$": "$.transcript_result.Payload.body.results.channels[0].alternatives[0].transcript",
                "audio_key.$": "$.Records[0].s3.object.key",
            })
        )

        definition = (
            sfn.Chain.start(
                sfn_deepgram_transcription_lambda_invoke
                .next(sfn_openai_entities_lambda_invoke),
            )
        )

        # Create the state machine with step functions
        self.state_machine = sfn.StateMachine(
            self,
            f"{environment}-guaca-transcription-state-machine",
            role=state_machine_role,
            definition=definition,
        )

        state_machine_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "states:StartExecution",
                    "states:StopExecution",
                ],
                effect=iam.Effect.ALLOW,
                resources=["*"],
            )
        )
