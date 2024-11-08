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

import logging
import os
import json
import boto3
import functools
from TextractorHandler import TextractorHandler
from textractor.parsers import response_parser

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger

from botocore.exceptions import ClientError

from status_info_layer.StatusEnum import StatusEnum

logger = Logger()

PAGE_CHUNK_SIZE = int(os.environ.get("PAGE_CHUNK_SIZE", 5))
dynamo_db_table_name = os.environ.get("DOCUMENTS_DYNAMO_DB_TABLE_NAME")

textract_client = boto3.client('textract')
table = boto3.resource("dynamodb").Table(dynamo_db_table_name)

# TODO: use aws_lambda_powertools.event_handler import APIGatewayRestResolver and CORSConfig to avoid having to
#  know about API GW response formats
def _format_response(handler):
    @functools.wraps(handler)
    def wrapper(event, context):
        response = handler(event, context)
        return {
            "statusCode": response["statusCode"],
            "job_id": response["job_id"],
            "pages_chunk_size": response["pages_chunk_size"],
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

def textract_get_detection_job(job_id, next_token=None):
    """
    Gets data for a previously started text detection job.

    :param job_id: The ID of the job to retrieve.
    :return: The job data, including a list of blocks that describe elements
             detected in the image.
    """
    try:

        if next_token:
            response = textract_client.get_document_text_detection(JobId=job_id, NextToken=next_token)
        else:
            response = textract_client.get_document_text_detection(JobId=job_id)
        job_status = response["JobStatus"]
        logger.info("Job %s status is %s.", job_id, job_status)
    except ClientError:
        logger.exception("Couldn't get data for job %s.", job_id)
        raise
    else:
        return response

def parse_textract_results(job_id):
    """
    Parse Textract results to a Textractor object
    @param job_id: Textract job id
    @return: Textractor object
    """

    logger.debug(f"Parsing Textract results for job {job_id}")

    detection_job = textract_get_detection_job(job_id)
    textract_results = detection_job.copy()

    while "NextToken" in detection_job:
        logger.debug(f"Getting next token for job {job_id}")
        detection_job = textract_get_detection_job(job_id, detection_job["NextToken"])
        print(detection_job["DocumentMetadata"])
        print(detection_job["JobStatus"])
        print(detection_job.get("NextToken", ""))
        textract_results["Blocks"].extend(detection_job["Blocks"])
        print(detection_job.get("Block appended", ""))

    logger.debug(f"Textract results for job {job_id} parsed")

    logger.debug(f"Parsing Textract results for job {job_id}")
    textractor_document = response_parser.parse(textract_results)
    logger.debug(f"Textract results for job {job_id} parsed")

    return textractor_document


@_format_response
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, _context: LambdaContext):
    """
    Lambda function to chunk a multipage text document
    @param event:
    @param context:
    @return:
    """

    logger.info(f"Received event: {event}")

    queue_message = json.loads(event[-1]["body"])  # Read only the last message

    logger.info(f"\n\nQueue message: {queue_message}")

    textract_result = json.loads(queue_message["Message"])
    logger.info(f"\n\nTextract result: {textract_result}")

    print("\n\nTextract result")
    print(type(textract_result))
    print(textract_result)

    # Validate Textract Job Status
    if textract_result["Status"] == "SUCCEEDED":
        job_id = textract_result["JobId"]

        # Parse textract results to Textractor
        try:
            textractor_document = parse_textract_results(job_id)
        except Exception as e:
            logger.error(f"Error parsing Textract results: {e}")
            return {
                "statusCode": 500,
                "error": "Failed to parse Textract response"
            }

        # Chunk document
        try:
            logger.info("Parsing document with textractor")
            textractor_handler = TextractorHandler(logger)
            logger.info("Chunking document")
            response = textractor_handler.get_document_text(textractor_document, chunk_size=PAGE_CHUNK_SIZE, page_overlap=1)
            logger.info("Document chunked")
        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            return {
                "statusCode": 500,
                "error": "Failed to chunk document"
            }

        # Update status in DynamoDB table
        try:
            table.update_item(
                Key={"id": job_id},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": StatusEnum.PAGE_CHUNKING.name},
            )
        except Exception as e:
            logger.error(f"Error updating DynamoDB: {e}")
            return {
                "statusCode": 500,
                "error": "Failed to update DynamoDB"
            }

        return {
            "statusCode": 200,
            "job_id": job_id,
            "body": response,
            "pages_chunk_size": PAGE_CHUNK_SIZE
        }
    else:
        return {
            "statusCode": 500,
            "error": "Textract job failed"
        }
