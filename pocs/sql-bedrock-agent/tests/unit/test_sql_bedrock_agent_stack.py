import aws_cdk as core
import aws_cdk.assertions as assertions

from sql_bedrock_agent.sql_bedrock_agent_stack import SqlBedrockAgentStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sql_bedrock_agent/sql_bedrock_agent_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SqlBedrockAgentStack(app, "sql-bedrock-agent")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
