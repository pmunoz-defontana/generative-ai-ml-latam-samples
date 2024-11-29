import json, decimal
import boto3
import os

from whatsapp import WhatsappService
from bedrock_agent import BedrockAgentService

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME")
table = dynamodb.Table(TABLE_NAME)


AGENT_ID = os.environ.get("AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("AGENT_ALIAS_ID")


def process_record(record):
    sns = record.get("Sns", {})
    sns_message_str = sns.get("Message", "{}")
    sns_message = json.loads(sns_message_str, parse_float=decimal.Decimal)
    whatsapp = WhatsappService(sns_message)
    sql_agent = BedrockAgentService(AGENT_ID, AGENT_ALIAS_ID)

    for message in whatsapp.messages:
        message.save(table)
        message.mark_as_read()
        message.reaction("👍")
        text = message.get_text()

        if text.startswith("/echo "):            
            message.text_reply(text.replace("/echo ", ""))
        
        if text.startswith("/sql "):
            user_query = text.replace("/sql ", "")
            print(f"query: {user_query}")
            response = sql_agent.invoke_agent(message.phone_number, user_query)
            print(f"agent response: {response}")
            message.text_reply(response)



def lambda_handler(event, context):
    #print(event)
    records = event.get("Records", [])
    print (f"processing {len(records)} records")
    for rec in records:
        process_record(rec)
