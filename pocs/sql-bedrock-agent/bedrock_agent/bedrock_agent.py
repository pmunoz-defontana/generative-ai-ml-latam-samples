import json
from constructs import Construct
from bedrock_agent.create_agent import CreateAgent
from bedrock_agent.create_role import CreateAgentRole
from bedrock_agent.load_data import load_ag_data


class Agent(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        file_path_ag_data,
        agent_data,
        function_arn,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Action Group Properties

        ag_property = load_ag_data(file_path_ag_data, function_arn)

        # Agent Execution Role
        agent_role = CreateAgentRole(self, "role")

        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_bedrock/CfnAgent.html
        # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-bedrock-agent-agentactiongroup.html#cfn-bedrock-agent-agentactiongroup-actiongroupstate

        self.agent = CreateAgent(
            self, "Agent", agent_data, agent_role, ag_property
        )
