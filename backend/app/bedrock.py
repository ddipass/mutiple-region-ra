import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import TypedDict, no_type_check

from app.config import BEDROCK_PRICING, DEFAULT_EMBEDDING_CONFIG
from app.config import DEFAULT_GENERATION_CONFIG as DEFAULT_CLAUDE_GENERATION_CONFIG
from app.config import DEFAULT_MISTRAL_GENERATION_CONFIG
from app.repositories.models.conversation import MessageModel
from app.repositories.models.custom_bot import GenerationParamsModel
from app.routes.schemas.conversation import type_model_name, real_model_name
from app.utils import convert_dict_keys_to_camel_case, get_bedrock_client, rename_model_id, get_model_id

logger = logging.getLogger(__name__)

DEFAULT_BEDROCK_REGION = '''{
    "claude-v3-sonnet": "us-east-2",
    "claude-v3.5-sonnet": "us-east-1",
    "claude-v3-opus": "us-west-2",
    "default": "us-west-2"
}'''
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", DEFAULT_BEDROCK_REGION)
BEDROCK_REGION_JSON = json.loads(BEDROCK_REGION)

ENABLE_MISTRAL = os.environ.get("ENABLE_MISTRAL", "") == "true"
DEFAULT_GENERATION_CONFIG = (
    DEFAULT_MISTRAL_GENERATION_CONFIG
    if ENABLE_MISTRAL
    else DEFAULT_CLAUDE_GENERATION_CONFIG
)

client = get_bedrock_client()

class ConverseApiRequest(TypedDict):
    inference_config: dict
    additional_model_request_fields: dict
    model_id: str
    messages: list[dict]
    stream: bool
    system: list[dict]

class ConverseApiResponseMessageContent(TypedDict):
    text: str

class ConverseApiResponseMessage(TypedDict):
    content: list[ConverseApiResponseMessageContent]
    role: str

class ConverseApiResponseOutput(TypedDict):
    message: ConverseApiResponseMessage

class ConverseApiResponseUsage(TypedDict):
    inputTokens: int
    outputTokens: int
    totalTokens: int

class ConverseApiResponse(TypedDict):
    ResponseMetadata: dict
    output: ConverseApiResponseOutput
    stopReason: str
    usage: ConverseApiResponseUsage

def compose_args(
    messages: list[MessageModel],
    model: type_model_name,
    instruction: str | None = None,
    stream: bool = False,
    generation_params: GenerationParamsModel | None = None,
) -> dict:
    logger.warn(
        "compose_args is deprecated. Use compose_args_for_converse_api instead."
    )
    return dict(
        compose_args_for_converse_api(
            messages, model, instruction, stream, generation_params
        )
    )

def _get_converse_supported_format(ext: str) -> str:
    supported_formats = {
        "pdf": "pdf",
        "csv": "csv",
        "doc": "doc",
        "docx": "docx",
        "xls": "xls",
        "xlsx": "xlsx",
        "html": "html",
        "txt": "txt",
        "md": "md",
    }
    return supported_formats.get(ext, "txt")

def _convert_to_valid_file_name(file_name: str) -> str:
    # Note: The document file name can only contain alphanumeric characters,
    # whitespace characters, hyphens, parentheses, and square brackets.
    # The name can't contain more than one consecutive whitespace character.
    file_name = re.sub(r"[^a-zA-Z0-9\s\-\(\)\[\]]", "", file_name)
    file_name = re.sub(r"\s+", " ", file_name)
    file_name = file_name.strip()

    return file_name

