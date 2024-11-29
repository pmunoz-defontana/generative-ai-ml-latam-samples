import aws_cdk as core
import aws_cdk.assertions as assertions

from end_user_messaging_bedrock.end_user_messaging_bedrock_stack import EndUserMessagingBedrockStack

# example tests. To run these tests, uncomment this file along with the example
# resource in end_user_messaging_bedrock/end_user_messaging_bedrock_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EndUserMessagingBedrockStack(app, "end-user-messaging-bedrock")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
