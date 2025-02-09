from aws_cdk import RemovalPolicy, aws_bedrock as bedrock
from constructs import Construct
DEFAULT_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"


class CreateAgent(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agent_role,
        agent_name = "simple-agent-cdk",
        agent_description = "Simple Agent",
        foundation_model = DEFAULT_MODEL_ID,
        agent_instruction = "You are a helpful AI Agent",
        action_groups=None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)


        agent_kwags = dict(
            agent_name=agent_name,
            description=agent_description,
            auto_prepare=True,
            idle_session_ttl_in_seconds=600,
            skip_resource_in_use_check_on_delete=True,
            test_alias_tags={"test_alias_tags_key": "testAliasTags"},
            agent_resource_role_arn=agent_role.role_arn,
            instruction=agent_instruction,
            foundation_model=foundation_model,
        )

        if action_groups:
            agent_kwags["action_groups"] = action_groups

        self.cfn_agent = bedrock.CfnAgent(self, "Agent", **agent_kwags)

        self.cfn_agent.apply_removal_policy(RemovalPolicy.DESTROY)

    def create_alias(self, alias_name):
        self.cfn_alias = bedrock.CfnAgentAlias(
            self,
            "AgentAlias",
            agent_id=self.cfn_agent.attr_agent_id,
            agent_alias_name=alias_name,
        )
        return self.cfn_alias
    