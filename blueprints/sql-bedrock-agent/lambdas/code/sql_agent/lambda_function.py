import json
import os
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_aws import  ChatBedrock

model_id = os.environ.get("MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0")

db = SQLDatabase.from_uri("sqlite:///Chinook.db")
print("dialect:",db.dialect)
print ("tables:")
print(db.get_usable_table_names())
llm =ChatBedrock(model = model_id,  beta_use_converse_api=True, model_kwargs={"temperature": 0})
agent_executor = create_sql_agent(llm, db=db, verbose=True)

def lambda_handler(event, context):
    print("Received event: ")
    print(event)

    actionGroup = event["actionGroup"]
    function = event["function"]
    parameters = event.get("parameters", [])
    inputText = event.get("inputText", "")

    print(f"inputText: {inputText}")
    response = "No query provided"

    if function == "queryData":
        query = None
        for param in parameters:
            if param["name"] == "userQuestion":
                query = param["value"]

        if query: response = query_db(query)

    response_body = {"TEXT": {"body": response}}
    print(f"Response body: {response_body}")

    # Create a dictionary containing the response details
    action_response = {
        "actionGroup": actionGroup,
        "function": function,
        "functionResponse": {"responseBody": response_body},
    }
    function_response = {'response': action_response, 'messageVersion': event['messageVersion']}

    print(f"Response: {function_response}")    

    return function_response


def query_db(consulta):
    response = agent_executor.invoke(consulta)
    return response.get("output")

