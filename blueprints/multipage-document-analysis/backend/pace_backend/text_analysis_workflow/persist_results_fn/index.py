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

import os
import logging
import uuid
import json
import decimal
import functools

import boto3

from status_info_layer.StatusEnum import StatusEnum

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

TABLE_NAME = os.getenv("DOCUMENTS_DYNAMO_DB_TABLE_NAME")

table = boto3.resource("dynamodb").Table(TABLE_NAME)

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        response = handler(event, context)
        return {
            "statusCode": response["statusCode"],
            "isBase64Encoded": False,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": True,
            },
            "body": response.get("body", ""),
            "error": response.get("error", None)
        }

    return wrapper

@_format_response
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, _context: LambdaContext):
    """
    Lambda function to put an item into DynamoDB
    @param event:
    @param context:
    @return:
    """

    logger.info("Received event")
    logger.info(event)

    job_id = event['Payload']['body']['job_id']
    report = event['Payload']['body']['report']

    # Update status in DynamoDB table
    try:
        table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #json_report = :json_report",
            ExpressionAttributeNames={"#json_report": "json_report"},
            ExpressionAttributeValues={":json_report": json.dumps(report)},
        )

        table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": StatusEnum.PDF_GENERATION.name},
        )
    except Exception as e:
        logger.error(f"Error updating DynamoDB: {e}")
        return {
            "statusCode": 500,
            "error": "Failed to update DynamoDB"
        }

    return {
        "statusCode": 200,
        "body": {
            "job_id": job_id
        }
    }
