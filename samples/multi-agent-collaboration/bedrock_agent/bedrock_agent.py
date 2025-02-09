from constructs import Construct
from bedrock_agent.create_agent import CreateAgent
from bedrock_agent.create_role import CreateAgentRole
from aws_cdk import custom_resources as cr, aws_iam as iam
from bedrock_agent.multiagent import MultiAgentCollaboration


class Agent(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        action_groups,
        agent_name,
        agent_description,
        foundation_model,
        agent_instruction,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Agent Execution Role
        self.agent_role = CreateAgentRole(self, "role", base_name=agent_name)
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_instruction = agent_instruction
        self.foundation_model = foundation_model
        self.collaboration_is_enabled = False
        self.agents_collaborators = []
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_bedrock/CfnAgent.html
        # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-bedrock-agent-agentactiongroup.html#cfn-bedrock-agent-agentactiongroup-actiongroupstate

        self.agent = CreateAgent(
            self,
            "Agent",
            self.agent_role.service_role,
            action_groups=action_groups,
            agent_name=self.agent_name,
            agent_description=self.agent_description,
            foundation_model=self.foundation_model,
            agent_instruction=self.agent_instruction,
        )
        self.agent.node.add_dependency(self.agent_role.service_role)
        self.physical_resource_id = cr.PhysicalResourceId.of(
            f"{agent_name}::MULTI::ENABLED"
        )
        self.prompt_overrride = {
            "promptConfigurations": [
                {
                    "promptType": "ROUTING_CLASSIFIER",
                    "foundationModel": self.foundation_model,
                    "parserMode": "DEFAULT",
                    "promptCreationMode": "DEFAULT",
                    "promptState": "ENABLED",
                }
            ]
        }

    def prepare_agent(self):
        self.preparation_cr = cr.AwsCustomResource(
            self,
            "Prepare",
            on_update=cr.AwsSdkCall(  # will also be called for a CREATE event
                service="@aws-sdk/client-bedrock-agent",
                action="prepareAgent",
                parameters={"agentId": self.agent.cfn_agent.attr_agent_id},
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"{self.agent_name}::PREPARED"
                ),
            ),
            install_latest_aws_sdk=True,
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )
        for ac in self.agents_collaborators:
            self.preparation_cr.node.add_dependency(ac)

    def enable_collaboration(self, how="SUPERVISOR"):
        self.how = how
        self.collaboration_enabled_cr = cr.AwsCustomResource(
            self,
            "EnableCollab",
            on_update=cr.AwsSdkCall(  # will also be called for a CREATE event
                service="@aws-sdk/client-bedrock-agent",
                action="updateAgent",
                parameters={
                    "agentId": self.agent.cfn_agent.attr_agent_id,
                    "agentCollaboration": self.how,
                    "agentName": self.agent_name,
                    "description": self.agent_description,
                    "instruction": self.agent_instruction,
                    "foundationModel": self.foundation_model,
                    "agentResourceRoleArn": self.agent_role.service_role.role_arn,
                    "promptOverrideConfiguration": self.prompt_overrride,
                },
                physical_resource_id=self.physical_resource_id,
            ),
            install_latest_aws_sdk=True,
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=["bedrock:UpdateAgent*"], resources=["*"]
                    ),
                    iam.PolicyStatement(
                        actions=["iam:PassRole"],
                        resources=[self.agent.cfn_agent.agent_resource_role_arn],
                    ),
                ]
            ),
        )
        self.collaboration_is_enabled = True
        self.collaboration_enabled_cr.node.add_dependency(self.agent.cfn_agent)

    def create_alias(self, alias_name):
        self.alias = self.agent.create_alias(alias_name)

    def add_collaborator(
        self, collaborator_alias, collaborator_name, collaboration_instruction
    ):

        if not self.collaboration_is_enabled:
            self.enable_collaboration()

        collaborator_cr = MultiAgentCollaboration(
            self,
            collaborator_name,
            agent_collaborator_alias=collaborator_alias,
            agent_supervisor=self.agent.cfn_agent,
            collaborator_name=collaborator_name,
            collaboration_instruction=collaboration_instruction,
        )
        collaborator_cr.node.add_dependency(self.collaboration_enabled_cr)
        self.agents_collaborators.append(collaborator_cr)
