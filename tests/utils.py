"""Utility functions module."""

import json

from deepeval.test_case import ToolCall, Turn

from app.schemas.chat import ChatResponse, ChatResponseDebug, MessageDebug


def extract_tool_calls_from_message(message: MessageDebug) -> list[str]:
    """Extracts tool calls from a Message or DebugMessage object.

    Parameters
    ----------
    message : Message | DebugMessage
        The message object containing tool calls.

    Returns:
    -------
    list[str]
        A list of tool call objects extracted from the message.
    """
    return [
        ToolCall(name=tool_call["function"]["name"], input_parameters=json.loads(tool_call["function"]["arguments"]))
        for tool_call in message.tool_calls
    ]


def extract_rag_context(response: ChatResponse | ChatResponseDebug) -> list[str]:
    """Extracts the content of messages with the role 'tool' from a ChatResponse or ChatResponseDebug object.

    Parameters
    ----------
    response : ChatResponse | ChatResponseDebug
        The chat response containing messages.

    Returns:
    -------
    list[str]
        A list of strings containing the content of messages with the role 'tool'.
    """
    return [message.content for message in response.messages if message.role == "tool"]


def convert_chat_response_into_deepeval_turns(response: ChatResponse | ChatResponseDebug) -> list[Turn]:
    """Convert a ChatResponse or ChatResponseDebug object into a list of Deepeval Turn objects.

    Parameters
    ----------
    response : ChatResponse | ChatResponseDebug
        The chat response containing messages to be converted.

    Returns:
    -------
    list[Turn]
        A list of Turn objects representing each message in the response.
    """
    return [
        Turn(
            role=message.role if message.role in ("user", "assistant") else "assistant",
            content=message.content,
            tools_called=extract_tool_calls_from_message(message),
            retrieval_context=extract_rag_context(response),
        )
        for message in response.messages
    ]
