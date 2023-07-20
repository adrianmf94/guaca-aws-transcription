import aws_cdk as core
import aws_cdk.assertions as assertions

from guaca_aws_transcription.guaca_aws_transcription_stack import GuacaAwsTranscriptionStack

# example tests. To run these tests, uncomment this file along with the example
# resource in guaca_aws_transcription/guaca_aws_transcription_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GuacaAwsTranscriptionStack(app, "guaca-aws-transcription")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
