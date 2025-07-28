"""This file contains the chat schema for the application."""

import re
from datetime import datetime
from typing import (
    List,
    Literal,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
)


class Message(BaseModel):
    """Message model for chat endpoint.

    Attributes:
        role: The role of the message sender (user or assistant).
        content: The content of the message.
    """

    model_config = {"extra": "ignore"}

    role: Literal["user", "assistant", "system"] = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message", min_length=1, max_length=20000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate the message content.

        Args:
            v: The content to validate

        Returns:
            str: The validated content

        Raises:
            ValueError: If the content contains disallowed patterns
        """
        # Check for potentially harmful content
        if re.search(r"<script.*?>.*?</script>", v, re.IGNORECASE | re.DOTALL):
            raise ValueError("Content contains potentially harmful script tags")

        # Check for null bytes
        if "\0" in v:
            raise ValueError("Content contains null bytes")

        return v


class MessageDebug(Message):
    """Debug message model for chat endpoint.

    Attributes:
        content: The content of the message (can be empty).
        name: Optional name associated with the message.
        tool_calls: Optional list of tool call dictionaries.
    """
    model_config = {"extra": "ignore"}
    
    role: Literal["user", "assistant", "system", "tool"] = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message", min_length=0, max_length=20000)
    tool_calls: Optional[list[dict]] = Field(..., default_factory=list, description="Tool call log")


class ChatRequest(BaseModel):
    """Request model for chat endpoint.

    Attributes:
        messages: List of messages in the conversation.
    """

    model: str = Field(default="model", description="LLM model to be used in response")
    stream: bool = Field(default=False, description="Use SSE or not")
    messages: List[Message] = Field(
        ...,
        description="List of messages in the conversation",
        min_length=1,
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint.

    Attributes:
        messages: List of messages in the conversation.
    """

    message: Message = Field(..., description="List of messages in the conversation")
    model: str = Field(default="model", description="LLM model to be used in response")
    @computed_field(return_type=str)
    @property
    def created_at(self) -> str:    #noqa
        return datetime.now().isoformat()
    

class ChatResponseDebug(BaseModel):
    """Response model for chat endpoint in debug mode.

    Attributes:
        messages: List of debug messages in the conversation.
    """
    messages: List[MessageDebug] = Field(..., description="List of messages in the conversation in debug mode")


class StreamResponse(BaseModel):
    """Response model for streaming chat endpoint.

    Attributes:
        content: The content of the current chunk.
        done: Whether the stream is complete.
    """
    model: str = Field(default="model", description="LLM model to be used in response")
    message: Message
    done: bool = Field(default=False, description="Whether the stream is complete")
    
    @computed_field(return_type=str)
    @property
    def created_at(self) -> str:    #noqa
        return datetime.now().isoformat()


class StreamFinalResponse(BaseModel):
    """Final response model for streaming chat endpoint.

    Attributes:
        model: The LLM model used in the response.
        done: Whether the stream is complete.
        created_at: The timestamp when the response was created.
    """
    model: str = Field(default="model", description="LLM model to be used in response")
    done: bool = Field(default=True, description="Whether the stream is complete")
    @computed_field(return_type=str)
    @property
    def created_at(self) -> str:    #noqa
        return datetime.now().isoformat()
