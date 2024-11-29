
import boto3
from botocore.exceptions import ClientError
import logging
logger = logging.getLogger(__name__)


class BedrockAgentService:
    def __init__(self, agent_id, alias_id= "TSTALIASID", client=None) -> None:
        self.agents_runtime_client = client if client else boto3.client('bedrock-agent-runtime')
        self.agent_id = agent_id
        self.alias_id = alias_id
        
    # from https://docs.aws.amazon.com/code-library/latest/ug/python_3_bedrock-agent-runtime_code_examples.html
    def invoke_agent(self, session_id, prompt):
        try:
            response = self.agents_runtime_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.alias_id,
                sessionId=session_id,
                inputText=prompt,
            )

            completion = ""

            for event in response.get("completion"):
                chunk = event["chunk"]
                completion = completion + chunk["bytes"].decode()

        except ClientError as e:
            logger.error(f"Couldn't invoke agent. {e}")
            raise

        return completion