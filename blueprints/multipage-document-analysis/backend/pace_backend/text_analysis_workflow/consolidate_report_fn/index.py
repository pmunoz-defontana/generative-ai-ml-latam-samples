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

import boto3
import os
import langchain_core
import functools

from aws_lambda_powertools import Logger

from langchain_aws import ChatBedrock

from retrying import retry

from prompt_selector.report_consolidation_prompt_selector import get_information_consolidation_prompt_selector

from doc_info_layer.section_definition import info_to_output_mapping

from aws_lambda_powertools.utilities.typing import LambdaContext

from status_info_layer.StatusEnum import StatusEnum

from botocore.exceptions import ClientError
from botocore.config import Config

class BedrockRetryableError(Exception):
    """Class to identify a Bedrock throttling error"""

    def __init__(self, msg):
        super().__init__(self)

        self.message = msg

langchain_core.globals.set_debug(True)

AWS_REGION = os.environ.get("REGION")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID")
LANGUAGE_ID = os.environ.get("LANGUAGE_ID")
DYNAMODB_TABLE_NAME = os.environ.get("DOCUMENTS_DYNAMO_DB_TABLE_NAME")

logger = Logger()

REPORT_CONSOLIDATION_MODEL_PARAMETERS = {
    "max_tokens": 1500,
    "temperature": 0.1,
    "top_k": 20,
}

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=BEDROCK_REGION,
    config=Config(retries={'max_attempts': 20})
)

table = boto3.resource("dynamodb").Table(DYNAMODB_TABLE_NAME)

@retry(wait_exponential_multiplier=10000, wait_exponential_max=60000, stop_max_attempt_number=10,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def consolidate_section(section_name, section):

    logger.debug(f"Consolidating section: {section_name}")
    logger.info(section)

    section_information_as_text = "\n\n".join([str(extracted_information) for extracted_information in section])
    logger.info("Information as text")
    logger.info(section_information_as_text)

    INFORMATION_CONSOLIDATION_PROMPT_SELECTOR = get_information_consolidation_prompt_selector(LANGUAGE_ID)

    bedrock_llm = ChatBedrock(
        model_id=MODEL_ID,
        model_kwargs=REPORT_CONSOLIDATION_MODEL_PARAMETERS,
        client=bedrock_runtime,
    )

    claude_information_consolidation_prompt_template = INFORMATION_CONSOLIDATION_PROMPT_SELECTOR.get_prompt(MODEL_ID)

    structured_llm = bedrock_llm.with_structured_output(info_to_output_mapping[section_name])

    structured_chain = claude_information_consolidation_prompt_template | structured_llm

    # Retry mechanism to workaround Bedrock Throttling
    try:
        information_consolidation_obj = structured_chain.invoke({
            "information": section,
        })
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'ThrottlingException':
            logger.error("Bedrock throttling. To try again")
            raise BedrockRetryableError(str(exc))
        elif exc.response['Error']['Code'] == 'ModelTimeoutException':
            logger.error("Bedrock ModelTimeoutException. To try again")
            raise BedrockRetryableError(str(exc))
        else:
            raise
    except bedrock_runtime.exceptions.ThrottlingException as throttlingExc:
        logger.error("Bedrock ThrottlingException. To try again")
        raise BedrockRetryableError(str(throttlingExc))
    except bedrock_runtime.exceptions.ModelTimeoutException as timeoutExc:
        logger.error("Bedrock ModelTimeoutException. To try again")
        raise BedrockRetryableError(str(timeoutExc))
    except Exception as e:

        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        logger.error(message)
        raise

    return information_consolidation_obj


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
    Lambda function to chunk a multipage text document
    @param event:
    @param context:
    @return:
    """

    results_per_section = {}
    consolidated_report = {}

    logger.info(f"Received event: {event}")

    job_id = event[0]["job_id"]

    # Loop through the results
    for element in event:

        logger.debug(element)

        #Validate no chunks from other Job Id are present
        if job_id !=  element["job_id"]:

            # Update status in DynamoDB table
            try:
                table.update_item(
                    Key={"id": job_id},
                    UpdateExpression="SET #status = :status",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={":status": StatusEnum.ERROR.name},
                )
            except Exception as e:
                logger.error(f"Error updating DynamoDB: {e}")
                return {
                    "statusCode": 500,
                    "error": "Failed to update DynamoDB"
                }

            raise ValueError("All elements must have the same job_id")

        logger.info(f"Processing elements for chunk: {element['chunk_index']}")

        # Add each section to its corresponding key
        for section_name in element["TaskResult"]["body"]["extracted_information"].keys():

            if section_name not in results_per_section:
                results_per_section[section_name] = []

            results_per_section[section_name].append(element["TaskResult"]["body"]["extracted_information"][section_name])

    logger.info(f"Retrieved the following sections {results_per_section.keys()}")
    logger.debug(f"Results per section: {results_per_section}")

    # Obtain a consolidated result per section
    for section in results_per_section:

        consolidated_section = consolidate_section(section, results_per_section[section])
        logger.debug(f"Consolidated section: {section}")
        logger.debug(consolidated_section)

        consolidated_report[section] = consolidated_section.model_dump()

    # Update status in DynamoDB table
    try:
        table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": StatusEnum.INFORMATION_CONSOLIDATION.name},
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
            "job_id": job_id,
            "report": consolidated_report
        }
    }