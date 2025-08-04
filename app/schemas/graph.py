"""This file contains the graph schema for the application."""

import re
import uuid
from typing import Annotated, Any

from langgraph.graph.message import add_messages
from langgraph.managed import RemainingSteps
from langgraph.prebuilt.chat_agent_executor import AgentState, AgentStatePydantic
from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class GraphState(AgentState):
    """State definition for the LangGraph Agent/Workflow."""
    session_id: str #= Field(..., description="The unique identifier for the conversation session")
    remaining_steps: RemainingSteps = 25
    # active_agent: str = Field(default_factory=str, description="Active agent")
    # task_description: str = Field(default_factory=str, description="Task description")

    # @field_validator("session_id")
    # @classmethod
    # def validate_session_id(cls, v: str) -> str:
    #     """Validate that the session ID is a valid UUID or follows safe pattern.

    #     Args:
    #         v: The thread ID to validate

    #     Returns:
    #         str: The validated session ID

    #     Raises:
    #         ValueError: If the session ID is not valid
    #     """
    #     # Try to validate as UUID
    #     try:
    #         uuid.UUID(v)
    #         return v
    #     except ValueError:
    #         # If not a UUID, check for safe characters only
    #         if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
    #             raise ValueError("Session ID must contain only alphanumeric characters, underscores, and hyphens")
    #         return v
