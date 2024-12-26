#!/usr/bin/env python3
import os

import aws_cdk as cdk

from end_user_messaging_bedrock.end_user_messaging_bedrock_stack import EndUserMessagingBedrockStack


app = cdk.App()
EndUserMessagingBedrockStack(app, "EUM-Social-Bedrock")

app.synth()
