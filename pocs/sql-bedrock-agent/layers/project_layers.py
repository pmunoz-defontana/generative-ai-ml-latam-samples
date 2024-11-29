from constructs import Construct

from aws_cdk import aws_lambda as _lambda


class LangchainAWS(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.layer = _lambda.LayerVersion(
            self,
            "LangchainAWS",
            code=_lambda.Code.from_asset("./layers/langchain-aws.zip"),
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_10,
                _lambda.Runtime.PYTHON_3_11,
                _lambda.Runtime.PYTHON_3_9,
                _lambda.Runtime.PYTHON_3_12
            ],
        )


class LangchainCommunity(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.layer = _lambda.LayerVersion(
            self,
            "LangchainCommunity",
            code=_lambda.Code.from_asset("./layers/langchaincommunity.zip"),
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_10,
                _lambda.Runtime.PYTHON_3_11,
                _lambda.Runtime.PYTHON_3_9,
                _lambda.Runtime.PYTHON_3_12
            ],
        )
