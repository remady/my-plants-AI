"""This file contains the session model for the application."""

import uuid
from typing import (
    TYPE_CHECKING,
    List,
)

from pydantic import UUID4
from sqlmodel import (
    Field,
    Relationship,
)

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Document(BaseModel, table=True):
    """Represents a document uploaded by a user, including metadata such as name, size, extension, and tags."""
    
    __tablename__ = "document"

    id: UUID4 = Field(default_factory=uuid.uuid4, primary_key=True)
    index_id: str = Field(default_factory=str, index=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str = Field(default="", index=True)
    size: int = Field(default=0)
    extension: str = Field(default="")
    tags: str = Field(default="")
    user: "User" = Relationship(back_populates="documents")