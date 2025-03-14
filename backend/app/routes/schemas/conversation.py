import base64
from typing import Literal

from app.routes.schemas.base import BaseSchema
from pydantic import Field, root_validator, validator

type_model_name = Literal[
    "claude-instant-v1",
    "claude-v2",
    "claude-v3-sonnet",
    "claude-v3.5-sonnet",
    "claude-v3-haiku",
    "claude-v3-opus",
    "mistral-7b-instruct",
    "mixtral-8x7b-instruct",
    "mistral-large",
]

real_model_name = Literal[
    "anthropic.claude-v2:1",
    "anthropic.claude-instant-v1",
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "anthropic.claude-3-opus-20240229-v1:0",
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "mistral.mistral-7b-instruct-v0:2",
    "mistral.mixtral-8x7b-instruct-v0:1",
    "mistral.mistral-large-2402-v1:0",
]

class Content(BaseSchema):
    content_type: Literal["text", "image", "attachment"] = Field(
        ..., description="Content type. Note that image is only available for claude 3."
    )
    media_type: str | None = Field(
        None,
        description="MIME type of the image. Must be specified if `content_type` is `image`.",
    )
    file_name: str | None = Field(
        None,
        description="File name of the attachment. Must be specified if `content_type` is `attachment`.",
    )
    body: str = Field(..., description="Content body.")

    @validator("media_type", pre=True)
    def check_media_type(cls, v, values):
        content_type = values.get("content_type")
        if content_type == "image" and v is None:
            raise ValueError("media_type is required if `content_type` is `image`")
        return v

    @validator("body", pre=True)
    def check_body(cls, v, values):
        content_type = values.get("content_type")

        if content_type == "text" and not isinstance(v, str):
            raise ValueError("body must be str if `content_type` is `text`")

        if content_type in ["image", "attachment"]:
            try:
                # Check if the body is a valid base64 string
                base64.b64decode(v, validate=True)
            except Exception:
                raise ValueError(
                    "body must be a valid base64 string if `content_type` is `image` or `attachment`"
                )

        return v


class FeedbackInput(BaseSchema):
    thumbs_up: bool
    category: str | None = Field(
        None, description="Reason category. Required if thumbs_up is False."
    )
    comment: str | None = Field(None, description="optional comment")

    @root_validator(pre=True)
    def check_category(cls, values):
        thumbs_up = values.get("thumbs_up")
        category = values.get("category")

        if not thumbs_up and category is None:
            raise ValueError("category is required if `thumbs_up` is `False`")

        return values


class FeedbackOutput(BaseSchema):
    thumbs_up: bool
    category: str
    comment: str


class Chunk(BaseSchema):
    content: str
    content_type: str
    source: str
    rank: int


class MessageInput(BaseSchema):
    role: str
    content: list[Content]
    model: type_model_name
    parent_message_id: str | None
    message_id: str | None = Field(
        None, description="Unique message id. If not provided, it will be generated."
    )


class MessageOutput(BaseSchema):
    role: str = Field(..., description="Role of the message. Either `user` or `bot`.")
    content: list[Content]
    model: type_model_name
    children: list[str]
    feedback: FeedbackOutput | None
    used_chunks: list[Chunk] | None
    parent: str | None


class ChatInput(BaseSchema):
    conversation_id: str
    message: MessageInput
    bot_id: str | None = Field(None)
    continue_generate: bool = Field(False)


class ChatOutput(BaseSchema):
    conversation_id: str
    message: MessageOutput
    bot_id: str | None
    create_time: float


class RelatedDocumentsOutput(BaseSchema):
    chunk_body: str
    content_type: Literal["s3", "url"]
    source_link: str
    rank: int


class ConversationMetaOutput(BaseSchema):
    id: str
    title: str
    create_time: float
    model: str
    bot_id: str | None


class Conversation(BaseSchema):
    id: str
    title: str
    create_time: float
    message_map: dict[str, MessageOutput]
    last_message_id: str
    bot_id: str | None
    should_continue: bool


class NewTitleInput(BaseSchema):
    new_title: str


class ProposedTitle(BaseSchema):
    title: str