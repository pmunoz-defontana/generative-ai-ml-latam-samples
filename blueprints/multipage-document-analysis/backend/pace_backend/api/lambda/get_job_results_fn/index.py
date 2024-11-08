# MIT No Attribution
#
# Copyright 2024 Amazon Web Services
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json
import os
import logging
import re
import functools
import boto3

from status_info_layer.StatusEnum import StatusEnum

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError

logger = Logger()

TABLE_NAME = os.getenv("DOCUMENTS_DYNAMO_DB_TABLE_NAME")
table = boto3.resource("dynamodb").Table(TABLE_NAME)

GET_TABLE_RESULTS_BY_ID_PATTERN = re.compile("(/[a-zA-Z0-9-]*)*/jobs/results/[A-Za-z0-9-]*")

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        lambda_response = handler(event, context)

        response = {
            "statusCode": lambda_response["statusCode"],
            "isBase64Encoded": False,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": "",
        }

        logger.info(lambda_response)

        if lambda_response["statusCode"] == 200:
            response["body"] = json.dumps({
                "job_id": lambda_response["job_id"],
                "json_report":  lambda_response["json_report"],
            })
        else:
            response["body"] = json.dumps({
                "message": f"Error retrieving results for job {lambda_response['job_id']}"
            })

        return response

    return wrapper

@_format_response
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, _context: LambdaContext):
    """
    Lambda function to retrieve items from DynamoDB
    @param event: Lambda
    @param context:
    @return:
    """
    logger.debug("Received event", event)
    method = event["httpMethod"]
    path = event["path"]
    id = event["pathParameters"]["id"]
    if method == "GET" and GET_TABLE_RESULTS_BY_ID_PATTERN.match(path):
        return _get_item_by_id(id)
    else:
        return {
            "statusCode": 500,
            "items": "Not implemented"
        }

def _get_item_by_id(id: str):
    """Given the ID of an item retrieve from DynamoDb and return it"""

    item = table.get_item(Key={"id": id})

    logger.info("Received item")
    logger.info(item)

    if "Item" not in item:
        return {
            "statusCode": 500,
            "message": "Not found",
            "job_id":  id,
        }

    if StatusEnum[item["Item"]["status"]].value < StatusEnum.REPORT_PERSISTANCE.value:
        return {
            "statusCode": 500,
            "message": "Report unavailable",
            "job_id":  id,
        }
    else:
        return {
            "statusCode": 200,
            "job_id": id,
            "json_report": json.loads(item["Item"]["json_report"])
        }

