from aws_cdk import (
    Duration,
    aws_iam as iam,
    aws_lambda,
)

from constructs import Construct
from layers import LangchainAWS, LangchainCommunity

LAMBDA_TIMEOUT = 900
DEFAULT_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"

# use an inference profile

DEFAULT_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

BASE_LAMBDA_CONFIG = dict(
    timeout=Duration.seconds(LAMBDA_TIMEOUT),
    runtime=aws_lambda.Runtime.PYTHON_3_12,
    architecture=aws_lambda.Architecture.ARM_64,
    tracing=aws_lambda.Tracing.ACTIVE,
    environment = {"MODEL_ID": DEFAULT_MODEL_ID},
    memory_size=512,
)


class Lambdas(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        LC_AWS = LangchainAWS(self, "LangchainAWS")
        LC_COMM = LangchainCommunity(self, "LangchainCommunity")

        # ======================================================================
        # SQL Agent Serverless using SQL Lite
        # ======================================================================
        
        self.sql_agent = aws_lambda.Function(
            self,
            "SQLAgent",
            handler="lambda_function.lambda_handler", 
            layers=[LC_AWS.layer, LC_COMM.layer],
            code=aws_lambda.Code.from_asset("./lambdas/code/sql_agent/"),
            **BASE_LAMBDA_CONFIG,
        )

        self.sql_agent.add_to_role_policy(
            iam.PolicyStatement(actions=["bedrock:*"], resources=["*"])
        )

        self.sql_agent.add_permission(
            f"invoke from Bedrock Service",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            action="lambda:invokeFunction",
        )
