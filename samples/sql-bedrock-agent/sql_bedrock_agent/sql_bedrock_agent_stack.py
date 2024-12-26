from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct
from lambdas import Lambdas, DEFAULT_MODEL_ID
from bedrock_agent import Agent

class SqlBedrockAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        Fn = Lambdas(self, "L")

        file_path_ag_data = "./bedrock_agent/ag_data.json"

        agent_data = {
            "agent_name": "ask-the-sql-database",
            "description": "Agentic BI using Natural Language questions",
            "foundation_model": DEFAULT_MODEL_ID,
            "agent_instruction": "Usted es un amable analista de negocios que responde las preguntas de los usuarios sobre la información estructurada en las tablas de bases de datos"
        }

        Agent(
            self,
            "SQLAgent",
            file_path_ag_data=file_path_ag_data,
            agent_data=agent_data,
            function_arn=Fn.sql_agent.function_arn,
        )
