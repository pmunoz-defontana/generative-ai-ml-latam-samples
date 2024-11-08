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
import re
import functools
import pydantic

from retrying import retry

from aws_lambda_powertools import Logger

from langchain_aws import ChatBedrock

from pydantic import BaseModel

from prompt_selector.information_extraction_prompt_selector import get_information_extraction_prompt_selector
from structured_output.InformationExtraction import InformationExtraction

from doc_info_layer.section_definition import info_to_output_mapping, report_sections
from status_info_layer.StatusEnum import StatusEnum

from aws_lambda_powertools.utilities.typing import LambdaContext

from botocore.exceptions import ClientError
from botocore.config import Config

class BedrockRetryableError(Exception):
    """Class to identify a Bedrock throttling error"""

    def __init__(self, msg):
        super().__init__(self)

        self.message = msg

langchain_core.globals.set_debug(True)

logger = Logger()


EXAMPLE_USE = os.environ.get("USE_EXAMPLES", "False")
USE_EXAMPLES = True if EXAMPLE_USE=="True" else False
AWS_REGION = os.environ.get("REGION")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID")
LANGUAGE_ID = os.environ.get("LANGUAGE_ID")
DYNAMODB_TABLE_NAME = os.environ.get("DOCUMENTS_DYNAMO_DB_TABLE_NAME")
EXTRACTION_CONFIDENCE_LEVEL = int(os.environ.get("EXTRACTION_CONFIDENCE_LEVEL"))

INFORMATION_EXTRACTION_MODEL_PARAMETERS = {
    "max_tokens": 1500,
    "temperature": 0.1,
    "top_k": 20,
}

FORMAT_RESPONSES_CLAUDE_PARAMETERS = {
    "max_tokens": 1500,
    "temperature": 0,
    "top_k": 20,
}

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=BEDROCK_REGION,
    config=Config(retries={'max_attempts': 20})
)

table = boto3.resource("dynamodb").Table(DYNAMODB_TABLE_NAME)

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


@retry(wait_exponential_multiplier=10000, wait_exponential_max=60000, stop_max_attempt_number=10,
       retry_on_exception=lambda ex: isinstance(ex, BedrockRetryableError))
def text_information_extraction(
        text: str,
        information_type: str,
        n_examples: int=0
) -> BaseModel:

    bedrock_llm = ChatBedrock(
        model_id=MODEL_ID,
        model_kwargs=INFORMATION_EXTRACTION_MODEL_PARAMETERS,
        client=bedrock_runtime,
    )

    if n_examples > 0:
        INFORMATION_EXTRACTION_PROMPT_SELECTOR = get_information_extraction_prompt_selector(LANGUAGE_ID, information_type)
    else:
        INFORMATION_EXTRACTION_PROMPT_SELECTOR = get_information_extraction_prompt_selector(LANGUAGE_ID)

    claude_information_extraction_prompt_template = INFORMATION_EXTRACTION_PROMPT_SELECTOR.get_prompt(MODEL_ID)

    structured_llm = bedrock_llm.with_structured_output(InformationExtraction)

    structured_chain = claude_information_extraction_prompt_template | structured_llm

    # Retry mechanism to workaround Bedrock Throttling
    try:
        if  n_examples > 0:
            logger.info(f"Extracting {information_type} information with {n_examples} examples")
            information_extraction_obj = structured_chain.invoke({
                "json_schema": info_to_output_mapping[information_type].model_json_schema(),
                "text": text,
                "n_examples": n_examples
            })
        else:
            logger.info(f"Extracting {information_type} information without examples")
            information_extraction_obj = structured_chain.invoke({
                "json_schema": info_to_output_mapping[information_type].model_json_schema(),
                "text": text
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

    return information_extraction_obj


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

    doc_text = event["text"]
    chunk_index = event["chunk_index"]
    job_id = event["job_id"]

    extracted_information = {}

    #Determine in runtime what is to be extracted
    #doc_sections = next(os.walk(os.path.join('prompt_selector/examples', LANGUAGE_ID, '.')))[1]

    #logger.info(f"Sections: {doc_sections}")

    for section in report_sections:

        try:
            # Invoke the model to extract the information
            logger.info(f"Extracting {section} information")

            if USE_EXAMPLES:
                # Use all the examples for the few shot prompt
                all_files = os.listdir(os.path.join('prompt_selector/examples', LANGUAGE_ID, section))
                txt_example_files = [file for file in all_files if re.match("^.*\.txt$", file)]

                section_information = text_information_extraction(doc_text, section, len(txt_example_files))
            else:
                section_information = text_information_extraction(doc_text, section)  # Do not use examples

            if section_information:
                # Only append sections for which data could be extracted

                if section_information.confidence_level > EXTRACTION_CONFIDENCE_LEVEL:
                    # Only save sections with a confidence level at least above a threshold

                    logger.info(f"Section {section} extracted")
                    logger.info(section_information)

                    """
                    formatted_information = format_extraction(
                        section_information.extracted_information,
                        section
                    )
                    extracted_information[section] = formatted_information.model_dump()
                    """

                    extracted_information[section] = section_information.extracted_information
                else:
                    logger.info(f"Section {section} has a confidence level of {section_information.confidence_level} and will not be saved")
                    logger.info(section_information)
        except pydantic.ValidationError as e:
            logger.error(f"Pydantic Validation error: {e}")
        except Exception as e:

            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            logger.error(message)
            raise


        # Update status in DynamoDB table
        try:
            table.update_item(
                Key={"id": job_id},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": StatusEnum.INFORMATION_EXTRACTION.name},
            )
        except Exception as e:
            logger.error(f"Error updating DynamoDB: {e}")
            return {
                "statusCode": 500,
                "error": "Failed to update DynamoDB"
            }

        logger.info(f"Extracted information: {extracted_information}")

    return {
        "statusCode": 200,
        "body": {
            "extracted_information": extracted_information,
            "chunk_index": chunk_index,
            "job_id": job_id
        }
    }