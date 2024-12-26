from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct

from lambdas import Lambdas
from topic import Topic
from databases import Tables


AGENT_ID = "YOURAGENTID"
AGENT_ALIAS_ID = "TSTALIASID"

class EndUserMessagingBedrockStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stk = Stack.of(self)
        region = stk.region
        account_id = stk.account



        Fn = Lambdas(self, "L")
        Tp = Topic(self, "WhatsappEventsDestination", lambda_function=Fn.whatsapp_event_handler)
        Tb = Tables(self, "T")

        Tb.messages.grant_read_write_data(Fn.whatsapp_event_handler)
        Fn.whatsapp_event_handler.add_environment("TABLE_NAME", Tb.messages.table_name)
        Fn.whatsapp_event_handler.add_environment("AGENT_ID", AGENT_ID)
        Fn.whatsapp_event_handler.add_environment("AGENT_ALIAS_ID", AGENT_ALIAS_ID)


        Tp.topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("social-messaging.amazonaws.com")],
                actions=["sns:Publish"],
                resources=[Tp.topic.topic_arn]
            )
        )

        Fn.whatsapp_event_handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=["social-messaging:SendWhatsAppMessage"],
                resources=[f"arn:aws:social-messaging:{region}:{account_id}:phone-number-id/*"]
            )
        )
        Fn.whatsapp_event_handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:Invoke*"],
                resources=[
                    f"arn:aws:bedrock:{region}:{account_id}:agent*",
                    "arn:aws:bedrock:us-east-1::foundation-model/*",
                    "arn:aws:bedrock:us-east-2::foundation-model/*",
                    "arn:aws:bedrock:us-west-2::foundation-model/*",
                    f"arn:aws:bedrock:{region}:{account_id}:inference-profile/*",
                    ]
            )
        )

        CfnOutput(self, "TopicArn", value=Tp.topic.topic_arn)