@no_type_check
def compose_args_for_converse_api(
    messages: list[MessageModel],
    model: type_model_name,
    instruction: str | None = None,
    stream: bool = False,
    generation_params: GenerationParamsModel | None = None,
) -> ConverseApiRequest:
    """Compose arguments for Converse API.
    Ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/converse_stream.html
    """
    arg_messages = []
    for message in messages:
        if message.role not in ["system", "instruction"]:
            content_blocks = []
            for c in message.content:
                if c.content_type == "text":
                    content_blocks.append({"text": c.body})
                elif c.content_type == "image":
                    # e.g. "image/png" -> "png"
                    format = c.media_type.split("/")[1]
                    content_blocks.append(
                        {
                            "image": {
                                "format": format,
                                # decode base64 encoded image
                                "source": {"bytes": base64.b64decode(c.body)},
                            }
                        }
                    )
                elif c.content_type == "attachment":
                    content_blocks.append(
                        {
                            "document": {
                                "format": _get_converse_supported_format(
                                    Path(c.file_name).suffix[
                                        1:
                                    ],  # e.g. "document.txt" -> "txt"
                                ),
                                "name": Path(
                                    _convert_to_valid_file_name(c.file_name)
                                ).stem,  # e.g. "document.txt" -> "document"
                                "source": {"bytes": base64.b64decode(c.body)},
                            }
                        }
                    )
                else:
                    raise NotImplementedError()
            arg_messages.append({"role": message.role, "content": content_blocks})

    inference_config = {
        **DEFAULT_GENERATION_CONFIG,
        **(
            {
                "maxTokens": generation_params.max_tokens,
                "temperature": generation_params.temperature,
                "topP": generation_params.top_p,
                "stopSequences": generation_params.stop_sequences,
            }
            if generation_params
            else {}
        ),
    }

    # `top_k` is configured in `additional_model_request_fields` instead of `inference_config`
    additional_model_request_fields = {"top_k": inference_config["top_k"]}
    del inference_config["top_k"]

    args: ConverseApiRequest = {
        "inference_config": convert_dict_keys_to_camel_case(inference_config),
        "additional_model_request_fields": additional_model_request_fields,
        "model_id": get_model_id(model),
        "messages": arg_messages,
        "stream": stream,
        "system": [],
    }
    if instruction:
        args["system"].append({"text": instruction})
    return args

def call_converse_api(args: ConverseApiRequest) -> ConverseApiResponse:
    messages = args["messages"]
    inference_config = args["inference_config"]
    additional_model_request_fields = args["additional_model_request_fields"]
    system = args["system"]

    model_id = args["model_id"]
    model_name = rename_model_id(model_id)
    BEDROCK_REGION_JSON = json.loads(BEDROCK_REGION)
    client = get_bedrock_client(BEDROCK_REGION_JSON[model_name])

    response= client.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig=inference_config,
        system=system,
        additionalModelRequestFields=additional_model_request_fields,
    )

    return response

def calculate_price(
    model: type_model_name,
    input_tokens: int,
    output_tokens: int,
    region: str = BEDROCK_REGION,
) -> float:
    model_name = rename_model_id(model)
    BEDROCK_REGION_JSON = json.loads(BEDROCK_REGION)
    region = BEDROCK_REGION_JSON[model_name]

    input_price = (
        BEDROCK_PRICING.get(region, {})
        .get(model, {})
        .get("input", BEDROCK_PRICING["default"][model]["input"])
    )
    output_price = (
        BEDROCK_PRICING.get(region, {})
        .get(model, {})
        .get("output", BEDROCK_PRICING["default"][model]["output"])
    )

    return input_price * input_tokens / 1000.0 + output_price * output_tokens / 1000.0

def calculate_query_embedding(question: str) -> list[float]:
    model_id = DEFAULT_EMBEDDING_CONFIG["model_id"]

    # Currently only supports "cohere.embed-multilingual-v3"
    assert model_id == "cohere.embed-multilingual-v3"

    payload = json.dumps({"texts": [question], "input_type": "search_query"})
    accept = "application/json"
    content_type = "application/json"

    response = client.invoke_model(
        accept=accept, contentType=content_type, body=payload, modelId=model_id
    )
    output = json.loads(response.get("body").read())
    embedding = output.get("embeddings")[0]

    return embedding

def calculate_document_embeddings(documents: list[str]) -> list[list[float]]:
    def _calculate_document_embeddings(documents: list[str]) -> list[list[float]]:
        payload = json.dumps({"texts": documents, "input_type": "search_document"})
        accept = "application/json"
        content_type = "application/json"

        response = client.invoke_model(
            accept=accept, contentType=content_type, body=payload, modelId=model_id
        )
        output = json.loads(response.get("body").read())
        embeddings = output.get("embeddings")

        return embeddings

    BATCH_SIZE = 10
    model_id = DEFAULT_EMBEDDING_CONFIG["model_id"]

    # Currently only supports "cohere.embed-multilingual-v3"
    assert model_id == "cohere.embed-multilingual-v3"

    embeddings = []
    for i in range(0, len(documents), BATCH_SIZE):
        # Split documents into batches to avoid exceeding the payload size limit
        batch = documents[i : i + BATCH_SIZE]
        embeddings += _calculate_document_embeddings(batch)

    return embeddings