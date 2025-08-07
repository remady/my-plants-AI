"""This file contains the document schema for the uploaded by the user files."""

import re
import uuid
from typing import Annotated

from langgraph.graph.message import add_messages
from pydantic import UUID4, BaseModel, Field, FilePath, field_validator


class DocumentResponse(BaseModel):
    """State definition for the LangGraph Agent/Workflow."""

    id: UUID4 = Field(default_factory=uuid.uuid4, description="Record UUID")
    index_id: str = Field(default_factory=str, description="Uploaded document vector store index id")
    name: str = Field(..., description="Uploaded file name")
    size: int = Field(..., description="Uploaded file size in MB")
    extension: str = Field(..., description="Uploaded file extension")
