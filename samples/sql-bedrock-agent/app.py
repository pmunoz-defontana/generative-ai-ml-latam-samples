#!/usr/bin/env python3
import os

import aws_cdk as cdk

from sql_bedrock_agent.sql_bedrock_agent_stack import SqlBedrockAgentStack


app = cdk.App()
SqlBedrockAgentStack(app, "SQL-BEDROCK-AGENT")

app.synth()
