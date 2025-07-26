"""This file contains the document schema for the uploaded by the user files."""

import re
import uuid
from typing import Annotated

from langgraph.graph.message import add_messages
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    FilePath,
    UUID4
)


class DocumentResponse(BaseModel):
    """State definition for the LangGraph Agent/Workflow."""

    id: UUID4 = Field(default_factory=uuid.uuid4, description="Record UUID")
    name: str = Field(..., description="Uploaded file name")
    size: int = Field(..., description="Uploaded file size in MB")
    extension: str = Field(..., description="Uploaded file extension")
    

    